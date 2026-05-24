# main.py
import os
import django
import secrets
import shutil

# 1. SETUP FIRST
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.wsgi import get_wsgi_application
from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Depends, Header
from fastapi.middleware.wsgi import WSGIMiddleware
from pydantic import BaseModel, ConfigDict, field_validator, Field
from typing import List, Optional
from django.db import transaction
from fastapi.staticfiles import StaticFiles

# 2. Initialize the Django WSGI application
django_app = get_wsgi_application()

# 3. Import models AFTER Django is set up
from inventory.models import Medicine, Category, Order, OrderItem, Review

# 4. Create the FastAPI app
app = FastAPI(title="Medicine Delivery API")

# Ensure the prescriptions directory exists
os.makedirs("media/prescriptions", exist_ok=True)

# ==========================================
# 5. DEFINE SCHEMAS (Must be above routes)
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

class OrderDetailSchema(BaseModel):
    id: int
    customer_name: str
    customer_email: str
    status: str
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

class ReviewSchema(BaseModel):
    id: int
    customer_name: str
    rating: int
    comment: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ReviewCreateSchema(BaseModel):
    customer_name: str
    # Enforce rating between 1 and 5
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

# ==========================================
# 6. DEFINE ROUTES
# ==========================================
@app.get("/api/categories")
def get_categories():
    return list(Category.objects.all().values('id', 'name'))

@app.get("/api/medicines", response_model=List[MedicineSchema])
def get_medicines(category_id: Optional[int] = None, search: Optional[str] = None):
    medicines = Medicine.objects.select_related('category').all()
    if category_id is not None:
        medicines = medicines.filter(category_id=category_id)
    if search is not None:
        medicines = medicines.filter(name__icontains=search)
    return list(medicines)

@app.get("/api/medicines/{medicine_id}", response_model=MedicineSchema)
def get_medicine(medicine_id: int):
    try:
        medicine = Medicine.objects.select_related('category').get(id=medicine_id)
        return medicine
    except Medicine.DoesNotExist:
        raise HTTPException(status_code=404, detail="Medicine not found")

@app.post("/api/medicines", response_model=MedicineSchema)
def create_medicine(medicine_in: MedicineCreateSchema):
    try:
        category = Category.objects.get(id=medicine_in.category_id)
    except Category.DoesNotExist:
        raise HTTPException(status_code=404, detail="Category not found")

    new_medicine = Medicine.objects.create(
        name=medicine_in.name,
        category=category,
        price=medicine_in.price,
        stock=medicine_in.stock
    )
    return new_medicine

@app.put("/api/medicines/{medicine_id}", response_model=MedicineSchema)
def update_medicine(medicine_id: int, medicine_in: MedicineUpdateSchema):
    try:
        medicine = Medicine.objects.get(id=medicine_id)
    except Medicine.DoesNotExist:
        raise HTTPException(status_code=404, detail="Medicine not found")

    medicine.price = medicine_in.price
    medicine.stock = medicine_in.stock
    medicine.save()
    return medicine

@app.delete("/api/medicines/{medicine_id}")
def delete_medicine(medicine_id: int):
    try:
        medicine = Medicine.objects.get(id=medicine_id)
    except Medicine.DoesNotExist:
        raise HTTPException(status_code=404, detail="Medicine not found")
    medicine.delete()
    return {"message": f"Medicine with ID {medicine_id} has been successfully deleted."}

@app.post("/api/upload-prescription")
def upload_prescription(file: UploadFile = File(...)):
    file_location = f"media/prescriptions/{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename}


@app.post("/api/orders", response_model=OrderResponseSchema)
def checkout(order_in: OrderCreateSchema):
    try:
        with transaction.atomic():
            # 1. Create the order FIRST (without the total price yet)
            order = Order.objects.create(
                customer_name=order_in.customer_name,
                customer_email=order_in.customer_email,
                status='PENDING',
                prescription_image=order_in.prescription_image
            )

            total_order_price = 0  # <-- Keep a running tally

            for item in order_in.items:
                medicine = Medicine.objects.get(id=item.medicine_id)
                if medicine.stock < item.quantity:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Not enough stock for {medicine.name}. Only {medicine.stock} left."
                    )

                # 2. Add to the running tally
                total_order_price += (medicine.price * item.quantity)

                OrderItem.objects.create(
                    order=order,
                    medicine=medicine,
                    quantity=item.quantity,
                    price_at_time_of_purchase=medicine.price
                )

                medicine.stock -= item.quantity
                medicine.save()

            # 3. Update the order with the final total price!
            order.total_price = total_order_price
            order.save()

            return {
                "id": order.id,
                "customer_name": order.customer_name,
                "status": order.status,
                "message": "Order placed successfully!"
            }
    except Medicine.DoesNotExist:
        raise HTTPException(status_code=404, detail="One of the medicines in your cart does not exist.")


@app.get("/api/orders/{order_id}", response_model=OrderDetailSchema)
def get_order(order_id: int):
    try:
        order = Order.objects.prefetch_related('items__medicine').get(id=order_id)
        return order
    except Order.DoesNotExist:
        raise HTTPException(status_code=404, detail="Order not found")

@app.get("/api/my-orders", response_model=List[OrderDetailSchema])
def get_my_orders(email: str):
    orders = Order.objects.filter(customer_email=email).prefetch_related('items__medicine')
    return list(orders)

# --- AUTHENTICATION ROUTES ---
@app.post("/api/register")
def register_user(user_data: UserRegisterSchema):
    if User.objects.filter(username=user_data.email).exists():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User.objects.create_user(
        username=user_data.email,
        email=user_data.email,
        password=user_data.password,
        first_name=user_data.name
    )
    return {"message": "Account created successfully", "user_id": new_user.id}


@app.post("/api/login")
def login_user(user_data: UserLoginSchema):
    auth_user = authenticate(username=user_data.email, password=user_data.password)

    if auth_user is not None:
        return {
            "message": "Login successful",
            "name": auth_user.first_name,
            "email": auth_user.email
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid email or password")


# ==========================================
# --- ADMIN SECURITY ---
# ==========================================
# Read the secret key from the environment variables
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "change-me-in-production")

def verify_admin(x_admin_key: str = Header(...)):
    # Securely compare the provided header with your secret key
    if not secrets.compare_digest(x_admin_key, ADMIN_API_KEY):
        raise HTTPException(status_code=403, detail="Unauthorized. Invalid Admin Key.")
    return x_admin_key

@app.get("/api/admin/orders", response_model=List[OrderDetailSchema], dependencies=[Depends(verify_admin)])
def get_all_orders():
    return list(Order.objects.prefetch_related('items__medicine').all())

@app.put("/api/admin/orders/{order_id}", dependencies=[Depends(verify_admin)])
def update_order_status(order_id: int, status: str):
    order = Order.objects.get(id=order_id)
    order.status = status
    order.save()
    return {"message": "Status updated"}
# ==========================================

@app.get("/api/me")
def get_current_user(request: Request):
    user = request.user
    if user.is_authenticated:
        return {"name": user.first_name, "email": user.email}
    raise HTTPException(status_code=401, detail="Not logged in")

@app.get("/api/medicines/{medicine_id}/reviews", response_model=List[ReviewSchema])
def get_reviews(medicine_id: int):
    reviews = Review.objects.filter(medicine_id=medicine_id).order_by('-created_at')
    return list(reviews)

@app.post("/api/medicines/{medicine_id}/reviews", response_model=ReviewSchema)
def create_review(medicine_id: int, review_in: ReviewCreateSchema):
    try:
        medicine = Medicine.objects.get(id=medicine_id)
    except Medicine.DoesNotExist:
        raise HTTPException(status_code=404, detail="Medicine not found")

    review = Review.objects.create(
        medicine=medicine,
        customer_name=review_in.customer_name,
        rating=review_in.rating,
        comment=review_in.comment
    )
    return review


# 7. Mount Django at the end
if os.path.exists("media"):
    app.mount("/media", StaticFiles(directory="media"), name="media")
app.mount("/", WSGIMiddleware(django_app))