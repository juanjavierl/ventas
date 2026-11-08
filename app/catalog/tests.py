import json
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.template.loader import render_to_string
from django.urls import reverse

from app.catalog.models import Category, Client, Orden, Pedido, Product, ProductAttribute
from app.catalog.templatetags.extras import pedido_atributos
from app.tiendas.models import Ciudad, Company, Plataforma, Tipo_company


class ProductAttributesFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.owner = User.objects.create_user(username='owner_attr', password='pw')
        cls.other_owner = User.objects.create_user(username='other_attr', password='pw')
        cls.plan = Plataforma.objects.create(
            name='Plan prueba', description='Plan', contracts_min='1', price_min=1,
            contracts_max='12', price_max=12, cantidad=100,
        )
        cls.city = Ciudad.objects.create(ciudad='La Paz')
        cls.kind = Tipo_company.objects.create(name='Tienda')
        cls.company = Company.objects.create(
            name='Tienda Uno', mobile='70000000', category=cls.kind,
            cuidad=cls.city, user=cls.owner, plan=cls.plan,
            expiration_date=date.today() + timedelta(days=365),
        )
        cls.other_company = Company.objects.create(
            name='Tienda Dos', mobile='71111111', category=cls.kind,
            cuidad=cls.city, user=cls.other_owner, plan=cls.plan,
            expiration_date=date.today() + timedelta(days=365),
        )
        cls.category = Category.objects.create(name='Electrónica')
        cls.product = Product.objects.create(
            name='Teléfono', category=cls.category, company=cls.company,
            price='100.00', stock=10, image=None,
        )
        cls.client_record = Client.objects.create(
            names='Cliente Prueba', mobile='+59170000001', email='cliente-attr@example.com'
        )

    def add_attribute(self, name, values, selectable=True, product=None):
        return ProductAttribute.objects.create(
            product=product or self.product, name=name, values=values,
            is_selectable=selectable,
        )

    def add_to_cart(self, selected=None):
        return self.client.post(
            reverse('detail_product', args=(self.company.id, self.product.id, self.product.get_slug())),
            {'cantidad': '1', 'atributos': json.dumps(selected or {})},
        )

    def test_product_without_attributes_remains_addable(self):
        response = self.add_to_cart()
        self.assertEqual(response.status_code, 200)
        self.assertIn('success', response.json())

    def test_informative_and_selectable_attributes_are_validated(self):
        info = self.add_attribute('Marca', ['Samsung'], selectable=False)
        color = self.add_attribute('Color', ['Negro', 'Azul'])
        self.assertEqual(info.values, [{'value': 'Samsung', 'price_extra': '0.00'}])
        self.assertTrue(color.is_selectable)
        with self.assertRaises(ValidationError):
            ProductAttribute(product=self.product, name='Talla', values=[], is_selectable=True).save()
        with self.assertRaises(ValidationError):
            ProductAttribute(product=self.product, name='Datos', values={'invalid': True}).save()

    def test_cart_requires_valid_options_and_groups_by_option_values(self):
        self.add_attribute('Color', ['Negro', 'Azul'])
        self.add_attribute('Almacenamiento', ['128 GB', '256 GB'])
        missing = self.add_to_cart({'Color': 'Negro'})
        self.assertEqual(missing.status_code, 400)
        invalid = self.add_to_cart({'Color': 'Rojo', 'Almacenamiento': '128 GB'})
        self.assertEqual(invalid.status_code, 400)
        self.add_to_cart({'Color': 'Negro', 'Almacenamiento': '128 GB'})
        self.add_to_cart({'Color': 'Azul', 'Almacenamiento': '128 GB'})
        same = self.add_to_cart({'Color': 'Negro', 'Almacenamiento': '128 GB'})
        cart = self.client.session['compra']
        self.assertEqual(len(cart), 2)
        self.assertEqual(cart[0]['cantidad'], 2)
        self.assertEqual(cart[1]['atributos']['Color'], 'Azul')
        self.assertEqual(same.status_code, 200)

    def test_attribute_management_is_scoped_to_product_owner(self):
        self.client.force_login(self.other_owner)
        response = self.client.post(
            reverse('manage_product_attribute', args=(self.product.id,)),
            {'name': 'Color', 'values': 'Negro\nAzul', 'is_selectable': 'on'},
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(ProductAttribute.objects.filter(product=self.product).exists())

    def test_confirmed_order_keeps_attribute_snapshot_and_old_orders_default_empty(self):
        self.add_attribute('Color', ['Negro', 'Azul'])
        self.add_to_cart({'Color': 'Negro'})
        old_order = Orden.objects.create(
            company=self.company, client=self.client_record, subtotal=0, total=0, tipo_venta='tienda'
        )
        old_line = Pedido.objects.create(orden=old_order, product=self.product, cant=1)
        self.assertEqual(old_line.atributos_seleccionados, {})

        response = self.client.post(reverse('confirmar_compra', args=(self.company.id,)), {
            'email': self.client_record.email, 'mobile': self.client_record.mobile,
            'tipo_envio': 'tienda',
            'date_time': (date.today() + timedelta(days=1)).strftime('%Y-%m-%dT12:00'),
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('success', response.json())
        line = Pedido.objects.exclude(pk=old_line.pk).get()
        self.assertEqual(line.atributos_seleccionados, {'Color': {'value': 'Negro', 'price_extra': '0.00'}})
        ProductAttribute.objects.filter(product=self.product, name='Color').delete()
        line.refresh_from_db()
        self.assertEqual(line.atributos_seleccionados, {'Color': {'value': 'Negro', 'price_extra': '0.00'}})
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)
        self.assertEqual(self.product.salida, 0)

    def test_option_prices_and_tampered_session_price_are_recalculated(self):
        self.add_attribute('RAM', [
            {'value': '8 GB', 'price_extra': '0'},
            {'value': '16 GB', 'price_extra': '500.25'},
        ])
        self.add_attribute('Disco', [
            {'value': '256 GB', 'price_extra': '0'},
            {'value': '128 GB', 'price_extra': '-300.10'},
        ])
        response = self.add_to_cart({'RAM': '16 GB', 'Disco': '128 GB'})
        self.assertEqual(response.status_code, 200)
        cart = self.client.session['compra']
        self.assertEqual(cart[0]['precio_uni'], '300.15')
        cart[0]['precio_uni'] = '0.01'
        self.client.session['compra'] = cart
        self.client.session.save()
        response = self.client.post(reverse('confirmar_compra', args=(self.company.id,)), {
            'email': self.client_record.email, 'mobile': self.client_record.mobile,
            'tipo_envio': 'tienda',
            'date_time': (date.today() + timedelta(days=1)).strftime('%Y-%m-%dT12:00'),
        })
        self.assertEqual(response.status_code, 200)
        line = Pedido.objects.latest('id')
        self.assertEqual(line.price, Decimal('300.15'))
        self.assertEqual(line.atributos_seleccionados['RAM']['price_extra'], '500.25')
        self.assertEqual(self.product.stock_actual(), 10)

    def test_legacy_options_and_invalid_decimal(self):
        attribute = self.add_attribute('Color', ['Negro', 'Azul'])
        response = self.add_to_cart({'Color': 'Azul'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session['compra'][0]['precio_uni'], '100.00')
        with self.assertRaises(ValidationError):
            ProductAttribute(product=self.product, name='RAM', values=[
                {'value': '8 GB', 'price_extra': 'not-a-number'}
            ], is_selectable=True).save()

    def test_order_attribute_report_presentation_supports_new_and_legacy_snapshots(self):
        order = Orden.objects.create(
            company=self.company, client=self.client_record, subtotal=0, total=0, tipo_venta='tienda'
        )
        line = Pedido.objects.create(
            orden=order, product=self.product, cant=1,
            atributos_seleccionados={
                'Disco duro': {'value': '500 GB', 'price_extra': '500.00'},
                'RAM': {'value': '16 GB', 'price_extra': '300.00'},
                'Descuento': {'value': 'Opción básica', 'price_extra': '-50.00'},
                'Color': {'value': 'Azul', 'price_extra': '0.00'},
                'Antiguo': 'Negro',
            },
        )
        html = render_to_string('reportes/_pedido_atributos.html', pedido_atributos(line))
        self.assertIn('Disco duro: 500 GB (P. extra: 500,00 Bs)', html)
        self.assertIn('RAM: 16 GB (P. extra: 300,00 Bs)', html)
        self.assertIn('Descuento: Opción básica (Descuento: -50,00 Bs)', html)
        self.assertIn('Color: Azul', html)
        self.assertIn('Antiguo: Negro', html)
        self.assertNotIn('Color: Azul (P. extra', html)
