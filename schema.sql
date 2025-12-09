-- ============================================================================
-- Local Artisan E-Marketplace Database Schema
-- ============================================================================
-- Purpose: Secure database design for preventing double-selling of unique items
-- Key Feature: Inventory locking using PostgreSQL's FOR UPDATE NOWAIT
-- ============================================================================

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ============================================================================
-- 1. USERS TABLE
-- ============================================================================
-- Stores all system users with role-based access control
-- Roles: 'artisan' (sellers), 'buyer' (customers), 'admin' (system managers)
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- Stores bcrypt hashed passwords
    role VARCHAR(20) NOT NULL CHECK (role IN ('artisan', 'buyer', 'admin')),
    full_name VARCHAR(200) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for users table
CREATE INDEX idx_username ON users(username);
CREATE INDEX idx_role ON users(role);

-- ============================================================================
-- 2. PRODUCTS TABLE
-- ============================================================================
-- Stores artisan products with inventory tracking
-- CRITICAL: stock_quantity is used for concurrency control
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    artisan_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    product_name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    stock_quantity INTEGER NOT NULL CHECK (stock_quantity >= 0),  -- CRITICAL for inventory locking
    category VARCHAR(100),  -- e.g., 'Shital Pati', 'Pottery', 'Textiles'
    image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for products table
CREATE INDEX idx_artisan ON products(artisan_id);
CREATE INDEX idx_category ON products(category);
CREATE INDEX idx_stock ON products(stock_quantity);

-- ============================================================================
-- 3. ORDERS TABLE
-- ============================================================================
-- Stores customer orders with status tracking
-- Status flow: 'pending' -> 'processing' -> 'shipped' -> 'delivered'
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    buyer_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    total_price DECIMAL(10, 2) NOT NULL CHECK (total_price >= 0),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled')),
    shipping_address TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for orders table
CREATE INDEX idx_buyer ON orders(buyer_id);
CREATE INDEX idx_product ON orders(product_id);
CREATE INDEX idx_status ON orders(status);
CREATE INDEX idx_created ON orders(created_at);

-- ============================================================================
-- 4. TRANSACTIONS TABLE
-- ============================================================================
-- Financial record of all purchases with commission calculation
-- Commission: Platform takes 5% from each sale for sustainability
CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    artisan_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    buyer_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    amount DECIMAL(10, 2) NOT NULL CHECK (amount >= 0),  -- Total purchase amount
    commission_fee DECIMAL(10, 2) NOT NULL CHECK (commission_fee >= 0),  -- 5% platform fee
    artisan_payout DECIMAL(10, 2) NOT NULL CHECK (artisan_payout >= 0),  -- 95% to artisan
    payment_status VARCHAR(20) NOT NULL DEFAULT 'completed' 
        CHECK (payment_status IN ('completed', 'pending', 'failed', 'refunded')),
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for transactions table
CREATE INDEX idx_order ON transactions(order_id);
CREATE INDEX idx_artisan_trans ON transactions(artisan_id);
CREATE INDEX idx_buyer_trans ON transactions(buyer_id);
CREATE INDEX idx_transaction_date ON transactions(transaction_date);

-- ============================================================================
-- 5. AUDIT_LOGS TABLE
-- ============================================================================
-- Complete audit trail for admin oversight and debugging
-- Logs all critical actions: purchases, inventory changes, status updates
CREATE TABLE audit_logs (
    log_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    action_type VARCHAR(50) NOT NULL,  -- e.g., 'purchase', 'status_update', 'product_created'
    entity_type VARCHAR(50),  -- e.g., 'order', 'product', 'user'
    entity_id INTEGER,  -- ID of the affected entity
    details JSONB,  -- Flexible field for storing action details
    ip_address VARCHAR(45),  -- For security tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for audit_logs table
CREATE INDEX idx_user_log ON audit_logs(user_id);
CREATE INDEX idx_action_type ON audit_logs(action_type);
CREATE INDEX idx_created_log ON audit_logs(created_at);

-- ============================================================================
-- SAMPLE DATA FOR TESTING
-- ============================================================================
-- Insert test users (passwords are 'password123' hashed with bcrypt)
-- Note: In production, use proper password hashing library

INSERT INTO users (username, password_hash, role, full_name, email, phone) VALUES
('artisan1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyB7P8yLGxVy', 'artisan', 'Kamrul Islam', 'kamrul@example.com', '+8801711111111'),
('buyer1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyB7P8yLGxVy', 'buyer', 'Sara Akter', 'sara@example.com', '+8801722222222'),
('admin1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyB7P8yLGxVy', 'admin', 'System Admin', 'admin@example.com', '+8801733333333');

-- Insert sample artisan products
INSERT INTO products (artisan_id, product_name, description, price, stock_quantity, category, image_url) VALUES
(1, 'Traditional Shital Pati Mat', 'Handwoven mat from Sylhet, made with natural reed. Size: 6x4 feet. Perfect for summer cooling.', 1500.00, 5, 'Shital Pati', '/images/shital-pati-1.jpg'),
(1, 'Premium Shital Pati Runner', 'Decorative runner with intricate patterns. Size: 8x3 feet. Limited edition design.', 2500.00, 2, 'Shital Pati', '/images/shital-pati-2.jpg'),
(1, 'Miniature Shital Pati Coaster Set', 'Set of 6 handmade coasters. Perfect gift item. Traditional craftsmanship.', 500.00, 10, 'Shital Pati', '/images/coaster-set.jpg');

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to update product updated_at timestamp
CREATE OR REPLACE FUNCTION update_product_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update product timestamp
CREATE TRIGGER update_product_modtime
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_product_timestamp();

-- Function to update order updated_at timestamp
CREATE OR REPLACE FUNCTION update_order_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update order timestamp
CREATE TRIGGER update_order_modtime
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_order_timestamp();

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View for artisan dashboard: Shows products with sales statistics
CREATE OR REPLACE VIEW artisan_products_view AS
SELECT 
    p.product_id,
    p.product_name,
    p.price,
    p.stock_quantity,
    p.category,
    p.created_at,
    COALESCE(SUM(o.quantity), 0) as total_sold,
    COALESCE(SUM(o.total_price), 0) as total_revenue
FROM products p
LEFT JOIN orders o ON p.product_id = o.product_id AND o.status != 'cancelled'
GROUP BY p.product_id;

-- View for admin financial audit: Complete transaction overview
CREATE OR REPLACE VIEW admin_financial_audit AS
SELECT 
    t.transaction_id,
    t.transaction_date,
    u_artisan.username as artisan_username,
    u_artisan.full_name as artisan_name,
    u_buyer.username as buyer_username,
    u_buyer.full_name as buyer_name,
    p.product_name,
    t.amount,
    t.commission_fee,
    t.artisan_payout,
    t.payment_status
FROM transactions t
JOIN users u_artisan ON t.artisan_id = u_artisan.user_id
JOIN users u_buyer ON t.buyer_id = u_buyer.user_id
JOIN products p ON t.product_id = p.product_id
ORDER BY t.transaction_date DESC;

-- ============================================================================
-- EXPLANATION FOR FACULTY
-- ============================================================================
-- 
-- KEY DESIGN DECISIONS:
--
-- 1. INVENTORY LOCKING MECHANISM:
--    - The stock_quantity field in products table is the critical control point
--    - Using PostgreSQL's "FOR UPDATE NOWAIT" in purchase transactions
--    - This prevents race conditions when two buyers try to purchase the last item
--
-- 2. ROLE-BASED ACCESS CONTROL:
--    - Three distinct roles: artisan, buyer, admin
--    - Enforced at database level with CHECK constraints
--    - JWT tokens will carry role information for API authorization
--
-- 3. FINANCIAL TRANSPARENCY:
--    - Transactions table records every purchase with commission calculation
--    - 5% platform fee is automatically calculated and stored separately
--    - Admin can audit all financial activities through the financial_audit view
--
-- 4. AUDIT TRAIL:
--    - audit_logs table captures all critical actions
--    - JSONB field allows flexible storage of action details
--    - Essential for debugging and security monitoring
--
-- 5. DATA INTEGRITY:
--    - Foreign key constraints ensure referential integrity
--    - CHECK constraints prevent invalid data (negative prices, invalid statuses)
--    - Indexes optimize query performance for common operations
--
-- ============================================================================
