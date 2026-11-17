from django.db import migrations

def cargar(apps, schema_editor):
    Pelicula = apps.get_model('moduloPeliculas', 'Pelicula')
    items = [
        ('Shrek', 'Comedia', 90, 'Un ogro emprende un viaje inesperado para rescatar a una princesa y recuperar la tranquilidad de su pantano.'),
        ('Cómo entrenar a tu dragón', 'Accion', 98, 'Un joven vikingo conoce a un dragón y descubre una amistad capaz de cambiar su aldea.'),
        ('Kung Fu Panda', 'Comedia', 92, 'Po, un panda entusiasta, descubre que puede convertirse en un héroe de las artes marciales.'),
        ('Madagascar', 'Comedia', 86, 'Cuatro amigos del zoológico terminan viviendo una aventura en una isla lejana.'),
        ('El gato con botas', 'Accion', 90, 'El Gato con Botas emprende una aventura con nuevos aliados y un objetivo imposible.'),
        ('Los Croods', 'Comedia', 98, 'Una familia prehistórica emprende un viaje para encontrar un nuevo hogar.'),
    ]
    for nombre, genero, duracion, resena in items:
        Pelicula.objects.get_or_create(nombre=nombre, defaults={'sucursal':'PlazaOeste','genero':genero,'clasificacion':'TE', 'duracion':duracion, 'resena':resena, 'sala':1, 'fecha_exhibicion':'2026-01-01', 'hora_exhibicion':'12:00', 'valor_ticket':0, 'imagen':'', 'estado':'estrenada'})

def noop(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [('moduloPeliculas', '0001_initial')]
    operations = [migrations.RunPython(cargar, noop)]
