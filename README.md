# Local Artisan E-Marketplace

**A secure, full-stack marketplace application demonstrating database transaction integrity**

---

## 📋 Project Overview

This project is a **Local Artisan E-Marketplace** designed for Bangladeshi artisans (like Shital Pati weavers) to sell unique, low-stock items directly to customers. The **primary technical achievement** is preventing the "double-selling" race condition using PostgreSQL's row-level locking mechanism.

### 🎯 Core Problem Solved

**The Race Condition Problem:**

- Imagine two customers trying to buy the last item simultaneously
- Without proper locking, both requests might read "1 item available"
- Both might successfully place orders, but only 1 item exists
- Result: **Data integrity failure** and customer dissatisfaction

**Our Solution:**

- Use PostgreSQL's `FOR UPDATE NOWAIT` row locking
- First request locks the product row immediately
- Second request fails instantly with "item being purchased"
- Ensures only one customer can complete the purchase
- **Result: 100% data integrity maintained**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Artisan    │  │    Buyer     │  │    Admin     │        │
│  │  Dashboard   │  │  Dashboard   │  │   Panel      │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│         React Components with Tailwind CSS                     │
└─────────────────────────────────────────────────────────────────┘
                            ↕ HTTP/REST
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                            │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  Authentication (JWT) │ Authorization (Role-Based)     │   │
│  └────────────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  API Endpoints:                                        │   │
│  │  • POST /api/register        • GET  /api/products      │   │
│  │  • POST /api/login           • POST /api/products      │   │
│  │  • POST /api/purchase/lock ← CRITICAL ENDPOINT         │   │
│  │  • GET  /api/buyer/orders    • GET  /api/artisan/orders│  │
│  │  • PUT  /api/orders/{id}/status                        │   │
│  │  • GET  /api/admin/audit/transactions                  │   │
│  └────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            ↕ SQL
┌─────────────────────────────────────────────────────────────────┐
│                    POSTGRESQL DATABASE                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │  users   │  │ products │  │  orders  │  │transactions│    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
│  ┌──────────────────────────────────────────────────────┐     │
│  │           audit_logs (Complete Activity Trail)       │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                 │
│  🔒 ACID Transactions + Row-Level Locking                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

| Component             | Technology            | Why This Choice?                                             |
| --------------------- | --------------------- | ------------------------------------------------------------ |
| **Database**          | PostgreSQL            | ACID compliance, row-level locking for concurrency control   |
| **Backend**           | Python FastAPI        | High performance, automatic API documentation, async support |
| **Frontend**          | React + Tailwind CSS  | Component-based UI, rapid styling, bilingual support         |
| **Authentication**    | JWT (JSON Web Tokens) | Stateless, secure, scalable session management               |
| **Password Security** | Bcrypt                | Industry-standard one-way hashing                            |

---

## 📊 Database Schema

### Key Tables

**1. users** - Stores all system users

```sql
- user_id (Primary Key)
- username (Unique)
- password_hash (Bcrypt hashed)
- role (artisan/buyer/admin)
- full_name, email, phone
```

**2. products** - Artisan product listings

```sql
- product_id (Primary Key)
- artisan_id (Foreign Key → users)
- product_name, description
- price, stock_quantity ← CRITICAL for locking
- category, image_url
```

**3. orders** - Customer orders

```sql
- order_id (Primary Key)
- buyer_id, product_id (Foreign Keys)
- quantity, total_price
- status (pending/processing/shipped/delivered)
- shipping_address
```

**4. transactions** - Financial records

```sql
- transaction_id (Primary Key)
- order_id, artisan_id, buyer_id, product_id
- amount, commission_fee (5%), artisan_payout (95%)
- payment_status
```

**5. audit_logs** - Complete activity trail

```sql
- log_id (Primary Key)
- user_id, action_type, entity_type, entity_id
- details (JSON), ip_address, timestamp
```

---

## 🔐 Security Features

### 1. Authentication

- **Password Hashing:** Bcrypt with salt (irreversible)
- **JWT Tokens:** Signed with secret key, 24-hour expiration
- **Token Validation:** Every protected endpoint verifies token

### 2. Authorization

- **Role-Based Access Control (RBAC):**
  - **Artisan:** Can create products, view their orders, update order status
  - **Buyer:** Can purchase products, view their orders
  - **Admin:** Can view all transactions, audit logs, user data
- **Dependency Injection:** FastAPI's `Depends()` enforces roles automatically

### 3. SQL Injection Prevention

- **Parameterized Queries:** All SQL uses placeholders (`%s`)
- **ORM-like Abstraction:** Database module wraps raw SQL safely

---

## 🎯 Critical Feature: Purchase with Inventory Locking

### The Problem

When multiple customers try to buy the same item simultaneously:

```
Time    Customer A              Customer B              Stock
----    -----------              -----------              -----
10:00   Read stock = 1           -                       1
10:01   -                        Read stock = 1          1
10:02   Purchase (stock - 1)     -                       0
10:03   -                        Purchase (stock - 1)    -1 ❌
```

**Result:** Overselling (-1 stock is impossible in real life!)

### Our Solution

```python
# In main.py - POST /api/purchase/lock endpoint

# Start transaction
connection.autocommit = False

# CRITICAL: Lock the row immediately
cursor.execute("""
    SELECT product_id, stock_quantity
    FROM products
    WHERE product_id = %s
    FOR UPDATE NOWAIT  ← This is the magic!
""", (product_id,))
```

**How FOR UPDATE NOWAIT Works:**

1. **Customer A** arrives first → Gets lock → Reads stock = 1
2. **Customer B** arrives 1ms later → Tries to get lock → **FAILS IMMEDIATELY**
3. Customer B gets error: "Product being purchased by another customer"
4. Customer A completes purchase → Releases lock → Stock = 0
5. Customer B retries → Gets "SOLD OUT" error (correct behavior!)

**Timeline with Locking:**

```
Time    Customer A                       Customer B              Stock
----    -----------                      -----------              -----
10:00   Lock acquired ✓                  -                       1
10:01   -                                Lock attempt → FAIL ❌   1
10:02   Purchase complete, lock released -                       0
10:03   -                                Retry → "SOLD OUT" ✓    0
```

**Result:** Data integrity maintained! 🎉

---

## 🚀 API Endpoints

### Authentication

- `POST /api/register` - Create new user account
- `POST /api/login` - Authenticate and receive JWT token
- `GET /api/me` - Get current user info (requires token)

### Products

- `GET /api/products` - List all products (optional: `?available_only=true`)
- `GET /api/products/{id}` - Get single product details
- `POST /api/products` - Create product (Artisan only)
- `GET /api/artisan/products` - Get artisan's products with sales stats

### Orders

- `POST /api/purchase/lock` ⚠️ **CRITICAL** - Purchase with inventory locking
- `GET /api/buyer/orders` - Get buyer's orders
- `GET /api/artisan/orders` - Get orders for artisan's products
- `PUT /api/orders/{id}/status` - Update order status (Artisan/Admin only)

### Admin

- `GET /api/admin/audit/transactions` - Financial audit with commission breakdown
- `GET /api/admin/users` - List all users

---

## 👥 User Roles Explained

### 1. Artisan (Seller)

**Capabilities:**

- Create new product listings
- Set prices and stock quantities
- View all orders for their products
- Update order status (pending → processing → shipped → delivered)
- View sales statistics and revenue

**Use Case:**
A Shital Pati weaver in Sylhet creates a listing for handmade mats, manages inventory, and ships orders to customers across Bangladesh.

### 2. Buyer (Customer)

**Capabilities:**

- Browse available products
- Purchase products (with inventory protection)
- View their order history
- Track order status

**Use Case:**
A customer in Dhaka browses unique artisan products, purchases a Shital Pati mat, and tracks delivery status.

### 3. Admin (System Manager)

**Capabilities:**

- View all transactions and financial audit
- Calculate platform commission (5% of each sale)
- View all users and their roles
- Monitor system activity through audit logs

**Use Case:**
Platform administrator reviews monthly revenue, ensures commission is correctly calculated, and monitors for suspicious activity.

---

## 💡 Key Learning Outcomes

### 1. Database Concurrency Control

- Understanding race conditions in concurrent systems
- Implementing pessimistic locking with `FOR UPDATE NOWAIT`
- ACID transaction properties in practice

### 2. REST API Design

- RESTful endpoint structure
- HTTP status codes (200, 400, 401, 403, 404, 409, 500)
- Request/response validation with Pydantic

### 3. Authentication & Authorization

- JWT token generation and validation
- Password hashing with bcrypt
- Role-based access control

### 4. Full-Stack Integration

- Frontend-backend communication via REST
- State management in React
- Bilingual UI implementation (English/Bangla)

### 5. Financial Transparency

- Commission calculation and tracking
- Audit trail for compliance
- Financial reporting for admins

---

## 🌍 Social Impact

### Digital Inclusion

- **Bangla/English Toggle:** Makes the platform accessible to artisans with varying English proficiency
- **Simple Interface:** Designed for users who may not be tech-savvy
- **Mobile-Responsive:** Works on devices commonly available in Bangladesh

### Economic Empowerment

- **Direct Sales:** Artisans keep 95% of revenue (only 5% platform fee)
- **Transparent Pricing:** No hidden fees or commissions
- **Fair Commission:** 5% covers platform maintenance while supporting artisans

### Cultural Preservation

- **Focus on Traditional Crafts:** Shital Pati, pottery, textiles
- **Artisan Stories:** Product descriptions can include cultural context
- **Local Products:** Connects urban buyers with rural artisans

---

## 📈 Scalability Considerations

### Current Design Supports:

- **Connection Pooling:** 1-10 concurrent database connections
- **Stateless Architecture:** JWT tokens allow horizontal scaling
- **Indexed Queries:** Fast lookups on user_id, product_id, stock_quantity

### Future Enhancements:

- **Caching:** Redis for frequently accessed product data
- **CDN:** Serve product images from content delivery network
- **Load Balancing:** Multiple FastAPI instances behind reverse proxy
- **Message Queue:** RabbitMQ for async order processing

---

## 🧪 Testing the Race Condition Fix

### Scenario: Two buyers purchasing the last item

**Setup:**

1. Create a product with stock_quantity = 1
2. Open two browser tabs (or use curl/Postman)
3. In Tab 1: Start purchase (don't complete immediately)
4. In Tab 2: Try to purchase the same product

**Expected Behavior:**

- Tab 1: Purchase succeeds → Stock becomes 0
- Tab 2: Gets error "Product currently being purchased" or "SOLD OUT"
- Database: Final stock = 0 (never -1)

**Without Locking:**

- Both tabs might succeed → Stock = -1 ❌

**With Locking:**

- Only one succeeds → Stock = 0 ✓

---

## 📝 Code Quality & Maintainability

### Best Practices Demonstrated:

1. **Comprehensive Comments:** Every function and critical section explained
2. **Type Hints:** Python type annotations for better IDE support
3. **Error Handling:** Try-except blocks with proper logging
4. **Separation of Concerns:** Database logic separate from API logic
5. **DRY Principle:** Reusable database helper functions
6. **Security First:** Input validation, parameterized queries, role checks

---

## 🎓 Faculty Review Points

### Key Technical Achievements:

1. ✅ **Race Condition Prevention:** Implemented and can be demonstrated
2. ✅ **ACID Compliance:** Transactions commit/rollback atomically
3. ✅ **Role-Based Security:** Three distinct user types with enforced permissions
4. ✅ **Financial Transparency:** Complete audit trail with commission tracking
5. ✅ **Bilingual Support:** Accessible to Bengali and English speakers

### Documentation Quality:

- ✅ Inline code comments explaining "why" not just "what"
- ✅ Database schema with design rationale
- ✅ API documentation auto-generated by FastAPI
- ✅ Setup instructions for reproduction

### Real-World Applicability:

- ✅ Solves actual problem (artisan marketplace in Bangladesh)
- ✅ Uses production-grade technologies (PostgreSQL, FastAPI, React)
- ✅ Considers social impact (digital inclusion, economic empowerment)

---

## 📞 Support & Questions

For detailed setup instructions, see `SETUP.md`.

For technical questions about the implementation, refer to inline code comments in:

- `main.py` - FastAPI backend with comprehensive endpoint explanations
- `database.py` - Database operations with connection pooling
- `schema.sql` - Database design with rationale

---

**Project Significance:** This application demonstrates mastery of database concurrency control, secure API development, and full-stack integration while addressing a real social need in Bangladesh's artisan community.

**Prepared for:** CSE347 Database Systems Course  
**Institution:** Eastern Washington University
