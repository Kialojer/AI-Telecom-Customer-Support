"""Integration checks: real FastAPI validation + compiled LangGraph, synthetic data."""
import os
import unittest
import xml.etree.ElementTree as ET
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import graph
import main
import postgres


class DemoIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)
        self.customer = deepcopy(postgres.DEMO_CUSTOMERS[0])
        graph.cached_offer.cache_clear()

    def post(self, message, customer=None):
        with patch.object(main, 'get_random_customer', return_value=customer or self.customer) as loader:
            response = self.client.post('/webhook/demo', json={'message': message})
        self.assertEqual(response.status_code, 200, response.text)
        loader.assert_called_once_with()
        data = response.json()
        self.assertEqual(data['customer_id'], (customer or self.customer)['id'])
        self.assertTrue(data['demo'])
        self.assertTrue(data['reply'])
        return data

    def test_technical_support(self):
        for message in ('Minha internet esta lenta', 'Preciso de suporte tecnico',
                        'Minha conexao caiu', 'A internet nao funciona', 'SEM   INTERNET'):
            with self.subTest(message=message):
                data = self.post(message)
                self.assertEqual(data['intent'], 'support')
                self.assertTrue(data['handoff'])
                self.assertEqual(data['queue'], 'customer_service')

    def test_human_handoff_and_cancellation(self):
        for message in ('Quero um atendente', 'Quero falar com humano',
                        'Quero falar com uma pessoa', 'Quero cancelar', 'Cancelamento do plano'):
            with self.subTest(message=message):
                data = self.post(message)
                self.assertEqual((data['intent'], data['handoff'], data['queue']),
                                 ('support', True, 'customer_service'))

    def test_billing_uses_each_supplied_snapshot(self):
        for customer in postgres.DEMO_CUSTOMERS:
            with self.subTest(customer=customer['id']):
                data = self.post('Quero minha fatura', customer)
                self.assertEqual(data['intent'], 'billing')
                self.assertIn(customer['invoice_total'], data['reply'])
                self.assertFalse(data['handoff'])
                self.assertIsNone(data['queue'])

    def test_accented_billing(self):
        self.assertEqual(self.post('Qual e a cobran\u00e7a?')['intent'], 'billing')

    def test_sales_routes_and_matches_interests(self):
        for message in ('Tem alguma oferta?', 'Quero contratar um novo plano',
                        'Quero comprar', 'Vendas', 'Promo\u00e7\u00e3o'):
            with self.subTest(message=message):
                data = self.post(message)
                self.assertEqual(data['intent'], 'offer')
                self.assertIn('streaming', data['reply'])
                self.assertFalse(data['handoff'])
                self.assertIsNone(data['queue'])
        self.assertIn('upgrade de internet', self.post('Ofertas', postgres.DEMO_CUSTOMERS[1])['reply'])

    def test_refused_consent_never_accesses_catalogue(self):
        with patch.object(graph, 'cached_offer', side_effect=AssertionError('consent bypass')):
            data = self.post('Quero uma oferta', postgres.DEMO_CUSTOMERS[2])
        self.assertEqual(data['intent'], 'offer')
        self.assertIn('nao autoriza', data['reply'])
        self.assertNotIn('R$', data['reply'])

    def test_consent_checked_after_cache_hit_and_on_each_request(self):
        customer = deepcopy(self.customer)
        self.post('Oferta', customer)
        self.post('Oferta', customer)
        self.assertEqual(graph.cached_offer.cache_info().hits, 1)
        before = graph.cached_offer.cache_info()
        customer['marketing_opt_in'] = False
        self.assertIn('nao autoriza', self.post('Oferta', customer)['reply'])
        self.assertEqual(graph.cached_offer.cache_info(), before)

    def test_missing_or_malformed_consent_fails_closed(self):
        for consent in (None, 'false', 'true', 1):
            customer = deepcopy(self.customer)
            customer['marketing_opt_in'] = consent
            with self.subTest(consent=consent):
                self.assertIn('nao autoriza', graph.respond(customer, 'Oferta')['reply'])
        del customer['marketing_opt_in']
        self.assertIn('nao autoriza', graph.respond(customer, 'Oferta')['reply'])

    def test_consent_does_not_block_requested_billing_or_support(self):
        customer = postgres.DEMO_CUSTOMERS[2]
        self.assertEqual(self.post('Fatura', customer)['intent'], 'billing')
        self.assertEqual(self.post('Suporte', customer)['intent'], 'support')

    def test_no_matching_offer(self):
        self.customer['interests'] = []
        self.assertIn('Nao encontrei', self.post('Oferta')['reply'])

    def test_faq_and_no_substring_false_positive(self):
        for message in ('Ola', 'Quero contato', 'Estou em contato'):
            with self.subTest(message=message):
                data = self.post(message)
                self.assertEqual(data['intent'], 'faq')
                self.assertIn(self.customer['plan'], data['reply'])
                self.assertFalse(data['handoff'])
                self.assertIsNone(data['queue'])

    def test_support_priority_then_billing_then_sales(self):
        self.assertEqual(self.post('Fatura e internet lenta, quero oferta')['intent'], 'support')
        self.assertEqual(self.post('Fatura e oferta')['intent'], 'billing')

    def test_no_cross_request_handoff_state(self):
        self.post('Atendente')
        data = self.post('Fatura')
        self.assertFalse(data['handoff'])
        self.assertIsNone(data['queue'])

    def test_invalid_requests(self):
        for body in ({}, {'message': ''}, {'message': ' \n\t'}, {'message': 'x' * 2001},
                     {'message': None}, {'message': 42}):
            with self.subTest(body=str(body)[:80]), patch.object(main, 'get_random_customer') as loader:
                self.assertEqual(self.client.post('/webhook/demo', json=body).status_code, 422)
                loader.assert_not_called()

    def test_health_and_random_profile_flow(self):
        self.assertEqual(self.client.get('/health').json(), {'status': 'ok', 'mode': 'synthetic-demo'})
        response = self.client.post('/webhook/demo', json={'message': 'Fatura'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(response.json()['customer_id'], {c['id'] for c in postgres.DEMO_CUSTOMERS})

    def test_customer_loader_returns_independent_copy(self):
        with patch.object(postgres.random, 'choice', return_value=postgres.DEMO_CUSTOMERS[0]):
            one = postgres.get_random_customer()
            one['interests'].append('changed')
            self.assertNotIn('changed', postgres.get_random_customer()['interests'])

    def test_cache_version_and_bound(self):
        graph.cached_offer(('internet',), 'v1')
        graph.cached_offer(('internet',), 'v2')
        self.assertEqual(graph.cached_offer.cache_info().misses, 2)
        for number in range(40):
            graph.cached_offer((), str(number))
        self.assertEqual(graph.cached_offer.cache_info().currsize, 32)


class PostgresAdapterTests(unittest.TestCase):
    """Adapter contract tests use a mocked connection, not a live SQL server."""
    def test_parameterized_lookup_decimal_and_missing_id(self):
        import psycopg
        row = deepcopy(postgres.DEMO_CUSTOMERS[0])
        row['invoice_total'] = Decimal('99.90')
        conn = MagicMock()
        conn.execute.return_value.fetchone.side_effect = [row, None]
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://synthetic-test'}), \
                patch.object(psycopg, 'connect') as connect:
            connect.return_value.__enter__.return_value = conn
            customer = postgres.load_customer_from_postgres("id' OR 1=1 --")
            self.assertEqual(customer['invoice_total'], '99,90')
            self.assertIn('99,90', graph.respond(customer, 'Fatura')['reply'])
            sql, params = conn.execute.call_args.args
            self.assertIn('WHERE id = %s', sql)
            self.assertNotIn("OR 1=1", sql)
            self.assertEqual(params, ("id' OR 1=1 --",))
            self.assertIsNone(postgres.load_customer_from_postgres('missing'))
            self.assertEqual(connect.call_args.kwargs['connect_timeout'], 5)


class ArchitectureTests(unittest.TestCase):
    def test_hld_integrity_and_route_labels(self):
        root = ET.parse(Path(__file__).resolve().parents[1] / 'architecture.drawio').getroot()
        cells = root.findall('.//mxCell')
        ids = {cell.attrib['id'] for cell in cells}
        self.assertEqual(len(ids), len(cells))
        for cell in cells:
            if cell.get('edge') == '1':
                self.assertIn(cell.get('source'), ids)
                self.assertIn(cell.get('target'), ids)
        labels = {cell.get('value') for cell in cells if cell.get('source') == 'router'}
        self.assertEqual(labels, {'faq', 'billing', 'offer', 'support'})
        for optional in ('sql', 'whatsapp'):
            cell = next(cell for cell in cells if cell.get('id') == optional)
            self.assertIn('dashed=1', cell.get('style'))


if __name__ == '__main__':
    unittest.main()
