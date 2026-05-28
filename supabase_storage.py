# supabase_storage.py
# ─────────────────────────────────────────
# Handles all file uploads/deletes to Supabase Storage.
# Used for medicine images and prescription uploads.
#
# In development (no SUPABASE_URL set), falls back silently to local disk.
# In production, all media goes to Supabase — disk is ephemeral on Railway.
# ─────────────────────────────────────────
import os
import uuid
import shutil
from django.conf import settings as django_settings

_supabase_client = None


def _get_client():
    """Lazy-init Supabase client. Returns None if not configured."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    if not django_settings.USE_SUPABASE_STORAGE:
        return None
    try:
        from supabase import create_client
        _supabase_client = create_client(
            django_settings.SUPABASE_URL,
            django_settings.SUPABASE_KEY,
        )
        return _supabase_client
    except Exception as e:
        print(f"[supabase_storage] Failed to init client: {e}")
        return None


def upload_file(file_bytes: bytes, filename: str, folder: str = "medicines", content_type: str = "image/jpeg") -> str:
    """
    Upload a file to Supabase Storage.
    Returns the public URL of the uploaded file.

    Falls back to saving locally if Supabase is not configured (dev mode).
    """
    client = _get_client()

    if client is None:
        # Dev fallback — save to local media folder
        local_dir = os.path.join(django_settings.MEDIA_ROOT, folder)
        os.makedirs(local_dir, exist_ok=True)
        local_path = os.path.join(local_dir, filename)
        with open(local_path, "wb") as f:
            f.write(file_bytes)
        return f"{folder}/{filename}"  # relative path — served via /media/

    try:
        storage_path = f"{folder}/{filename}"
        bucket = django_settings.SUPABASE_BUCKET
        client.storage.from_(bucket).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": content_type, "upsert": "true"},
        )
        # Return full public URL
        return f"{django_settings.SUPABASE_URL}/storage/v1/object/public/{bucket}/{storage_path}"
    except Exception as e:
        raise RuntimeError(f"Supabase upload failed: {e}")


def delete_file(filename: str, folder: str = "medicines"):
    """Delete a file from Supabase Storage. Silently ignores errors."""
    client = _get_client()
    if client is None:
        # Dev fallback — delete local file
        local_path = os.path.join(django_settings.MEDIA_ROOT, folder, filename)
        try:
            os.remove(local_path)
        except FileNotFoundError:
            pass
        return

    try:
        storage_path = f"{folder}/{filename}"
        client.storage.from_(django_settings.SUPABASE_BUCKET).remove([storage_path])
    except Exception:
        pass  # Don't crash the app over a failed delete


def public_url(path: str) -> str:
    """
    Given a stored path (could be relative local path or full Supabase URL),
    return the correct URL to serve to the frontend.
    """
    if not path:
        return ""
    # Already a full URL (Supabase)
    if path.startswith("http"):
        return path
    # Local relative path — serve via Django /media/
    return f"{django_settings.MEDIA_URL}{path}"