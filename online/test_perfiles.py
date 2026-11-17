from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from online.models import Usuario, Preguntas

class PerfilesTests(TestCase):
    def setUp(self):
        cache.clear()
        self.cliente=Usuario.objects.create_user('cliente@test.invalid','cliente', 'OtraClave_493!')
        self.tecnico=Usuario.objects.create_user('tecnico@test.invalid','tecnico', 'OtraClave_493!', tecnico=True)
        self.admin=Usuario.objects.create_user('admin@test.invalid','administrador', 'OtraClave_493!', admin=True)
        self.datos={'Titulo':'Falla al iniciar','Pregunta':'El juego se cierra','plataforma':'pc','categoria':'software','prioridad':'media'}

    def invitado(self):
        self.client.post(reverse('invitado'),{'nombre':'Visitante'})
        return Usuario.objects.get(pk=self.client.session['_auth_user_id'])

    def test_guest_entry_is_post_and_unusable_password(self):
        self.client.get(reverse('invitado'))
        self.assertEqual(Usuario.objects.filter(es_invitado=True).count(),0)
        guest=self.invitado()
        self.assertFalse(guest.has_usable_password())
        self.assertFalse(guest.admin or guest.tecnico)

    def test_guest_second_open_ticket_blocked_and_existing_accessible(self):
        guest=self.invitado(); url=reverse('inicio',args=[guest.pk])
        self.client.post(url,self.datos)
        response=self.client.post(url,self.datos)
        self.assertEqual(Preguntas.objects.filter(Usuario=guest).count(),1)
        self.assertContains(response,'máximo de 1')
        pregunta=Preguntas.objects.get(Usuario=guest)
        self.assertTrue(pregunta.origen_invitado)
        self.assertEqual(self.client.get(reverse('respuestas',args=[guest.pk,pregunta.pk])).status_code,200)

    def test_client_five_open_limit_and_closed_frees_slot(self):
        self.client.force_login(self.cliente);url=reverse('inicio',args=[self.cliente.pk])
        for _ in range(5):self.client.post(url,self.datos)
        self.assertContains(self.client.post(url,self.datos),'máximo de 5')
        self.assertEqual(Preguntas.objects.filter(Usuario=self.cliente).count(),5)
        first=Preguntas.objects.filter(Usuario=self.cliente).first();first.estado='cerrado';first.save()
        self.client.post(url,self.datos)
        self.assertEqual(Preguntas.objects.filter(Usuario=self.cliente).count(),6)

    def test_guest_ia_cap_cannot_be_bypassed_by_post(self):
        guest=self.invitado();url=reverse('inicio',args=[guest.pk])
        data={'accion':'asistente','buscar_ayuda':'Ayuda con PC','consentimiento':'on'}
        with patch('online.views.AsistenteIA.generar_respuesta_automatica',return_value='Sugerencia') as call:
            for _ in range(3):
                cache.clear();self.client.post(url,data)
            self.assertEqual(call.call_count,2)
        guest.refresh_from_db();self.assertEqual(guest.consultas_ia_invitado,2)

    def test_invalid_consent_does_not_consume_ia(self):
        guest=self.invitado()
        self.client.post(reverse('inicio',args=[guest.pk]),{'accion':'asistente','buscar_ayuda':'Ayuda'})
        guest.refresh_from_db();self.assertEqual(guest.consultas_ia_invitado,0)

    def test_guest_registration_keeps_ticket_and_origin(self):
        guest=self.invitado()
        self.client.post(reverse('inicio',args=[guest.pk]),self.datos)
        result=self.client.post(reverse('Register'),{'usuario':'convertido','correo':'convertido@test.invalid','rut':'','password':'ClaveNueva_493!','password_2':'ClaveNueva_493!'})
        self.assertEqual(result.status_code,302)
        guest.refresh_from_db();self.assertFalse(guest.es_invitado)
        self.assertEqual(guest.usuario,'convertido')
        self.assertTrue(Preguntas.objects.get(Usuario=guest).origen_invitado)

    def test_other_session_cannot_access_guest_conversation(self):
        guest=self.invitado();self.client.post(reverse('inicio',args=[guest.pk]),self.datos)
        pregunta=Preguntas.objects.get(Usuario=guest)
        outsider=Client();outsider.force_login(self.cliente)
        self.assertEqual(outsider.get(reverse('respuestas',args=[guest.pk,pregunta.pk])).status_code,302)

    def test_staff_distinct_interface_and_restricted_admin_menu(self):
        self.client.force_login(self.tecnico)
        page=self.client.get(reverse('administracion'))
        self.assertContains(page,'Panel técnico');self.assertContains(page,'theme-tecnico')
        self.assertNotContains(page,'Todas las cuentas')
        self.assertEqual(self.client.get(reverse('gestion_usuarios')).status_code,302)
        self.client.force_login(self.admin)
        page=self.client.get(reverse('administracion'))
        self.assertContains(page,'Panel de administración');self.assertContains(page,'theme-admin')
        self.assertContains(page,'Técnicos inscritos')

    def test_technician_filters_and_guest_excluded_from_accounts(self):
        guest=self.invitado();self.client.force_login(self.admin)
        page=self.client.get(reverse('gestion_usuarios')+'?tipo=tecnicos')
        self.assertEqual(list(page.context['Usuarios'].object_list),[self.tecnico])
        self.assertNotIn(guest,list(self.client.get(reverse('gestion_usuarios')).context['Usuarios'].object_list))

    def test_detail_is_escaped_and_has_accessible_dialog(self):
        question=Preguntas.objects.create(Usuario=self.cliente,Titulo='<script>alert(1)</script>',Pregunta='Detalle')
        self.client.force_login(self.cliente)
        page=self.client.get(reverse('inicio',args=[self.cliente.pk]))
        self.assertContains(page,'&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertContains(page,f'aria-labelledby="titulo-{question.pk}"')
        self.assertNotContains(page,'<script>alert(1)</script>')
