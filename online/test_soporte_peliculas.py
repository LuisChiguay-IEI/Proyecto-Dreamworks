from django.test import TestCase
from django.urls import reverse
from online.models import Preguntas, Usuario

class SoportePeliculasTests(TestCase):
    def setUp(self):
        self.user = Usuario.objects.create_user('peliculas@example.invalid', 'usuario-peliculas', 'ClaveSegura_349!')
        self.admin = Usuario.objects.create_user('adminpelis@example.invalid', 'admin-peliculas', 'ClaveSegura_349!', admin=True)
        self.archivada = Preguntas.objects.create(Usuario=self.user, Titulo='Consulta antigua de juego', Pregunta='PC falla', archivada=True)
    def test_formulario_de_peliculas_y_consulta_archivada_no_ocupa_cupo(self):
        self.client.force_login(self.user)
        url=reverse('inicio',args=[self.user.pk])
        page=self.client.get(url)
        self.assertNotContains(page, 'Plataforma de juego')
        self.assertNotContains(page, 'Consulta antigua de juego')
        self.assertContains(page, 'Reproducción')
        result=self.client.post(url, {'Titulo':'Problema de reproducción','Pregunta':'No carga la película', 'categoria':'reproduccion'})
        self.assertEqual(result.status_code,302)
        self.assertTrue(Preguntas.objects.filter(Usuario=self.user,categoria='reproduccion',archivada=False).exists())
    def test_panel_administrador_oculta_archivadas_y_accede_a_gestion(self):
        self.client.force_login(self.admin)
        page=self.client.get(reverse('administracion'))
        self.assertNotContains(page, 'Consulta antigua de juego')
        self.assertContains(page, reverse('peliculas:gestion'))
        self.assertTrue(Preguntas.objects.filter(pk=self.archivada.pk).exists())
