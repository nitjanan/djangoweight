"""แผงเที่ยวส่งออกที่กรอกข้อมูลไม่ครบในหน้า weight table

ทดสอบเฉพาะตรรกะนับช่องที่ยังว่าง ไม่แตะ db (settings ชี้ db จริง ห้ามสร้าง/ลบข้อมูลใน test)
"""
import copy
from decimal import Decimal

from django.test import SimpleTestCase

from weightapp.views import (
    INCOMPLETE_NO_DEST_WEIGHT,
    INCOMPLETE_NO_ORIGIN_WEIGHT,
    INCOMPLETE_NO_TEAM,
    _exportDocumentIncomplete,
)


def _row(weight_id, origin='30', dest='29.5', team_missing=False):
    # แถวจาก _exportDocumentRows : นน. ที่ไม่ได้ชั่ง (0) ถูกแปลงเป็น None มาแล้ว
    return {
        'weight_id': weight_id,
        'origin_weight': Decimal(origin) if origin is not None else None,
        'dest_weight': Decimal(dest) if dest is not None else None,
        'team_missing': team_missing,
    }


class IncompleteTests(SimpleTestCase):

    def test_complete_trip_is_not_listed(self):
        items, counts = _exportDocumentIncomplete([_row(1)])
        self.assertEqual(items, [])
        self.assertEqual(counts['total'], 1)
        self.assertEqual(counts['complete'], 1)
        self.assertEqual(counts['incomplete'], 0)

    def test_each_missing_field(self):
        rows = [_row(1, team_missing=True), _row(2, origin=None), _row(3, dest=None)]
        items, counts = _exportDocumentIncomplete(rows)
        self.assertEqual([i['reasons'] for i in items], [
            [INCOMPLETE_NO_TEAM], [INCOMPLETE_NO_ORIGIN_WEIGHT], [INCOMPLETE_NO_DEST_WEIGHT]])
        self.assertEqual(counts[INCOMPLETE_NO_TEAM], 1)
        self.assertEqual(counts[INCOMPLETE_NO_ORIGIN_WEIGHT], 1)
        self.assertEqual(counts[INCOMPLETE_NO_DEST_WEIGHT], 1)
        self.assertEqual(counts['incomplete'], 3)

    def test_trip_missing_several_fields_counts_once_in_total(self):
        items, counts = _exportDocumentIncomplete(
            [_row(1, origin=None, dest=None, team_missing=True), _row(2)])
        self.assertEqual(items[0]['reasons'], [
            INCOMPLETE_NO_TEAM, INCOMPLETE_NO_ORIGIN_WEIGHT, INCOMPLETE_NO_DEST_WEIGHT])
        self.assertEqual(counts['incomplete'], 1)
        self.assertEqual(counts['complete'], 1)
        self.assertEqual(counts['total'], 2)

    def test_keeps_input_order_and_does_not_mutate_rows(self):
        rows = [_row(3, dest=None), _row(2), _row(1, team_missing=True)]
        before = copy.deepcopy(rows)
        items, _ = _exportDocumentIncomplete(rows)
        self.assertEqual([i['weight_id'] for i in items], [3, 1])
        self.assertEqual(rows, before)

    def test_empty_month(self):
        items, counts = _exportDocumentIncomplete([])
        self.assertEqual(items, [])
        self.assertEqual(counts['total'], 0)
        self.assertEqual(counts['incomplete'], 0)
