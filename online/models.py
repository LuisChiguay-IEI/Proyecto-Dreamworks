from django.db import models
from django.core.validators import MaxLengthValidator
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, correo, usuario, password=None, **extra_fields):
        """
        Crea y guarda un usuario con el correo, usuario y password dados.
        """
        if not correo:
            raise ValueError('El usuario debe tener un correo electrónico')
        if not usuario:
            raise ValueError('El usuario debe tener un nombre de usuario')

        user = self.model(
            correo=self.normalize_email(correo),
            usuario=usuario,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, correo, usuario, password=None, **extra_fields):
        """
        Crea y guarda un superusuario con el correo, usuario y password dados.
        """
        extra_fields.setdefault('admin', True)
        extra_fields.setdefault('activo', True)
        extra_fields.setdefault('tecnico', True)

        if extra_fields.get('admin') is not True:
            raise ValueError('Superuser debe tener admin=True.')

        return self.create_user(correo, usuario, password, **extra_fields)

class Usuario(AbstractBaseUser):
    nombre = models.CharField(
        verbose_name='Nombre',
        max_length=30,
        blank=True,
        null=True
    )
    apellido = models.CharField(
        verbose_name='Apellido',
        max_length=30,
        blank=True,
        null=True
    )
    rut = models.CharField(
        verbose_name='RUT',
        max_length=12,
        unique=True,
        blank=True,
        null=True
    )
    correo = models.EmailField(
        verbose_name='Correo electrónico',
        max_length=70,
        unique=True,
    )
    usuario = models.CharField(
        verbose_name='Usuario',
        max_length=50,
        unique=True,
    )
    fecha_nacimiento = models.DateField(
        verbose_name='Fecha de nacimiento',
        null=True,
        blank=True
    )
    activo = models.BooleanField(default=True)
    admin = models.BooleanField(default=False)
    tecnico = models.BooleanField(default=False)

    es_invitado = models.BooleanField(default=False)
    consultas_ia_invitado = models.PositiveSmallIntegerField(default=0)

    @property
    def perfil(self):
        if self.admin:
            return 'Administrador'
        if self.tecnico:
            return 'Técnico'
        return 'Invitado' if self.es_invitado else 'Cliente'

    @property
    def tema(self):
        if self.admin:
            return 'admin'
        if self.tecnico:
            return 'tecnico'
        return 'invitado' if self.es_invitado else 'cliente'

    USERNAME_FIELD = 'usuario'
    REQUIRED_FIELDS = ['correo']

    objects = UserManager()

    def get_full_name(self):
        return f"{self.nombre} {self.apellido}"

    def get_short_name(self):
        return self.usuario

    def has_perm(self, perm, obj=None):
        return self.is_active and self.admin

    def has_module_perms(self, app_label):
        return self.is_active and self.admin

    @property
    def is_active(self):
        return self.activo

    @property
    def is_staff(self):
        return self.admin

    @property
    def is_admin(self):
        return self.admin

    def __str__(self):
        return self.usuario

class Preguntas(models.Model):
    idPregunta = models.AutoField(primary_key=True)
    Titulo = models.CharField(max_length=60)
    Pregunta = models.TextField(validators=[MaxLengthValidator(5000)])
    Fecha_creacion = models.DateTimeField(default=timezone.now)
    Usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)

    origen_invitado = models.BooleanField(default=False)
    pelicula = models.ForeignKey('moduloPeliculas.Pelicula', null=True, blank=True, on_delete=models.SET_NULL, related_name='consultas')

    archivada = models.BooleanField(default=False, db_index=True)

    # Campo histórico conservado para registros anteriores.

    plataforma = models.CharField('Plataforma de juego', max_length=20,
        default='sin_especificar', choices=[
            ('sin_especificar', 'Sin especificar'), ('pc', 'PC'),
            ('playstation', 'PlayStation'), ('xbox', 'Xbox'),
            ('nintendo', 'Nintendo'), ('movil', 'Móvil')])

    categoria = models.CharField(max_length=20, default='otros', choices=[
        ('pelicula', 'Información de películas'), ('reproduccion', 'Reproducción'),
        ('catalogo', 'Catálogo'), ('cuenta', 'Cuenta'), ('pago', 'Pago'), ('otros', 'Otros')])
    estado = models.CharField(max_length=15, default='abierto', choices=[
        ('abierto', 'Abierto'), ('en_proceso', 'En proceso'), ('resuelto', 'Resuelto'), ('cerrado', 'Cerrado')])
    prioridad = models.CharField(max_length=10, default='media', choices=[
        ('baja', 'Baja'), ('media', 'Media'), ('alta', 'Alta')])
    fecha_resolucion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.idPregunta} - {self.Titulo}"

class Respuesta(models.Model):
    idRespuesta = models.AutoField(primary_key=True)
    Respuesta = models.TextField(verbose_name='Respuesta', validators=[MaxLengthValidator(2000)])
    id_Pregunta = models.ForeignKey(Preguntas, on_delete=models.CASCADE)
    Usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    FechaHora = models.DateTimeField(default=timezone.now)

    # Innovación 3: solo una respuesta aceptada por consulta, incluso en BD.
    es_solucion = models.BooleanField('Respuesta marcada como solución', default=False)
    valoracion_cliente = models.CharField('Valoración del cliente', max_length=15, blank=True,
        choices=[('util', 'Útil'), ('insatisfactoria', 'Insatisfactoria')], default='')

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['id_Pregunta'], condition=models.Q(es_solucion=True),
            name='una_solucion_por_pregunta')]

    def __str__(self):
        return f"{self.idRespuesta} - {self.Respuesta[:20]}"


# Innovación 2: las notas se guardan separadas de las respuestas públicas.
class NotaInterna(models.Model):
    pregunta = models.ForeignKey(Preguntas, on_delete=models.CASCADE,
                                 related_name='notas_internas')
    autor = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True,
                              related_name='notas_soporte')
    contenido = models.TextField('Nota interna', validators=[MaxLengthValidator(2000)])
    fecha_creacion = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['fecha_creacion', 'pk']

    def __str__(self):
        return f'Nota {self.pk} de consulta {self.pregunta_id}'
