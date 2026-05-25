# main.py
import os
import django
import secrets
import shutil
import uuid
from datetime import datetime, date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.wsgi import get_wsgi_application
from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Depends, Header
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, field_validator, Field
from typing import List, Optional, Literal
from django.db import transaction
from django.db.models import Sum, Count
from django.utils import timezone
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import io

django_app = get_wsgi_application()

from inventory.models import Medicine, Category, Order, OrderItem, Review, ServiceArea, UserProfile, Coupon, MedicineBatch

app = FastAPI(title="Medicine Delivery API")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("media/prescriptions", exist_ok=True)
os.makedirs("media/medicines", exist_ok=True)
os.makedirs("media/invoices", exist_ok=True)

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "change-me-in-production")


# ==========================================
# ADMIN AUTH
# ==========================================
def verify_admin(x_admin_key: str = Header(...)):
    if not secrets.compare_digest(x_admin_key, ADMIN_API_KEY):
        raise HTTPException(status_code=403, detail="Unauthorized.")
    return x_admin_key


# ==========================================
# SCHEMAS
# ==========================================
class CategorySchema(BaseModel):
    name: str
    model_config = ConfigDict(from_attributes=True)


class MedicineSchema(BaseModel):
    id: int
    name: str
    category: CategorySchema
    price: float
    stock: int
    image: Optional[str] = None
    requires_prescription: bool = False

    @field_validator('image', mode='before')
    @classmethod
    def extract_image_string(cls, value):
        if not value:
            return None
        if hasattr(value, 'name'):
            return value.name
        return str(value)

    model_config = ConfigDict(from_attributes=True)


class MedicineDetailSchema(BaseModel):
    id: int
    name: str
    brand: Optional[str] = None
    category: CategorySchema
    dosage_form: str = ""
    strength: str = ""
    description: Optional[str] = None
    price: float
    stock: int
    image: Optional[str] = None
    requires_prescription: bool = False

    @field_validator('image', mode='before')
    @classmethod
    def extract_image_string(cls, value):
        if not value:
            return None
        if hasattr(value, 'name'):
            return value.name
        return str(value)

    model_config = ConfigDict(from_attributes=True)


class OrderItemCreateSchema(BaseModel):
    medicine_id: int
    quantity: int


class OrderCreateSchema(BaseModel):
    customer_name: str
    customer_email: str
    customer_phone: str
    delivery_address: str
    pincode: str
    prescription_image: Optional[str] = None
    coupon_code: Optional[str] = None
    items: List[OrderItemCreateSchema]


class OrderResponseSchema(BaseModel):
    id: int
    customer_name: str
    status: str
    total_price: float
    discount_applied: int
    message: str


class OrderMedicineSchema(BaseModel):
    name: str
    model_config = ConfigDict(from_attributes=True)


class OrderItemDetailSchema(BaseModel):
    medicine: OrderMedicineSchema
    quantity: int
    price_at_time_of_purchase: float
    model_config = ConfigDict(from_attributes=True)


class OrderDetailSchema(BaseModel):
    id: int
    customer_name: str
    customer_email: str
    customer_phone: str = ""
    delivery_address: str = ""
    pincode: str = ""
    status: str
    total_price: float = 0
    discount_applied: int = 0
    coupon_code: Optional[str] = None
    created_at: Optional[datetime] = None
    prescription_image: Optional[str] = None
    items: List[OrderItemDetailSchema]
    model_config = ConfigDict(from_attributes=True)


class UserRegisterSchema(BaseModel):
    name: str
    email: str
    password: str


class UserLoginSchema(BaseModel):
    email: str
    password: str


class ProfileUpdateSchema(BaseModel):
    email: str
    name: str
    phone: str
    address: str
    pincode: str
    area_name: str = ""


class ReviewSchema(BaseModel):
    id: int
    customer_name: str
    rating: int
    comment: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class ReviewCreateSchema(BaseModel):
    customer_name: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


# ==========================================
# HELPER — serialize order
# ==========================================
def serialize_order(order):
    return {
        "id": order.id,
        "customer_name": order.customer_name,
        "customer_email": order.customer_email,
        "customer_phone": order.customer_phone,
        "delivery_address": order.delivery_address,
        "pincode": order.pincode,
        "status": order.status,
        "total_price": float(order.total_price),
        "discount_applied": order.discount_applied,
        "coupon_code": order.coupon_code,
        "created_at": order.created_at,
        "prescription_image": order.prescription_image,
        "items": [
            {
                "medicine": {"name": item.medicine.name},
                "quantity": item.quantity,
                "price_at_time_of_purchase": float(item.price_at_time_of_purchase),
            }
            for item in order.items.all()
        ],
    }


# ==========================================
# ROUTES — HEALTH CHECK
# ==========================================
@app.get("/api/health")
def health():
    return {"status": "ok"}


# ==========================================
# ROUTES — AUTH
# ==========================================
@app.post("/api/register")
def register_user(user_data: UserRegisterSchema):
    if User.objects.filter(username=user_data.email).exists():
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User.objects.create_user(
        username=user_data.email,
        email=user_data.email,
        password=user_data.password,
        first_name=user_data.name,
    )
    return {"message": "Account created successfully", "user_id": new_user.id}


@app.post("/api/login")
@limiter.limit("10/minute")
def login_user(request: Request, user_data: UserLoginSchema):
    auth_user = authenticate(username=user_data.email, password=user_data.password)
    if auth_user is not None:
        return {
            "message": "Login successful",
            "name": auth_user.first_name,
            "email": auth_user.email,
            "is_admin": auth_user.is_staff or auth_user.is_superuser,
        }
    raise HTTPException(status_code=401, detail="Invalid email or password")


@app.get("/api/me")
def get_me(email: str):
    user = User.objects.filter(email=email).first()
    if not user:
        return {"is_admin": False}
    return {"is_admin": user.is_staff or user.is_superuser}


# ==========================================
# ROUTES — USER PROFILE
# ==========================================
@app.get("/api/profile")
def get_profile(email: str):
    user = User.objects.filter(email=email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return {
        "name": user.first_name,
        "email": user.email,
        "phone": profile.phone,
        "address": profile.address,
        "pincode": profile.pincode,
        "area_name": profile.area_name,
    }


@app.put("/api/profile")
def update_profile(data: ProfileUpdateSchema):
    user = User.objects.filter(email=data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.first_name = data.name
    user.save()
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.phone = data.phone
    profile.address = data.address
    profile.pincode = data.pincode
    profile.area_name = data.area_name
    profile.save()
    return {"message": "Profile saved."}


# ==========================================
# ROUTES — SERVICE AREA
# ==========================================
@app.get("/api/check-pincode")
def check_pincode(pincode: str):
    area = ServiceArea.objects.filter(pincode=pincode.strip(), is_active=True).first()
    if area:
        return {"serviceable": True, "area_name": area.area_name}
    return {"serviceable": False, "area_name": None}


# ==========================================
# ROUTES — COUPONS
# ==========================================
@app.get("/api/coupons/validate")
def validate_coupon(code: str):
    coupon = Coupon.objects.filter(code=code.upper().strip(), is_active=True).first()
    if not coupon or coupon.times_used >= coupon.max_uses:
        return {"valid": False, "discount": 0}
    return {"valid": True, "discount": coupon.discount_percent}


# ==========================================
# ROUTES — CATEGORIES
# ==========================================
@app.get("/api/categories")
def get_categories():
    return list(Category.objects.all().values('id', 'name'))


# ==========================================
# ROUTES — MEDICINES
# ==========================================
@app.get("/api/medicines", response_model=List[MedicineSchema])
def get_medicines(category_id: Optional[int] = None, search: Optional[str] = None):
    medicines = Medicine.objects.select_related('category').all()
    if category_id is not None:
        medicines = medicines.filter(category_id=category_id)
    if search is not None:
        medicines = medicines.filter(name__icontains=search) | medicines.filter(brand__icontains=search)
    return list(medicines)


@app.get("/api/medicines/{medicine_id}", response_model=MedicineDetailSchema)
def get_medicine(medicine_id: int):
    try:
        return Medicine.objects.select_related('category').get(id=medicine_id)
    except Medicine.DoesNotExist:
        raise HTTPException(status_code=404, detail="Medicine not found")


# ==========================================
# ROUTES — BATCH EXPIRY
# ==========================================
@app.get("/api/admin/batches/alerts", dependencies=[Depends(verify_admin)])
def get_batch_alerts():
    today = timezone.now().date()
    alert_date = today + timezone.timedelta(days=30)

    expiring = MedicineBatch.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=alert_date
    ).select_related('medicine').order_by('expiry_date')

    expired = MedicineBatch.objects.filter(
        expiry_date__lt=today
    ).select_related('medicine').order_by('expiry_date')

    return {
        "expiring_soon": [
            {
                "medicine": b.medicine.name,
                "batch": b.batch_number,
                "quantity": b.quantity,
                "expiry_date": str(b.expiry_date),
                "days_left": b.days_until_expiry,
            }
            for b in expiring
        ],
        "expired": [
            {
                "medicine": b.medicine.name,
                "batch": b.batch_number,
                "quantity": b.quantity,
                "expiry_date": str(b.expiry_date),
                "days_ago": abs(b.days_until_expiry),
            }
            for b in expired
        ],
    }


# ==========================================
# ROUTES — ANALYTICS
# ==========================================
@app.get("/api/admin/analytics", dependencies=[Depends(verify_admin)])
def get_analytics():
    from django.db.models.functions import TruncDate
    from django.db.models import FloatField
    from django.db.models.functions import Cast

    orders = Order.objects.exclude(status='CANCELLED')

    # Revenue by day (last 30 days)
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    daily = (
        orders.filter(created_at__gte=thirty_days_ago)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(revenue=Sum('total_price'), count=Count('id'))
        .order_by('day')
    )

    # Top medicines by quantity sold
    top_medicines = (
        OrderItem.objects
        .values('medicine__name')
        .annotate(total_qty=Sum('quantity'), total_revenue=Sum('price_at_time_of_purchase'))
        .order_by('-total_qty')[:10]
    )

    # Orders by pincode
    by_pincode = (
        Order.objects.values('pincode')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # Status breakdown
    status_counts = (
        Order.objects.values('status')
        .annotate(count=Count('id'))
    )

    # Total revenue
    total_revenue = orders.aggregate(total=Sum('total_price'))['total'] or 0
    total_orders = Order.objects.count()
    delivered = Order.objects.filter(status='DELIVERED').count()
    cancelled = Order.objects.filter(status='CANCELLED').count()

    return {
        "summary": {
            "total_revenue": float(total_revenue),
            "total_orders": total_orders,
            "delivered": delivered,
            "cancelled": cancelled,
            "delivery_rate": round(delivered / total_orders * 100, 1) if total_orders else 0,
        },
        "daily_revenue": [
            {
                "date": str(d['day']),
                "revenue": float(d['revenue'] or 0),
                "orders": d['count'],
            }
            for d in daily
        ],
        "top_medicines": [
            {
                "name": m['medicine__name'],
                "qty_sold": m['total_qty'],
                "revenue": float(m['total_revenue'] or 0),
            }
            for m in top_medicines
        ],
        "by_pincode": [{"pincode": p['pincode'], "orders": p['count']} for p in by_pincode],
        "status_breakdown": {s['status']: s['count'] for s in status_counts},
    }


# ==========================================
# ROUTES — PRESCRIPTIONS
# ==========================================
@app.post("/api/upload-prescription")
def upload_prescription(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.pdf']:
        raise HTTPException(status_code=400, detail="Only JPG, PNG, or PDF files are allowed.")
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    file_location = f"media/prescriptions/{safe_filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": safe_filename}


@app.get("/api/prescriptions/{filename}")
def serve_prescription(filename: str, x_admin_key: str = Header(...)):
    if not secrets.compare_digest(x_admin_key, ADMIN_API_KEY):
        raise HTTPException(status_code=403, detail="Unauthorized")
    safe_filename = os.path.basename(filename)
    path = f"media/prescriptions/{safe_filename}"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


# ==========================================
# ROUTES — PDF INVOICE
# ==========================================
@app.get("/api/orders/{order_id}/invoice")
def download_invoice(order_id: int, email: str):
    """Generate and stream a PDF invoice for an order."""
    try:
        order = Order.objects.prefetch_related('items__medicine').get(id=order_id)
    except Order.DoesNotExist:
        raise HTTPException(status_code=404, detail="Order not found")

    # Only the customer or admin can download
    if order.customer_email != email:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    except ImportError:
        raise HTTPException(status_code=500, detail="reportlab not installed. Run: pip install reportlab")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm,
                            leftMargin=20*mm, rightMargin=20*mm)
    styles = getSampleStyleSheet()
    elements = []

    # Header
    title_style = ParagraphStyle('title', parent=styles['Heading1'], fontSize=20, spaceAfter=4)
    sub_style = ParagraphStyle('sub', parent=styles['Normal'], fontSize=10, textColor=colors.grey)
    elements.append(Paragraph("Your Local Pharmacy", title_style))
    elements.append(Paragraph("Medicine delivery — Cash on delivery", sub_style))
    elements.append(Spacer(1, 8*mm))

    # Invoice info
    info_style = ParagraphStyle('info', parent=styles['Normal'], fontSize=11, spaceAfter=3)
    elements.append(Paragraph(f"<b>Invoice #</b> {order.id}", info_style))
    elements.append(Paragraph(f"<b>Date:</b> {order.created_at.strftime('%d %b %Y, %I:%M %p')}", info_style))
    elements.append(Paragraph(f"<b>Status:</b> {order.status}", info_style))
    elements.append(Spacer(1, 4*mm))

    # Customer info
    elements.append(Paragraph("<b>Delivery Details</b>", styles['Heading3']))
    elements.append(Paragraph(f"{order.customer_name}", info_style))
    elements.append(Paragraph(f"Phone: {order.customer_phone}", info_style))
    elements.append(Paragraph(f"Address: {order.delivery_address}", info_style))
    elements.append(Paragraph(f"Pincode: {order.pincode}", info_style))
    elements.append(Spacer(1, 6*mm))

    # Items table
    elements.append(Paragraph("<b>Items Ordered</b>", styles['Heading3']))
    elements.append(Spacer(1, 2*mm))

    table_data = [['Medicine', 'Qty', 'Unit Price', 'Total']]
    subtotal = 0
    for item in order.items.all():
        line_total = item.quantity * float(item.price_at_time_of_purchase)
        subtotal += line_total
        table_data.append([
            item.medicine.name,
            str(item.quantity),
            f"Rs. {float(item.price_at_time_of_purchase):.2f}",
            f"Rs. {line_total:.2f}",
        ])

    # Discount row
    if order.discount_applied:
        discount_amt = subtotal * order.discount_applied / 100
        table_data.append(['', '', f'Discount ({order.discount_applied}%)', f'- Rs. {discount_amt:.2f}'])

    table_data.append(['', '', 'TOTAL', f"Rs. {float(order.total_price):.2f}"])

    table = Table(table_data, colWidths=[90*mm, 20*mm, 40*mm, 35*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f5f5f5')]),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
    ]))
    elements.append(table)

    elements.append(Spacer(1, 8*mm))
    elements.append(Paragraph("Thank you for your order! Pay on delivery.", sub_style))
    elements.append(Paragraph("For support, contact us on WhatsApp.", sub_style))

    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoice_{order.id}.pdf"}
    )


# ==========================================
# ROUTES — ORDERS
# ==========================================
@app.post("/api/orders", response_model=OrderResponseSchema)
def checkout(order_in: OrderCreateSchema):
    area = ServiceArea.objects.filter(pincode=order_in.pincode.strip(), is_active=True).first()
    if not area:
        raise HTTPException(status_code=400, detail="We don't deliver to this pincode yet.")

    item_ids = [i.medicine_id for i in order_in.items]
    rx_required = Medicine.objects.filter(id__in=item_ids, requires_prescription=True).exists()
    if rx_required and not order_in.prescription_image:
        raise HTTPException(status_code=400, detail="A prescription is required for one or more items.")

    coupon = None
    discount_percent = 0
    if order_in.coupon_code:
        coupon = Coupon.objects.filter(
            code=order_in.coupon_code.upper().strip(), is_active=True
        ).first()
        if not coupon or coupon.times_used >= coupon.max_uses:
            raise HTTPException(status_code=400, detail="Invalid or expired coupon code.")
        discount_percent = coupon.discount_percent

    try:
        with transaction.atomic():
            order = Order.objects.create(
                customer_name=order_in.customer_name,
                customer_email=order_in.customer_email,
                customer_phone=order_in.customer_phone,
                delivery_address=order_in.delivery_address,
                pincode=order_in.pincode,
                status='PENDING',
                prescription_image=order_in.prescription_image,
                coupon_code=order_in.coupon_code,
                discount_applied=discount_percent,
            )

            total_order_price = 0
            for item in order_in.items:
                try:
                    medicine = Medicine.objects.get(id=item.medicine_id)
                except Medicine.DoesNotExist:
                    raise HTTPException(status_code=404, detail=f"Medicine ID {item.medicine_id} not found.")

                if medicine.stock < item.quantity:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Not enough stock for {medicine.name}. Only {medicine.stock} left."
                    )
                total_order_price += float(medicine.price) * item.quantity
                OrderItem.objects.create(
                    order=order,
                    medicine=medicine,
                    quantity=item.quantity,
                    price_at_time_of_purchase=medicine.price,
                )
                medicine.stock -= item.quantity
                medicine.save()

            if discount_percent:
                total_order_price *= (1 - discount_percent / 100)
                coupon.times_used += 1
                coupon.save()

            order.total_price = round(total_order_price, 2)
            order.save()

            return {
                "id": order.id,
                "customer_name": order.customer_name,
                "status": order.status,
                "total_price": float(order.total_price),
                "discount_applied": discount_percent,
                "message": "Order placed successfully!",
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Checkout failed: {str(e)}")


@app.get("/api/orders/{order_id}", response_model=OrderDetailSchema)
def get_order(order_id: int):
    try:
        order = Order.objects.prefetch_related('items__medicine').get(id=order_id)
        return serialize_order(order)
    except Order.DoesNotExist:
        raise HTTPException(status_code=404, detail="Order not found")


@app.get("/api/my-orders", response_model=List[OrderDetailSchema])
def get_my_orders(email: str):
    orders = Order.objects.filter(customer_email=email).prefetch_related('items__medicine').order_by('-created_at')
    return [serialize_order(o) for o in orders]


@app.put("/api/orders/{order_id}/cancel")
def cancel_order(order_id: int, email: str):
    try:
        order = Order.objects.prefetch_related('items__medicine').get(
            id=order_id, customer_email=email
        )
    except Order.DoesNotExist:
        raise HTTPException(status_code=404, detail="Order not found.")

    if order.status != 'PENDING':
        raise HTTPException(status_code=400, detail="Only pending orders can be cancelled.")

    with transaction.atomic():
        for item in order.items.all():
            item.medicine.stock += item.quantity
            item.medicine.save()
        order.status = 'CANCELLED'
        order.save()

    return {"message": "Order cancelled and stock restored."}


# ==========================================
# ROUTES — ADMIN ORDERS
# ==========================================
@app.get("/api/admin/orders", response_model=List[OrderDetailSchema], dependencies=[Depends(verify_admin)])
def get_all_orders():
    orders = Order.objects.prefetch_related('items__medicine').order_by('-created_at')
    return [serialize_order(o) for o in orders]


@app.put("/api/admin/orders/{order_id}", dependencies=[Depends(verify_admin)])
def update_order_status(
    order_id: int,
    status: Literal['PENDING', 'SHIPPED', 'DELIVERED', 'CANCELLED']
):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        raise HTTPException(status_code=404, detail="Order not found.")
    order.status = status
    order.save()
    return {"message": "Status updated"}


# ==========================================
# ROUTES — REVIEWS
# ==========================================
@app.get("/api/medicines/{medicine_id}/reviews", response_model=List[ReviewSchema])
def get_reviews(medicine_id: int):
    return list(Review.objects.filter(medicine_id=medicine_id).order_by('-created_at'))


@app.post("/api/medicines/{medicine_id}/reviews", response_model=ReviewSchema)
def create_review(medicine_id: int, review_in: ReviewCreateSchema):
    try:
        medicine = Medicine.objects.get(id=medicine_id)
    except Medicine.DoesNotExist:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return Review.objects.create(
        medicine=medicine,
        customer_name=review_in.customer_name,
        rating=review_in.rating,
        comment=review_in.comment,
    )


# ==========================================
# MOUNT DJANGO
# ==========================================
app.mount("/", WSGIMiddleware(django_app))