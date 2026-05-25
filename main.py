# main.py
import os
import django
import secrets
import shutil
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.wsgi import get_wsgi_application
from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Depends, Header
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, field_validator, Field
from typing import List, Optional, Literal
from django.db import transaction
from fastapi.staticfiles import StaticFiles

django_app = get_wsgi_application()

from inventory.models import Medicine, Category, Order, OrderItem, Review, ServiceArea, UserProfile

app = FastAPI(title="Medicine Delivery API")

# FIX: CORS middleware so frontend can talk to backend without browser blocks
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("media/prescriptions", exist_ok=True)


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


class MedicineCreateSchema(BaseModel):
    name: str
    category_id: int
    price: float
    stock: int


class MedicineUpdateSchema(BaseModel):
    price: float
    stock: int


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
    items: List[OrderItemCreateSchema]


class OrderResponseSchema(BaseModel):
    id: int
    customer_name: str
    status: str
    message: str


class OrderMedicineSchema(BaseModel):
    name: str
    model_config = ConfigDict(from_attributes=True)


class OrderItemDetailSchema(BaseModel):
    medicine: OrderMedicineSchema
    quantity: int
    price_at_time_of_purchase: float
    model_config = ConfigDict(from_attributes=True)


# FIX: duplicate 'pincode' field removed — had it defined twice
class OrderDetailSchema(BaseModel):
    id: int
    customer_name: str
    customer_email: str
    customer_phone: str = ""
    delivery_address: str = ""
    pincode: str = ""
    status: str
    total_price: float = 0
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
    # FIX: rating validated server-side — rejects anything outside 1-5
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


# ==========================================
# ADMIN AUTH
# ==========================================
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "change-me-in-production")


def verify_admin(x_admin_key: str = Header(...)):
    # FIX: secrets.compare_digest prevents timing attacks
    if not secrets.compare_digest(x_admin_key, ADMIN_API_KEY):
        raise HTTPException(status_code=403, detail="Unauthorized.")
    return x_admin_key


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
# ROUTES — USER PROFILE
# ==========================================
@app.get("/api/profile")
def get_profile(email: str):
    try:
        user = User.objects.get(email=email)
        # get_or_create so first-time users never get a 404
        profile, _ = UserProfile.objects.get_or_create(user=user)
        return {
            "name": user.first_name,
            "email": user.email,
            "phone": profile.phone,
            "address": profile.address,
            "pincode": profile.pincode,
            "area_name": profile.area_name,
        }
    except User.DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")


@app.put("/api/profile")
def update_profile(data: ProfileUpdateSchema):
    try:
        user = User.objects.get(email=data.email)
        user.first_name = data.name
        user.save()
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.phone = data.phone
        profile.address = data.address
        profile.pincode = data.pincode
        profile.area_name = data.area_name
        profile.save()
        return {"message": "Profile saved."}
    except User.DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")


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
        # searches name AND brand so "Dolo" and "Cipla" both work
        medicines = medicines.filter(name__icontains=search) | medicines.filter(brand__icontains=search)
    return list(medicines)


@app.get("/api/medicines/{medicine_id}", response_model=MedicineSchema)
def get_medicine(medicine_id: int):
    try:
        return Medicine.objects.select_related('category').get(id=medicine_id)
    except Medicine.DoesNotExist:
        raise HTTPException(status_code=404, detail="Medicine not found")


# ==========================================
# ROUTES — PRESCRIPTIONS
# ==========================================
@app.post("/api/upload-prescription")
def upload_prescription(file: UploadFile = File(...)):
    # FIX: uuid prefix prevents two patients overwriting each other's files
    ext = os.path.splitext(file.filename)[1]
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    file_location = f"media/prescriptions/{safe_filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": safe_filename}


# ==========================================
# ROUTES — ORDERS
# ==========================================
@app.post("/api/orders", response_model=OrderResponseSchema)
def checkout(order_in: OrderCreateSchema):
    # FIX: server-side pincode validation — can't be bypassed by calling API directly
    area = ServiceArea.objects.filter(pincode=order_in.pincode.strip(), is_active=True).first()
    if not area:
        raise HTTPException(status_code=400, detail="We don't deliver to this pincode yet.")

    # FIX: server-side prescription check — can't be bypassed by calling API directly
    item_ids = [i.medicine_id for i in order_in.items]
    rx_required = Medicine.objects.filter(id__in=item_ids, requires_prescription=True).exists()
    if rx_required and not order_in.prescription_image:
        raise HTTPException(status_code=400, detail="A prescription is required for one or more items.")

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
            )

            total_order_price = 0
            for item in order_in.items:
                medicine = Medicine.objects.get(id=item.medicine_id)
                if medicine.stock < item.quantity:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Not enough stock for {medicine.name}. Only {medicine.stock} left."
                    )
                total_order_price += medicine.price * item.quantity
                OrderItem.objects.create(
                    order=order,
                    medicine=medicine,
                    quantity=item.quantity,
                    price_at_time_of_purchase=medicine.price,
                )
                medicine.stock -= item.quantity
                medicine.save()

            order.total_price = total_order_price
            order.save()

            return {
                "id": order.id,
                "customer_name": order.customer_name,
                "status": order.status,
                "message": "Order placed successfully!",
            }
    except Medicine.DoesNotExist:
        raise HTTPException(status_code=404, detail="One of the medicines does not exist.")


@app.get("/api/orders/{order_id}", response_model=OrderDetailSchema)
def get_order(order_id: int):
    try:
        return Order.objects.prefetch_related('items__medicine').get(id=order_id)
    except Order.DoesNotExist:
        raise HTTPException(status_code=404, detail="Order not found")


@app.get("/api/my-orders", response_model=List[OrderDetailSchema])
def get_my_orders(email: str):
    return list(
        Order.objects.filter(customer_email=email)
        .prefetch_related('items__medicine')
        .order_by('-created_at')
    )


# FIX: cancel route restores stock atomically
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
def login_user(user_data: UserLoginSchema):
    auth_user = authenticate(username=user_data.email, password=user_data.password)
    if auth_user is not None:
        return {
            "message": "Login successful",
            "name": auth_user.first_name,
            "email": auth_user.email,
        }
    raise HTTPException(status_code=401, detail="Invalid email or password")


# ==========================================
# ROUTES — ADMIN
# ==========================================
@app.get("/api/admin/orders", response_model=List[OrderDetailSchema], dependencies=[Depends(verify_admin)])
def get_all_orders():
    return list(
        Order.objects.prefetch_related('items__medicine').order_by('-created_at')
    )


# FIX: status restricted to valid choices via Literal — rejects typos like "SHIPED"
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
# MOUNT STATIC + DJANGO
# ==========================================
if os.path.exists("media"):
    app.mount("/media", StaticFiles(directory="media"), name="media")
app.mount("/", WSGIMiddleware(django_app))