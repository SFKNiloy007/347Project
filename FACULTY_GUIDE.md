# Faculty Presentation Guide

## Local Artisan E-Marketplace - CSE347 Database Systems Project

**Student:** [Your Name]  
**Course:** CSE347 - Database Systems  
**Institution:** Eastern Washington University  
**Date:** December 2024

---

## 🎯 Project Summary (30 seconds)

**What:** A secure e-marketplace for Bangladeshi artisans to sell unique handmade items

**Key Achievement:** Prevents the "double-selling" race condition using PostgreSQL row-level locking

**Technologies:** PostgreSQL + Python FastAPI + React

**Result:** 100% data integrity even when multiple customers purchase the last item simultaneously

---

## 📊 Live Demonstration Script (5 minutes)

### Demo 1: Show the Application (2 minutes)

**Step 1:** Open `app.html` in browser

- Show bilingual interface (English/Bangla toggle)
- Explain role-based access control

**Step 2:** Login as Artisan (`artisan1` / `password123`)

- Create a product with stock = 1
- Show product management dashboard

**Step 3:** Login as Buyer (`buyer1` / `password123`)

- Browse available products
- Show purchase interface

**Step 4:** Login as Admin (`admin1` / `password123`)

- Show financial audit with 5% commission tracking
- Display all transactions and user data

### Demo 2: The Critical Test - Race Condition Prevention (3 minutes)

**Setup:**

```
Product: "Last Item" with stock = 1
Two buyers want to purchase it simultaneously
```

**Without Proper Locking (Explain the problem):**

```
Time    Buyer A              Buyer B              Stock
----    --------             --------             -----
10:00   Read: stock = 1      -                    1
10:01   -                    Read: stock = 1      1
10:02   Buy (stock - 1)      -                    0
10:03   -                    Buy (stock - 1)      -1 ❌
```

**Result:** Overselling! Stock = -1 (impossible in real life)

**With Our Solution (Demonstrate):**

1. Open TWO browser windows side-by-side
2. In both windows, login as different buyers
3. Click "Buy Now" on the product with stock = 1
4. Click "Purchase" in BOTH windows as fast as possible

**Expected Result:**

- Window 1: ✓ "Purchase successful! Remaining stock: 0"
- Window 2: ✗ "SOLD OUT" or "Product currently being purchased"

**Verify in Database:**

```sql
SELECT product_id, product_name, stock_quantity
FROM products
WHERE product_name = 'Last Item';
-- Shows: stock_quantity = 0 (not -1!)
```

**Explanation:**

- First buyer's request locks the database row
- Second buyer's request cannot access the locked row
- PostgreSQL's `FOR UPDATE NOWAIT` prevents simultaneous access
- Result: Only one purchase succeeds, data integrity maintained

---

## 🏗️ Technical Architecture

### System Components

```
┌─────────────┐
│   Browser   │ (React + Tailwind CSS)
│  (Frontend) │ English/Bangla bilingual
└──────┬──────┘
       │ HTTP/REST
       │ JWT Authentication
┌──────▼──────┐
│   FastAPI   │ (Python Backend)
│   Backend   │ • JWT + Bcrypt security
│             │ • Role-based authorization
│             │ • Purchase with locking ⚠️
└──────┬──────┘
       │ SQL
       │ Parameterized queries
┌──────▼──────┐
│ PostgreSQL  │ (Database)
│  Database   │ • ACID transactions
│             │ • Row-level locking 🔒
│             │ • Audit trail
└─────────────┘
```

### Database Schema (5 tables)

**1. users** - Authentication and roles

- artisan (sellers), buyer (customers), admin (managers)

**2. products** - Artisan listings

- `stock_quantity` ← CRITICAL field for locking

**3. orders** - Customer orders

- Status tracking: pending → processing → shipped → delivered

**4. transactions** - Financial records

- Automatic 5% commission calculation
- 95% payout to artisans

**5. audit_logs** - Complete activity trail

- Every action logged for transparency

---

## 🔐 Security Implementation

### 1. Password Security

- **Bcrypt hashing:** One-way, cannot be reversed
- **Salt:** Each password has unique salt
- **Cost factor:** 12 rounds (industry standard)

**Code Reference:** `main.py` lines 80-90

### 2. Authentication

- **JWT tokens:** Stateless, no server-side sessions
- **Payload:** Contains user_id, username, role
- **Expiration:** 24 hours
- **Signature:** Prevents token tampering

**Code Reference:** `main.py` lines 95-130

### 3. Authorization

- **Role-based access control (RBAC)**
- **Dependency injection:** FastAPI's `Depends()` enforces roles
- **Example:**
  ```python
  @app.post("/api/products")
  def create_product(user: dict = Depends(require_role(["artisan"]))):
      # Only artisans can create products
  ```

**Code Reference:** `main.py` lines 135-150

### 4. SQL Injection Prevention

- **Parameterized queries:** Never concatenate user input
- **Example:**
  ```python
  cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
  # NOT: f"SELECT * FROM users WHERE username = '{username}'"
  ```

**Code Reference:** `database.py` throughout

---

## 🎯 The Core Innovation: Inventory Locking

### The Problem

**Scenario:** Last item in stock

- Two customers click "Buy" at the same time
- Both see "1 item available"
- Both try to purchase
- Without locking: Both succeed → Stock = -1 ❌

### Our Solution: PostgreSQL Row Locking

**Code:** `main.py` lines 400-500 (POST /api/purchase/lock)

```python
# Start database transaction
connection.autocommit = False

# LOCK THE ROW IMMEDIATELY
cursor.execute("""
    SELECT product_id, stock_quantity
    FROM products
    WHERE product_id = %s
    FOR UPDATE NOWAIT  ← This is the critical line!
""", (product_id,))
```

**What `FOR UPDATE NOWAIT` does:**

1. **Locks** the specific product row
2. **Blocks** other transactions from reading/writing that row
3. **Fails immediately** (NOWAIT) if row is already locked
4. **Releases lock** when transaction commits/rollback

**Sequence Diagram:**

```
Buyer A                    Database                    Buyer B
───────                    ────────                    ───────
  │                           │                           │
  ├─── Lock Product ─────────>│                           │
  │    (FOR UPDATE NOWAIT)    │                           │
  │    ✓ Lock acquired        │                           │
  │                           │<─── Lock Product ─────────┤
  │                           │     (FOR UPDATE NOWAIT)   │
  │                           │     ✗ BLOCKED/FAILS       │
  │                           │─────────────────────────>│
  │                           │     "Product being        │
  │                           │      purchased"           │
  ├─── Check stock = 1 ──────>│                           │
  ├─── Purchase ─────────────>│                           │
  ├─── Update stock = 0 ─────>│                           │
  ├─── Commit ───────────────>│                           │
  │    (releases lock)         │                           │
  │                           │<─── Retry ────────────────┤
  │                           │     stock = 0             │
  │                           │─────────────────────────>│
  │                           │     "SOLD OUT" ✓          │
```

**Result:** Data integrity maintained!

---

## 💰 Financial Transparency

### Commission Structure

- **Platform fee:** 5% of each sale
- **Artisan payout:** 95% of each sale
- **Automatic calculation:** Computed in transaction creation

**Example Transaction:**

```
Sale Amount:        ৳1,500.00
Platform Commission: ৳75.00 (5%)
Artisan Payout:     ৳1,425.00 (95%)
```

### Audit Trail

Every transaction recorded in `transactions` table:

- Transaction ID
- Order ID
- Buyer, Artisan, Product IDs
- Amounts (total, commission, payout)
- Timestamp

**Admin Dashboard:** Shows complete financial audit for oversight

**Code Reference:** `main.py` lines 450-470, `database.py` lines 250-280

---

## 🌍 Social Impact

### Problem Statement

- Bangladeshi artisans (Shital Pati weavers, potters) lack digital marketplace access
- Traditional intermediaries take 30-40% commission
- Language barrier (many artisans not fluent in English)

### Our Solution

1. **Digital Access:** Web-based platform accessible from any device
2. **Fair Commission:** Only 5% (vs. 30-40% traditional)
3. **Bilingual Interface:** English/Bangla toggle for accessibility
4. **Direct Sales:** Artisans connect directly with customers

### Impact Metrics (Potential)

- **Income Increase:** Artisans keep 95% vs. 60-70% with intermediaries
- **Market Reach:** Connect rural artisans with urban buyers
- **Cultural Preservation:** Promote traditional crafts like Shital Pati

---

## 🧪 Testing & Validation

### Unit Tests

- Authentication (login, registration, token validation)
- Product CRUD operations
- Order creation and status updates

### Integration Tests

- End-to-end purchase flow
- Role-based access control
- Financial calculations

### Concurrency Test (The Big One!)

**Run:** `python test_concurrency.py`

**What it does:**

1. Creates product with stock = 1
2. Simulates two simultaneous purchase attempts
3. Verifies only one succeeds
4. Confirms final stock = 0 (not -1)

**Expected Output:**

```
[12:34:56.789] Buyer 1: Attempting purchase...
[12:34:56.790] Buyer 2: Attempting purchase...
[12:34:56.850] Buyer 1: ✓ SUCCESS - Order #123
[12:34:56.851] Buyer 2: ✗ SOLD OUT

✓ TEST PASSED
Data integrity maintained!
```

---

## 📚 Learning Outcomes

### Database Concepts Applied

1. **ACID Properties:** Atomicity, Consistency, Isolation, Durability
2. **Transactions:** Multi-step operations executed atomically
3. **Concurrency Control:** Pessimistic locking with `FOR UPDATE`
4. **Referential Integrity:** Foreign key constraints
5. **Indexing:** Fast lookups on frequently queried columns

### Software Engineering Practices

1. **RESTful API Design:** Clear endpoint structure
2. **Authentication/Authorization:** JWT + RBAC
3. **Error Handling:** Proper HTTP status codes
4. **Code Documentation:** Comprehensive inline comments
5. **Separation of Concerns:** Database, business logic, presentation layers

### Real-World Skills

1. **Full-Stack Development:** Frontend + Backend + Database
2. **Security Best Practices:** Password hashing, SQL injection prevention
3. **Scalability Considerations:** Connection pooling, stateless architecture
4. **User Experience:** Bilingual support, responsive design
5. **Financial Systems:** Commission calculation, audit trails

---

## 🎓 Evaluation Criteria Checklist

### Technical Requirements

- ✅ PostgreSQL database with proper schema design
- ✅ ACID transactions with proper commit/rollback
- ✅ Concurrency control (row-level locking)
- ✅ RESTful API with CRUD operations
- ✅ Authentication and authorization
- ✅ SQL injection prevention

### Code Quality

- ✅ Comprehensive inline comments
- ✅ Type hints and documentation strings
- ✅ Error handling and logging
- ✅ DRY principle (Don't Repeat Yourself)
- ✅ Separation of concerns

### Documentation

- ✅ README with project overview
- ✅ SETUP guide with step-by-step instructions
- ✅ Architecture diagrams
- ✅ Database schema explanation
- ✅ Code comments explaining "why" not just "what"

### Innovation

- ✅ Addresses real-world problem (artisan marketplace)
- ✅ Demonstrates advanced database concept (locking)
- ✅ Social impact consideration (digital inclusion)
- ✅ Bilingual support (accessibility)

### Demonstration

- ✅ Can run locally and demonstrate all features
- ✅ Race condition test is reproducible
- ✅ All three user roles functional
- ✅ Data integrity verifiable

---

## 🚀 Future Enhancements

### Phase 2 (If Time Permits)

1. **Payment Integration:** Connect to bKash/Nagad for real payments
2. **Image Upload:** Allow artisans to upload product photos
3. **Search & Filters:** Category, price range, location filters
4. **Reviews & Ratings:** Buyers can rate products and artisans
5. **Analytics Dashboard:** Sales trends, popular products

### Scalability

1. **Caching:** Redis for frequently accessed data
2. **CDN:** Serve images from content delivery network
3. **Load Balancing:** Multiple API servers
4. **Message Queue:** Async order processing
5. **Database Replication:** Read replicas for scalability

---

## 📞 Q&A Preparation

### Expected Questions & Answers

**Q: Why PostgreSQL instead of MySQL?**
A: PostgreSQL has more robust support for row-level locking with `FOR UPDATE NOWAIT`. MySQL requires `FOR UPDATE` but doesn't have NOWAIT option, making it less suitable for this use case.

**Q: Why JWT instead of session-based auth?**
A: JWT is stateless, meaning we don't need to store sessions on the server. This makes the API easier to scale horizontally (multiple servers) and works well with modern frontend frameworks.

**Q: How does the locking prevent race conditions?**
A: When Transaction A locks a row, Transaction B cannot access that row until A finishes. If B tries to access it, PostgreSQL immediately fails B's request (NOWAIT). This ensures only one transaction can modify the stock at a time.

**Q: What happens if the server crashes during a purchase?**
A: PostgreSQL's ACID properties ensure that uncommitted transactions are rolled back automatically. If the server crashes before commit, the purchase is canceled and stock is not reduced.

**Q: Can this handle 1000 simultaneous purchases?**
A: Yes, but with considerations:

- Connection pooling handles concurrent requests (currently 1-10 connections)
- Each purchase locks only its specific product row
- Other products can be purchased simultaneously
- For 1000+ users, we'd increase pool size or use a load balancer

**Q: Why only 5% commission?**
A: To support artisans while covering platform costs. Traditional intermediaries take 30-40%, leaving artisans with less income. Our goal is economic empowerment.

**Q: How do you prevent SQL injection?**
A: We use parameterized queries throughout. User input is never concatenated into SQL strings. The database driver escapes all parameters automatically.

**Q: What about NoSQL databases like MongoDB?**
A: NoSQL databases don't have the same ACID guarantees or row-level locking mechanisms. For an application where data integrity is critical (inventory management), SQL databases like PostgreSQL are the better choice.

---

## 📁 File Structure Reference

```
347 Projectr/
│
├── schema.sql              ← Database tables, sample data, views
├── database.py             ← Connection pooling, helper functions
├── main.py                 ← FastAPI backend, ALL endpoints
├── app.html                ← React frontend (single-page)
├── requirements.txt        ← Python dependencies
├── README.md               ← Project documentation
├── SETUP.md                ← Installation instructions
├── test_concurrency.py     ← Race condition test script
├── quickstart.ps1          ← Automated setup verification
└── FACULTY_GUIDE.md        ← This document
```

**Key Files to Review:**

1. `main.py` lines 400-500: Purchase with locking (critical feature)
2. `database.py` lines 50-100: Connection pooling setup
3. `schema.sql` lines 60-100: Products table with indexes
4. `app.html` lines 500-700: React purchase component

---

## 🎬 Closing Statement

**This project demonstrates:**

- Mastery of database concurrency control
- Secure API development practices
- Full-stack integration skills
- Real-world problem-solving
- Social impact awareness

**The inventory locking mechanism is not just a technical achievement—it's essential for any e-commerce system.** Without it, platforms like Amazon, eBay, or local marketplaces would face constant overselling issues.

**By building this application, I've shown that I can:**

- Design complex database schemas
- Implement transaction-level controls
- Build secure, scalable APIs
- Create user-friendly interfaces
- Document and explain technical concepts clearly

**Thank you for your consideration.** I'm ready to answer any questions!

---

**Prepared by:** [Your Name]  
**Date:** December 2024  
**Contact:** [Your Email]
