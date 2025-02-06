from django.db import models

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
    codigo = models.TextField(verbose_name='Código Pixel de Facebook', null=True, blank=True, help_text='Copie aqui el código pixel de facebook')

    def __str__(self):
        return self.name

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

class Bank_dashboard(models.Model):
    """Model definition for Bancos."""
    name = models.CharField(max_length=50, verbose_name='Nombre del Banco')
    cuenta = models.CharField(max_length=50, verbose_name='Nro. de cuenta')
    qr_img = models.ImageField(null=True, blank=True, upload_to='img_qr', verbose_name='Img QR de pago', help_text="Imagen que tenga validacion de un año")
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, verbose_name='Negocio')
    class Meta:
        """Meta definition for Bancos."""

        verbose_name = 'Banco'
        verbose_name_plural = 'Bancos'

    def __str__(self):
        """Unicode representation of Bancos."""
        return self.name