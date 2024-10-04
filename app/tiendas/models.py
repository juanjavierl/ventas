from datetime import datetime, date
from random import randint
from django.forms import model_to_dict
from django.db import models
from django.contrib.auth.forms import User

from ventas import settings

class Tipo_company(models.Model):
    """Model definition for Categoria  ."""
    name = models.CharField('Categoria', max_length=50)
    description = models.CharField('Descripción',max_length=255, blank=True, null=True)
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

    def num_vistos(self):
        num = randint(1500,5000)
        return num

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
    name = models.CharField(max_length=20, verbose_name="Nombre")
    description = models.CharField(max_length=150, verbose_name="Descripción")
    
    contracts_min = models.CharField(verbose_name="Tiempo de minimo", max_length=50)
    price_min = models.IntegerField(verbose_name="Precio")

    contracts_max = models.CharField(verbose_name="Tiempo de maximo", max_length=50)
    price_max = models.IntegerField(verbose_name="Precio")

    icono = models.CharField(max_length=100, verbose_name="Icono de Bootstrap", default="bi bi-clipboard2-check")
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
    description = models.CharField(max_length=500, null=True, blank=True, verbose_name='Descripción de su catalogo (Opcional)')
    ruc = models.CharField(max_length=15, blank=True, null=True, verbose_name='Número de NIT (Opcional)')
    address = models.CharField(max_length=200, verbose_name='Dirección (Zona, Calle, #)')
    mobile = models.CharField(max_length=10, verbose_name='Celular (WhatsApp)')
    category = models.ForeignKey(Tipo_company, on_delete=models.CASCADE, verbose_name='Tipo de Compañia')
    cuidad = models.ForeignKey(Ciudad, on_delete=models.CASCADE, verbose_name='Ciudad')
    #phone = models.CharField(max_length=9, verbose_name='Teléfono convencional')
    #email = models.CharField(max_length=50, verbose_name='Email')
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    website = models.CharField(max_length=250, verbose_name='Link a grupo de WhatsApp', blank=True, null=True, help_text="Tus clientes se uniran mediante este link")
    #iva = models.DecimalField(default=0.00, decimal_places=2, max_digits=9, verbose_name='IVA')
    image = models.ImageField(null=True, blank=True, upload_to='company/%Y/%m/%d', verbose_name='Logotipo de la empresa (Opcional)')    
    date_joined = models.DateField(default=datetime.now, verbose_name='Fecha de registro')
    plan = models.ForeignKey(Plataforma, on_delete=models.CASCADE, verbose_name="Seleccione un plan")

    def __str__(self):
        return self.name
    
    def contarLikes(self):
        from app.catalog.models import Like
        suma_likes = Like.objects.filter(company_id=self.id).aggregate(like=models.Sum('like'))
        if suma_likes['like'] == None:
            suma_likes = {'like':0}
            return suma_likes
        else:
            return suma_likes

    def get_iva(self):
        return float(self.iva)

    def get_image(self):
        if self.image:
            return f'{settings.MEDIA_URL}{self.image}'
        return f'{settings.STATIC_URL}img/default/empty.png'

    def toJSON(self):
        item = model_to_dict(self)
        item['image'] = self.get_image()
        item['id'] = int(self.id)
        item['name'] = self.name
        item['mobile'] = self.mobile
        item['description'] = self.description
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
    destinatario = models.CharField(max_length=60, verbose_name='A Nombre de')
    cuenta = models.CharField(max_length=50, verbose_name='Nro. de cuenta')
    qr_img = models.ImageField(null=True, blank=True, upload_to='img_qr', verbose_name='Img QR de pago', help_text="Recomendación que sea valido de un año o mas")
    company = models.OneToOneField(Company, on_delete=models.CASCADE, verbose_name='Negocio')
    class Meta:
        """Meta definition for Bancos."""
        verbose_name = 'Banco'
        verbose_name_plural = 'Bancos'

    def __str__(self):
        return self.name

    def get_image(self):
        if self.qr_img:
            return f'{settings.MEDIA_URL}{self.qr_img}'
        return f'{settings.STATIC_URL}img/empty.png'
    
    def toJSON(self):
        item = model_to_dict(self)
        item['name'] = self.name
        item['destinatario'] = self.destinatario
        item['cuenta'] = self.cuenta
        item['qr_img'] = self.get_image()
        #item['company'] = self.category.toJSON()
        return item

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

    def toJSON(self):
        item = model_to_dict(self)
        item['company'] = self.company.name
        item['precio'] = self.precio
        item['date_joined'] = self.date_joined.strftime('%Y-%m-%d')
        return item

class Aviso(models.Model):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, verbose_name='Negocio')
    Tiempo_entrega = models.CharField(verbose_name='Tiempo de Entrega', max_length=50, help_text="Ejemplo: En 24 Hrs.")
    envios = models.CharField(verbose_name='Lugar de envio', max_length=50, help_text="Ejemplo: Envios a todo el pais")
    pedidos = models.CharField(verbose_name='Pedidos', max_length=50, help_text="Ejemplo: Pedidos las 24 hrs.")
    pide_ahora = models.CharField(verbose_name='Metodo de Pedir', max_length=50, help_text="Ejemplo: Pide ahora y pague en casa")

    def __str__(self):
        return self.company.name

    def toJSON(self):
        item = model_to_dict(self)
        item['company'] = self.company.name
        item['Tiempo_entrega'] = self.Tiempo_entrega
        item['envios'] = self.envios
        item['pedidos'] = self.pedidos
        item['pide_ahora'] = self.pide_ahora
        return item