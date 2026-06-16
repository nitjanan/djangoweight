from django.test import TestCase, Client
from django.urls import reverse
from weightapp.models import BaseCompany, BaseWeightStation, WeightDelivery, DeliveryOrder
import json

class UCWeightDeliveryTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create a test company
        self.company = BaseCompany.objects.create(
            name="Test Company",
            code="TEST_COMP"
        )
        
        # Create a test weight station
        self.bws = BaseWeightStation.objects.create(
            id="BWS_01",
            des="Test Station 1",
            company=self.company
        )

    def test_uc_weight_delivery_success_under_limit(self):
        # Initial capacity is 2
        payload = {
            'weight_id': 101,
            'bws': 'BWS_01',
            'delivery_date': '2026-06-12',
            'do_id': 501,
            'do_doc_no': 'DOC_001',
            'carry_type_name': 'ส่งให้',
            'weight_ton': 10.5,
            'weight_q': 0.0,
            'unit_name': 'ตัน',
            'car_company': 2,
            'car_customer': 0
        }
        
        response = self.client.post(
            '/api/uc_weight_delivery/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertEqual(res_data['status'], 'Create New Item')
        self.assertEqual(res_data['weight_id'], 101)

        # Check DeliveryOrder is updated with correct counts/limits
        do = DeliveryOrder.objects.get(doc_no='DOC_001', comp_code='TEST_COMP')
        self.assertEqual(do.car_company_tot, 1)
        self.assertEqual(do.car_company_rem, 1)

    def test_uc_weight_delivery_limit_exceeded(self):
        # Create one existing active delivery
        WeightDelivery.objects.create(
            weight_id=101,
            delivery_date='2026-06-12',
            bws='BWS_01',
            comp_code='TEST_COMP',
            do_id=501,
            do_doc_no='DOC_001',
            carry_type_name='ส่งให้',
            weight_ton=10.5,
            weight_q=0.0,
            unit_name='ตัน'
        )
        
        # Now limit is 1, and we try to add another active delivery (weight_id 102)
        payload = {
            'weight_id': 102,
            'bws': 'BWS_01',
            'delivery_date': '2026-06-12',
            'do_id': 501,
            'do_doc_no': 'DOC_001',
            'carry_type_name': 'ส่งให้',
            'weight_ton': 10.5,
            'weight_q': 0.0,
            'unit_name': 'ตัน',
            'car_company': 1,
            'car_customer': 0
        }
        
        response = self.client.post(
            '/api/uc_weight_delivery/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 422)
        res_data = response.json()
        self.assertEqual(res_data['status'], 'fail')
        self.assertIn('limit exceeded', res_data['message'])

    def test_uc_weight_delivery_update_allowed_when_limit_reached(self):
        # Limit is 1, and we have 1 delivery. So remaining is 0.
        wd = WeightDelivery.objects.create(
            weight_id=101,
            delivery_date='2026-06-12',
            bws='BWS_01',
            comp_code='TEST_COMP',
            do_id=501,
            do_doc_no='DOC_001',
            carry_type_name='ส่งให้',
            weight_ton=10.5,
            weight_q=0.0,
            unit_name='ตัน'
        )
        
        # We try to update the SAME delivery (weight_id 101).
        # Even though the limit is 1 and it's already reached, this should succeed.
        payload = {
            'weight_id': 101,
            'bws': 'BWS_01',
            'delivery_date': '2026-06-12',
            'do_id': 501,
            'do_doc_no': 'DOC_001',
            'carry_type_name': 'ส่งให้',
            'weight_ton': 12.0, # changed weight
            'weight_q': 0.0,
            'unit_name': 'ตัน',
            'car_company': 1,
            'car_customer': 0
        }
        
        response = self.client.post(
            '/api/uc_weight_delivery/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertEqual(res_data['status'], 'Update Item')
        
        # Verify weight is updated
        wd.refresh_from_db()
        self.assertEqual(wd.weight_ton, 12.0)

    def test_uc_weight_delivery_cancel_allowed_even_when_exceeded(self):
        # We have 1 active delivery and limit is 0
        WeightDelivery.objects.create(
            weight_id=101,
            delivery_date='2026-06-12',
            bws='BWS_01',
            comp_code='TEST_COMP',
            do_id=501,
            do_doc_no='DOC_001',
            carry_type_name='ส่งให้',
            weight_ton=10.5,
            weight_q=0.0,
            unit_name='ตัน'
        )
        
        # Try to update it with is_cancel = True when limit is 0.
        # This is releasing capacity, so it should succeed.
        payload = {
            'weight_id': 101,
            'bws': 'BWS_01',
            'delivery_date': '2026-06-12',
            'do_id': 501,
            'do_doc_no': 'DOC_001',
            'carry_type_name': 'ส่งให้',
            'weight_ton': 10.5,
            'weight_q': 0.0,
            'unit_name': 'ตัน',
            'car_company': 0,
            'car_customer': 0,
            'is_cancel': True
        }
        
        response = self.client.post(
            '/api/uc_weight_delivery/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertEqual(res_data['status'], 'Update Item')

    def test_uc_weight_delivery_preserves_existing_delivery_order_fields(self):
        # Create an existing DeliveryOrder with status, qty, car_company
        DeliveryOrder.objects.create(
            doc_no='DOC_002',
            comp_code='TEST_COMP',
            delivery_date='2026-06-12',
            status='open',
            qty=100.0,
            car_company=5,
            car_customer=2,
            unit_name='ตัน'
        )

        # Call uc_weight_delivery without status, qty, car_company, car_customer in payload
        payload = {
            'weight_id': 102,
            'bws': 'BWS_01',
            'delivery_date': '2026-06-12',
            'do_id': 502,
            'do_doc_no': 'DOC_002',
            'carry_type_name': 'ส่งให้',
            'weight_ton': 15.0,
            'weight_q': 0.0,
            'unit_name': 'ตัน'
        }

        response = self.client.post(
            '/api/uc_weight_delivery/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # Verify that the DeliveryOrder fields are preserved and not cleared/reset to 0
        do = DeliveryOrder.objects.get(doc_no='DOC_002', comp_code='TEST_COMP')
        self.assertEqual(do.status, 'open')
        self.assertEqual(float(do.qty), 100.0)
        self.assertEqual(do.car_company, 5)
        self.assertEqual(do.car_customer, 2)

    def test_uc_status_cancel_do_single_dict(self):
        # Create a DeliveryOrder
        DeliveryOrder.objects.create(
            doc_no='DOC_CANCEL_1',
            comp_code='TEST_COMP',
            delivery_date='2026-06-12',
            status='open'
        )
        
        payload = {
            'doc_no': 'DOC_CANCEL_1',
            'comp_code': 'TEST_COMP',
            'delivery_date': '2026-06-12',
            'status': 'cancelled'
        }
        
        response = self.client.post(
            '/api/uc_status_cancel_do/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertEqual(res_data['status'], 'success')
        self.assertEqual(res_data['updated_count'], 1)
        
        do = DeliveryOrder.objects.get(doc_no='DOC_CANCEL_1', comp_code='TEST_COMP')
        self.assertEqual(do.status, 'cancelled')

    def test_uc_status_cancel_do_list(self):
        # Create DeliveryOrders
        DeliveryOrder.objects.create(
            doc_no='DOC_CANCEL_2',
            comp_code='TEST_COMP',
            delivery_date='2026-06-12',
            status='open'
        )
        DeliveryOrder.objects.create(
            doc_no='DOC_CANCEL_3',
            comp_code='TEST_COMP',
            delivery_date='2026-06-12',
            status='open'
        )
        
        payload = [
            {
                'doc_no': 'DOC_CANCEL_2',
                'comp_code': 'TEST_COMP',
                'delivery_date': '2026-06-12',
                'status': 'cancelled'
            },
            {
                'doc_no': 'DOC_CANCEL_3',
                'comp_code': 'TEST_COMP',
                'delivery_date': '2026-06-12',
                'status': 'cancelled'
            }
        ]
        
        response = self.client.post(
            '/api/uc_status_cancel_do/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertEqual(res_data['status'], 'success')
        self.assertEqual(res_data['updated_count'], 2)
        
        do2 = DeliveryOrder.objects.get(doc_no='DOC_CANCEL_2', comp_code='TEST_COMP')
        self.assertEqual(do2.status, 'cancelled')
        do3 = DeliveryOrder.objects.get(doc_no='DOC_CANCEL_3', comp_code='TEST_COMP')
        self.assertEqual(do3.status, 'cancelled')
