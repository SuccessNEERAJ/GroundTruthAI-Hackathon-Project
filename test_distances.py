"""
Test script to demonstrate distance calculations for each customer.
"""

# Suppress warnings
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import warnings
warnings.filterwarnings('ignore')

from database import init_db, get_all_customers, get_nearest_store_for_customer

print("=" * 80)
print("Customer Distance Analysis")
print("=" * 80)

# Initialize database
init_db()

# Get all customers
customers = get_all_customers()

print(f"\nTotal Customers: {len(customers)}\n")

# Show distance for each customer
for customer in customers:
    customer_id = customer['id']
    name = customer['name']
    address = customer.get('address', 'N/A')
    
    # Get nearest store
    nearest_store = get_nearest_store_for_customer(customer_id)
    
    if nearest_store:
        distance = nearest_store.get('distance_m', 0)
        store_name = nearest_store['name']
        
        # Format distance
        if distance >= 1000:
            distance_str = f"{distance/1000:.2f} km"
        else:
            distance_str = f"{int(distance)} m"
        
        print(f"Customer: {name}")
        print(f"  Address: {address}")
        print(f"  Nearest Store: {store_name}")
        print(f"  Distance: {distance_str}")
        print()

print("=" * 80)
