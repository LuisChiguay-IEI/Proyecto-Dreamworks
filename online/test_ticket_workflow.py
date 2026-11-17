from django.test import TestCase
from django.urls import reverse
from online.models import Usuario, Preguntas, Respuesta
from online.forms import PreguntasForm


class TicketWorkflowTests(TestCase):
    def setUp(self):
        self.owner = Usuario.objects.create(usuario='owner_flow', correo='owner@flow.test')
        self.other = Usuario.objects.create(usuario='other_flow', correo='other@flow.test')
        self.tech = Usuario.objects.create(usuario='tech_flow', correo='tech@flow.test', tecnico=True)
        self.admin = Usuario.objects.create(usuario='admin_flow', correo='admin@flow.test', admin=True)
        self.q = Preguntas.objects.create(Titulo='Prueba', Pregunta='Detalle', Usuario=self.owner)
        self.r = Respuesta.objects.create(Respuesta='Solución', id_Pregunta=self.q, Usuario=self.tech, es_solucion=True)
        self.chat = reverse('respuestas', args=[self.owner.pk, self.q.pk])

    def test_client_cannot_assign_priority(self):
        self.assertNotIn('prioridad', PreguntasForm().fields)
        self.client.force_login(self.owner)
        self.client.post(reverse('inicio', args=[self.owner.pk]), {'Titulo':'Nuevo', 'Pregunta':'Detalle', 'plataforma':'pc', 'categoria':'software', 'prioridad':'alta', 'estado':'cerrado'})
        q = Preguntas.objects.latest('pk')
        self.assertEqual(q.prioridad,'media')
        self.assertEqual(q.estado,'abierto')
        self.assertEqual(self.client.post(reverse('gestionar_caso',args=[self.q.pk]),{'estado':'cerrado','prioridad':'alta'}).status_code,403)

    def test_staff_manage_and_reopen_case(self):
        for staff in (self.tech,self.admin):
            self.client.force_login(staff)
            for state in ('en_proceso','resuelto','cerrado','abierto'):
                response = self.client.post(reverse('gestionar_caso',args=[self.q.pk]),{'estado':state,'prioridad':'alta'})
                self.assertEqual(response.status_code,302)
                self.q.refresh_from_db()
                self.assertEqual(self.q.estado,state)
                self.assertEqual(self.q.prioridad,'alta')
                self.assertEqual(self.q.fecha_resolucion is not None,state in ('resuelto','cerrado'))
            self.assertEqual(self.client.post(reverse('gestionar_caso',args=[self.q.pk]),{'estado':'inventado','prioridad':'alta'}).status_code,400)

    def test_owner_closes_and_chat_rejects_new_messages(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(reverse('cerrar_caso',args=[self.q.pk])).status_code,403)
        self.client.force_login(self.owner)
        self.assertContains(self.client.get(self.chat),'Mi asunto quedó resuelto')
        self.client.post(reverse('cerrar_caso',args=[self.q.pk]))
        self.q.refresh_from_db();self.assertEqual(self.q.estado,'cerrado')
        self.assertIsNotNone(self.q.fecha_resolucion)
        self.assertNotContains(self.client.get(self.chat),'Enviar respuesta')
        for user in (self.owner,self.tech):
            self.client.force_login(user)
            self.client.post(self.chat,{'Respuesta':'No debe guardarse'})
        self.assertEqual(Respuesta.objects.count(),1)

    def test_only_owner_rates_selected_solution_and_cannot_remove_mark(self):
        rate = reverse('valorar_solucion',args=[self.q.pk,self.r.pk])
        for user in (self.other,self.tech,self.admin):
            self.client.force_login(user)
            self.assertEqual(self.client.post(rate,{'valoracion':'util'}).status_code,403)
        self.client.force_login(self.owner)
        response=self.client.get(self.chat)
        self.assertNotContains(response,'Quitar marca de solución')
        self.assertContains(response,'✓ Útil');self.assertContains(response,'✗ Insatisfactoria')
        for vote in ('util','insatisfactoria'):
            self.assertEqual(self.client.post(rate,{'valoracion':vote}).status_code,302)
            self.r.refresh_from_db();self.assertEqual(self.r.valoracion_cliente,vote)
            self.assertTrue(self.r.es_solucion)
        self.assertEqual(self.client.post(rate,{'valoracion':'inventado'}).status_code,400)
        self.assertEqual(self.client.post(reverse('marcar_solucion',args=[self.q.pk,self.r.pk]),{'accion':'retirar'}).status_code,403)
        self.client.force_login(self.tech)
        self.assertContains(self.client.get(self.chat),'Quitar marca de solución')
        self.client.post(reverse('marcar_solucion',args=[self.q.pk,self.r.pk]),{'accion':'retirar'})
        self.r.refresh_from_db();self.assertFalse(self.r.es_solucion)

    def test_ratings_reject_other_ticket_and_unselected_answer(self):
        self.client.force_login(self.owner)
        self.r.es_solucion=False;self.r.save()
        self.assertEqual(self.client.post(reverse('valorar_solucion',args=[self.q.pk,self.r.pk]),{'valoracion':'util'}).status_code,404)
        for route,args in [('valorar_solucion',[self.q.pk,self.r.pk]),('cerrar_caso',[self.q.pk]),('gestionar_caso',[self.q.pk])]:
            self.assertEqual(self.client.get(reverse(route,args=args)).status_code,405)
