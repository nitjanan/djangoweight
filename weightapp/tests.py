from django.test import TestCase, Client
from django.urls import reverse
from weightapp.models import BaseCompany, BaseWeightStation, WeightDelivery, DeliveryOrder
import json
from unittest.mock import patch, MagicMock

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

    @patch('weightapp.views.requests.get')
    @patch('weightapp.views.get_base_api')
    def test_insert_delivery_from_api_k2m_insert_and_update(self, mock_get_base_api, mock_requests_get):
        from weightapp.views import insertDeliveryFromApiK2M
        from datetime import date

        # Setup mock responses for the first run (Insert)
        mock_response_insert_1 = MagicMock()
        mock_response_insert_1.json.return_value = {
            "data": [
                {
                    "docNo": "DOC_K2M_001",
                    "qty": 50.0,
                    "carCompany": 3,
                    "carCustomer": 1,
                    "customerCode": "CUST01",
                    "customerName": "Cust Name 1",
                    "customerAddress": "Addr 1",
                    "siteId": "SITE01",
                    "siteName": "Site Name 1",
                    "productCode": "PROD01",
                    "productName": "Prod Name 1",
                    "saleName": "Sale 1",
                    "note": "Note 1",
                    "status": "open",
                    "unitName": "ตัน"
                }
            ]
        }
        mock_response_insert_1.raise_for_status = MagicMock()

        mock_response_insert_2 = MagicMock()
        mock_response_insert_2.json.return_value = {
            "data": []
        }
        mock_response_insert_2.raise_for_status = MagicMock()

        mock_requests_get.side_effect = [mock_response_insert_1, mock_response_insert_2]
        
        # Call the function for insert
        delivery_date = date(2026, 6, 12)
        result = insertDeliveryFromApiK2M(delivery_date)
        self.assertIn("Insert=1", result)
        self.assertIn("Update=0", result)

        # Verify it was created in the database with all fields
        do = DeliveryOrder.objects.get(doc_no="DOC_K2M_001", comp_code="TEST_COMP")
        self.assertEqual(float(do.qty), 50.0)
        self.assertEqual(do.car_company, 3)
        self.assertEqual(do.car_customer, 1)
        self.assertEqual(do.customer_code, "CUST01")
        self.assertEqual(do.site_id, "SITE01")
        self.assertEqual(do.site_name, "Site Name 1")
        self.assertEqual(do.status, "open")

        # Now, setup mock responses for the second run (Update on 'open' status)
        # We simulate the API returning the same order but with updated status and other fields modified.
        # Since the existing status is 'open' (not cancel/cancelled), all fields should be updated.
        mock_response_update_1 = MagicMock()
        mock_response_update_1.json.return_value = {
            "data": [
                {
                    "docNo": "DOC_K2M_001",
                    "qty": 100.0,            # Changed
                    "carCompany": 10,         # Changed
                    "carCustomer": 5,         # Changed
                    "customerCode": "CUST02", # Changed
                    "customerName": "Cust Name 2", # Changed
                    "customerAddress": "Addr 2", # Changed
                    "siteId": "SITE02",       # Changed
                    "siteName": "Site Name 2", # Changed
                    "productCode": "PROD02",  # Changed
                    "productName": "Prod Name 2", # Changed
                    "saleName": "Sale 2",     # Changed
                    "note": "Note 2",         # Changed
                    "status": "closed",       # Changed
                    "unitName": "ชิ้น"         # Changed
                }
            ]
        }
        mock_response_update_1.raise_for_status = MagicMock()

        mock_response_update_2 = MagicMock()
        mock_response_update_2.json.return_value = {
            "data": []
        }
        mock_response_update_2.raise_for_status = MagicMock()

        mock_requests_get.side_effect = [mock_response_update_1, mock_response_update_2]

        # Call the function for update
        result_update = insertDeliveryFromApiK2M(delivery_date)
        self.assertIn("Insert=0", result_update)
        self.assertIn("Update=1", result_update)

        # Verify that only specified fields were updated
        do.refresh_from_db()
        self.assertEqual(do.status, "closed")
        self.assertEqual(float(do.qty), 50.0) # Not updated! Remains 50.0
        self.assertEqual(do.car_company, 3) # Not updated! Remains 3
        self.assertEqual(do.car_customer, 1) # Not updated! Remains 1
        self.assertEqual(do.customer_code, "CUST02") # Updated!
        self.assertEqual(do.customer_name, "Cust Name 2") # Updated!
        self.assertEqual(do.site_id, "SITE02") # Updated!
        self.assertEqual(do.site_name, "Site Name 2") # Updated!
        self.assertEqual(do.unit_name, "ชิ้น") # Updated!

        # Now set the status to 'cancelled' in the DB to test the cancel logic
        do.status = 'cancelled'
        do.save()

        # We simulate the API returning the order again but with status changed back to 'open'
        # and other fields changed.
        mock_response_cancel_1 = MagicMock()
        mock_response_cancel_1.json.return_value = {
            "data": [
                {
                    "docNo": "DOC_K2M_001",
                    "qty": 200.0,            # Changed
                    "carCompany": 20,         # Changed
                    "carCustomer": 15,        # Changed
                    "customerCode": "CUST03", # Changed
                    "customerName": "Cust Name 3", # Changed
                    "customerAddress": "Addr 3", # Changed
                    "siteId": "SITE03",       # Changed
                    "siteName": "Site Name 3", # Changed
                    "productCode": "PROD03",  # Changed
                    "productName": "Prod Name 3", # Changed
                    "saleName": "Sale 3",     # Changed
                    "note": "Note 3",         # Changed
                    "status": "open",         # Changed back to open
                    "unitName": "กล่อง"        # Changed
                }
            ]
        }
        mock_response_cancel_1.raise_for_status = MagicMock()

        mock_response_cancel_2 = MagicMock()
        mock_response_cancel_2.json.return_value = {
            "data": []
        }
        mock_response_cancel_2.raise_for_status = MagicMock()

        mock_requests_get.side_effect = [mock_response_cancel_1, mock_response_cancel_2]

        # Call the function for update on a cancelled order
        result_cancel = insertDeliveryFromApiK2M(delivery_date)
        self.assertIn("Insert=0", result_cancel)
        self.assertIn("Update=1", result_cancel)

        # Verify that only the specified fields were updated
        do.refresh_from_db()
        self.assertEqual(do.status, "open")             # Updated!
        self.assertEqual(float(do.qty), 50.0)            # Kept original 50.0 (not updated to 200.0)
        self.assertEqual(do.car_company, 3)              # Kept original 3
        self.assertEqual(do.car_customer, 1)              # Kept original 1
        self.assertEqual(do.customer_code, "CUST03")      # Updated!
        self.assertEqual(do.customer_name, "Cust Name 3") # Updated!
        self.assertEqual(do.site_id, "SITE03")      # Updated!
        self.assertEqual(do.site_name, "Site Name 3") # Updated!
        self.assertEqual(do.unit_name, "กล่อง")             # Updated!
