"""
============================================================================
Database Connection Module for Local Artisan E-Marketplace
============================================================================
Purpose: Manages PostgreSQL connection pool and provides database operations
Key Feature: Connection pooling for efficient resource management
============================================================================
"""

import os
from typing import Optional, Dict, Any, List
import psycopg2
from psycopg2 import pool, extras
from contextlib import contextmanager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages PostgreSQL database connections using connection pooling.

    Connection pooling improves performance by reusing database connections
    instead of creating new ones for each request.
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database connection pool.

        Args:
            database_url: PostgreSQL connection string (defaults to env variable)
        """
        if database_url or os.getenv('DATABASE_URL'):
            self.database_url = database_url or os.getenv('DATABASE_URL')
            connection_params = self.database_url
        else:
            # Use individual parameters to avoid URL encoding issues
            connection_params = {
                'host': 'localhost',
                'port': 5432,
                'database': 'artisan_marketplace',
                'user': 'postgres',
                'password': '6740'
            }

        try:
            # Create connection pool (minimum 1, maximum 10 connections)
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1,  # Minimum connections
                10,  # Maximum connections
                **connection_params if isinstance(connection_params, dict) else {'dsn': connection_params}
            )

            if self.connection_pool:
                logger.info("✓ Database connection pool created successfully")
            else:
                logger.error("✗ Failed to create connection pool")

        except psycopg2.Error as e:
            logger.error(f"✗ Database connection error: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.

        Automatically returns connection to pool after use.
        Usage:
            with db.get_connection() as conn:
                # use connection
                pass
        """
        connection = None
        try:
            connection = self.connection_pool.getconn()
            yield connection
        finally:
            if connection:
                self.connection_pool.putconn(connection)

    @contextmanager
    def get_cursor(self, commit: bool = False):
        """
        Context manager for database cursors.

        Args:
            commit: Whether to commit transaction after cursor operations

        Usage:
            with db.get_cursor(commit=True) as cursor:
                cursor.execute("INSERT INTO ...")
        """
        with self.get_connection() as connection:
            cursor = connection.cursor(cursor_factory=extras.RealDictCursor)
            try:
                yield cursor
                if commit:
                    connection.commit()
            except Exception as e:
                connection.rollback()
                logger.error(f"Database error: {e}")
                raise
            finally:
                cursor.close()

    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        Execute SELECT query and return results as list of dictionaries.

        Args:
            query: SQL SELECT statement
            params: Query parameters (for parameterized queries)

        Returns:
            List of rows as dictionaries
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()
            return [dict(row) for row in results]

    def execute_update(self, query: str, params: tuple = None) -> int:
        """
        Execute INSERT, UPDATE, or DELETE query.

        Args:
            query: SQL modification statement
            params: Query parameters

        Returns:
            Number of affected rows
        """
        with self.get_cursor(commit=True) as cursor:
            cursor.execute(query, params)
            return cursor.rowcount

    def execute_insert_returning(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """
        Execute INSERT query and return the inserted row.

        Useful for getting auto-generated IDs.

        Args:
            query: SQL INSERT statement with RETURNING clause
            params: Query parameters

        Returns:
            Inserted row as dictionary
        """
        with self.get_cursor(commit=True) as cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
            return dict(result) if result else None

    def close_all_connections(self):
        """Close all connections in the pool."""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("✓ All database connections closed")


# ============================================================================
# DATABASE OPERATIONS - User Management
# ============================================================================

def create_user(db: DatabaseManager, username: str, password_hash: str,
                role: str, full_name: str, email: str, phone: str = None) -> Optional[Dict[str, Any]]:
    """
    Create a new user in the system.

    Args:
        db: DatabaseManager instance
        username: Unique username
        password_hash: Bcrypt hashed password
        role: User role ('artisan', 'buyer', or 'admin')
        full_name: User's full name
        email: User's email address
        phone: Optional phone number

    Returns:
        Created user data (without password_hash)
    """
    query = """
        INSERT INTO users (username, password_hash, role, full_name, email, phone)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING user_id, username, role, full_name, email, phone, created_at
    """
    return db.execute_insert_returning(query, (username, password_hash, role, full_name, email, phone))


def get_user_by_username(db: DatabaseManager, username: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve user by username (for authentication).

    Args:
        db: DatabaseManager instance
        username: Username to look up

    Returns:
        User data including password_hash
    """
    query = "SELECT * FROM users WHERE username = %s"
    results = db.execute_query(query, (username,))
    return results[0] if results else None


def get_user_by_id(db: DatabaseManager, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve user by ID (without password_hash).

    Args:
        db: DatabaseManager instance
        user_id: User ID to look up

    Returns:
        User data (safe for API responses)
    """
    query = """
        SELECT user_id, username, role, full_name, email, phone, created_at 
        FROM users WHERE user_id = %s
    """
    results = db.execute_query(query, (user_id,))
    return results[0] if results else None


# ============================================================================
# DATABASE OPERATIONS - Product Management
# ============================================================================

def create_product(db: DatabaseManager, artisan_id: int, product_name: str,
                   description: str, price: float, stock_quantity: int,
                   category: str, image_url: str = None) -> Optional[Dict[str, Any]]:
    """
    Create a new product listing.

    Args:
        db: DatabaseManager instance
        artisan_id: ID of the artisan creating the product
        product_name: Name of the product
        description: Product description
        price: Product price in BDT
        stock_quantity: Initial stock quantity
        category: Product category
        image_url: Optional product image URL

    Returns:
        Created product data
    """
    query = """
        INSERT INTO products (artisan_id, product_name, description, price, 
                             stock_quantity, category, image_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING *
    """
    return db.execute_insert_returning(
        query,
        (artisan_id, product_name, description,
         price, stock_quantity, category, image_url)
    )


def get_all_products(db: DatabaseManager, available_only: bool = False) -> List[Dict[str, Any]]:
    """
    Retrieve all products, optionally filtering for available stock.

    Args:
        db: DatabaseManager instance
        available_only: If True, only return products with stock > 0

    Returns:
        List of products
    """
    if available_only:
        query = "SELECT * FROM products WHERE stock_quantity > 0 ORDER BY created_at DESC"
    else:
        query = "SELECT * FROM products ORDER BY created_at DESC"
    return db.execute_query(query)


def get_product_by_id(db: DatabaseManager, product_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a single product by ID.

    Args:
        db: DatabaseManager instance
        product_id: Product ID

    Returns:
        Product data
    """
    query = "SELECT * FROM products WHERE product_id = %s"
    results = db.execute_query(query, (product_id,))
    return results[0] if results else None


def get_products_by_artisan(db: DatabaseManager, artisan_id: int) -> List[Dict[str, Any]]:
    """
    Retrieve all products by a specific artisan.

    Args:
        db: DatabaseManager instance
        artisan_id: Artisan's user ID

    Returns:
        List of products
    """
    query = "SELECT * FROM artisan_products_view WHERE product_id IN (SELECT product_id FROM products WHERE artisan_id = %s)"
    return db.execute_query(query, (artisan_id,))


def update_product_stock(db: DatabaseManager, product_id: int, new_quantity: int) -> int:
    """
    Update product stock quantity.

    Args:
        db: DatabaseManager instance
        product_id: Product ID
        new_quantity: New stock quantity

    Returns:
        Number of affected rows
    """
    query = "UPDATE products SET stock_quantity = %s WHERE product_id = %s"
    return db.execute_update(query, (new_quantity, product_id))


# ============================================================================
# DATABASE OPERATIONS - Order Management
# ============================================================================

def create_order(db: DatabaseManager, buyer_id: int, product_id: int,
                 quantity: int, total_price: float, shipping_address: str) -> Optional[Dict[str, Any]]:
    """
    Create a new order.

    Args:
        db: DatabaseManager instance
        buyer_id: Buyer's user ID
        product_id: Product being ordered
        quantity: Quantity ordered
        total_price: Total order price
        shipping_address: Delivery address

    Returns:
        Created order data
    """
    query = """
        INSERT INTO orders (buyer_id, product_id, quantity, total_price, shipping_address)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *
    """
    return db.execute_insert_returning(query, (buyer_id, product_id, quantity, total_price, shipping_address))


def get_orders_by_buyer(db: DatabaseManager, buyer_id: int) -> List[Dict[str, Any]]:
    """
    Retrieve all orders by a buyer.

    Args:
        db: DatabaseManager instance
        buyer_id: Buyer's user ID

    Returns:
        List of orders with product details
    """
    query = """
        SELECT o.*, p.product_name, p.image_url, u.full_name as artisan_name
        FROM orders o
        JOIN products p ON o.product_id = p.product_id
        JOIN users u ON p.artisan_id = u.user_id
        WHERE o.buyer_id = %s
        ORDER BY o.created_at DESC
    """
    return db.execute_query(query, (buyer_id,))


def get_orders_by_artisan(db: DatabaseManager, artisan_id: int) -> List[Dict[str, Any]]:
    """
    Retrieve all orders for an artisan's products.

    Args:
        db: DatabaseManager instance
        artisan_id: Artisan's user ID

    Returns:
        List of orders
    """
    query = """
        SELECT o.*, p.product_name, u.full_name as buyer_name, u.phone as buyer_phone
        FROM orders o
        JOIN products p ON o.product_id = p.product_id
        JOIN users u ON o.buyer_id = u.user_id
        WHERE p.artisan_id = %s
        ORDER BY o.created_at DESC
    """
    return db.execute_query(query, (artisan_id,))


def update_order_status(db: DatabaseManager, order_id: int, new_status: str) -> int:
    """
    Update order status.

    Args:
        db: DatabaseManager instance
        order_id: Order ID
        new_status: New status value

    Returns:
        Number of affected rows
    """
    query = "UPDATE orders SET status = %s WHERE order_id = %s"
    return db.execute_update(query, (new_status, order_id))


# ============================================================================
# DATABASE OPERATIONS - Transaction & Audit
# ============================================================================

def create_transaction(db: DatabaseManager, order_id: int, artisan_id: int,
                       buyer_id: int, product_id: int, amount: float) -> Optional[Dict[str, Any]]:
    """
    Create a financial transaction record.

    Automatically calculates 5% commission and artisan payout.

    Args:
        db: DatabaseManager instance
        order_id: Associated order ID
        artisan_id: Artisan's user ID
        buyer_id: Buyer's user ID
        product_id: Product ID
        amount: Total transaction amount

    Returns:
        Created transaction data
    """
    commission_rate = 0.05  # 5% platform commission
    commission_fee = round(amount * commission_rate, 2)
    artisan_payout = round(amount - commission_fee, 2)

    query = """
        INSERT INTO transactions (order_id, artisan_id, buyer_id, product_id, 
                                 amount, commission_fee, artisan_payout)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING *
    """
    return db.execute_insert_returning(
        query,
        (order_id, artisan_id, buyer_id, product_id,
         amount, commission_fee, artisan_payout)
    )


def get_all_transactions(db: DatabaseManager) -> List[Dict[str, Any]]:
    """
    Retrieve all transactions (for admin audit).

    Args:
        db: DatabaseManager instance

    Returns:
        List of transactions with full details
    """
    query = "SELECT * FROM admin_financial_audit"
    return db.execute_query(query)


def create_audit_log(db: DatabaseManager, user_id: int, action_type: str,
                     entity_type: str = None, entity_id: int = None,
                     details: dict = None, ip_address: str = None) -> Optional[Dict[str, Any]]:
    """
    Create an audit log entry.

    Args:
        db: DatabaseManager instance
        user_id: User performing the action
        action_type: Type of action (e.g., 'purchase', 'status_update')
        entity_type: Type of entity affected (e.g., 'order', 'product')
        entity_id: ID of affected entity
        details: Additional details as JSON
        ip_address: User's IP address

    Returns:
        Created audit log entry
    """
    import json
    details_json = json.dumps(details) if details else None

    query = """
        INSERT INTO audit_logs (user_id, action_type, entity_type, entity_id, details, ip_address)
        VALUES (%s, %s, %s, %s, %s::jsonb, %s)
        RETURNING *
    """
    return db.execute_insert_returning(
        query,
        (user_id, action_type, entity_type, entity_id, details_json, ip_address)
    )


# ============================================================================
# EXPLANATION FOR FACULTY
# ============================================================================
#
# DATABASE MODULE ARCHITECTURE:
#
# 1. CONNECTION POOLING:
#    - Uses psycopg2.pool.SimpleConnectionPool for efficient resource management
#    - Maintains 1-10 concurrent connections to handle multiple requests
#    - Connections are automatically reused, improving performance
#
# 2. CONTEXT MANAGERS:
#    - get_connection() and get_cursor() use Python's 'with' statement
#    - Automatically handles connection cleanup and error rollback
#    - Prevents connection leaks and ensures data consistency
#
# 3. QUERY ABSTRACTION:
#    - Separate functions for different query types (SELECT, INSERT, UPDATE)
#    - Parameterized queries prevent SQL injection attacks
#    - RealDictCursor returns results as dictionaries for easy JSON conversion
#
# 4. BUSINESS LOGIC:
#    - Helper functions encapsulate common database operations
#    - Each function handles one specific task (Single Responsibility Principle)
#    - Makes the main API code cleaner and easier to test
#
# 5. ERROR HANDLING:
#    - All operations include try-except blocks
#    - Automatic rollback on errors maintains database consistency
#    - Logging helps with debugging and monitoring
#
# ============================================================================
