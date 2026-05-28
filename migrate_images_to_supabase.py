# migrate_images_to_supabase.py
# ─────────────────────────────────────────
# Run ONCE locally before deploying to push all existing
# medicine images from your local media/ folder to Supabase.
#
# Usage:
#   1. Fill in your Supabase credentials below (or set env vars)
#   2. python migrate_images_to_supabase.py
#   3. It will print each uploaded URL and update your DB automatically
# ─────────────────────────────────────────
import os
import django
from dotenv import load_dotenv

load_dotenv()

# Point to your local DB while running this migration
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from inventory.models import Medicine
from supabase import create_client

SUPABASE_URL    = os.getenv('SUPABASE_URL')
SUPABASE_KEY    = os.getenv('SUPABASE_KEY')
SUPABASE_BUCKET = os.getenv('SUPABASE_BUCKET', 'medicine-images')
MEDIA_ROOT      = os.getenv('MEDIA_ROOT', 'media')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Set SUPABASE_URL and SUPABASE_KEY in your .env file first.")
    exit(1)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

medicines = Medicine.objects.exclude(image='').exclude(image__isnull=True)
print(f"Found {medicines.count()} medicines with images.\n")

success = 0
skipped = 0
failed  = 0

for med in medicines:
    image_field = med.image

    # Already migrated (already a full Supabase URL)
    if str(image_field).startswith("http"):
        print(f"  SKIP  {med.name} — already a URL")
        skipped += 1
        continue

    # Local relative path e.g. "medicines/aspirin.jpg"
    local_path = os.path.join(MEDIA_ROOT, str(image_field))
    if not os.path.exists(local_path):
        print(f"  MISS  {med.name} — file not found at {local_path}")
        failed += 1
        continue

    filename   = os.path.basename(local_path)
    ext        = os.path.splitext(filename)[1].lower()
    ct_map     = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp'}
    content_type = ct_map.get(ext, 'image/jpeg')
    storage_path = f"medicines/{filename}"

    try:
        with open(local_path, "rb") as f:
            file_bytes = f.read()

        client.storage.from_(SUPABASE_BUCKET).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": content_type, "upsert": "true"},
        )

        public = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{storage_path}"
        med.image = public
        med.save(update_fields=['image'])

        print(f"  OK    {med.name} → {public}")
        success += 1

    except Exception as e:
        print(f"  FAIL  {med.name} — {e}")
        failed += 1

print(f"\nDone. {success} uploaded, {skipped} skipped, {failed} failed.")