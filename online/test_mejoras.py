from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache
from online.models import Usuario, Preguntas, Respuesta
from online.forms import RegisterForm
from online.ia_utils import AsistenteIA
from administracion.services import estadisticas

class MejorasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cliente=Usuario.objects.create_user('cliente@ejemplo.cl','cliente','ClavePrueba2026!')
        cls.admin=Usuario.objects.create_user('admin@ejemplo.cl','admin','ClavePrueba2026!',admin=True)
        cls.tecnico=Usuario.objects.create_user('tecnico@ejemplo.cl','tecnico','ClavePrueba2026!',tecnico=True)
        cls.pregunta=Preguntas.objects.create(Titulo='Problema de video',Pregunta='No inicia',Usuario=cls.cliente)
    def setUp(self):
        cache.clear()
    def registro(self,**extra):
        datos=dict(usuario='nuevo',correo='nuevo@ejemplo.cl',rut='12.345.678-5',password='NuevaClave2026!',password_2='NuevaClave2026!')
        datos.update(extra)
        return RegisterForm(datos)
    def test_rut_valido(self):
        form=self.registro();self.assertTrue(form.is_valid(),form.errors)
        self.assertEqual(form.cleaned_data['rut'],'12345678-5')
    def test_rut_invalido(self):
        self.assertIn('rut',self.registro(rut='12345678-9').errors)
    def test_correo_duplicado(self):
        self.assertIn('correo',self.registro(correo='CLIENTE@ejemplo.cl').errors)
    def test_usuario_duplicado(self):
        self.assertIn('usuario',self.registro(usuario='cliente').errors)
    def test_rut_duplicado(self):
        self.cliente.rut='12.345.678-5';self.cliente.save()
        self.assertIn('rut',self.registro().errors)
    def test_registro_hash(self):
        form=self.registro();self.assertTrue(form.is_valid(),form.errors)
        user=form.save();self.assertTrue(user.check_password('NuevaClave2026!'))
        self.assertNotEqual(user.password,'NuevaClave2026!')
    def test_crear_ignora_autor_adulterado(self):
        self.client.force_login(self.cliente)
        response=self.client.post(reverse('inicio',args=[self.cliente.pk]),{'Titulo':'Nueva','Pregunta':'Detalle','categoria':'hardware','prioridad':'alta','plataforma':'pc','Usuario':self.admin.pk,'Fecha_creacion':'2000-01-01','estado':'cerrado'})
        self.assertEqual(response.status_code,302)
        pregunta=Preguntas.objects.latest('pk');self.assertEqual(pregunta.Usuario,self.cliente)
        self.assertEqual(pregunta.estado,'abierto');self.assertEqual(pregunta.categoria,'hardware')
        self.assertGreater(pregunta.Fecha_creacion,timezone.now()-timedelta(minutes=1))
    def test_error_formulario_conservado(self):
        self.client.force_login(self.cliente)
        response=self.client.post(reverse('inicio',args=[self.cliente.pk]),{'Pregunta':'Sin título'})
        self.assertIn('Titulo',response.context['form'].errors);self.assertContains(response,'Sin título')
    def test_limite_respuesta(self):
        self.client.force_login(self.cliente)
        response=self.client.post(reverse('respuestas',args=[self.cliente.pk,self.pregunta.pk]),{'Respuesta':'x'*2001})
        self.assertIn('Respuesta',response.context['form'].errors);self.assertEqual(Respuesta.objects.count(),0)
    def test_tecnico_no_modifica_ni_borra(self):
        self.client.force_login(self.tecnico)
        for nombre,args in [('modificar_pregunta',[self.pregunta.pk]),('borrar_pregunta',[self.admin.pk,self.pregunta.pk])]:
            self.client.post(reverse(nombre,args=args),{'Titulo':'Alterado'})
        self.pregunta.refresh_from_db();self.assertEqual(self.pregunta.Titulo,'Problema de video')
    def test_admin_no_se_desactiva_ni_degrada(self):
        self.client.force_login(self.admin)
        for campos in ({'admin':'on'},{'activo':'on'},{}):
            self.client.post(reverse('gestion_usuarios'),{'Userid':self.admin.pk,**campos})
            self.admin.refresh_from_db();self.assertTrue(self.admin.activo);self.assertTrue(self.admin.admin)
    def test_navegacion_sin_loop(self):
        for user in (self.cliente,self.tecnico,self.admin):
            self.client.force_login(user);response=self.client.get(reverse('index'),follow=True)
            self.assertEqual(response.status_code,200);self.assertLessEqual(len(response.redirect_chain),1)
            self.assertNotContains(response,'window.location')
    def test_panel_sin_ia(self):
        self.client.force_login(self.admin)
        with patch('online.ia_utils.OpenAI') as proveedor:
            self.assertEqual(self.client.get(reverse('administracion')).status_code,200)
            proveedor.assert_not_called()
    def test_metrica_primera_respuesta_tecnica(self):
        inicio=timezone.now()-timedelta(hours=4);self.pregunta.Fecha_creacion=inicio;self.pregunta.save()
        Respuesta.objects.create(Respuesta='Detalle',id_Pregunta=self.pregunta,Usuario=self.cliente,FechaHora=inicio+timedelta(minutes=10))
        self.assertEqual(estadisticas()['preguntas_sin_respuesta'],1)
        self.assertEqual(estadisticas()['porcentaje_resueltas'],0)
        Respuesta.objects.create(Respuesta='Atención',id_Pregunta=self.pregunta,Usuario=self.tecnico,FechaHora=inicio+timedelta(hours=2))
        self.assertEqual(estadisticas()['tiempo_promedio_respuesta'],'2.00 horas')
        self.assertEqual(estadisticas()['preguntas_sin_respuesta'],0)
    def test_resolucion_y_reapertura(self):
        self.client.force_login(self.admin)
        datos={'Titulo':'Actualizado','Pregunta':'Detalle','categoria':'software','prioridad':'alta','plataforma':'pc','estado':'resuelto','Usuario':self.admin.pk}
        self.client.post(reverse('modificar_pregunta',args=[self.pregunta.pk]),datos)
        self.pregunta.refresh_from_db();self.assertEqual(self.pregunta.Usuario,self.cliente)
        self.assertIsNotNone(self.pregunta.fecha_resolucion)
        datos['estado']='abierto';self.client.post(reverse('modificar_pregunta',args=[self.pregunta.pk]),datos)
        self.pregunta.refresh_from_db();self.assertIsNone(self.pregunta.fecha_resolucion)
    @override_settings(GEMINI_API_KEY='')
    def test_ia_sin_clave(self):
        self.assertIn('no está configurada',AsistenteIA().generar_respuesta_automatica('Ayuda'))
    @override_settings(GEMINI_API_KEY='prueba')
    def test_timeout_seguro(self):
        with patch.object(AsistenteIA,'_client',side_effect=TimeoutError('SECRETO_INTERNO')):
            texto=AsistenteIA().generar_respuesta_automatica('Ayuda')
            self.assertNotIn('SECRETO_INTERNO',texto);self.assertIn('no está disponible',texto)
    def test_consentimiento_y_limite_ia(self):
        self.client.force_login(self.cliente);ruta=reverse('inicio',args=[self.cliente.pk])
        with patch.object(AsistenteIA,'generar_respuesta_automatica',return_value='Sugerencia de prueba') as generar:
            self.client.post(ruta,{'accion':'asistente','buscar_ayuda':'Ayuda'});generar.assert_not_called()
            datos={'accion':'asistente','buscar_ayuda':'Ayuda','consentimiento':'on'}
            self.assertContains(self.client.post(ruta,datos),'Sugerencia de prueba')
            self.client.post(ruta,datos);self.assertEqual(generar.call_count,1)
    def test_inexistente(self):
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(reverse('respuestas',args=[self.cliente.pk,99999])).status_code,404)
    def test_rutas_protegidas(self):
        for nombre,args in [('inicio',[self.cliente.pk]),('administracion',[]),('gestion_usuarios',[]),('analytics_ia',[]),('modificar_pregunta',[self.pregunta.pk]),('respuestas',[self.cliente.pk,self.pregunta.pk]),('borrar_pregunta',[self.cliente.pk,self.pregunta.pk]),('eliminar_usuario',[self.cliente.pk])]:
            response=self.client.get(reverse(nombre,args=args));self.assertEqual(response.status_code,302);self.assertIn('/Login/',response.url)
    def test_paginas_administrativas(self):
        self.client.force_login(self.admin)
        for nombre,args in [('gestion_usuarios',[]),('analytics_ia',[]),('modificar_pregunta',[self.pregunta.pk])]:
            response=self.client.get(reverse(nombre,args=args));self.assertEqual(response.status_code,200);self.assertContains(response,'Cerrar sesión')
    def test_filtros(self):
        self.client.force_login(self.admin)
        response=self.client.get(reverse('administracion'),{'categoria':'hardware'})
        self.assertEqual(len(response.context['Preguntas']),0)
