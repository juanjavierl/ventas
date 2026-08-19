from urllib.parse import urlparse

from django import forms
from PIL import Image, UnidentifiedImageError
from app.catalog.models import *
from django.core.exceptions import ValidationError
import phonenumbers

ALLOWED_VIDEO_HOSTS = (
    'youtube.com',
    'youtu.be',
    'tiktok.com',
    'facebook.com',
    'fb.watch',
)


def validate_product_video_url(value):
    if not value:
        return value

    value = value.strip()

    if '<' in value or '>' in value:
        raise ValidationError(
            'Ingrese solo la URL del video, no código HTML ni iframe.'
        )

    parsed = urlparse(value)
    if parsed.scheme not in ('http', 'https'):
        raise ValidationError('Ingrese una URL válida con http o https.')

    host = parsed.netloc.lower()
    if host.startswith('www.'):
        host = host[4:]

    if not any(host == allowed or host.endswith('.' + allowed) for allowed in ALLOWED_VIDEO_HOSTS):
        raise ValidationError(
            'Solo se permiten enlaces de YouTube, TikTok o Facebook.'
        )

    return value


class ProductVideoUrlMixin:
    def clean_video_url(self):
        return validate_product_video_url(self.cleaned_data.get('video_url'))

class ClientFormOrder(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['names'].widget.attrs['autofocus'] = True

    class Meta:
        model = Client
        exclude = ('gender','date_joined',)
        #fields = '__all__'

    def clean_mobile(self):
        mobile = self.cleaned_data['mobile']
        try:
            parsed = phonenumbers.parse(mobile, None)
            if not phonenumbers.is_valid_number(parsed):
                raise ValidationError("Número de teléfono inválido.")
        except:
            raise ValidationError("Ingrese un número válido con su código de país.")
        
        return mobile

class formUpdateProducto(ProductVideoUrlMixin, forms.ModelForm):
    def clean_image(self):
        image = self.cleaned_data.get('image')

        if image:
            try:
                # Intentar abrir con Pillow para verificar si realmente es una imagen
                img = Image.open(image)
                img.verify()  # Lanza error si no es una imagen válida

                # Validar el formato permitido
                formato_permitido = ['JPEG', 'JPG', 'PNG', 'WEBP']
                if img.format.upper() not in formato_permitido:
                    raise forms.ValidationError("Formato de imagen no permitido. Solo se permiten JPG, PNG o WEBP.")

            except UnidentifiedImageError:
                raise forms.ValidationError("El archivo no es una imagen válida.")
            except Exception:
                raise forms.ValidationError("Error al procesar la imagen.")
        return image

    class Meta:
        model = Product
        exclude = ['company', 'salida', 'date_joined', 'stock']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea({'class': 'form-control', 'rows': 2, 'cols': 3}),
           
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'price_before': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'video_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://...',
            }),
        }

class formProducto(ProductVideoUrlMixin, forms.ModelForm):
    class Meta:
        model = Product
        exclude = ['company', 'salida', 'date_joined']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control','autofocus': True,}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea({'class': 'form-control', 'rows': 2, 'cols': 3}),
           
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'price_before': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control','accept': 'jpeg, jpg, png, webp',}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'video_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://...',
            }),
        }

class formCategory(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['autofocus'] = True

    class Meta:
        model = Category
        #exclude = ('gender','date_joined','email',)
        fields = '__all__'

class FormLike(forms.ModelForm):
    class Meta:
        model = Like
        exclude = ('company','date_joined')

class FormImgProducto(forms.ModelForm):
    class Meta:
        model = Imagen
        exclude = ('items',)