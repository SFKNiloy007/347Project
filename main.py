"""
============================================================================
Local Artisan E-Marketplace - FastAPI Backend
============================================================================
Purpose: Secure REST API for managing artisan products and preventing
         double-selling through PostgreSQL transaction locking
Key Feature: Race condition prevention using FOR UPDATE NOWAIT
============================================================================
"""

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
import jwt
import bcrypt
from datetime import datetime, timedelta
import logging
import os
from database import (
    DatabaseManager, create_user, get_user_by_username, get_user_by_id,
    create_product, get_all_products, get_product_by_id, get_products_by_artisan,
    create_order, get_orders_by_buyer, get_orders_by_artisan, update_order_status,
    create_transaction, get_all_transactions, create_audit_log, update_product_stock
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# APPLICATION SETUP
# ============================================================================

app = FastAPI(
    title="Local Artisan E-Marketplace API",
    description="Secure marketplace for Bangladeshi artisans with inventory locking",
    version="1.0.0"
)

# CORS Configuration - Allow frontend to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
db = DatabaseManager()

# JWT Configuration
SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Security scheme
security = HTTPBearer()


# ============================================================================
# PYDANTIC MODELS (Request/Response Validation)
# ============================================================================

class UserRegister(BaseModel):
    """Model for user registration request"""
    username: str
    password: str
    role: str
    full_name: str
    email: EmailStr
    phone: Optional[str] = None

    @validator('role')
    def validate_role(cls, v):
        if v not in ['artisan', 'buyer', 'admin']:
            raise ValueError('Role must be artisan, buyer, or admin')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v


class UserLogin(BaseModel):
    """Model for user login request"""
    username: str
    password: str


class ProductCreate(BaseModel):
    """Model for creating a new product"""
    product_name: str
    description: str
    price: float
    stock_quantity: int
    category: str
    image_url: Optional[str] = None

    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return v

    @validator('stock_quantity')
    def validate_stock(cls, v):
        if v < 0:
            raise ValueError('Stock quantity cannot be negative')
        return v


class PurchaseRequest(BaseModel):
    """Model for purchase request with inventory locking"""
    product_id: int
    quantity: int
    shipping_address: str

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v


class OrderStatusUpdate(BaseModel):
    """Model for updating order status"""
    status: str

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['pending', 'processing',
                          'shipped', 'delivered', 'cancelled']
        if v not in valid_statuses:
            raise ValueError(
                f'Status must be one of: {", ".join(valid_statuses)}')
        return v


# ============================================================================
# AUTHENTICATION & AUTHORIZATION
# ============================================================================

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.

    Args:
        data: Payload to encode (user_id, username, role)
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Decode JWT token and extract payload.

    Args:
        token: JWT token string

    Returns:
        Decoded payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency to get current authenticated user from JWT token.

    Usage in routes:
        @app.get("/protected")
        def protected_route(current_user: dict = Depends(get_current_user)):
            # current_user contains user_id, username, role
            pass
    """
    token = credentials.credentials
    payload = decode_token(token)
    return payload


def require_role(required_roles: List[str]):
    """
    Dependency factory to check user role.

    Usage:
        @app.get("/admin-only")
        def admin_route(user: dict = Depends(require_role(["admin"]))):
            pass
    """
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(required_roles)}"
            )
        return current_user
    return role_checker


# ============================================================================
# API ROUTES - Authentication
# ============================================================================

@app.post("/api/register", status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserRegister):
    """
    Register a new user.

    Returns:
        User data and JWT token
    """
    try:
        # Check if username already exists
        existing_user = get_user_by_username(db, user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )

        # Hash password and create user
        password_hash = hash_password(user_data.password)
        user = create_user(
            db,
            username=user_data.username,
            password_hash=password_hash,
            role=user_data.role,
            full_name=user_data.full_name,
            email=user_data.email,
            phone=user_data.phone
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )

        # Create access token
        token_data = {
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user["role"]
        }
        access_token = create_access_token(token_data)

        logger.info(
            f"✓ New user registered: {user['username']} ({user['role']})")

        return {
            "message": "User registered successfully",
            "user": user,
            "access_token": access_token,
            "token_type": "bearer"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@app.post("/api/login")
def login(credentials: UserLogin):
    """
    Authenticate user and return JWT token.

    Returns:
        User data and JWT token
    """
    try:
        # Get user from database
        user = get_user_by_username(db, credentials.username)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

        # Verify password
        if not verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

        # Create access token
        token_data = {
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user["role"]
        }
        access_token = create_access_token(token_data)

        # Remove password hash from response
        user_safe = {k: v for k, v in user.items() if k != "password_hash"}

        logger.info(f"✓ User logged in: {user['username']} ({user['role']})")

        return {
            "message": "Login successful",
            "user": user_safe,
            "access_token": access_token,
            "token_type": "bearer"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@app.get("/api/me")
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user's information.

    Requires valid JWT token in Authorization header.
    """
    user = get_user_by_id(db, current_user["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


# ============================================================================
# API ROUTES - Products
# ============================================================================

@app.get("/api/products")
def list_products(available_only: bool = False):
    """
    List all products.

    Query Parameters:
        available_only: If true, only return products with stock > 0
    """
    try:
        products = get_all_products(db, available_only=available_only)
        return {"products": products, "count": len(products)}
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch products"
        )


@app.get("/api/products/{product_id}")
def get_product(product_id: int):
    """Get a single product by ID"""
    product = get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


@app.post("/api/products", status_code=status.HTTP_201_CREATED)
def create_new_product(
    product_data: ProductCreate,
    current_user: dict = Depends(require_role(["artisan"]))
):
    """
    Create a new product listing (Artisan only).

    Requires JWT token with 'artisan' role.
    """
    try:
        product = create_product(
            db,
            artisan_id=current_user["user_id"],
            product_name=product_data.product_name,
            description=product_data.description,
            price=product_data.price,
            stock_quantity=product_data.stock_quantity,
            category=product_data.category,
            image_url=product_data.image_url
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create product"
            )

        # Create audit log
        create_audit_log(
            db,
            user_id=current_user["user_id"],
            action_type="product_created",
            entity_type="product",
            entity_id=product["product_id"],
            details={"product_name": product["product_name"]}
        )

        logger.info(
            f"✓ Product created: {product['product_name']} by {current_user['username']}")

        return {
            "message": "Product created successfully",
            "product": product
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create product"
        )


@app.get("/api/artisan/products")
def get_artisan_products(current_user: dict = Depends(require_role(["artisan"]))):
    """
    Get all products by the current artisan.

    Includes sales statistics from the artisan_products_view.
    """
    try:
        products = get_products_by_artisan(db, current_user["user_id"])
        return {"products": products, "count": len(products)}
    except Exception as e:
        logger.error(f"Error fetching artisan products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch products"
        )


# ============================================================================
# API ROUTES - Purchase with Inventory Locking (CRITICAL FEATURE)
# ============================================================================

@app.post("/api/purchase/lock")
def purchase_with_lock(
    purchase_data: PurchaseRequest,
    request: Request,
    current_user: dict = Depends(require_role(["buyer"]))
):
    """
    ⚠️ CRITICAL ENDPOINT: Purchase product with inventory locking

    This endpoint prevents the double-selling race condition using PostgreSQL's
    FOR UPDATE NOWAIT locking mechanism.

    Process:
    1. Start database transaction
    2. Lock the product row using FOR UPDATE NOWAIT
    3. Check if sufficient stock is available
    4. If yes: Create order, update stock, create transaction, commit
    5. If no or locked: Rollback and return error

    This ensures that even if two buyers try to purchase the last item
    simultaneously, only one will succeed.
    """
    connection = None
    cursor = None

    try:
        # Get database connection
        connection = db.connection_pool.getconn()
        cursor = connection.cursor()

        # Start transaction
        connection.autocommit = False

        # ====================================================================
        # CRITICAL SECTION: Row-level locking
        # ====================================================================
        # FOR UPDATE NOWAIT locks the row immediately or fails if already locked
        # This prevents two concurrent transactions from reading the same stock value
        # ====================================================================

        lock_query = """
            SELECT product_id, artisan_id, product_name, price, stock_quantity
            FROM products
            WHERE product_id = %s
            FOR UPDATE NOWAIT
        """

        try:
            cursor.execute(lock_query, (purchase_data.product_id,))
            product = cursor.fetchone()
        except Exception as lock_error:
            # If we can't get the lock, another transaction is processing this product
            connection.rollback()
            logger.warning(
                f"⚠️ Lock conflict for product {purchase_data.product_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product is currently being purchased by another customer. Please try again."
            )

        if not product:
            connection.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        product_id, artisan_id, product_name, price, stock_quantity = product

        # Check if sufficient stock is available
        if stock_quantity < purchase_data.quantity:
            connection.rollback()

            if stock_quantity == 0:
                logger.warning(
                    f"⚠️ SOLD OUT: Product {product_id} ({product_name})")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"SOLD OUT: This item is no longer available"
                )
            else:
                logger.warning(
                    f"⚠️ Insufficient stock for product {product_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock. Only {stock_quantity} items available"
                )

        # Calculate total price
        total_price = price * purchase_data.quantity

        # Update stock (reduce by purchased quantity)
        new_stock = stock_quantity - purchase_data.quantity
        update_stock_query = """
            UPDATE products 
            SET stock_quantity = %s 
            WHERE product_id = %s
        """
        cursor.execute(update_stock_query, (new_stock, product_id))

        # Create order
        create_order_query = """
            INSERT INTO orders (buyer_id, product_id, quantity, total_price, shipping_address)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING order_id, created_at
        """
        cursor.execute(
            create_order_query,
            (current_user["user_id"], product_id, purchase_data.quantity,
             total_price, purchase_data.shipping_address)
        )
        order_result = cursor.fetchone()
        order_id, created_at = order_result

        # Create transaction record (with 5% commission)
        commission_rate = 0.05
        commission_fee = round(total_price * commission_rate, 2)
        artisan_payout = round(total_price - commission_fee, 2)

        create_transaction_query = """
            INSERT INTO transactions (order_id, artisan_id, buyer_id, product_id,
                                     amount, commission_fee, artisan_payout)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING transaction_id
        """
        cursor.execute(
            create_transaction_query,
            (order_id, artisan_id, current_user["user_id"], product_id,
             total_price, commission_fee, artisan_payout)
        )
        transaction_result = cursor.fetchone()
        transaction_id = transaction_result[0]

        # Create audit log
        import json
        audit_details = {
            "product_name": product_name,
            "quantity": purchase_data.quantity,
            "total_price": float(total_price),
            "old_stock": stock_quantity,
            "new_stock": new_stock
        }

        create_audit_query = """
            INSERT INTO audit_logs (user_id, action_type, entity_type, entity_id, 
                                   details, ip_address)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s)
        """
        cursor.execute(
            create_audit_query,
            (current_user["user_id"], "purchase", "order", order_id,
             json.dumps(audit_details), request.client.host)
        )

        # Commit transaction - all changes are applied atomically
        connection.commit()

        logger.info(
            f"✓ PURCHASE SUCCESS: Order {order_id} - {product_name} x{purchase_data.quantity} "
            f"by {current_user['username']} - Stock: {stock_quantity} → {new_stock}"
        )

        return {
            "message": "Purchase successful",
            "order_id": order_id,
            "transaction_id": transaction_id,
            "product_name": product_name,
            "quantity": purchase_data.quantity,
            "total_price": float(total_price),
            "commission_fee": float(commission_fee),
            "artisan_payout": float(artisan_payout),
            "remaining_stock": new_stock,
            "created_at": created_at.isoformat()
        }

    except HTTPException:
        # Re-raise HTTP exceptions (400, 404, 409)
        raise

    except Exception as e:
        # Rollback on any unexpected error
        if connection:
            connection.rollback()
        logger.error(f"✗ Purchase error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Purchase failed. Please try again."
        )

    finally:
        # Clean up resources
        if cursor:
            cursor.close()
        if connection:
            connection.autocommit = True
            db.connection_pool.putconn(connection)


# ============================================================================
# API ROUTES - Orders
# ============================================================================

@app.get("/api/buyer/orders")
def get_buyer_orders(current_user: dict = Depends(require_role(["buyer"]))):
    """Get all orders by the current buyer"""
    try:
        orders = get_orders_by_buyer(db, current_user["user_id"])
        return {"orders": orders, "count": len(orders)}
    except Exception as e:
        logger.error(f"Error fetching buyer orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch orders"
        )


@app.get("/api/artisan/orders")
def get_artisan_orders(current_user: dict = Depends(require_role(["artisan"]))):
    """Get all orders for the current artisan's products"""
    try:
        orders = get_orders_by_artisan(db, current_user["user_id"])
        return {"orders": orders, "count": len(orders)}
    except Exception as e:
        logger.error(f"Error fetching artisan orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch orders"
        )


@app.put("/api/orders/{order_id}/status")
def update_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    current_user: dict = Depends(require_role(["artisan", "admin"]))
):
    """
    Update order status (Artisan/Admin only).

    Allows tracking logistics: pending → processing → shipped → delivered
    """
    try:
        rows_affected = update_order_status(db, order_id, status_data.status)

        if rows_affected == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        # Create audit log
        create_audit_log(
            db,
            user_id=current_user["user_id"],
            action_type="status_update",
            entity_type="order",
            entity_id=order_id,
            details={"new_status": status_data.status}
        )

        logger.info(
            f"✓ Order {order_id} status updated to {status_data.status} by {current_user['username']}")

        return {
            "message": "Order status updated successfully",
            "order_id": order_id,
            "new_status": status_data.status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating order status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order status"
        )


# ============================================================================
# API ROUTES - Admin Panel
# ============================================================================

@app.get("/api/admin/audit/transactions")
def get_financial_audit(current_user: dict = Depends(require_role(["admin"]))):
    """
    Get complete financial audit log (Admin only).

    Returns all transactions with commission calculations for oversight.
    """
    try:
        transactions = get_all_transactions(db)

        # Calculate summary statistics
        total_revenue = sum(t["amount"] for t in transactions)
        total_commission = sum(t["commission_fee"] for t in transactions)
        total_artisan_payout = sum(t["artisan_payout"] for t in transactions)

        logger.info(
            f"✓ Admin {current_user['username']} accessed financial audit")

        return {
            "transactions": transactions,
            "count": len(transactions),
            "summary": {
                "total_revenue": float(total_revenue),
                "total_commission": float(total_commission),
                "total_artisan_payout": float(total_artisan_payout)
            }
        }

    except Exception as e:
        logger.error(f"Error fetching financial audit: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch audit data"
        )


@app.get("/api/admin/users")
def get_all_users(current_user: dict = Depends(require_role(["admin"]))):
    """Get all users (Admin only)"""
    try:
        query = """
            SELECT user_id, username, role, full_name, email, phone, created_at
            FROM users
            ORDER BY created_at DESC
        """
        users = db.execute_query(query)
        return {"users": users, "count": len(users)}
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users"
        )


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
def root():
    """Serve the frontend HTML application"""
    return FileResponse("app.html")


@app.get("/api")
def api_info():
    """API information endpoint"""
    return {
        "message": "Local Artisan E-Marketplace API",
        "version": "1.0.0",
        "features": [
            "User authentication with JWT",
            "Role-based access control (Artisan, Buyer, Admin)",
            "Product management with inventory tracking",
            "Purchase with PostgreSQL row locking (prevents double-selling)",
            "Order management and logistics tracking",
            "Financial audit and commission tracking"
        ],
        "documentation": "/docs"
    }


# ============================================================================
# APPLICATION LIFECYCLE
# ============================================================================

@app.on_event("shutdown")
def shutdown_event():
    """Clean up database connections on shutdown"""
    db.close_all_connections()
    logger.info("✓ Application shutdown complete")


# ============================================================================
# EXPLANATION FOR FACULTY
# ============================================================================
#
# FASTAPI APPLICATION ARCHITECTURE:
#
# 1. SECURITY IMPLEMENTATION:
#    - JWT (JSON Web Tokens) for stateless authentication
#    - Bcrypt password hashing (one-way, cannot be reversed)
#    - Role-based access control using dependency injection
#    - CORS configured to allow frontend access
#
# 2. INVENTORY LOCKING MECHANISM (THE CORE FEATURE):
#    - Uses PostgreSQL's "SELECT ... FOR UPDATE NOWAIT"
#    - Locks the product row during the entire purchase transaction
#    - If another request tries to lock the same row, it fails immediately
#    - Prevents race condition: Two buyers trying to buy the last item
#
#    Example scenario:
#    - Product has 1 item in stock
#    - Buyer A clicks "Purchase" at 10:00:00.000
#    - Buyer B clicks "Purchase" at 10:00:00.001
#    - Buyer A's request locks the row first
#    - Buyer B's request gets "NOWAIT" error → "Product currently being purchased"
#    - Buyer A's purchase completes, stock becomes 0
#    - Buyer B tries again, gets "SOLD OUT" error
#    - Result: No double-selling, data integrity maintained
#
# 3. REST API DESIGN:
#    - Clear endpoint naming: /api/products, /api/purchase/lock
#    - HTTP methods match operations: GET (read), POST (create), PUT (update)
#    - Proper status codes: 200 (success), 400 (bad request), 401 (unauthorized)
#    - Pydantic models validate all input data automatically
#
# 4. TRANSACTION MANAGEMENT:
#    - Purchase endpoint performs multiple operations atomically:
#      a) Lock product row
#      b) Check stock
#      c) Update stock
#      d) Create order
#      e) Create transaction record
#      f) Create audit log
#    - If ANY step fails, ALL changes are rolled back (ACID compliance)
#
# 5. AUDIT TRAIL:
#    - Every critical action is logged with user_id, timestamp, and details
#    - Admin can review all purchases and status changes
#    - Helps with debugging and dispute resolution
#
# 6. ROLE SEPARATION:
#    - Artisans: Can create products, view their orders
#    - Buyers: Can purchase products, view their orders
#    - Admins: Can view all data, access financial reports
#    - Enforced through JWT claims and dependency injection
#
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
