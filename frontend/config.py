import os
from dotenv import load_dotenv

load_dotenv()

API_URL         = os.getenv('API_URL', 'http://127.0.0.1:8000/api')
ADMIN_API_KEY   = os.getenv('ADMIN_API_KEY', 'change-me-in-production')
ADMIN_HEADERS   = {"x-admin-key": ADMIN_API_KEY}
WHATSAPP_NUMBER = os.getenv('WHATSAPP_NUMBER', '91XXXXXXXXXX')

SESSION_DEFAULTS = {
    'show_profile':         False,
    'show_admin':           False,
    'show_analytics':       False,
    'show_medicine_detail': False,
    'selected_medicine_id': None,
    'cart':                 [],
    'user':                 None,
    'last_area_name':       '',
    'last_pending_count':   0,
}
