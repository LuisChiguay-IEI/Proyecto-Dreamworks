import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.utils import timezone
from online.models import Preguntas, Usuario, NotaInterna
from online.forms import PreguntaAdminForm
from .services import estadisticas

logger = logging.getLogger(__name__)

def denegado(request):
    messages.error(request, 'No tienes permisos para realizar esta acción.')
    return redirect('administracion') if request.user.tecnico else redirect('inicio', id=request.user.pk)

@login_required
def IndexAdmin(request):
    if not (request.user.admin or request.user.tecnico):
        return denegado(request)
    preguntas = Preguntas.objects.filter(archivada=False).select_related('Usuario').order_by('-Fecha_creacion')
    for campo in ('categoria', 'estado', 'prioridad'):
        valor = request.GET.get(campo, '')
        if valor:
            preguntas = preguntas.filter(**{campo: valor})
    return render(request, 'indexAdmin.html', {'Preguntas': Paginator(preguntas, 20).get_page(request.GET.get('page')),
        'estadisticas_ia': estadisticas(), 'filtros': PreguntaAdminForm()})

@login_required
@require_POST
def BorrarPregunta(request, idUser, idPregunta):
    if not request.user.admin:
        return denegado(request)
    pregunta = get_object_or_404(Preguntas, pk=idPregunta)
    logger.info('Administrador %s eliminó consulta %s', request.user.pk, pregunta.pk)
    pregunta.delete()
    messages.success(request, 'Pregunta eliminada correctamente.')
    return redirect('administracion')

@login_required
def GestionUsuarios(request):
    if not request.user.admin:
        return denegado(request)
    if request.method == 'POST':
        with transaction.atomic():
            # Bloquear administradores y objetivo para proteger la última cuenta activa.
            list(Usuario.objects.select_for_update().filter(admin=True).order_by('pk'))
            usuario = get_object_or_404(Usuario.objects.select_for_update(), pk=request.POST.get('Userid') or 0, es_invitado=False)
            activo = request.POST.get('activo') == 'on'
            admin = request.POST.get('admin') == 'on'
            if usuario.pk == request.user.pk and (not activo or not admin):
                messages.error(request, 'No puedes desactivar tu cuenta ni quitarte el permiso de administrador.')
            elif usuario.admin and usuario.activo and (not activo or not admin) and not Usuario.objects.filter(admin=True, activo=True).exclude(pk=usuario.pk).exists():
                messages.error(request, 'Debe mantenerse al menos un administrador activo.')
            else:
                usuario.activo, usuario.admin = activo, admin
                usuario.tecnico = request.POST.get('tecnico') == 'on'
                usuario.save(update_fields=['activo', 'admin', 'tecnico'])
                logger.info('Administrador %s actualizó permisos de %s', request.user.pk, usuario.pk)
                messages.success(request, 'Permisos actualizados.')
        return redirect('gestion_usuarios')
    usuarios = Usuario.objects.filter(es_invitado=False).annotate(num_preguntas=Count('preguntas', filter=Q(preguntas__archivada=False))).order_by('pk')
    tipo = request.GET.get('tipo', '')
    if tipo == 'tecnicos':
        usuarios = usuarios.filter(tecnico=True, admin=False)
    elif tipo == 'clientes':
        usuarios = usuarios.filter(tecnico=False, admin=False)
    elif tipo == 'administradores':
        usuarios = usuarios.filter(admin=True)
    return render(request, 'GestionUsuarios.html', {'Usuarios': Paginator(usuarios, 20).get_page(request.GET.get('page'))})

@login_required
@require_POST
def EliminarUsuario(request, idUser):
    if not request.user.admin:
        return denegado(request)
    with transaction.atomic():
        list(Usuario.objects.select_for_update().filter(admin=True).order_by('pk'))
        usuario = get_object_or_404(Usuario.objects.select_for_update(), pk=idUser)
        if usuario.pk == request.user.pk:
            messages.error(request, 'No puedes eliminar tu propia cuenta.')
        elif usuario.admin and usuario.activo and not Usuario.objects.filter(admin=True, activo=True).exclude(pk=usuario.pk).exists():
            messages.error(request, 'No puedes eliminar al último administrador activo.')
        else:
            logger.info('Administrador %s eliminó usuario %s', request.user.pk, usuario.pk)
            usuario.delete()
            messages.success(request, 'Usuario eliminado.')
    return redirect('gestion_usuarios')

@login_required
def ModificarPregunta(request, idPregunta):
    if not request.user.admin:
        return denegado(request)
    pregunta = get_object_or_404(Preguntas, pk=idPregunta)
    form = PreguntaAdminForm(request.POST or None, instance=pregunta)
    if request.method == 'POST' and form.is_valid():
        pregunta = form.save(commit=False)
        if pregunta.estado in ('resuelto', 'cerrado'):
            pregunta.fecha_resolucion = pregunta.fecha_resolucion or timezone.now()
        else:
            pregunta.fecha_resolucion = None
        pregunta.save()
        logger.info('Administrador %s actualizó consulta %s', request.user.pk, pregunta.pk)
        messages.success(request, 'Consulta actualizada.')
        return redirect('administracion')
    return render(request, 'ModificarPregunta.html', {'form': form, 'pregunta': pregunta})

@login_required
def AnalyticsIA(request):
    if not request.user.admin:
        return denegado(request)
    return render(request, 'analytics_ia.html', {'analytics_data': estadisticas()})


@login_required
def NotasInternas(request):
    if not request.user.admin:
        return denegado(request)
    notas = NotaInterna.objects.filter(pregunta__archivada=False).select_related('autor', 'pregunta', 'pregunta__Usuario').order_by('-fecha_creacion', '-pk')
    return render(request, 'notasInternas.html', {
        'notas': Paginator(notas, 20).get_page(request.GET.get('page'))})
