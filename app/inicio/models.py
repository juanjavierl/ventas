from django.db import models
from ventas import settings
from django.utils.text import slugify
from urllib.parse import urlparse, parse_qs
# Create your models here.
class Dashboard(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='Nombre del Sistema')
    description = models.TextField(verbose_name='Descripcion', help_text='Escriba una descripción de que trata.?')
    icon = models.CharField(max_length=100, verbose_name='Icono FontAwesome', default="bi bi-shop-window")
    image = models.ImageField(upload_to='dashboard/%Y/%m/%d', null=True, blank=True, verbose_name='Logo')
    author = models.CharField(max_length=120, verbose_name='Autor', default="jjavierl")
    mobile = models.CharField(max_length=10, verbose_name='Celular*')
    email = models.CharField(max_length=50, null=True, blank=True, verbose_name='Email')
    address = models.CharField(max_length=500, null=True, blank=True, verbose_name='Dirección*', help_text="Ingrese:Calle,Nro,Zona")
    codigo = models.CharField(max_length=50, verbose_name='Pixel_id', null=True, blank=True, help_text='Copie pixel id de Meta')

    def __str__(self):
        return self.name

    def get_meta_title(self):
        return self.name

    def get_meta_description(self):
        return self.description

    def get_meta_image(self):
        return self.get_image()

    def get_meta_url(self):
        return '/'

    def get_image(self):
        if self.image:
            return f'{settings.MEDIA_URL}{self.image}'
        return f'{settings.STATIC_URL}img/empty.png'

    class Meta:
        verbose_name = 'Dashboard'
        verbose_name_plural = 'Dashboards'
        default_permissions = ()
        permissions = (
            ('view_dashboard', 'Can view Dashboard'),
        )

class Proyecto(models.Model):
    """Model definition for Proyecto."""
    name = models.CharField(max_length=150, verbose_name='Nombre del Proyecto')
    description = models.TextField(verbose_name='Descripcion', help_text='Escriba una descripción de que trata.?')
    technology = models.TextField(verbose_name='Tecnologia', help_text='Tecnologias utilizadas')
    warning = models.TextField(verbose_name='Aviso', help_text='Aviso legal o de privacidad')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio', help_text='Ingrese el precio del proyecto')
    module = models.TextField(verbose_name='Modulo', help_text='Ingrese los modulos del proyecto')
    image = models.ImageField(upload_to='proyectos', null=True, blank=True, verbose_name='Imagen del Proyecto')
    video_url = models.URLField(verbose_name='Video URL', help_text='Ingrese la URL del video')
    def __str__(self):
        return self.name

    def get_slug_name(self):
        slug = slugify(self.name)
        return slug or f'producto-{self.id}'

    class Meta:
        """Meta definition for Proyecto."""

        verbose_name = 'Proyecto'
        verbose_name_plural = 'Proyectos'

    def get_video_embed(self):
        if not self.video_url:
            return ''

        url = self.video_url.strip()

        # YouTube normal
        if 'youtube.com/watch' in url:
            query = parse_qs(urlparse(url).query)
            video_id = query.get('v', [None])[0]

            if video_id:
                return f'https://www.youtube.com/embed/{video_id}'

        # YouTube corto
        if 'youtu.be/' in url:
            video_id = urlparse(url).path.strip('/')

            if video_id:
                return f'https://www.youtube.com/embed/{video_id}'

        # Si ya registraste un enlace embed
        if 'youtube.com/embed/' in url:
            return url

        return ''