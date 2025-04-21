from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from app.catalog.models import Company, Product
from app.tiendas.models import Tipo_company, Ciudad

class IndexSitemap(Sitemap):
    changefreq = "daily"
    priority = 1.0

    def items(self):
        return ['inicio']  # El nombre de tu vista en urls.py

    def location(self, item):
        return reverse(item)

class CompanySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Company.objects.filter(status=True)

    def location(self, obj):
        return f'/{obj.id}/catalogo'


class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Product.objects.filter(company__status=True)

    def location(self, obj):
        return f'/{obj.id}/{obj.company.id}/detail_product'

class TipoCompanySitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return Tipo_company.objects.all()

    def location(self, obj):
        return f'/{obj.id}/type/'

class CiudadSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return Ciudad.objects.all()

    def location(self, obj):
        return f'/{obj.id}/city/'