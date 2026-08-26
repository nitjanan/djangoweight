import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weight.settings')
django.setup()

from weightapp.models import CarryingweightRate

data = [
    {"name": "0-35", "description": "น้ำหนัก 0 ถึง 35 ตัน", "min_weight": 0.00, "max_weight": 35.00},
    {"name": "35.01-40", "description": "น้ำหนัก 35.01 ถึง 40 ตัน", "min_weight": 35.01, "max_weight": 40.00},
    {"name": "40.01-50", "description": "น้ำหนัก 40.01 ถึง 50 ตัน", "min_weight": 40.01, "max_weight": 50.00},
    {"name": "50.01 ขึ้นไป", "description": "น้ำหนัก 50.01 ตันขึ้นไป", "min_weight": 50.01, "max_weight": 999999.99},
]

for item in data:
    obj, created = CarryingweightRate.objects.get_or_create(
        name=item["name"],
        defaults=item
    )
    if created:
        print(f"Created: {obj.name}")
    else:
        print(f"Already exists: {obj.name}")

print("Mock data generated successfully!")
