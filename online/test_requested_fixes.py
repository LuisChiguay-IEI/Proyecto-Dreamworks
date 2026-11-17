from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from online.models import Usuario, Preguntas, NotaInterna


class RequestedFixesTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create(usuario='admin_fix', correo='admin@fix.test', admin=True)
        self.tech = Usuario.objects.create(usuario='tech_fix', correo='tech@fix.test', tecnico=True)
        self.guest = Usuario.objects.create(usuario='guest_fix', correo='guest@fix.test', nombre='X', es_invitado=True)
        self.question = Preguntas.objects.create(Titulo='Prueba', Pregunta='Detalle', Usuario=self.guest,
            Fecha_creacion=timezone.now(), prioridad='alta', estado='en_proceso', origen_invitado=True)
        self.note = NotaInterna.objects.create(pregunta=self.question, autor=self.tech, contenido='Comentario reservado')

    def test_guest_conversion_updates_display_name_preserving_history(self):
        self.client.force_login(self.guest)
        response = self.client.post(reverse('Register'), {'usuario':'NuevoZ', 'correo':'nuevo@fix.test',
            'rut':'', 'password':'Dragon-Cuenta-93!', 'password_2':'Dragon-Cuenta-93!'})
        self.assertEqual(response.status_code, 302)
        self.guest.refresh_from_db()
        self.assertEqual(self.guest.usuario, 'NuevoZ')
        self.assertEqual(self.guest.nombre, 'NuevoZ')
        self.assertFalse(self.guest.es_invitado)
        self.question.refresh_from_db()
        self.assertEqual(self.question.Usuario_id, self.guest.pk)
        self.assertContains(self.client.get(response.url), 'NuevoZ')

    def test_technician_history_shows_colored_state_and_priority(self):
        self.client.force_login(self.tech)
        response = self.client.get(reverse('administracion'))
        for text in ('<th>Estado</th>', '<th>Prioridad</th>', 'state-en_proceso', 'priority-alta'):
            self.assertContains(response, text)

    def test_internal_notes_admin_only(self):
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse('notas_internas')), 'Comentario reservado')
        self.assertContains(self.client.get(reverse('administracion')), reverse('notas_internas'))
        for user in (self.tech, self.guest):
            self.client.force_login(user)
            response = self.client.get(reverse('notas_internas'))
            self.assertEqual(response.status_code, 302)
            self.assertNotIn(b'Comentario reservado', response.content)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('notas_internas')).status_code, 302)

    def test_sessions_expire_after_server_restart_for_all_roles(self):
        for user in (self.admin, self.tech, self.guest):
            self.client.force_login(user)
            session = self.client.session
            session['_server_session_id'] = 'launch-one'
            session.save()
            with override_settings(SERVER_SESSION_ID='launch-one'):
                self.client.get(reverse('index'))
                self.assertIn('_auth_user_id', self.client.session)
            with override_settings(SERVER_SESSION_ID='launch-two'):
                self.client.get(reverse('index'))
                self.assertNotIn('_auth_user_id', self.client.session)

    @override_settings(SERVER_SESSION_ID='launch-new')
    def test_old_sessions_without_launch_id_are_logged_out(self):
        self.client.force_login(self.admin)
        self.client.get(reverse('index'))
        self.assertNotIn('_auth_user_id', self.client.session)

    @override_settings(SERVER_SESSION_ID='launch-new')
    def test_login_is_stamped_and_remains_valid(self):
        self.admin.set_password('Dragon-Admin-93!')
        self.admin.save()
        response = self.client.post(reverse('Login'), {'Usuario':self.admin.usuario,'password':'Dragon-Admin-93!', 'remember_me':'on'})
        self.assertEqual(response.status_code,302)
        self.assertEqual(self.client.session['_server_session_id'],'launch-new')
        self.assertContains(self.client.get(reverse('administracion')), 'Panel de administración')
