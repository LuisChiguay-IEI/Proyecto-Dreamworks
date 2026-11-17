from django import forms
from .models import Resena, Pelicula

class ResenaForm(forms.ModelForm):
    puntuacion = forms.TypedChoiceField(choices=[(i, f'{i} / 5') for i in range(1, 6)], coerce=int)
    class Meta:
        model = Resena
        fields = ['puntuacion', 'comentario']
        widgets = {'comentario': forms.Textarea(attrs={'rows': 4, 'maxlength': 1000})}


class PeliculaAdminForm(forms.ModelForm):
    class Meta:
        model = Pelicula
        fields = ['nombre', 'genero', 'clasificacion', 'duracion', 'resena', 'estado', 'imagen_subida']
        labels = {'nombre': 'Título', 'genero': 'Género', 'clasificacion': 'Clasificación', 'duracion': 'Duración en minutos', 'resena': 'Descripción', 'estado': 'Estado', 'imagen_subida': 'Imagen o afiche'}
        widgets = {'resena': forms.Textarea(attrs={'rows': 4}), 'imagen_subida': forms.ClearableFileInput(attrs={'accept': 'image/png,image/jpeg,image/webp'})}

    def clean_imagen_subida(self):
        imagen = self.cleaned_data.get('imagen_subida')
        if imagen and hasattr(imagen, 'size') and imagen.size > 5 * 1024 * 1024:
            raise forms.ValidationError('La imagen debe pesar como máximo 5 MB.')
        if imagen and hasattr(imagen, 'content_type') and imagen.content_type not in ('image/jpeg', 'image/png', 'image/webp'):
            raise forms.ValidationError('Usa una imagen JPG, PNG o WebP.')
        return imagen
