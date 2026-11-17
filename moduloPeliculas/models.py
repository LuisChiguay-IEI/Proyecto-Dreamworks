from django.db import models
from django.templatetags.static import static
from django.core.validators import MinValueValidator, MaxValueValidator

class Pelicula(models.Model):
    SUCURSAL_CHOICES = [
        ('PlazaOeste', 'Plaza Oeste'),
        ('MallAraucoMaipu', 'Mall Arauco Maipu'),
        ('CinepolisMaipu', 'Cinepolis Maipu'),
        ('PlazaVespucio', 'Plaza Vespucio'),
    ]

    GENERO_CHOICES = [
        ('Accion', 'Acción'),
        ('Comedia', 'Comedia'),
        ('Drama', 'Drama'),
        ('Suspenso', 'Suspenso'),
        ('Crimen', 'Crimen'),
        ('Romance', 'Romance'),
        ('Terror', 'Terror'),
        ('Musical', 'Musical'),
    ]

    CLASIFICACION_CHOICES = [
        ('TE', 'TE'),
        ('TE+7', 'TE+7'),
        ('14+', '14+'),
        ('18+', '18+'),
    ]

    ESTADO_CHOICES = [
        ('estrenada', 'Película estrenada'),
        ('proximo_es', 'Próximo estreno')
    ]

    # Definimos el campo estado una sola vez
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='estrenada')

    sucursal = models.CharField(max_length=100, choices=SUCURSAL_CHOICES)
    nombre = models.CharField(max_length=50, help_text='Nombre de la película')
    genero = models.CharField(max_length=20, choices=GENERO_CHOICES, blank=False)
    clasificacion = models.CharField(max_length=8, choices=CLASIFICACION_CHOICES, blank=False)
    duracion = models.PositiveIntegerField(help_text='Tiempo de duración en minutos')
    resena = models.TextField(blank=True, help_text='Breve reseña del contenido de la película')
    sala = models.IntegerField(
        validators=[
            MinValueValidator(1, message="El número de sala debe ser mayor o igual a 1."),
            MaxValueValidator(15, message="El número de sala debe ser menor o igual a 15.")
        ],
        help_text='Sala en la que se exhibe'
    )
    fecha_exhibicion = models.DateField(help_text='Fecha de la exhibición', blank=False)
    hora_exhibicion = models.TimeField(help_text='Hora de la exhibición', blank=False)
    valor_ticket = models.PositiveIntegerField(help_text='Valor del ticket')
    imagen = models.CharField(max_length=300, blank=True, help_text='Imagen incluida con el proyecto')
    imagen_subida = models.ImageField(upload_to='peliculas/', blank=True, null=True, verbose_name='Afiche de la película')

    @property
    def cartel_local(self):
        return {
            'Shrek': 'peliculas/shrek.jpg',
            'Cómo entrenar a tu dragón': 'peliculas/dragon.jpg',
            'Kung Fu Panda': 'peliculas/panda.jpg',
        }.get(self.nombre, '')

    @property
    def cartel_url(self):
        if self.imagen_subida:
            return self.imagen_subida.url
        ruta = self.imagen or self.cartel_local
        return static(ruta) if ruta else ''

    def __str__(self):
        return self.nombre


class Resena(models.Model):
    pelicula = models.ForeignKey(Pelicula, on_delete=models.CASCADE, related_name='resenas')
    usuario = models.ForeignKey('online.Usuario', on_delete=models.CASCADE)
    visible = models.BooleanField(default=True)
    puntuacion = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.TextField(max_length=1000)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

class Favorito(models.Model):
    usuario = models.ForeignKey('online.Usuario', on_delete=models.CASCADE, related_name='peliculas_favoritas')
    pelicula = models.ForeignKey(Pelicula, on_delete=models.CASCADE, related_name='favoritos')
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['usuario', 'pelicula'], name='favorito_unico_usuario_pelicula')]
        ordering = ['-fecha_agregado', '-pk']

class VisitaPelicula(models.Model):
    usuario = models.ForeignKey('online.Usuario', on_delete=models.CASCADE, related_name='peliculas_visitadas')
    pelicula = models.ForeignKey(Pelicula, on_delete=models.CASCADE, related_name='visitas')
    fecha_visita = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['usuario', 'pelicula'], name='visita_unica_usuario_pelicula')]
        ordering = ['-fecha_visita', '-pk']
