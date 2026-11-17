from django.test import TestCase, Client
from django.urls import reverse
from django.db import IntegrityError, transaction
from online.models import Usuario, Preguntas, Respuesta, NotaInterna
from online.forms import PreguntasForm

class InnovacionesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dueno=Usuario.objects.create_user('dueno@prueba.cl','dueno','ClavePrueba2026!')
        cls.otro=Usuario.objects.create_user('otro@prueba.cl','otro','ClavePrueba2026!')
        cls.tecnico=Usuario.objects.create_user('tecnico@prueba.cl','tecnico','ClavePrueba2026!',tecnico=True)
        cls.admin=Usuario.objects.create_user('admin@prueba.cl','admin','ClavePrueba2026!',admin=True)
        cls.pregunta=Preguntas.objects.create(Titulo='No inicia',Pregunta='Error al jugar',Usuario=cls.dueno)
        cls.ajena=Preguntas.objects.create(Titulo='Ajena',Pregunta='Otro error',Usuario=cls.otro)
        cls.r1=Respuesta.objects.create(Respuesta='Actualiza los controladores',id_Pregunta=cls.pregunta,Usuario=cls.tecnico)
        cls.r2=Respuesta.objects.create(Respuesta='Reinstala el juego',id_Pregunta=cls.pregunta,Usuario=cls.admin)
        cls.r_ajena=Respuesta.objects.create(Respuesta='De otro ticket',id_Pregunta=cls.ajena,Usuario=cls.tecnico)
        cls.nota=NotaInterna.objects.create(pregunta=cls.pregunta,autor=cls.tecnico,contenido='NOTA-PRIVADA-987')
    def conversacion(self):
        return reverse('respuestas',args=[self.dueno.pk,self.pregunta.pk])
    def solucion(self,respuesta=None):
        return reverse('marcar_solucion',args=[self.pregunta.pk,(respuesta or self.r1).pk])
    def nota_url(self):
        return reverse('agregar_nota_interna',args=[self.pregunta.pk])
    def test_plataformas_se_guardan_y_muestran(self):
        self.client.force_login(self.dueno)
        for valor,etiqueta in [('pc','PC'),('playstation','PlayStation'),('xbox','Xbox'),('nintendo','Nintendo'),('movil','Móvil')]:
            response=self.client.post(reverse('inicio',args=[self.dueno.pk]),{'Titulo':'Prueba '+etiqueta,'Pregunta':'Descripción','plataforma':valor,'categoria':'software','prioridad':'media'})
            self.assertEqual(response.status_code,302)
            pregunta=Preguntas.objects.latest('pk');self.assertEqual(pregunta.plataforma,valor)
            response=self.client.get(reverse('respuestas',args=[self.dueno.pk,pregunta.pk]))
            self.assertContains(response,'Plataforma: '+etiqueta)
            pregunta.estado='cerrado';pregunta.save()  # liberar cupo para probar la siguiente plataforma
    def test_plataforma_invalida(self):
        form=PreguntasForm({'Titulo':'Prueba','Pregunta':'Detalle','categoria':'otros','prioridad':'media','plataforma':'inventada'})
        self.assertFalse(form.is_valid());self.assertIn('plataforma',form.errors)
    def test_anteriores_sin_especificar(self):
        self.assertEqual(self.pregunta.plataforma,'sin_especificar')
    def test_cliente_no_recibe_notas_ni_formulario(self):
        self.client.force_login(self.dueno);response=self.client.get(self.conversacion())
        self.assertNotContains(response,'NOTA-PRIVADA-987')
        self.assertNotContains(response,'Guardar nota interna')
        self.assertNotIn('notas_internas',response.context)
        self.assertNotIn('nota_form',response.context)
    def test_cliente_no_puede_escribir_nota(self):
        self.client.force_login(self.dueno)
        response=self.client.post(self.nota_url(),{'contenido':'No autorizado'})
        self.assertEqual(response.status_code,403);self.assertEqual(NotaInterna.objects.count(),1)
    def test_personal_puede_ver_y_escribir_notas(self):
        for user in (self.tecnico,self.admin):
            self.client.force_login(user)
            self.assertContains(self.client.get(self.conversacion()),'NOTA-PRIVADA-987')
            response=self.client.post(self.nota_url(),{'contenido':'Nota '+user.usuario,'autor':self.dueno.pk,'pregunta':self.ajena.pk})
            self.assertEqual(response.status_code,302)
            nota=NotaInterna.objects.latest('pk');self.assertEqual(nota.autor,user);self.assertEqual(nota.pregunta,self.pregunta)
        self.assertEqual(Respuesta.objects.count(),3)
    def test_nota_invalida_conserva_error(self):
        self.client.force_login(self.tecnico)
        response=self.client.post(self.nota_url(),{'contenido':''})
        self.assertEqual(response.status_code,200);self.assertIn('contenido',response.context['nota_form'].errors)
        self.assertEqual(NotaInterna.objects.count(),1)
    def test_limite_nota(self):
        self.client.force_login(self.admin)
        response=self.client.post(self.nota_url(),{'contenido':'x'*2001})
        self.assertIn('contenido',response.context['nota_form'].errors)
    def test_notas_escapan_html(self):
        NotaInterna.objects.create(pregunta=self.pregunta,autor=self.admin,contenido='<script>alert(1)</script>')
        self.client.force_login(self.tecnico)
        response=self.client.get(self.conversacion())
        self.assertContains(response,'&lt;script&gt;');self.assertNotContains(response,'<script>alert(1)</script>')
    def test_solucion_dueno_y_reemplazo_por_personal(self):
        self.client.force_login(self.dueno)
        self.assertEqual(self.client.post(self.solucion()).status_code,302)
        self.r1.refresh_from_db();self.assertTrue(self.r1.es_solucion)
        self.assertContains(self.client.get(self.conversacion()),'Respuesta marcada como solución')
        self.assertEqual(self.client.post(self.solucion(self.r2)).status_code,403)
        self.client.force_login(self.tecnico)
        self.client.post(self.solucion(self.r2))
        self.r1.refresh_from_db();self.r2.refresh_from_db()
        self.assertFalse(self.r1.es_solucion);self.assertTrue(self.r2.es_solucion)
        self.pregunta.refresh_from_db();self.assertEqual(self.pregunta.estado,'abierto')
    def test_quitar_marca(self):
        self.client.force_login(self.dueno)
        self.client.post(self.solucion())
        self.assertEqual(self.client.post(self.solucion(),{'accion':'retirar'}).status_code,403)
        self.client.force_login(self.tecnico)
        self.client.post(self.solucion(),{'accion':'retirar'})
        self.assertFalse(Respuesta.objects.filter(id_Pregunta=self.pregunta,es_solucion=True).exists())
    def test_otro_cliente_no_puede_marcar_solucion(self):
        for user in (self.otro,):
            self.client.force_login(user)
            self.assertEqual(self.client.post(self.solucion()).status_code,403)
        self.assertFalse(Respuesta.objects.filter(es_solucion=True).exists())
    def test_respuesta_de_otra_consulta_rechazada(self):
        self.client.force_login(self.dueno)
        self.assertEqual(self.client.post(self.solucion(self.r_ajena)).status_code,404)
    def test_solucion_unica_en_base_de_datos(self):
        self.r1.es_solucion=True;self.r1.save()
        with self.assertRaises(IntegrityError),transaction.atomic():
            self.r2.es_solucion=True;self.r2.save()
    def test_acciones_solo_post(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(self.nota_url()).status_code,405)
        self.client.force_login(self.dueno)
        self.assertEqual(self.client.get(self.solucion()).status_code,405)
    def test_anonimo_redirigido(self):
        self.assertEqual(self.client.post(self.nota_url(),{'contenido':'texto'}).status_code,302)
        self.assertEqual(self.client.post(self.solucion()).status_code,302)
    def test_csrf_obligatorio(self):
        cliente=Client(enforce_csrf_checks=True);cliente.force_login(self.dueno)
        self.assertEqual(cliente.post(self.solucion()).status_code,403)
        cliente.force_login(self.tecnico)
        self.assertEqual(cliente.post(self.nota_url(),{'contenido':'texto'}).status_code,403)
    def test_personal_tiene_boton_solucion(self):
        self.client.force_login(self.tecnico)
        self.assertContains(self.client.get(self.conversacion()),'Marcar como solución')
