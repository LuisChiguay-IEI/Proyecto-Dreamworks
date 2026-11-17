from django.test import TestCase
from django.urls import reverse
from online.models import Usuario, Preguntas
from .models import Pelicula, Resena

class FlujoCatalogoTest(TestCase):
    def setUp(self):
        self.user = Usuario.objects.create_user(correo='prueba@example.invalid', usuario='prueba', password='Clave12345!')
        self.movie = Pelicula.objects.get(nombre='Shrek')
    def test_catalogo_y_busqueda(self):
        self.assertContains(self.client.get(reverse('peliculas:catalogo'), {'q': 'Shrek'}), 'Shrek')
        self.assertNotContains(self.client.get(reverse('peliculas:catalogo'), {'q': 'Shrek'}), 'Madagascar')
    def test_pelicula_consulta_y_enlace(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('peliculas:consultar', args=[self.movie.pk]))
        self.assertIn('pelicula=', response.url)
        response = self.client.post(reverse('inicio', args=[self.user.pk]), {'pelicula': self.movie.pk,'Titulo':'Consulta Shrek','Pregunta':'Una duda de la película','plataforma':'sin_especificar','categoria':'otros'})
        self.assertEqual(response.status_code,302)
        pregunta = Preguntas.objects.get(Titulo='Consulta Shrek')
        self.assertEqual(pregunta.pelicula, self.movie)
        response = self.client.get(reverse('respuestas', args=[self.user.pk,pregunta.pk]))
        self.assertContains(response, reverse('peliculas:detalle', args=[self.movie.pk]))
    def test_resena_debe_tener_autor_y_pelicula(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('peliculas:detalle',args=[self.movie.pk]), {'puntuacion':5,'comentario':'Muy entretenida'})
        self.assertEqual(response.status_code,302)
        self.assertTrue(Resena.objects.filter(usuario=self.user,pelicula=self.movie,puntuacion=5).exists())
    def test_consulta_anonima_guarda_pelicula(self):
        response = self.client.get(reverse('peliculas:consultar',args=[self.movie.pk]))
        self.assertRedirects(response, reverse('Login'))
        self.assertEqual(self.client.session['pelicula_pendiente'], self.movie.pk)

from io import BytesIO
from tempfile import TemporaryDirectory
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

class GestionPeliculasTest(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(correo='admin-test@example.invalid', usuario='admin-test', password='Clave12345!', admin=True)
        self.tecnico = Usuario.objects.create_user(correo='tech-test@example.invalid', usuario='tech-test', password='Clave12345!', tecnico=True)
        self.movie = Pelicula.objects.get(nombre='Shrek')
    def test_solo_administrador_accede_y_modifica(self):
        self.client.force_login(self.tecnico)
        for nombre, args in [('gestion', []), ('crear', []), ('editar', [self.movie.pk]), ('eliminar', [self.movie.pk])]:
            self.assertEqual(self.client.get(reverse('peliculas:' + nombre, args=args)).status_code, 403)
        self.assertEqual(self.client.post(reverse('peliculas:eliminar', args=[self.movie.pk])).status_code, 403)
        self.assertTrue(Pelicula.objects.filter(pk=self.movie.pk).exists())
    def test_crear_con_imagen_editar_y_eliminar(self):
        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            self.client.force_login(self.admin)
            image = BytesIO(); Image.new('RGB', (20, 30), 'blue').save(image, format='PNG')
            file = SimpleUploadedFile('afiche.png', image.getvalue(), content_type='image/png')
            data = {'nombre':'Nueva película','genero':'Comedia','clasificacion':'TE','duracion':90,'resena':'Una historia','estado':'estrenada','imagen_subida':file}
            self.assertEqual(self.client.post(reverse('peliculas:crear'), data).status_code, 302)
            movie = Pelicula.objects.get(nombre='Nueva película')
            self.assertTrue(movie.imagen_subida)
            self.assertContains(self.client.get(reverse('peliculas:catalogo')), movie.imagen_subida.url)
            self.assertContains(self.client.get(reverse('peliculas:detalle', args=[movie.pk])), movie.imagen_subida.url)
            data.pop('imagen_subida'); data['nombre'] = 'Película editada'
            self.assertEqual(self.client.post(reverse('peliculas:editar',args=[movie.pk]), data).status_code,302)
            movie.refresh_from_db(); self.assertEqual(movie.nombre, 'Película editada'); self.assertTrue(movie.imagen_subida)
            self.assertEqual(self.client.get(reverse('peliculas:eliminar',args=[movie.pk])).status_code,200)
            self.assertTrue(Pelicula.objects.filter(pk=movie.pk).exists())
            self.assertEqual(self.client.post(reverse('peliculas:eliminar',args=[movie.pk])).status_code,302)
            self.assertFalse(Pelicula.objects.filter(pk=movie.pk).exists())
    def test_conservar_afiche_al_cambiar_nombre(self):
        self.client.force_login(self.admin)
        data={'nombre':'Shrek actualizado','genero':'Comedia','clasificacion':'TE','duracion':90,'resena':'Prueba','estado':'estrenada'}
        self.assertEqual(self.client.post(reverse('peliculas:editar',args=[self.movie.pk]),data).status_code,302)
        self.movie.refresh_from_db()
        self.assertTrue(self.movie.cartel_url.endswith('/peliculas/shrek.jpg'))

from .models import Favorito, VisitaPelicula

class ListaPersonalTest(TestCase):
    def setUp(self):
        self.user = Usuario.objects.create_user(correo='uno@example.invalid', usuario='usuario-uno', password='Clave12345!')
        self.otro = Usuario.objects.create_user(correo='dos@example.invalid', usuario='usuario-dos', password='Clave12345!')
        self.invitado = Usuario.objects.create_user(correo='invitado@example.invalid', usuario='invitado-test', es_invitado=True)
        self.admin = Usuario.objects.create_user(correo='administrador@example.invalid', usuario='admin-test2', password='Clave12345!', admin=True)
        self.movie = Pelicula.objects.get(nombre='Shrek')
    def test_guardar_quitar_favoritos_y_privacidad(self):
        self.client.force_login(self.user)
        url = reverse('peliculas:favorito', args=[self.movie.pk])
        self.assertEqual(self.client.get(url).status_code,405)
        self.client.post(url, {'accion':'agregar'}); self.client.post(url, {'accion':'agregar'})
        self.assertEqual(Favorito.objects.filter(usuario=self.user, pelicula=self.movie).count(),1)
        self.assertContains(self.client.get(reverse('peliculas:mi_lista', args=['favoritos'])), 'Shrek')
        self.client.force_login(self.otro)
        self.assertNotContains(self.client.get(reverse('peliculas:mi_lista', args=['favoritos'])), 'Shrek')
        self.client.force_login(self.user)
        self.client.post(url, {'accion':'quitar'})
        self.assertFalse(Favorito.objects.filter(usuario=self.user, pelicula=self.movie).exists())
    def test_visitas_se_actualizan_y_separan_por_usuario(self):
        self.client.force_login(self.user)
        self.client.get(reverse('peliculas:detalle',args=[self.movie.pk]))
        self.client.get(reverse('peliculas:detalle',args=[self.movie.pk]))
        self.assertEqual(VisitaPelicula.objects.filter(usuario=self.user,pelicula=self.movie).count(),1)
        self.assertContains(self.client.get(reverse('peliculas:mi_lista',args=['historial'])),'Shrek')
        self.client.force_login(self.otro)
        self.assertNotContains(self.client.get(reverse('peliculas:mi_lista',args=['historial'])),'Shrek')
    def test_invitado_no_guarda_favoritos_ni_visitas(self):
        self.client.force_login(self.invitado)
        self.client.get(reverse('peliculas:detalle',args=[self.movie.pk]))
        self.client.post(reverse('peliculas:favorito',args=[self.movie.pk]),{'accion':'agregar'})
        self.assertFalse(VisitaPelicula.objects.filter(usuario=self.invitado).exists())
        self.assertFalse(Favorito.objects.filter(usuario=self.invitado).exists())
    def test_admin_y_cliente_entran_por_mismo_login(self):
        for u in (self.user,self.admin):
            self.client.logout()
            r=self.client.post(reverse('Login'),{'Usuario':u.usuario,'password':'Clave12345!'})
            self.assertRedirects(r,reverse('peliculas:catalogo'))
    def test_login_redireccion_interna_y_descarta_externa(self):
        self.client.post(reverse('Login')+'?next=/peliculas/mi-lista/favoritos/',{'Usuario':self.user.usuario,'password':'Clave12345!'})
        self.assertEqual(self.client.get(reverse('peliculas:mi_lista',args=['favoritos'])).status_code,200)
        self.client.logout()
        r=self.client.post(reverse('Login')+'?next=https://ejemplo.invalid/',{'Usuario':self.user.usuario,'password':'Clave12345!'})
        self.assertRedirects(r,reverse('peliculas:catalogo'))

class VistaAdministradorCatalogoTest(TestCase):
    def test_admin_edita_desde_ficha_sin_favoritos_ni_historial(self):
        admin=Usuario.objects.create_user('admin-vista@example.invalid','admin-vista','ClaveSegura_349!',admin=True)
        pelicula=Pelicula.objects.get(nombre='Shrek')
        self.client.force_login(admin)
        portada=self.client.get(reverse('peliculas:catalogo'))
        self.assertNotContains(portada, reverse('peliculas:mi_lista',args=['favoritos']))
        ficha=self.client.get(reverse('peliculas:detalle',args=[pelicula.pk]))
        self.assertContains(ficha, reverse('peliculas:editar',args=[pelicula.pk]))
        self.assertNotContains(ficha, reverse('peliculas:favorito',args=[pelicula.pk]))
        self.assertFalse(VisitaPelicula.objects.filter(usuario=admin).exists())
        self.assertRedirects(self.client.get(reverse('peliculas:mi_lista',args=['historial'])),reverse('peliculas:gestion'))
        self.assertEqual(self.client.post(reverse('peliculas:favorito',args=[pelicula.pk]),{'accion':'agregar'}).status_code,403)

class AccionesAdminPeliculaTest(TestCase):
    def test_admin_puede_ver_resenas_pero_no_publicar(self):
        admin=Usuario.objects.create_user('admin-resena@example.invalid','admin-resena','ClaveSegura_349!',admin=True)
        pelicula=Pelicula.objects.get(nombre='Shrek')
        self.client.force_login(admin)
        url=reverse('peliculas:detalle',args=[pelicula.pk])
        response=self.client.get(url)
        self.assertContains(response, 'Reseñas de la comunidad')
        self.assertNotContains(response,'Escribe tu reseña')
        self.assertNotContains(response,reverse('peliculas:consultar',args=[pelicula.pk]))
        self.assertContains(response,reverse('peliculas:editar',args=[pelicula.pk]))
        self.assertEqual(self.client.post(url,{'puntuacion':5,'comentario':'Prueba'}).status_code,403)
        self.assertFalse(Resena.objects.filter(usuario=admin).exists())

class ModeracionResenasTest(TestCase):
    def setUp(self):
        self.admin=Usuario.objects.create_user('mod-admin@example.invalid','mod-admin','ClaveSegura_349!',admin=True)
        self.cliente=Usuario.objects.create_user('mod-cliente@example.invalid','mod-cliente','ClaveSegura_349!')
        self.pelicula=Pelicula.objects.get(nombre='Shrek')
        self.resena=Resena.objects.create(pelicula=self.pelicula,usuario=self.cliente,puntuacion=4,comentario='Una opinión de prueba')
        self.detail=reverse('peliculas:detalle',args=[self.pelicula.pk])
        self.toggle=reverse('peliculas:visibilidad_resena',args=[self.pelicula.pk,self.resena.pk])
        self.delete=reverse('peliculas:eliminar_resena',args=[self.pelicula.pk,self.resena.pk])
    def test_ocultar_y_volver_a_mostrar(self):
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(self.detail),'Ocultar reseña')
        self.assertEqual(self.client.get(self.toggle).status_code,405)
        self.client.post(self.toggle,{'accion':'ocultar'})
        self.resena.refresh_from_db();self.assertFalse(self.resena.visible)
        self.assertContains(self.client.get(self.detail),'Oculta para el público')
        self.client.force_login(self.cliente)
        self.assertNotContains(self.client.get(self.detail),'Una opinión de prueba')
        self.assertEqual(self.client.post(self.toggle,{'accion':'mostrar'}).status_code,403)
        self.client.force_login(self.admin)
        self.client.post(self.toggle,{'accion':'mostrar'})
        self.client.force_login(self.cliente)
        self.assertContains(self.client.get(self.detail),'Una opinión de prueba')
    def test_eliminar_requiere_confirmacion_y_administrador(self):
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.post(self.delete).status_code,403)
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(self.delete),'eliminar definitivamente')
        self.assertTrue(Resena.objects.filter(pk=self.resena.pk).exists())
        self.client.post(self.delete)
        self.assertFalse(Resena.objects.filter(pk=self.resena.pk).exists())
