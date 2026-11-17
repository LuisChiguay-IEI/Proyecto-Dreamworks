from django.urls import path
from . import views
app_name = 'peliculas'
urlpatterns = [
    path('', views.catalogo, name='catalogo'),
    path('mi-lista/<str:seccion>/', views.mi_lista, name='mi_lista'),
    path('<int:pk>/favorito/', views.favorito, name='favorito'),
    path('gestion/', views.gestion, name='gestion'),
    path('gestion/nueva/', views.editar, name='crear'),
    path('gestion/<int:pk>/editar/', views.editar, name='editar'),
    path('gestion/<int:pk>/eliminar/', views.eliminar, name='eliminar'),
    path('<int:pk>/resena/<int:resena_id>/visibilidad/', views.visibilidad_resena, name='visibilidad_resena'),
    path('<int:pk>/resena/<int:resena_id>/eliminar/', views.eliminar_resena, name='eliminar_resena'),
    path('<int:pk>/', views.detalle, name='detalle'),
    path('<int:pk>/consultar/', views.consultar, name='consultar'),
]
