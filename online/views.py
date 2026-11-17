import uuid
from django.db.models import F
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseForbidden
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.core.paginator import Paginator
from django.core.cache import cache
from django.contrib import messages
from online.forms import AsistenteForm, NotaInternaForm, InvitadoForm, GestionCasoForm
from online.ia_utils import AsistenteIA
from django.contrib.auth import logout
from django.utils import timezone
from django.views.decorators.http import require_POST
from online.forms import RegisterForm, LoginForm, PreguntasForm, RespuestaForm
from django.views.generic import CreateView, FormView
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from online.models import Preguntas, Usuario, Respuesta, NotaInterna

def _ir_a_consulta_pendiente(request, user):
    pelicula = request.session.pop('pelicula_pendiente', None)
    if pelicula and not (user.admin or user.tecnico):
        return redirect(reverse('inicio', args=[user.pk]) + '?pelicula=' + str(pelicula) + '#formulario-pregunta')
    siguiente = request.POST.get('next') or request.GET.get('next')
    if siguiente and url_has_allowed_host_and_scheme(siguiente, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(siguiente)
    return redirect('peliculas:catalogo')

# Vista para la página principal
def Index(request):
    """
    Página principal del sitio
    """
    if request.user.is_authenticated:
        return redirect('administracion') if request.user.admin or request.user.tecnico else redirect('inicio', id=request.user.pk)
    return redirect(reverse('Login') + '?next=' + reverse('index'))

def AccesoInvitado(request):
    if request.user.is_authenticated:
        return redirect('index')
    form = InvitadoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        identificador = uuid.uuid4().hex
        usuario = Usuario.objects.create_user(
            correo=f'{identificador}@guest.invalid', usuario=f'invitado_{identificador}',
            nombre=form.cleaned_data['nombre'], es_invitado=True)
        # Sin contraseña utilizable: solo la sesión creada permite acceder a esta cuenta.
        login(request, usuario, backend='django.contrib.auth.backends.ModelBackend')
        request.session.set_expiry(0)
        pelicula = request.session.pop('pelicula_pendiente', None)
        destino = reverse('inicio', args=[usuario.pk])
        return redirect(destino + ('?pelicula=' + str(pelicula) + '#formulario-pregunta' if pelicula else ''))
    return render(request, 'invitado.html', {'form': form})


# Vista para logout personalizada
@require_POST
def logout_view(request):
    """
    Vista personalizada para logout
    """
    logout(request)
    return redirect('peliculas:catalogo')

# Vista de inicio de usuario
@login_required
def Inicio(request, id):
    """
    Vista del panel de usuario
    """
    if request.user.admin or request.user.tecnico:
        return redirect('administracion')
    try:
        User = Usuario.objects.get(id=id)
        if request.user.id != User.id:
            return redirect('inicio', id=request.user.pk)
        preguntas = Preguntas.objects.filter(Usuario=User, archivada=False).order_by('-Fecha_creacion')
        now = timezone.now()
        form = PreguntasForm(initial={'pelicula': request.GET.get('pelicula')})

        limite = 1 if User.es_invitado else 5
        activas = preguntas.exclude(estado__in=['resuelto', 'cerrado']).count()
        if request.method == "POST" and request.POST.get("accion") != "asistente":
            form = PreguntasForm(request.POST)
            if form.is_valid():
                with transaction.atomic():
                    # Serializar la comprobación y creación por usuario.
                    titular = Usuario.objects.select_for_update().get(pk=User.pk)
                    limite = 1 if titular.es_invitado else 5
                    activas = Preguntas.objects.filter(Usuario=titular, archivada=False).exclude(estado__in=['resuelto', 'cerrado']).count()
                    if activas >= limite:
                        form.add_error(None, f'Alcanzaste el máximo de {limite} consultas de soporte abiertas. ' +
                                       ('Regístrate para ampliar tu límite.' if titular.es_invitado else
                                        'Espera a que el equipo resuelva o cierre una consulta.'))
                    else:
                        pregunta = form.save(commit=False)
                        pregunta.Usuario = titular
                        pregunta.origen_invitado = titular.es_invitado
                        pregunta.Fecha_creacion = now
                        pregunta.save()
                        return redirect('inicio', id=id)

        ayuda = None
        ayuda_form = AsistenteForm(request.POST if request.method == 'POST' and request.POST.get('accion') == 'asistente' else None)
        if ayuda_form.is_bound and ayuda_form.is_valid():
            llave = f'ia-usuario-{request.user.pk}'
            if not cache.add(llave, True, timeout=60):
                messages.warning(request, 'Espera un minuto antes de volver a consultar al asistente.')
            else:
                permitido = True
                if User.es_invitado:
                    # UPDATE condicional: nunca permite consumir una tercera solicitud.
                    permitido = bool(Usuario.objects.filter(pk=User.pk, es_invitado=True,
                        consultas_ia_invitado__lt=2).update(consultas_ia_invitado=F('consultas_ia_invitado') + 1))
                if permitido:
                    ayuda = AsistenteIA().generar_respuesta_automatica(ayuda_form.cleaned_data['buscar_ayuda'])
                else:
                    messages.warning(request, 'Ya utilizaste tus 2 consultas de IA como invitado. Regístrate para continuar.')
                    cache.delete(llave)
        User.refresh_from_db()
        return render(request, "inicio.html", {
            'ayuda_form': ayuda_form, 'ayuda': ayuda,
            'limite_soporte': limite, 'consultas_activas': activas,
            'ia_restantes': max(0, 2 - User.consultas_ia_invitado),
            'sin_cupo_ia': User.es_invitado and User.consultas_ia_invitado >= 2,
            "Preguntas": Paginator(preguntas, 15).get_page(request.GET.get("page")),
            "form": form,
            "id": id
        })
    except Usuario.DoesNotExist:
        return redirect('/')

def _contexto_conversacion(request, pregunta, respuesta_form=None, nota_form=None):
    personal = request.user.admin or request.user.tecnico
    contexto = {
        'Pregunta': pregunta,
        'tiene_solucion': Respuesta.objects.filter(id_Pregunta=pregunta, es_solucion=True).exists(),
        'form': respuesta_form if respuesta_form is not None else RespuestaForm(),
        'Respuestas': Respuesta.objects.filter(id_Pregunta=pregunta)
            .select_related('Usuario').order_by('FechaHora', 'idRespuesta'),
    }
    # No consultar ni enviar notas en el contexto de un cliente.
    if personal:
        contexto['notas_internas'] = pregunta.notas_internas.select_related('autor').all()
        contexto['gestion_form'] = GestionCasoForm(instance=pregunta)
        contexto['nota_form'] = nota_form if nota_form is not None else NotaInternaForm()
    return contexto


@login_required
def ViewRespuestas(request, idUser, idPregunta):
    pregunta = get_object_or_404(Preguntas, idPregunta=idPregunta)
    if not (request.user.pk == pregunta.Usuario_id or request.user.admin or request.user.tecnico):
        return redirect('inicio', id=request.user.pk)
    form = RespuestaForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and pregunta.estado in ('resuelto', 'cerrado'):
        messages.warning(request, 'Este chat está terminado. El personal debe reabrir el caso para continuar.')
        return redirect('respuestas', idUser=request.user.pk, idPregunta=pregunta.pk)
    if request.method == 'POST' and form.is_valid():
        respuesta = form.save(commit=False)
        respuesta.id_Pregunta = pregunta
        respuesta.Usuario = request.user
        respuesta.FechaHora = timezone.now()
        respuesta.save()
        return redirect('respuestas', idUser=request.user.pk, idPregunta=pregunta.pk)
    return render(request, 'Respuestas.html', _contexto_conversacion(request, pregunta, respuesta_form=form))


@login_required
@require_POST
def AgregarNotaInterna(request, idPregunta):
    if not (request.user.admin or request.user.tecnico):
        return HttpResponseForbidden('Las notas internas son exclusivas del personal de soporte.')
    pregunta = get_object_or_404(Preguntas, pk=idPregunta)
    form = NotaInternaForm(request.POST)
    if form.is_valid():
        nota = form.save(commit=False)
        nota.pregunta = pregunta
        nota.autor = request.user
        nota.save()
        messages.success(request, 'Nota interna registrada. Solo el personal puede verla.')
        return redirect('respuestas', idUser=request.user.pk, idPregunta=pregunta.pk)
    return render(request, 'Respuestas.html', _contexto_conversacion(request, pregunta, nota_form=form))


@login_required
@require_POST
def MarcarSolucion(request, idPregunta, idRespuesta):
    with transaction.atomic():
        pregunta = get_object_or_404(Preguntas.objects.select_for_update(), pk=idPregunta)
        personal = request.user.admin or request.user.tecnico
        if not (personal or request.user.pk == pregunta.Usuario_id):
            return HttpResponseForbidden('No puedes modificar la solución de esta consulta.')
        respuesta = get_object_or_404(Respuesta, pk=idRespuesta, id_Pregunta=pregunta)
        if request.POST.get('accion') == 'retirar':
            if not personal:
                return HttpResponseForbidden('Solo técnicos y administradores pueden quitar la marca de solución.')
            Respuesta.objects.filter(pk=respuesta.pk).update(es_solucion=False)
            messages.success(request, 'Se retiró la selección de solución.')
        else:
            if not personal and Respuesta.objects.filter(id_Pregunta=pregunta, es_solucion=True).exclude(pk=respuesta.pk).exists():
                return HttpResponseForbidden('Solicita al personal cambiar la solución seleccionada.')
            Respuesta.objects.filter(id_Pregunta=pregunta, es_solucion=True).update(es_solucion=False)
            Respuesta.objects.filter(pk=respuesta.pk).update(es_solucion=True)
            messages.success(request, 'Respuesta marcada como solución.')
    return redirect('respuestas', idUser=request.user.pk, idPregunta=idPregunta)


# Vistas basadas en clases
class RegisterView(CreateView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.es_invitado:
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.user.is_authenticated and self.request.user.es_invitado:
            kwargs['instance'] = self.request.user
            kwargs.setdefault('initial', {}).update({'usuario': '', 'correo': '', 'rut': ''})
        return kwargs

    form_class = RegisterForm
    template_name = 'register.html'
    success_url = '/'

    def form_valid(self, form):
        request = self.request
        user = form.save(commit=False)
        if user.es_invitado:
            user.nombre = user.usuario
        user.es_invitado = False
        user.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return _ir_a_consulta_pendiente(request, user)

class LoginView(FormView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.es_invitado:
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)

    form_class = LoginForm
    template_name = 'login.html'
    success_url = '/'

    def form_valid(self, form):
        request = self.request
        usuario = form.cleaned_data.get("Usuario")
        password = form.cleaned_data.get("password")

        user = authenticate(request, username=usuario, password=password)
        if user is not None:
            login(request, user)
            request.session.set_expiry(0)
            return _ir_a_consulta_pendiente(request, user)
        form.add_error(None, "Usuario o contraseña incorrectos.")
        return super().form_invalid(form)

@login_required
@require_POST
def GestionarCaso(request, idPregunta):
    if not (request.user.admin or request.user.tecnico):
        return HttpResponseForbidden('Solo el personal puede cambiar estado y prioridad.')
    with transaction.atomic():
        pregunta = get_object_or_404(Preguntas.objects.select_for_update(), pk=idPregunta)
        form = GestionCasoForm(request.POST, instance=pregunta)
        if not form.is_valid():
            return HttpResponse('Estado o prioridad inválidos.', status=400)
        pregunta = form.save(commit=False)
        pregunta.fecha_resolucion = (pregunta.fecha_resolucion or timezone.now()) if pregunta.estado in ('resuelto', 'cerrado') else None
        pregunta.save(update_fields=['estado', 'prioridad', 'fecha_resolucion'])
    messages.success(request, 'Estado y prioridad actualizados.')
    return redirect('respuestas', idUser=request.user.pk, idPregunta=idPregunta)


@login_required
@require_POST
def CerrarCaso(request, idPregunta):
    with transaction.atomic():
        pregunta = get_object_or_404(Preguntas.objects.select_for_update(), pk=idPregunta)
        if request.user.pk != pregunta.Usuario_id or request.user.admin or request.user.tecnico:
            return HttpResponseForbidden('Esta acción corresponde al cliente dueño de la consulta.')
        pregunta.estado = 'cerrado'
        pregunta.fecha_resolucion = pregunta.fecha_resolucion or timezone.now()
        pregunta.save(update_fields=['estado', 'fecha_resolucion'])
    messages.success(request, 'Confirmaste que tu asunto quedó resuelto. Caso cerrado.')
    return redirect('respuestas', idUser=request.user.pk, idPregunta=idPregunta)


@login_required
@require_POST
def ValorarSolucion(request, idPregunta, idRespuesta):
    with transaction.atomic():
        pregunta = get_object_or_404(Preguntas.objects.select_for_update(), pk=idPregunta)
        if request.user.pk != pregunta.Usuario_id or request.user.admin or request.user.tecnico:
            return HttpResponseForbidden('Solo el cliente dueño de la consulta puede valorar la solución.')
        respuesta = get_object_or_404(Respuesta, pk=idRespuesta, id_Pregunta=pregunta, es_solucion=True)
        valoracion = request.POST.get('valoracion')
        if valoracion not in ('util', 'insatisfactoria'):
            return HttpResponse('Valoración inválida.', status=400)
        respuesta.valoracion_cliente = valoracion
        respuesta.save(update_fields=['valoracion_cliente'])
    messages.success(request, 'Tu valoración fue registrada.')
    return redirect('respuestas', idUser=request.user.pk, idPregunta=idPregunta)
