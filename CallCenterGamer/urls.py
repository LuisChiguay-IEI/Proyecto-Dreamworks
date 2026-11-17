from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from moduloPeliculas.views import catalogo
from online.views import GestionarCaso, CerrarCaso, ValorarSolucion, AccesoInvitado, Index, Inicio, RegisterView, LoginView, ViewRespuestas, logout_view, AgregarNotaInterna, MarcarSolucion
from administracion.views import NotasInternas, IndexAdmin, BorrarPregunta, GestionUsuarios, EliminarUsuario, ModificarPregunta, AnalyticsIA

urlpatterns = [
    path('peliculas/', include('moduloPeliculas.urls')),
    path('Consulta/<int:idPregunta>/gestion/', GestionarCaso, name='gestionar_caso'),
    path('Consulta/<int:idPregunta>/cerrar/', CerrarCaso, name='cerrar_caso'),
    path('Consulta/<int:idPregunta>/solucion/<int:idRespuesta>/valorar/', ValorarSolucion, name='valorar_solucion'),
    path('NotasInternas/', NotasInternas, name='notas_internas'),
    path('Consulta/<int:idPregunta>/nota/', AgregarNotaInterna, name='agregar_nota_interna'),
    path('Consulta/<int:idPregunta>/solucion/<int:idRespuesta>/', MarcarSolucion, name='marcar_solucion'),
    path('Invitado/', AccesoInvitado, name='invitado'),
    path('admin/', admin.site.urls),
    path('', catalogo, name='portada_catalogo'),
    path('bienvenida/', Index, name='index'),
    path('Administracion/', IndexAdmin, name='administracion'),
    path('AnalyticsIA/', AnalyticsIA, name='analytics_ia'),
    path('Login/', LoginView.as_view(), name='Login'),
    path('Register/', RegisterView.as_view(), name='Register'),
    path('Inicio/<int:id>/', Inicio, name='inicio'),

    # Usar vista personalizada para logout
    path('Logout/', logout_view, name='Logout'),

    path('Respuesta/<int:idUser>/<int:idPregunta>/', ViewRespuestas, name='respuestas'),
    path('BorrarPregunta/<int:idUser>/<int:idPregunta>/', BorrarPregunta, name='borrar_pregunta'),
    path('GestionUsuarios/', GestionUsuarios, name='gestion_usuarios'),
    path('EliminarUsuario/<int:idUser>/', EliminarUsuario, name='eliminar_usuario'),
    path('ModificarPregunta/<int:idPregunta>/', ModificarPregunta, name='modificar_pregunta'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
