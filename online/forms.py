from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import re
from online.models import Usuario, Preguntas, Respuesta, NotaInterna

class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        label='',
        widget=forms.PasswordInput(attrs={'placeholder': 'Contraseña'})
    )
    password_2 = forms.CharField(
        label='',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirmar contraseña'})
    )

    class Meta:
        model = Usuario
        fields = ['usuario', 'correo', 'rut']
        widgets = {
            'correo': forms.EmailInput(attrs={'placeholder': 'Ingrese su correo'}),
            'usuario': forms.TextInput(attrs={'placeholder': 'Ingrese su usuario'}),
            'rut': forms.TextInput(attrs={'placeholder': 'Ingrese su rut'})
        }

    def clean_correo(self):
        correo = self.cleaned_data.get('correo')
        if Usuario.objects.filter(correo__iexact=correo).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("El correo ya está en uso")
        return correo

    def clean_rut(self):
        rut = re.sub(r'[.\s]', '', self.cleaned_data.get('rut') or '').upper()
        if not rut:
            return None
        if not re.fullmatch(r'\d{7,8}-[0-9K]', rut):
            raise forms.ValidationError('Ingrese un RUT válido, por ejemplo 12.345.678-5.')
        cuerpo, dv = rut.split('-')
        total = sum(int(n) * (2 + i % 6) for i, n in enumerate(reversed(cuerpo)))
        valor = 11 - total % 11
        esperado = '0' if valor == 11 else 'K' if valor == 10 else str(valor)
        if int(cuerpo) == 0 or dv != esperado:
            raise forms.ValidationError('El dígito verificador del RUT es incorrecto.')
        # Comparar también con RUT existentes que tengan puntos.
        if any(re.sub(r'[.\s]', '', r or '').upper() == rut for r in Usuario.objects.exclude(pk=self.instance.pk).values_list('rut', flat=True)):
            raise forms.ValidationError('El RUT ya está registrado.')
        return rut

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_2 = cleaned_data.get("password_2")
        usuario = cleaned_data.get("usuario")

        if usuario and len(usuario) > 20:
            self.add_error("usuario", "El nombre de usuario es demasiado largo!")
        if not usuario:
            self.add_error("usuario", "Debe ingresar un nombre de usuario!")
        if password and len(password) < 8:
            self.add_error("password", "La contraseña debe ser mayor a 8 dígitos")
        if password and password_2 and password != password_2:
            self.add_error("password_2", "Las contraseñas no coinciden")
        if password:
            try:
                validate_password(password, Usuario(usuario=usuario or '', correo=cleaned_data.get('correo', '')))
            except ValidationError as exc:
                self.add_error('password', exc)
        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data["password"])
        if commit:
            usuario.save()
        return usuario

class LoginForm(forms.Form):
    Usuario = forms.CharField(
        label='',
        max_length=63,
        widget=forms.TextInput(attrs={'placeholder': 'Ingrese su usuario'})
    )
    password = forms.CharField(
        label='',
        max_length=63,
        widget=forms.PasswordInput(attrs={'placeholder': 'Ingrese su contraseña'})
    )

class PreguntasForm(forms.ModelForm):
    class Meta:
        model = Preguntas
        # Autor y fecha se asignan en el servidor, nunca desde campos ocultos.
        fields = ['pelicula', 'Titulo', 'Pregunta', 'categoria']
        labels = {'pelicula': 'Película relacionada (opcional)', 'Titulo': 'Título', 'Pregunta': 'Detalle del problema', 'categoria': 'Motivo de la consulta', 'prioridad': 'Prioridad'}
        widgets = {'Pregunta': forms.Textarea(attrs={'rows': 5, 'maxlength': 5000})}

class PreguntaAdminForm(PreguntasForm):
    class Meta(PreguntasForm.Meta):
        fields = PreguntasForm.Meta.fields + ['prioridad', 'estado']

class RespuestaForm(forms.ModelForm):
    class Meta:
        model = Respuesta
        fields = ['Respuesta']
        widgets = {'Respuesta': forms.Textarea(attrs={'rows': 3, 'maxlength': 2000})}

class AsistenteForm(forms.Form):
    buscar_ayuda = forms.CharField(label='¿En qué podemos ayudarte?', max_length=1000,
                                  widget=forms.Textarea(attrs={'rows': 3}))
    consentimiento = forms.BooleanField(label='Acepto enviar esta consulta al proveedor de IA. No incluiré datos personales.')


class NotaInternaForm(forms.ModelForm):
    class Meta:
        model = NotaInterna
        # Autor y consulta siempre se asignan a partir de la sesión y la URL.
        fields = ['contenido']
        widgets = {'contenido': forms.Textarea(attrs={
            'rows': 3, 'maxlength': 2000, 'placeholder': 'Observación solo para el equipo de soporte'})}


class InvitadoForm(forms.Form):
    nombre = forms.CharField(label='¿Cómo te llamas?', max_length=30,
                             widget=forms.TextInput(attrs={'placeholder': 'Tu nombre o alias', 'autocomplete': 'nickname'}))


class GestionCasoForm(forms.ModelForm):
    class Meta:
        model = Preguntas
        fields = ['estado', 'prioridad']
        labels = {'estado': 'Estado del caso', 'prioridad': 'Prioridad de atención'}
