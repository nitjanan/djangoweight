# -*- coding: utf-8 -*-
import gzip
import io
import zlib

from django.http import JsonResponse

# ข้อมูลชุดละ 200 แถวคลายออกมาไม่ถึง 1 MB ; กันไฟล์ gzip ที่คลายแล้วใหญ่ผิดปกติ (gzip bomb)
MAX_DECOMPRESSED_BYTES = 20 * 1024 * 1024


class GzipRequestMiddleware:
    """คลาย body ของ request ที่ส่งมาแบบ Content-Encoding: gzip (ตาชั่ง WeightMirrorSync.cs)

    Django/DRF ไม่คลาย gzip ของ request ให้เอง ; request ที่ไม่ได้บีบอัดผ่านไปตามเดิม
    ต้องอยู่ก่อน middleware ตัวที่อ่าน body (เช่น CsrfViewMiddleware)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.META.get('HTTP_CONTENT_ENCODING', '').strip().lower() == 'gzip':
            try:
                with gzip.GzipFile(fileobj=io.BytesIO(request.body)) as gz:
                    body = gz.read(MAX_DECOMPRESSED_BYTES + 1)
            except (OSError, EOFError, zlib.error):
                return JsonResponse({'error': 'gzip body เสีย'}, status=400)
            if len(body) > MAX_DECOMPRESSED_BYTES:
                return JsonResponse({'error': 'body ใหญ่เกินไป'}, status=413)

            # request.body อ่าน stream ไปแล้ว ต้องแทนทั้ง _body และ _stream ให้ DRF อ่านตัวที่คลายแล้ว
            request._body = body
            request._stream = io.BytesIO(body)
            request.META['CONTENT_LENGTH'] = str(len(body))
            del request.META['HTTP_CONTENT_ENCODING']

        return self.get_response(request)
