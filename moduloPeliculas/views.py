from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q, Case, When, Value, IntegerField
from .models import Pelicula, Resena, Favorito, VisitaPelicula
from .forms import ResenaForm


def catalogo(request):
    peliculas = Pelicula.objects.annotate(orden_destacado=Case(When(nombre='Shrek', then=Value(0)), When(nombre='Cómo entrenar a tu dragón', then=Value(1)), When(nombre='Kung Fu Panda', then=Value(2)), default=Value(3), output_field=IntegerField())).order_by('orden_destacado', 'nombre')
    q = request.GET.get('q', '').strip()
    genero = request.GET.get('genero', '')
    if q:
        peliculas = peliculas.filter(Q(nombre__icontains=q) | Q(resena__icontains=q))
    if genero:
        peliculas = peliculas.filter(genero=genero)
    return render(request, 'peliculas/catalogo.html', {'peliculas': peliculas, 'q': q, 'genero': genero, 'generos': Pelicula.GENERO_CHOICES})


def detalle(request, pk):
    pelicula = get_object_or_404(Pelicula, pk=pk)
    registrado = request.user.is_authenticated and not request.user.es_invitado
    if request.method == 'GET' and registrado and not request.user.admin:
        VisitaPelicula.objects.update_or_create(usuario=request.user, pelicula=pelicula)
    es_favorita = registrado and Favorito.objects.filter(usuario=request.user, pelicula=pelicula).exists()
    form = ResenaForm(request.POST or None)
    if request.method == 'POST':
        if request.user.is_authenticated and request.user.admin:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden('Las reseñas están disponibles para clientes.')
        if not request.user.is_authenticated or request.user.es_invitado:
            messages.info(request, 'Inicia sesión con una cuenta registrada para escribir una reseña.')
            return redirect('Login')
        if form.is_valid():
            resena = form.save(commit=False)
            resena.usuario = request.user
            resena.pelicula = pelicula
            resena.save()
            messages.success(request, 'Tu reseña fue publicada.')
            return redirect('peliculas:detalle', pk=pk)
    resenas = pelicula.resenas.select_related('usuario')
    if not (request.user.is_authenticated and request.user.admin):
        resenas = resenas.filter(visible=True)
    return render(request, 'peliculas/detalle.html', {'pelicula': pelicula, 'form': form, 'es_favorita': es_favorita, 'resenas': resenas})


def consultar(request, pk):
    pelicula = get_object_or_404(Pelicula, pk=pk)
    if not request.user.is_authenticated:
        request.session['pelicula_pendiente'] = pelicula.pk
        return redirect('Login')
    if request.user.admin or request.user.tecnico:
        return redirect('administracion')
    from django.urls import reverse
    return redirect(reverse('inicio', args=[request.user.pk]) + '?pelicula=' + str(pelicula.pk) + '#formulario-pregunta')

from datetime import time
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from .forms import PeliculaAdminForm


def administrador_requerido(view):
    @wraps(view)
    @login_required
    def wrapped(request, *args, **kwargs):
        if not request.user.admin or not request.user.is_active:
            return HttpResponseForbidden('Esta sección es exclusiva del administrador.')
        return view(request, *args, **kwargs)
    return wrapped


@administrador_requerido
@require_http_methods(['POST'])
def visibilidad_resena(request, pk, resena_id):
    resena = get_object_or_404(Resena, pk=resena_id, pelicula_id=pk)
    accion = request.POST.get('accion')
    if accion not in ('ocultar', 'mostrar'):
        from django.http import HttpResponseBadRequest
        return HttpResponseBadRequest('Acción no válida.')
    resena.visible = accion == 'mostrar'
    resena.save(update_fields=['visible'])
    messages.success(request, 'Reseña visible de nuevo.' if resena.visible else 'Reseña ocultada.')
    return redirect('peliculas:detalle', pk=pk)


@administrador_requerido
@require_http_methods(['GET', 'POST'])
def eliminar_resena(request, pk, resena_id):
    resena = get_object_or_404(Resena.objects.select_related('pelicula', 'usuario'), pk=resena_id, pelicula_id=pk)
    if request.method == 'POST':
        resena.delete()
        messages.success(request, 'Reseña eliminada.')
        return redirect('peliculas:detalle', pk=pk)
    return render(request, 'peliculas/eliminar_resena.html', {'resena': resena, 'pelicula': resena.pelicula})


@administrador_requerido
def gestion(request):
    return render(request, 'peliculas/gestion.html', {'peliculas': Pelicula.objects.all().order_by('nombre')})


@administrador_requerido
@require_http_methods(['GET', 'POST'])
def editar(request, pk=None):
    pelicula = get_object_or_404(Pelicula, pk=pk) if pk else None
    imagen_original = (pelicula.imagen or pelicula.cartel_local) if pelicula else ''
    form = PeliculaAdminForm(request.POST or None, request.FILES or None, instance=pelicula)
    if request.method == 'POST' and form.is_valid():
        movie = form.save(commit=False)
        if not pelicula:
            # Campos heredados del catálogo original de cartelera de cines.
            movie.sucursal = 'PlazaOeste'
            movie.sala = 1
            movie.fecha_exhibicion = timezone.localdate()
            movie.hora_exhibicion = time(12, 0)
            movie.valor_ticket = 0
        elif not movie.imagen:
            movie.imagen = imagen_original
        movie.save()
        messages.success(request, 'Película guardada correctamente.')
        return redirect('peliculas:gestion')
    return render(request, 'peliculas/pelicula_form.html', {'form': form, 'pelicula': pelicula})


@administrador_requerido
@require_http_methods(['GET', 'POST'])
def eliminar(request, pk):
    pelicula = get_object_or_404(Pelicula, pk=pk)
    if request.method == 'POST':
        pelicula.delete()
        messages.success(request, 'Película eliminada del catálogo.')
        return redirect('peliculas:gestion')
    return render(request, 'peliculas/eliminar.html', {'pelicula': pelicula})


@login_required
def mi_lista(request, seccion):
    if request.user.admin:
        return redirect('peliculas:gestion')
    if request.user.es_invitado:
        messages.info(request, 'Crea una cuenta para guardar tus películas.')
        return redirect('Register')
    if seccion == 'favoritos':
        registros = Favorito.objects.filter(usuario=request.user).select_related('pelicula')
    elif seccion == 'historial':
        registros = VisitaPelicula.objects.filter(usuario=request.user).select_related('pelicula')
    else:
        from django.http import Http404
        raise Http404
    return render(request, 'peliculas/mi_lista.html', {'registros': registros, 'seccion': seccion})


@login_required
@require_http_methods(['POST'])
def favorito(request, pk):
    if request.user.admin:
        return HttpResponseForbidden('Los favoritos están disponibles para clientes.')
    if request.user.es_invitado:
        messages.info(request, 'Crea una cuenta para guardar películas en favoritos.')
        return redirect('Register')
    pelicula = get_object_or_404(Pelicula, pk=pk)
    accion = request.POST.get('accion')
    if accion == 'agregar':
        Favorito.objects.get_or_create(usuario=request.user, pelicula=pelicula)
        messages.success(request, 'Película agregada a favoritos.')
    elif accion == 'quitar':
        Favorito.objects.filter(usuario=request.user, pelicula=pelicula).delete()
        messages.success(request, 'Película quitada de favoritos.')
    else:
        from django.http import HttpResponseBadRequest
        return HttpResponseBadRequest('Acción no válida.')
    if request.POST.get('origen') == 'favoritos':
        return redirect('peliculas:mi_lista', seccion='favoritos')
    return redirect('peliculas:detalle', pk=pelicula.pk)
