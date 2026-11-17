from rest_framework import serializers
from .models import Pelicula, Resena


class ResenaSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = Resena
        fields = ['id', 'pelicula', 'usuario', 'usuario_nombre', 'puntuacion', 'comentario', 'fecha', 'visible']
        read_only_fields = ['fecha']


class PeliculaSerializer(serializers.ModelSerializer):
    cartel_url = serializers.ReadOnlyField()
    resenas = ResenaSerializer(many=True, read_only=True)

    class Meta:
        model = Pelicula
        fields = [
            'id', 'nombre', 'estado', 'sucursal', 'genero',
            'clasificacion', 'duracion', 'resena', 'sala',
            'fecha_exhibicion', 'hora_exhibicion', 'valor_ticket',
            'cartel_url', 'resenas'
        ]
