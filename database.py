"""
Database module for managing SQLite database operations.
Handles customer, store, order, and coupon data.
"""

import sqlite3
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from config import DB_PATH
import math


def get_connection() -> sqlite3.Connection:
    """
    Create and return a connection to the SQLite database.
    
    Returns:
        sqlite3.Connection: Database connection object.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


def init_db() -> None:
    """
    Initialize the database with tables and seed data.
    Creates tables if they don't exist and populates with sample data.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create customers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            preferred_drink TEXT,
            loyalty_level TEXT,
            address TEXT,
            latitude REAL,
            longitude REAL
        )
    """)
    
    # Create stores table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stores (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            address TEXT,
            open_time TEXT,
            close_time TEXT
        )
    """)
    
    # Create orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            store_id INTEGER,
            item_name TEXT,
            item_type TEXT,
            size TEXT,
            status TEXT,
            timestamp TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (store_id) REFERENCES stores(id)
        )
    """)
    
    # Create coupons table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coupons (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            description TEXT,
            product_name TEXT,
            discount_percent REAL,
            valid_until TEXT,
            is_active INTEGER,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)
    
    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM customers")
    if cursor.fetchone()[0] == 0:
        # Seed customers with diverse profiles and locations around NYC
        # BeanHaven Coffee - Downtown is at (40.7589, -73.9851)
        # BeanHaven Coffee - Uptown is at (40.7829, -73.9654)
        # BeanHaven Coffee - Midtown is at (40.7549, -73.9840)
        customers_data = [
            (1, "Neeraj Kumar", "+1-555-0101", "neeraj.kumar@example.com", "Hot Cocoa", "Gold", 
             "120 Main St, New York, NY", 40.7592, -73.9855),  # ~50m from Downtown
            (2, "Alice Johnson", "+1-555-0102", "alice.j@example.com", "Caramel Latte", "Silver",
             "200 Broadway, New York, NY", 40.7595, -73.9870),  # ~150m from Downtown
            (3, "Michael Chen", "+1-555-0103", "m.chen@example.com", "Espresso", "Platinum",
             "350 5th Ave, New York, NY", 40.7610, -73.9880),  # ~300m from Downtown
            (4, "Sarah Williams", "+1-555-0104", "sarah.w@example.com", "Cappuccino", "Gold",
             "89 Madison Ave, New York, NY", 40.7545, -73.9835),  # ~50m from Midtown
            (5, "David Martinez", "+1-555-0105", "david.m@example.com", "Americano", "Bronze",
             "567 Lexington Ave, New York, NY", 40.7620, -73.9900),  # ~500m from Downtown
            (6, "Emily Brown", "+1-555-0106", "emily.brown@example.com", "Latte", "Silver",
             "125 Main St, New York, NY", 40.7590, -73.9852),  # ~30m from Downtown
            (7, "James Wilson", "+1-555-0107", "j.wilson@example.com", "Cold Brew", "Gold",
             "789 Park Ave, New York, NY", 40.7835, -73.9660),  # ~80m from Uptown
            (8, "Lisa Anderson", "+1-555-0108", "lisa.a@example.com", "Frappuccino", "Bronze",
             "234 West St, New York, NY", 40.7560, -73.9830),  # ~150m from Midtown
            (9, "Robert Taylor", "+1-555-0109", "robert.t@example.com", "Hot Cocoa", "Silver",
             "456 East St, New York, NY", 40.7600, -73.9860),  # ~100m from Downtown
            (10, "Jennifer Lee", "+1-555-0110", "jennifer.lee@example.com", "Iced Latte", "Platinum",
             "678 Central Ave, New York, NY", 40.7825, -73.9650),  # ~60m from Uptown
        ]
        cursor.executemany(
            "INSERT INTO customers (id, name, phone, email, preferred_drink, loyalty_level, address, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            customers_data
        )
        
        # Seed stores - BeanHaven Coffee branches
        stores_data = [
            (1, "BeanHaven Coffee - Downtown", 40.7589, -73.9851, "123 Main St, New York, NY", "06:00", "21:00"),
            (2, "BeanHaven Coffee - Uptown", 40.7829, -73.9654, "456 Park Ave, New York, NY", "07:00", "20:00"),
            (3, "BeanHaven Coffee - Midtown", 40.7549, -73.9840, "789 Broadway, New York, NY", "06:30", "22:00"),
        ]
        cursor.executemany(
            "INSERT INTO stores (id, name, latitude, longitude, address, open_time, close_time) VALUES (?, ?, ?, ?, ?, ?, ?)",
            stores_data
        )
        
        # Seed orders with more variety
        now = datetime.now()
        orders_data = [
            (1, 1, 1, "Hot Cocoa", "hot_drink", "Medium", "completed", (now - timedelta(days=2)).isoformat()),
            (2, 1, 1, "Cappuccino", "hot_drink", "Large", "completed", (now - timedelta(days=5)).isoformat()),
            (3, 2, 1, "Caramel Latte", "hot_drink", "Medium", "ready", now.isoformat()),
            (4, 2, 2, "Iced Coffee", "cold_drink", "Large", "completed", (now - timedelta(days=1)).isoformat()),
            (5, 3, 1, "Espresso", "hot_drink", "Small", "completed", (now - timedelta(days=1)).isoformat()),
            (6, 3, 1, "Espresso", "hot_drink", "Small", "completed", (now - timedelta(days=3)).isoformat()),
            (7, 4, 2, "Cappuccino", "hot_drink", "Large", "in_progress", now.isoformat()),
            (8, 5, 1, "Americano", "hot_drink", "Medium", "completed", (now - timedelta(days=4)).isoformat()),
            (9, 6, 1, "Latte", "hot_drink", "Medium", "completed", (now - timedelta(days=2)).isoformat()),
            (10, 7, 2, "Cold Brew", "cold_drink", "Large", "ready", now.isoformat()),
            (11, 8, 1, "Frappuccino", "cold_drink", "Medium", "completed", (now - timedelta(days=1)).isoformat()),
            (12, 9, 1, "Hot Cocoa", "hot_drink", "Large", "completed", (now - timedelta(days=3)).isoformat()),
            (13, 10, 2, "Iced Latte", "cold_drink", "Medium", "completed", (now - timedelta(days=1)).isoformat()),
        ]
        cursor.executemany(
            "INSERT INTO orders (id, customer_id, store_id, item_name, item_type, size, status, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            orders_data
        )
        
        # Seed coupons with more variety
        future_date = (now + timedelta(days=30)).strftime("%Y-%m-%d")
        near_future = (now + timedelta(days=15)).strftime("%Y-%m-%d")
        coupons_data = [
            (1, 1, "10% OFF Hot Cocoa", "Hot Cocoa", 10.0, future_date, 1),
            (2, 2, "15% OFF Any Latte", "Latte", 15.0, future_date, 1),
            (3, 3, "20% OFF Espresso", "Espresso", 20.0, future_date, 1),
            (4, 4, "Buy 1 Get 1 Free Cappuccino", "Cappuccino", 50.0, near_future, 1),
            (5, 5, "5% OFF Any Drink", "Any Drink", 5.0, future_date, 1),
            (6, 6, "Free Size Upgrade", "Any Drink", 0.0, future_date, 1),
            (7, 7, "15% OFF Cold Brew", "Cold Brew", 15.0, future_date, 1),
            (8, 9, "10% OFF Hot Cocoa", "Hot Cocoa", 10.0, future_date, 1),
            (9, 10, "20% OFF Iced Drinks", "Iced Latte", 20.0, near_future, 1),
        ]
        cursor.executemany(
            "INSERT INTO coupons (id, customer_id, description, product_name, discount_percent, valid_until, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)",
            coupons_data
        )
        
        conn.commit()
        print(f"✓ Database initialized and seeded at {DB_PATH}")
    
    conn.close()


def get_customer_context(customer_id: int) -> Dict:
    """
    Retrieve comprehensive context for a specific customer.
    
    Args:
        customer_id: The customer's unique identifier.
    
    Returns:
        Dict: Customer information including recent orders and active coupons.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get customer info
    cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    customer = cursor.fetchone()
    
    if not customer:
        conn.close()
        return {}
    
    # Get recent orders (last 5)
    cursor.execute("""
        SELECT o.*, s.name as store_name
        FROM orders o
        JOIN stores s ON o.store_id = s.id
        WHERE o.customer_id = ?
        ORDER BY o.timestamp DESC
        LIMIT 5
    """, (customer_id,))
    orders = [dict(row) for row in cursor.fetchall()]
    
    # Get active coupons
    cursor.execute("""
        SELECT * FROM coupons
        WHERE customer_id = ? AND is_active = 1
        ORDER BY valid_until DESC
    """, (customer_id,))
    coupons = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    # Convert to dict to use .get() method
    customer_dict = dict(customer)
    
    return {
        "id": customer_dict["id"],
        "name": customer_dict["name"],
        "phone": customer_dict["phone"],
        "email": customer_dict["email"],
        "address": customer_dict.get("address", "N/A"),
        "latitude": customer_dict.get("latitude"),
        "longitude": customer_dict.get("longitude"),
        "preferred_drink": customer_dict["preferred_drink"],
        "loyalty_level": customer_dict["loyalty_level"],
        "recent_orders": orders,
        "active_coupons": coupons
    }


def get_store_context(store_id: int) -> Dict:
    """
    Retrieve context for a specific store.
    
    Args:
        store_id: The store's unique identifier.
    
    Returns:
        Dict: Store information including location and operating hours.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM stores WHERE id = ?", (store_id,))
    store = cursor.fetchone()
    
    conn.close()
    
    if not store:
        return {}
    
    return dict(store)


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the distance between two GPS coordinates using the Haversine formula.
    
    Args:
        lat1: Latitude of point 1
        lon1: Longitude of point 1
        lat2: Latitude of point 2
        lon2: Longitude of point 2
    
    Returns:
        float: Distance in meters
    """
    # Earth's radius in meters
    R = 6371000
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    
    return round(distance, 1)


def get_nearest_store_for_customer(customer_id: int) -> Dict:
    """
    Get the nearest store for a specific customer based on their location.
    
    Args:
        customer_id: The customer's unique identifier.
    
    Returns:
        Dict: Store information with calculated distance.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get customer location
    cursor.execute("SELECT latitude, longitude FROM customers WHERE id = ?", (customer_id,))
    customer_row = cursor.fetchone()
    
    if not customer_row or not customer_row['latitude'] or not customer_row['longitude']:
        # Fallback to default store with default distance
        cursor.execute("SELECT * FROM stores LIMIT 1")
        store = cursor.fetchone()
        conn.close()
        
        if not store:
            return {}
        
        store_dict = dict(store)
        store_dict["distance_m"] = 50  # Default distance
        return store_dict
    
    customer_lat = customer_row['latitude']
    customer_lon = customer_row['longitude']
    
    # Get all stores and calculate distances
    cursor.execute("SELECT * FROM stores")
    stores = cursor.fetchall()
    
    conn.close()
    
    if not stores:
        return {}
    
    # Calculate distance to each store and find the nearest
    nearest_store = None
    min_distance = float('inf')
    
    for store in stores:
        distance = calculate_distance(
            customer_lat, customer_lon,
            store['latitude'], store['longitude']
        )
        
        if distance < min_distance:
            min_distance = distance
            nearest_store = dict(store)
            nearest_store["distance_m"] = distance
    
    return nearest_store


def get_nearest_store_for_demo() -> Dict:
    """
    Get the nearest store for demo purposes (backward compatibility).
    
    Returns:
        Dict: Store information with simulated distance.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # For demo, just return the first store with a simulated distance
    cursor.execute("SELECT * FROM stores LIMIT 1")
    store = cursor.fetchone()
    
    conn.close()
    
    if not store:
        return {}
    
    store_dict = dict(store)
    store_dict["distance_m"] = 50  # Simulated: 50 meters away
    
    return store_dict


def get_all_customers() -> List[Dict]:
    """
    Get all customers from the database.
    
    Returns:
        List[Dict]: List of all customer records.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, phone, email, preferred_drink, loyalty_level, address, latitude, longitude FROM customers ORDER BY name")
    customers = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return customers


if __name__ == "__main__":
    # Initialize database when run directly
    init_db()
    
    # Test queries
    print("\n=== Customer Context Test ===")
    ctx = get_customer_context(1)
    print(f"Customer: {ctx['name']}")
    print(f"Preferred drink: {ctx['preferred_drink']}")
    print(f"Active coupons: {len(ctx['active_coupons'])}")
    print(f"Recent orders: {len(ctx['recent_orders'])}")
    
    print("\n=== Store Context Test ===")
    store = get_nearest_store_for_demo()
    print(f"Store: {store['name']}")
    print(f"Distance: {store['distance_m']}m")
    print(f"Hours: {store['open_time']} - {store['close_time']}")
