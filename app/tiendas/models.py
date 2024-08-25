from datetime import datetime, date

from django.db import models
from django.contrib.auth.forms import User

class Tipo_company(models.Model):
    """Model definition for Categoria  ."""
    name = models.CharField('Categoria', max_length=50)
    description = models.CharField('Descripcion',max_length=255, blank=True, null=True)
    icono = models.CharField('Icono de Bootstrap', default="bi bi-shop-window",max_length=50)
    is_new = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_mod = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta definition for Categoria   ."""

        verbose_name = 'Tipo_company'
        verbose_name_plural = 'Tipo_companys'
    
    def __str__(self):
        """Unicode representation of Categoria ."""
        return self.name


class Ciudad(models.Model):
    """Model definition for Cuidad."""
    ciudad = models.CharField('Lugar/Ciudad', max_length=50)

    class Meta:
        """Meta definition for Cuidad."""

        verbose_name = 'Ciudad'
        verbose_name_plural = 'Ciudads'

    def __str__(self):
        """Unicode representation of Cuidad."""
        return self.ciudad

class Plataforma(models.Model):
    name = models.CharField(max_length=20)
    description = models.CharField(max_length=150, verbose_name="Descripcion")
    icono = models.CharField(max_length=100, verbose_name="Icono de Bootstrap", default="bi bi-file-bar-graph")
    qr_img = models.ImageField(upload_to='img_qr', verbose_name='Img QR de pago', help_text="Imagen que tenga validacion de un año")

    class Meta:
        """Meta definition for Cuidad."""

        verbose_name = 'Plataforma'
        verbose_name_plural = 'Plataformas'
    
    def __str__(self):
        """Unicode representation of Cuidad."""
        return self.name

class Company(models.Model):
    name = models.CharField(max_length=50, verbose_name='Nombre/Razón social')
    description = models.CharField(max_length=500, null=True, blank=True, verbose_name='Descripcion de su catalogo (Opcional)')
    ruc = models.CharField(max_length=15, blank=True, null=True, verbose_name='Número de NIT (Opcional)')
    address = models.CharField(max_length=200, verbose_name='Dirección (Calle, Nro, Zona)')
    mobile = models.CharField(max_length=10, verbose_name='Celular (WhatsApp)')
    category = models.ForeignKey(Tipo_company, on_delete=models.CASCADE, verbose_name='Tipo de Compañia')
    cuidad = models.ForeignKey(Ciudad, on_delete=models.CASCADE, verbose_name='Cuidad')
    #phone = models.CharField(max_length=9, verbose_name='Teléfono convencional')
    #email = models.CharField(max_length=50, verbose_name='Email')
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    #website = models.CharField(max_length=250, verbose_name='Dirección de página web', blank=True, null=True)
    #iva = models.DecimalField(default=0.00, decimal_places=2, max_digits=9, verbose_name='IVA')
    image = models.ImageField(null=True, blank=True, upload_to='company/%Y/%m/%d', verbose_name='Logotipo de la empresa (Opcional)')    
    date_joined = models.DateField(default=datetime.now, verbose_name='Fecha de registro')
    plan = models.ForeignKey(Plataforma, on_delete=models.CASCADE, verbose_name="Seleccione un plan")

    def __str__(self):
        return self.name

    def get_iva(self):
        return float(self.iva)

    def get_image(self):
        if self.image:
            return f'{settings.MEDIA_URL}{self.image}'
        return f'{settings.STATIC_URL}img/default/empty.png'

    def toJSON(self):
        item = model_to_dict(self)
        item['image'] = self.get_image()
        item['iva'] = float(self.iva)
        return item

    class Meta:
        verbose_name = 'Compañia'
        verbose_name_plural = 'Compañias'
        default_permissions = ()
        permissions = (
            ('view_company', 'Can view Empresa'),
        )

class Banco(models.Model):
    """Model definition for Bancos."""
    name = models.CharField(max_length=50, verbose_name='Nombre del Banco')
    destinatario = models.CharField(max_length=60, verbose_name='Nombre Destinatario')
    cuenta = models.CharField(max_length=50, verbose_name='Nro. de cuenta')
    qr_img = models.ImageField(null=True, blank=True, upload_to='img_qr', verbose_name='Img QR de pago', help_text="Imagen que tenga validacion de un año o mas")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Negocio')
    class Meta:
        """Meta definition for Bancos."""

        verbose_name = 'Banco'
        verbose_name_plural = 'Bancos'

    def __str__(self):
        """Unicode representation of Bancos."""
        return self.name

class Sucursal(models.Model):
    company=models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Negocio')
    latitud=models.CharField(max_length=50, verbose_name='Latitud')
    longitud=models.CharField(max_length=50, verbose_name='Longitud')
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company.name

class Precio_envio(models.Model):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, verbose_name='Negocio')
    precio = models.IntegerField(verbose_name='Precio de Envio')
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company.name