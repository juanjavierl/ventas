from datetime import date, timedelta
from importlib import import_module
from types import SimpleNamespace

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection, transaction
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from app.catalog.models import Client, Orden
from app.tiendas.models import (
    Ciudad,
    Company,
    CuentaPuntos,
    Fidelidad,
    Plataforma,
    Tipo_company,
)


class CuentaPuntosTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='owner', password='test')
        self.category = Tipo_company.objects.create(name='Tienda')
        self.city = Ciudad.objects.create(ciudad='La Paz')
        self.plan = Plataforma.objects.create(
            name='Plan', description='Plan', contracts_min='1', price_min=1,
            contracts_max='12', price_max=1,
        )
        self.company_a = self.make_company('Negocio A')
        self.company_b = self.make_company('Negocio B')
        self.client_record = Client.objects.create(
            names='Cliente', mobile='70000000', email='cliente@example.com'
        )

    def make_company(self, name):
        return Company.objects.create(
            name=name, mobile='70000000', category=self.category, cuidad=self.city,
            user=self.user, plan=self.plan, expiration_date=date.today() + timedelta(days=365),
        )

    def test_accounts_are_independent_by_company_and_client(self):
        account_a = CuentaPuntos.objects.create(company=self.company_a, cliente=self.client_record, puntos=5)
        account_b = CuentaPuntos.objects.create(company=self.company_b, cliente=self.client_record, puntos=9)
        self.assertEqual(CuentaPuntos.objects.filter(cliente=self.client_record).count(), 2)
        self.assertNotEqual(account_a.puntos, account_b.puntos)

    def test_duplicate_company_client_pair_is_rejected(self):
        CuentaPuntos.objects.create(company=self.company_a, cliente=self.client_record)
        with self.assertRaises(IntegrityError), transaction.atomic():
            CuentaPuntos.objects.create(company=self.company_a, cliente=self.client_record)

    def test_migration_assigns_only_unambiguous_account_histories(self):
        ambiguous_client = Client.objects.create(
            names='Ambiguo', mobile='70000001', email='ambiguo@example.com'
        )
        no_orders_client = Client.objects.create(
            names='Sin órdenes', mobile='70000002', email='sin-ordenes@example.com'
        )
        CuentaPuntos.objects.create(cliente=self.client_record)
        CuentaPuntos.objects.create(cliente=ambiguous_client)
        CuentaPuntos.objects.create(cliente=no_orders_client)
        Orden.objects.create(company=self.company_a, client=self.client_record, tipo_venta='tienda')
        Orden.objects.create(company=self.company_a, client=self.client_record, tipo_venta='tienda')
        Orden.objects.create(company=self.company_a, client=ambiguous_client, tipo_venta='tienda')
        Orden.objects.create(company=self.company_b, client=ambiguous_client, tipo_venta='tienda')

        migration = import_module('app.tiendas.migrations.0019_cuentapuntos_company_scope')
        migration.assign_unambiguous_companies(
            apps,
            SimpleNamespace(connection=connection),
        )

        self.assertEqual(
            CuentaPuntos.objects.get(cliente=self.client_record).company_id,
            self.company_a.pk,
        )
        self.assertIsNone(CuentaPuntos.objects.get(cliente=ambiguous_client).company_id)
        self.assertIsNone(CuentaPuntos.objects.get(cliente=no_orders_client).company_id)

    def test_authorizing_order_awards_points_only_once(self):
        Fidelidad.objects.create(
            company=self.company_a, fecha_inicio=date.today() - timedelta(days=1),
            fecha_fin=date.today() + timedelta(days=1), compra_mayores=10,
        )
        order = Orden.objects.create(
            company=self.company_a, client=self.client_record, total=25, tipo_venta='tienda',
        )
        url = reverse('autorizar_orden', args=[order.pk])
        self.client.force_login(self.user)
        self.client.post(url)
        self.client.post(url)
        account = CuentaPuntos.objects.get(company=self.company_a, cliente=self.client_record)
        self.assertEqual(account.puntos, 2)
        self.assertEqual(account.cantidad_compras, 1)

    def test_expired_promotion_activation_resets_only_its_company(self):
        Fidelidad.objects.create(
            company=self.company_a, fecha_inicio=date.today() - timedelta(days=20),
            fecha_fin=date.today() - timedelta(days=1), compra_mayores=10,
        )
        account_a = CuentaPuntos.objects.create(company=self.company_a, cliente=self.client_record, puntos=12, cantidad_compras=4)
        account_b = CuentaPuntos.objects.create(company=self.company_b, cliente=self.client_record, puntos=7, cantidad_compras=3)
        self.client.force_login(self.user)
        response = self.client.post(reverse('add_fidelidad', args=[self.company_a.pk]), {
            'activar_nueva': '1', 'nombre': 'Nueva', 'descripcion': 'Nueva promo',
            'fecha_inicio': (date.today() + timedelta(days=1)).strftime('%d/%m/%Y'),
            'fecha_fin': (date.today() + timedelta(days=30)).strftime('%d/%m/%Y'),
            'compra_mayores': 10, 'activo': 'on',
        })
        self.assertEqual(response.status_code, 200)
        account_a.refresh_from_db()
        account_b.refresh_from_db()
        self.assertEqual((account_a.puntos, account_a.cantidad_compras), (0, 0))
        self.assertEqual((account_b.puntos, account_b.cantidad_compras), (7, 3))

    def test_invalid_dates_and_non_owner_cannot_reset_points(self):
        Fidelidad.objects.create(
            company=self.company_a, fecha_inicio=date.today() - timedelta(days=20),
            fecha_fin=date.today() - timedelta(days=1), compra_mayores=10,
        )
        account = CuentaPuntos.objects.create(company=self.company_a, cliente=self.client_record, puntos=12, cantidad_compras=4)
        self.client.force_login(self.user)
        invalid = self.client.post(reverse('add_fidelidad', args=[self.company_a.pk]), {
            'activar_nueva': '1', 'nombre': 'Nueva', 'descripcion': 'Nueva promo',
            'fecha_inicio': (date.today() + timedelta(days=5)).strftime('%d/%m/%Y'),
            'fecha_fin': (date.today() + timedelta(days=1)).strftime('%d/%m/%Y'),
            'compra_mayores': 10, 'activo': 'on',
        })
        self.assertEqual(invalid.status_code, 400)
        account.refresh_from_db()
        self.assertEqual(account.puntos, 12)

    def test_activation_failure_rolls_back_promotion_and_points(self):
        old_end = date.today() - timedelta(days=1)
        promotion = Fidelidad.objects.create(
            company=self.company_a, fecha_inicio=date.today() - timedelta(days=20),
            fecha_fin=old_end, compra_mayores=10,
        )
        account = CuentaPuntos.objects.create(company=self.company_a, cliente=self.client_record, puntos=12, cantidad_compras=4)
        self.client.force_login(self.user)
        with patch.object(CuentaPuntos.objects, 'filter') as filter_mock:
            filter_mock.return_value.update.side_effect = RuntimeError('forced failure')
            response = self.client.post(reverse('add_fidelidad', args=[self.company_a.pk]), {
                'activar_nueva': '1', 'nombre': 'Nueva', 'descripcion': 'Nueva promo',
                'fecha_inicio': (date.today() + timedelta(days=1)).strftime('%d/%m/%Y'),
                'fecha_fin': (date.today() + timedelta(days=30)).strftime('%d/%m/%Y'),
                'compra_mayores': 10, 'activo': 'on',
            })
        self.assertEqual(response.status_code, 500)
        promotion.refresh_from_db()
        account.refresh_from_db()
        self.assertEqual(promotion.fecha_fin, old_end)
        self.assertEqual((account.puntos, account.cantidad_compras), (12, 4))

        other_user = get_user_model().objects.create_user(username='other', password='test')
        self.client.force_login(other_user)
        denied = self.client.post(reverse('add_fidelidad', args=[self.company_a.pk]), {'activar_nueva': '1'})
        self.assertEqual(denied.status_code, 404)
        account.refresh_from_db()
        self.assertEqual(account.puntos, 12)

    def test_fidelity_ranking_shows_positive_points_for_company_in_order(self):
        Fidelidad.objects.create(
            company=self.company_a, fecha_inicio=date.today() - timedelta(days=1),
            fecha_fin=date.today() + timedelta(days=1), compra_mayores=10,
        )
        second_client = Client.objects.create(
            names='Ana', mobile='70000001', email='ana@example.com',
        )
        CuentaPuntos.objects.create(company=self.company_a, cliente=self.client_record, puntos=5)
        CuentaPuntos.objects.create(company=self.company_a, cliente=second_client, puntos=12)
        CuentaPuntos.objects.create(company=self.company_a, cliente=Client.objects.create(
            names='Sin puntos', mobile='70000002', email='sinpuntos@example.com',
        ), puntos=0)
        CuentaPuntos.objects.create(company=self.company_b, cliente=self.client_record, puntos=99)

        self.client.force_login(self.user)
        response = self.client.get(reverse('ranking_fidelidad', args=[self.company_a.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [cuenta.puntos for cuenta in response.context['cuentas']],
            [12, 5],
        )
        self.assertContains(response, 'Ana')
        self.assertNotContains(response, 'Sin puntos')

    def test_fidelity_ranking_requires_owner_and_current_program(self):
        Fidelidad.objects.create(
            company=self.company_a, fecha_inicio=date.today() - timedelta(days=5),
            fecha_fin=date.today() - timedelta(days=1), compra_mayores=10,
        )
        self.client.force_login(self.user)
        expired = self.client.get(reverse('ranking_fidelidad', args=[self.company_a.pk]))
        self.assertEqual(expired.status_code, 404)

        Fidelidad.objects.filter(company=self.company_a).update(
            fecha_fin=date.today() + timedelta(days=1),
            activo=False,
        )
        inactive = self.client.get(reverse('ranking_fidelidad', args=[self.company_a.pk]))
        self.assertEqual(inactive.status_code, 404)

        other_user = get_user_model().objects.create_user(username='ranking-other', password='test')
        Fidelidad.objects.filter(company=self.company_a).update(activo=True)
        self.client.force_login(other_user)
        not_owner = self.client.get(reverse('ranking_fidelidad', args=[self.company_a.pk]))
        self.assertEqual(not_owner.status_code, 404)
