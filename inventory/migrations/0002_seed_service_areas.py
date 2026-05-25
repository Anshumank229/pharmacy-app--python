# inventory/migrations/0002_seed_service_areas.py
#
# HOW TO USE:
#   1. Run your normal migrations first:  python manage.py migrate
#   2. Create an empty migration:
#        python manage.py makemigrations inventory --empty --name seed_service_areas
#   3. Replace the generated file's contents with this file entirely.
#   4. Run:  python manage.py migrate
#
# This seeds your 3 delivery pincodes automatically so checkout works on first run.

from django.db import migrations


def seed_service_areas(apps, schema_editor):
    ServiceArea = apps.get_model('inventory', 'ServiceArea')
    areas = [
        ('811214', 'Jamalpur'),
        ('811201', 'Munger'),
        ('800001', 'Patna'),
    ]
    for pincode, area_name in areas:
        ServiceArea.objects.get_or_create(
            pincode=pincode,
            defaults={'area_name': area_name, 'is_active': True}
        )


def reverse_seed(apps, schema_editor):
    ServiceArea = apps.get_model('inventory', 'ServiceArea')
    ServiceArea.objects.filter(pincode__in=['811214', '811201', '800001']).delete()


class Migration(migrations.Migration):

    # IMPORTANT: update this to match your actual last migration filename
    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_service_areas, reverse_seed),
    ]