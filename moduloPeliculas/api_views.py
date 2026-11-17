from rest_framework import viewsets
from .models import Pelicula, Resena
from .serializers import PeliculaSerializer, ResenaSerializer


class PeliculaViewSet(viewsets.ModelViewSet):
    queryset = Pelicula.objects.all()
    serializer_class = PeliculaSerializer


class ResenaViewSet(viewsets.ModelViewSet):
    queryset = Resena.objects.filter(visible=True)
    serializer_class = ResenaSerializer
