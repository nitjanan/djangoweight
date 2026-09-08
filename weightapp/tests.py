from django.test import TestCase, Client
from django.urls import reverse
from weightapp.models import BaseCompany, BaseWeightStation, WeightDelivery, DeliveryOrder, BaseCarryType, BaseTransport
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
                    "deliveryCode": "01-V-002___SITE01",
                    "deliveryLocation": "Site Name 1",
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
                    "deliveryCode": "01-V-002___SITE02",       # Changed
                    "deliveryLocation": "Site Name 2", # Changed
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
                    "deliveryCode": "01-V-002___SITE03",       # Changed
                    "deliveryLocation": "Site Name 3", # Changed
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


class UpdateWeightDeliveryAndDeliveryOrderTests(TestCase):
    def setUp(self):
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
        
        # Create carry types
        self.carry_type_customer = BaseCarryType.objects.create(
            base_carry_type_id="CUST_CARRY",
            base_carry_type_name="รับเอง"
        )
        self.carry_type_company = BaseCarryType.objects.create(
            base_carry_type_id="COMP_CARRY",
            base_carry_type_name="ส่งให้"
        )
        
        # Create transports
        self.transport_customer = BaseTransport.objects.create(
            base_transport_id="TRANS_CUST",
            base_transport_name="Customer Transport",
            base_carry_type=self.carry_type_customer
        )
        self.transport_company = BaseTransport.objects.create(
            base_transport_id="TRANS_COMP",
            base_transport_name="Company Transport",
            base_carry_type=self.carry_type_company
        )

        # Create DeliveryOrder
        self.do = DeliveryOrder.objects.create(
            delivery_date="2026-06-18",
            doc_no="DOC_002",
            car_company=1,
            car_customer=1,
            car_company_tot=0,
            car_customer_tot=0,
            car_company_rem=1,
            car_customer_rem=1,
            comp_code="TEST_COMP",
            unit_name="ตัน"
        )

    def test_update_weight_delivery_and_delivery_order_limit_exceeded(self):
        from weightapp.views import updateWeightDeliveryAndDeliveryOrder
        
        # Create existing active deliveries to reach limit
        WeightDelivery.objects.create(
            weight_id=1,
            delivery_date='2026-06-18',
            bws='BWS_01',
            comp_code='TEST_COMP',
            do_id=self.do.id,
            do_doc_no='DOC_002',
            carry_type_name='รับเอง',
            weight_ton=10.0,
            weight_q=0.0,
            unit_name='ตัน'
        )
        
        # Now try to update another weight to 'รับเอง' which would exceed the customer car limit (max 1)
        success, error_msg = updateWeightDeliveryAndDeliveryOrder(
            weight_id=2,
            new_transport=self.transport_customer,
            do_doc_no='DOC_002',
            delivery_date='2026-06-18',
            comp_code='TEST_COMP',
            weight_ton=5.0,
            weight_q=0.0,
            unit_name='ตัน',
            bws_id='BWS_01',
            is_cancel=False
        )
        self.assertFalse(success)
        self.assertEqual(error_msg, "รถลูกค้ามากกว่าที่ plan ไว้ไม่สามารถแก้ไขข้อมูลได้")

    def test_update_weight_delivery_and_delivery_order_success(self):
        from weightapp.views import updateWeightDeliveryAndDeliveryOrder
        
        # We update weight 2 to 'ส่งให้' which is under the limit of 1
        success, error_msg = updateWeightDeliveryAndDeliveryOrder(
            weight_id=2,
            new_transport=self.transport_company,
            do_doc_no='DOC_002',
            delivery_date='2026-06-18',
            comp_code='TEST_COMP',
            weight_ton=5.0,
            weight_q=0.0,
            unit_name='ตัน',
            bws_id='BWS_01',
            is_cancel=False
        )
        self.assertTrue(success)
        self.assertIsNone(error_msg)
        
        # Check that DeliveryOrder was updated properly
        self.do.refresh_from_db()
        self.assertEqual(self.do.car_company_tot, 1)
        self.assertEqual(self.do.car_company_rem, 0)



class ExportExcelWeightTableTests(TestCase):
    """export ของหน้า weight/table : /weight/table/export/"""

    def setUp(self):
        from django.contrib.auth.models import User
        from weightapp.models import UserProfile, Weight, BaseWeightType

        self.client = Client()

        self.company = BaseCompany.objects.create(name="Export Company", code="EXP_COMP")
        self.other_company = BaseCompany.objects.create(name="Other Company", code="OTH_COMP")

        self.weight_type = BaseWeightType.objects.create(name="ขาย")

        self.bws = BaseWeightStation.objects.create(
            id="BWS_EXP", des="Export Station",
            weight_type=self.weight_type, company=self.company)
        self.other_bws = BaseWeightStation.objects.create(
            id="BWS_OTH", des="Other Station",
            weight_type=self.weight_type, company=self.other_company)

        self.user = User.objects.create_user(username="exporter", password="pass12345")
        profile = UserProfile.objects.create(user=self.user)
        profile.company.add(self.company)

        # 25 รายการ (มากกว่า 1 หน้าที่หน้าเว็บแบ่งไว้หน้าละ 10)
        for n in range(25):
            Weight.objects.create(
                weight_id=1000 + n,
                bws=self.bws,
                date='2026-06-01',
                doc_id='DOC%03d' % n,
                do_doc_no='DO%03d' % n,
                car_registration_name='กข %d' % n,
                customer_name='ลูกค้า %d' % n,
                stone_type_name='หิน %d' % n,
                stone_desc='หินก้อนใหญ่',
                stone_color='แดง',
                driver_name='คนขับ %d' % n,
                car_team_name='ทีม A',
                transport='TRANS01',
                carry_type_name='ส่งให้',
                province='ระยอง',
                pay='เงินสด',
                clean_type='ล้างหิน',
                scoop_name='รถตัก 1',
                note='หมายเหตุทดสอบ',
                line_type='สายสั้น',
                vat_type='รวมภาษี',
                weight_in=10,
                weight_out=4,
                weight_total=6,
                q=1.5,
                origin_weight=6.5,
                origin_q=1.6,
                oil_content=2.25,
                price_per_ton=100.5,
                amount=603.0,
                vat=42.21,
                amount_vat=645.21,
                is_s=True,
                is_cancel=False,
                is_apw=True,
                scale_name='ผู้ชั่ง',
            )

        # รายการที่มีค่าว่าง (null) ทั้งแถว
        Weight.objects.create(weight_id=2000, bws=self.bws, date='2026-06-01', doc_id='DOC_NULL')

        # รายการของบริษัทอื่น ต้องไม่ถูก export
        Weight.objects.create(weight_id=3000, bws=self.other_bws, date='2026-06-01', doc_id='DOC_OTHER')

    def login(self):
        self.client.login(username="exporter", password="pass12345")
        session = self.client.session
        session['company_code'] = 'EXP_COMP'
        session.save()

    def loadSheet(self, response):
        import openpyxl
        from io import BytesIO
        return openpyxl.load_workbook(BytesIO(response.content)).active

    def test_export_requires_login(self):
        response = self.client.get('/weight/table/export/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])

    def test_export_returns_xlsx(self):
        self.login()
        response = self.client.get('/weight/table/export/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertIn('weight_table_', response['Content-Disposition'])
        self.assertIn('.xlsx', response['Content-Disposition'])
        # ไฟล์ xlsx เปิดอ่านได้จริง
        self.assertIsNotNone(self.loadSheet(response))

    def test_export_headers_match_edit_weight_labels(self):
        from weightapp.views import WEIGHT_TABLE_EXPORT_COLUMNS

        self.login()
        sheet = self.loadSheet(self.client.get('/weight/table/export/'))
        headers = [cell.value for cell in sheet[1]]

        self.assertEqual(headers, [label for key, label, fmt in WEIGHT_TABLE_EXPORT_COLUMNS])
        # ชื่อหัวคอลัมน์ตรงกับที่ใช้ในหน้า editWeightSell / editWeightStock / editWeightPort
        for label in ['เลขที่เอกสาร', 'วันที่', 'ทะเบียนรถ', 'ลูกค้า', 'ชนิดหิน',
                      'ต้นทาง', 'ปลายทาง', 'น้ำหนักเข้า', 'น้ำหนักออก', 'น้ำหนักสุทธิ']:
            self.assertIn(label, headers)

    def test_export_headers_no_duplicates(self):
        """ฟิลด์เดียวกันที่ปรากฏในหลายฟอร์มแก้ไข ต้อง export แค่ครั้งเดียว"""
        from weightapp.views import WEIGHT_TABLE_EXPORT_COLUMNS

        self.login()
        sheet = self.loadSheet(self.client.get('/weight/table/export/'))
        headers = [cell.value for cell in sheet[1]]

        self.assertEqual(len(headers), len(set(headers)))
        self.assertEqual(len(WEIGHT_TABLE_EXPORT_COLUMNS), len(set(k for k, l, f in WEIGHT_TABLE_EXPORT_COLUMNS)))

    def test_export_includes_all_fields_from_edit_weight_port(self):
        """ทุกฟิลด์ที่แสดง/แก้ไขได้ใน editWeightPort.html ต้องอยู่ใน export"""
        self.login()
        sheet = self.loadSheet(self.client.get('/weight/table/export/'))
        headers = [cell.value for cell in sheet[1]]

        port_labels = [
            'วันที่', 'เลขที่เอกสาร', 'จ่ายเงิน', 'ประเภทสาย', 'ลูกค้า', 'ปลายทาง',
            'รหัสขนส่ง', 'ขนส่ง', 'ทะเบียนรถ', 'จังหวัด', 'ผู้ขับ', 'ทีม', 'ต้นทาง', 'ชนิดหิน',
            'รายละเอียดหิน', 'หมายเหตุ', 'น้ำหนักเข้า', 'น้ำหนักออก', 'น้ำหนักสุทธิ',
            'คิว', 'น้ำหนักสุทธิต้นทาง', 'คิวต้นทาง', 'ภาษี', 'น้ำมัน', 'ราคา/ตัน',
            'จำนวนเงิน', 'vat 7%', 'จำนวนเงินสุทธิ',
        ]
        for label in port_labels:
            self.assertIn(label, headers, "missing editWeightPort field: %s" % label)

    def test_export_includes_all_fields_from_edit_weight_sell(self):
        """ทุกฟิลด์ที่แสดง/แก้ไขได้ใน editWeightSell.html ต้องอยู่ใน export"""
        self.login()
        sheet = self.loadSheet(self.client.get('/weight/table/export/'))
        headers = [cell.value for cell in sheet[1]]

        sell_labels = [
            'วันที่', 'เลขที่เอกสาร', 'เลขที่ใบส่งของ', 'จ่ายเงิน', 'S.', 'ลูกค้า',
            'ปลายทาง', 'รหัสขนส่ง', 'ขนส่ง', 'ทะเบียนรถ', 'จังหวัด', 'ผู้ขับ', 'ทีม', 'ต้นทาง',
            'ชนิดหิน', 'รายละเอียดหิน', 'ประเภทหิน', 'การล้าง', 'ผู้ตัก', 'หมายเหตุ',
            'น้ำหนักเข้า', 'น้ำหนักออก', 'น้ำหนักสุทธิ', 'คิว', 'ภาษี', 'น้ำมัน',
            'ราคา/ตัน', 'จำนวนเงิน', 'vat 7%', 'จำนวนเงินสุทธิ',
        ]
        for label in sell_labels:
            self.assertIn(label, headers, "missing editWeightSell field: %s" % label)

    def test_export_includes_all_fields_from_edit_weight_stock(self):
        """ทุกฟิลด์ที่แสดง/แก้ไขได้ใน editWeightStock.html ต้องอยู่ใน export"""
        self.login()
        sheet = self.loadSheet(self.client.get('/weight/table/export/'))
        headers = [cell.value for cell in sheet[1]]

        stock_labels = [
            'วันที่', 'เลขที่เอกสาร', 'ลูกค้า', 'ทะเบียนรถ', 'ผู้ขับ', 'ต้นทาง',
            'ปลายทาง', 'ชนิดหิน', 'รายละเอียดหิน', 'ผู้ตัก', 'หมายเหตุ',
            'น้ำหนักเข้า', 'น้ำหนักออก', 'น้ำหนักสุทธิ',
        ]
        for label in stock_labels:
            self.assertIn(label, headers, "missing editWeightStock field: %s" % label)

    def test_export_is_apw_shown_as_icon(self):
        """สถานะตรวจสอบรายการชั่งแล้ว (is_apw) ต้อง export เป็นไอคอน ✔/✘ สีเขียว/แดง ไม่ใช่ข้อความ"""
        from weightapp.views import (
            WEIGHT_TABLE_EXPORT_ICON_TRUE, WEIGHT_TABLE_EXPORT_ICON_FALSE,
            WEIGHT_TABLE_EXPORT_ICON_FONT_TRUE, WEIGHT_TABLE_EXPORT_ICON_FONT_FALSE,
        )

        self.login()

        # DOC001 ถูกสร้างด้วย is_apw=True
        sheet_true = self.loadSheet(self.client.get('/weight/table/export/?doc_id=DOC001'))
        headers = [cell.value for cell in sheet_true[1]]
        col = headers.index('สถานะตรวจสอบรายการชั่งแล้ว') + 1
        cell_true = sheet_true.cell(row=2, column=col)
        self.assertEqual(cell_true.value, WEIGHT_TABLE_EXPORT_ICON_TRUE)
        self.assertEqual(cell_true.font.color.rgb[-6:], WEIGHT_TABLE_EXPORT_ICON_FONT_TRUE.color.rgb[-6:])
        self.assertEqual(cell_true.alignment.horizontal, 'center')

        # DOC_NULL ถูกสร้างโดยไม่ระบุ is_apw (default False)
        sheet_false = self.loadSheet(self.client.get('/weight/table/export/?doc_id=DOC_NULL'))
        headers_f = [cell.value for cell in sheet_false[1]]
        col_f = headers_f.index('สถานะตรวจสอบรายการชั่งแล้ว') + 1
        cell_false = sheet_false.cell(row=2, column=col_f)
        self.assertEqual(cell_false.value, WEIGHT_TABLE_EXPORT_ICON_FALSE)
        self.assertEqual(cell_false.font.color.rgb[-6:], WEIGHT_TABLE_EXPORT_ICON_FONT_FALSE.color.rgb[-6:])

    def test_export_new_field_values_are_correct(self):
        """ค่าฟิลด์ใหม่ export ตรงกับข้อมูลที่บันทึกไว้ และตัวเลข/บูลีนเป็นชนิดที่ถูกต้อง"""
        self.login()
        sheet = self.loadSheet(self.client.get('/weight/table/export/?doc_id=DOC001'))
        headers = [cell.value for cell in sheet[1]]

        def cell(label):
            return sheet.cell(row=2, column=headers.index(label) + 1).value

        self.assertEqual(cell('เลขที่ใบส่งของ'), 'DO001')
        self.assertEqual(cell('จ่ายเงิน'), 'เงินสด')
        self.assertEqual(cell('S.'), 'ใช่')
        self.assertIsNone(cell('สถานะยกเลิก'))
        self.assertEqual(cell('ประเภทสาย'), 'สายสั้น')
        self.assertEqual(cell('จังหวัด'), 'ระยอง')
        self.assertEqual(cell('ผู้ขับ'), 'คนขับ 1')
        self.assertEqual(cell('ทีม'), 'ทีม A')
        self.assertEqual(cell('รหัสขนส่ง'), 'TRANS01')
        self.assertEqual(cell('ขนส่ง'), 'ส่งให้')
        self.assertEqual(cell('รายละเอียดหิน'), 'หินก้อนใหญ่')
        self.assertEqual(cell('ประเภทหิน'), 'แดง')
        self.assertEqual(cell('การล้าง'), 'ล้างหิน')
        self.assertEqual(cell('ผู้ตัก'), 'รถตัก 1')
        self.assertEqual(cell('หมายเหตุ'), 'หมายเหตุทดสอบ')
        self.assertEqual(cell('ภาษี'), 'รวมภาษี')

        self.assertEqual(float(cell('คิว')), 1.5)
        self.assertEqual(float(cell('น้ำหนักสุทธิต้นทาง')), 6.5)
        self.assertEqual(float(cell('คิวต้นทาง')), 1.6)
        self.assertEqual(float(cell('น้ำมัน')), 2.25)
        self.assertEqual(float(cell('ราคา/ตัน')), 100.5)
        self.assertEqual(float(cell('จำนวนเงิน')), 603.0)
        self.assertEqual(float(cell('vat 7%')), 42.21)
        self.assertEqual(float(cell('จำนวนเงินสุทธิ')), 645.21)
        self.assertNotIsInstance(cell('คิว'), str)
        self.assertNotIsInstance(cell('จำนวนเงินสุทธิ'), str)

    def test_export_contains_all_rows_not_only_first_page(self):
        self.login()
        sheet = self.loadSheet(self.client.get('/weight/table/export/'))
        # 26 รายการของบริษัทนี้ + หัวตาราง
        self.assertEqual(sheet.max_row, 27)

    def test_export_excludes_other_company(self):
        self.login()
        sheet = self.loadSheet(self.client.get('/weight/table/export/'))
        doc_ids = [row[1] for row in sheet.iter_rows(min_row=2, values_only=True)]
        self.assertNotIn('DOC_OTHER', doc_ids)

    def test_export_respects_filter(self):
        self.login()
        sheet = self.loadSheet(self.client.get('/weight/table/export/?doc_id=DOC001'))
        self.assertEqual(sheet.max_row, 2)
        self.assertEqual(sheet.cell(row=2, column=2).value, 'DOC001')

    def test_export_numeric_values_stay_numeric(self):
        self.login()
        sheet = self.loadSheet(self.client.get('/weight/table/export/?doc_id=DOC001'))
        headers = [cell.value for cell in sheet[1]]
        total = sheet.cell(row=2, column=headers.index('น้ำหนักสุทธิ') + 1).value
        self.assertEqual(float(total), 6.0)
        self.assertNotIsInstance(total, str)

    def test_export_handles_null_values(self):
        self.login()
        sheet = self.loadSheet(self.client.get('/weight/table/export/?doc_id=DOC_NULL'))
        headers = [cell.value for cell in sheet[1]]
        self.assertEqual(sheet.max_row, 2)
        self.assertIsNone(sheet.cell(row=2, column=headers.index('ทะเบียนรถ') + 1).value)
        self.assertIsNone(sheet.cell(row=2, column=headers.index('น้ำหนักสุทธิ') + 1).value)
        # ปลายทาง/ต้นทาง ว่าง แสดง '-' เหมือนหน้า weight/table
        self.assertEqual(sheet.cell(row=2, column=headers.index('ปลายทาง') + 1).value, '-')
        self.assertEqual(sheet.cell(row=2, column=headers.index('ต้นทาง') + 1).value, '-')
        # ฟิลด์ใหม่ที่เป็นค่าว่าง (NULL) ต้องไม่ error และไม่แปลงเป็นข้อความ "None"
        self.assertIsNone(sheet.cell(row=2, column=headers.index('เลขที่ใบส่งของ') + 1).value)
        self.assertIsNone(sheet.cell(row=2, column=headers.index('คิว') + 1).value)
        self.assertIsNone(sheet.cell(row=2, column=headers.index('น้ำหนักสุทธิต้นทาง') + 1).value)
        # boolean ที่เป็นค่า default (False) ต้องแสดงเป็นเซลล์ว่าง ไม่ใช่ 'False' ดิบ
        self.assertIsNone(sheet.cell(row=2, column=headers.index('S.') + 1).value)
        self.assertIsNone(sheet.cell(row=2, column=headers.index('สถานะยกเลิก') + 1).value)

    def test_weight_table_page_still_works(self):
        from django.test import override_settings
        self.login()
        # หน้าเว็บใช้ static manifest ซึ่งไม่มีใน test env จึงสลับเป็น storage ธรรมดา
        with override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage'):
            response = self.client.get('/weight/table')
        self.assertEqual(response.status_code, 200)
        # ยังแบ่งหน้าละ 10 เหมือนเดิม
        self.assertEqual(len(response.context['weight'].object_list), 10)
        self.assertEqual(response.context['weight'].paginator.count, 26)
