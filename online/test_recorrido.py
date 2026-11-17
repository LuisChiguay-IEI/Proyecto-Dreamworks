from django.test import TestCase
from django.urls import reverse
from online.models import Usuario

class RecorridoCentroAyudaTests(TestCase):
    def test_catalogo_envia_al_acceso_compartido(self):
        page = self.client.get(reverse('peliculas:catalogo'))
        self.assertContains(page, 'href="/bienvenida/">Centro de ayuda')
        response = self.client.get(reverse('index'))
        self.assertEqual(response.url, '/Login/?next=/bienvenida/')
        login = self.client.get(response.url)
        self.assertContains(login, 'Continuar como invitado')
        self.assertContains(login, '/Register/?next=/bienvenida/')

    def test_registro_conserva_destino_del_centro(self):
        response = self.client.post(reverse('Register') + '?next=/bienvenida/', {
            'usuario': 'prueba_recorrido', 'correo': 'ruta@example.invalid', 'rut': '',
            'password': 'ClaveNueva_493!', 'password_2': 'ClaveNueva_493!', 'next': '/bienvenida/'})
        self.assertRedirects(response, '/bienvenida/', fetch_redirect_response=False)
        follow = self.client.get(response.url)
        self.assertEqual(follow.url, reverse('inicio', args=[Usuario.objects.get(usuario='prueba_recorrido').pk]))

    def test_invitado_entra_en_su_espacio(self):
        response = self.client.post(reverse('invitado'), {'nombre':'Visitante'})
        guest = Usuario.objects.get(usuario__startswith='invitado_')
        self.assertRedirects(response, reverse('inicio', args=[guest.pk]))
        self.assertContains(self.client.get(response.url), 'Estás explorando como invitado')
