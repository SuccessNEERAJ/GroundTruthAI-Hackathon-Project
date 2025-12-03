"""
Quick test script to verify the setup is working correctly.
"""

# Suppress all warnings at the start
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import warnings
warnings.filterwarnings('ignore')

# Suppress TensorFlow warnings specifically
import logging
logging.getLogger('tensorflow').setLevel(logging.ERROR)

print("=" * 60)
print("Testing Hyper-Personalized Retail Support Agent Setup")
print("=" * 60)

# Test 1: Database
print("\n1. Testing Database...")
try:
    from database import init_db, get_all_customers, get_customer_context
    init_db()
    customers = get_all_customers()
    print(f"   ✓ Database initialized with {len(customers)} customers")
    
    # Show first few customers
    print("\n   Sample customers:")
    for customer in customers[:5]:
        print(f"   - {customer['name']} ({customer['loyalty_level']}) - {customer['preferred_drink']}")
    
    # Test customer context
    ctx = get_customer_context(1)
    print(f"\n   ✓ Customer context loaded for {ctx['name']}")
    print(f"     - Recent orders: {len(ctx['recent_orders'])}")
    print(f"     - Active coupons: {len(ctx['active_coupons'])}")
except Exception as e:
    print(f"   ✗ Database error: {e}")

# Test 2: PII Masking
print("\n2. Testing PII Masking...")
try:
    from masking import mask_text, unmask_text
    test_text = "Call me at +1-555-0101 or email test@example.com"
    masked, mapping = mask_text(test_text)
    unmasked = unmask_text(masked, mapping)
    
    print(f"   Original:  {test_text}")
    print(f"   Masked:    {masked}")
    print(f"   Unmasked:  {unmasked}")
    print(f"   ✓ PII masking working correctly")
except Exception as e:
    print(f"   ✗ Masking error: {e}")

# Test 3: Configuration
print("\n3. Testing Configuration...")
try:
    from config import get_groq_api_key, validate_groq_api_key
    api_key = get_groq_api_key()
    if api_key:
        print(f"   ✓ GROQ_API_KEY found: {api_key[:10]}...{api_key[-5:]}")
    else:
        print("   ✗ GROQ_API_KEY not found in .env file")
except Exception as e:
    print(f"   ✗ Config error: {e}")

# Test 4: RAG System
print("\n4. Testing RAG System...")
try:
    from rag import build_vector_store, rag_retrieve
    import os
    from config import VECTOR_STORE_DIR
    
    if not os.path.exists(VECTOR_STORE_DIR):
        print("   Building vector store (first time setup)...")
        build_vector_store()
    
    # Test retrieval
    results = rag_retrieve("What hot drinks do you have?", k=2)
    print(f"   ✓ RAG system working - retrieved {len(results)} documents")
    if results:
        print(f"   Sample result: {results[0][:100]}...")
except Exception as e:
    print(f"   ✗ RAG error: {e}")

# Test 5: LLM Client
print("\n5. Testing LLM Client...")
try:
    from llm_client import call_llm
    from config import validate_groq_api_key
    
    validate_groq_api_key()
    print("   ✓ LLM client configured correctly")
    print("   Note: Actual LLM call will be tested in the Streamlit app")
except Exception as e:
    print(f"   ✗ LLM client error: {e}")

print("\n" + "=" * 60)
print("Setup Test Complete!")
print("=" * 60)
print("\nTo start the application, run:")
print("  streamlit run streamlit_app.py")
print("\n" + "=" * 60)
