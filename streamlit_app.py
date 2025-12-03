"""
Main Streamlit application for the Hyper-Personalized Retail Support Agent.
Provides a chat interface that combines customer context, store data, and RAG.
"""

# Suppress warnings before any imports
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import warnings
warnings.filterwarnings('ignore')

import streamlit as st
from typing import Dict, List

# Import our modules
from config import TOP_K_RAG, VECTOR_STORE_DIR
from database import init_db, get_customer_context, get_nearest_store_for_customer, get_all_customers
from rag import build_vector_store, rag_retrieve, get_rag_system
from masking import mask_text, unmask_text, mask_customer_context
from llm_client import call_llm_with_system


# Page configuration
st.set_page_config(
    page_title="Hyper-Personalized Retail Assistant",
    page_icon="☕",
    layout="wide"
)


def initialize_app():
    """Initialize database and vector store on first run."""
    # Initialize database
    init_db()
    
    # Check if vector store exists, build if not
    if not os.path.exists(VECTOR_STORE_DIR):
        with st.spinner("Building knowledge base for the first time... This may take a minute."):
            try:
                build_vector_store()
                st.success("✓ Knowledge base built successfully!")
            except Exception as e:
                st.error(f"Error building knowledge base: {e}")
                st.info("The app will continue without RAG functionality.")


def build_prompt(customer_ctx: Dict, store_ctx: Dict, rag_docs: List[str], user_message: str) -> tuple[str, str]:
    """
    Build the system and user prompts for the LLM.
    
    Args:
        customer_ctx: Customer context dictionary.
        store_ctx: Store context dictionary.
        rag_docs: Retrieved document snippets.
        user_message: The user's message (already masked).
    
    Returns:
        tuple[str, str]: System prompt and user prompt.
    """
    # System prompt
    system_prompt = """You are a hyper-personalized retail assistant for a coffee shop chain.

Your role:
- Provide helpful, specific, and context-aware responses
- Use customer history and preferences to personalize suggestions
- Mention nearby stores, distances, and operating hours when relevant
- Highlight available coupons and discounts
- Be warm, friendly, and concise
- If the user expresses a need (like "I'm cold"), proactively suggest relevant products

Guidelines:
- Always prioritize customer satisfaction
- Use the provided context to give specific answers
- Don't make up information not in the context
- Keep responses conversational and natural
"""
    
    # Build user prompt with context
    user_prompt_parts = []
    
    # Customer context
    if customer_ctx:
        user_prompt_parts.append("=== CUSTOMER CONTEXT ===")
        user_prompt_parts.append(f"Name: {customer_ctx.get('name', 'Unknown')}")
        user_prompt_parts.append(f"Loyalty Level: {customer_ctx.get('loyalty_level', 'None')}")
        user_prompt_parts.append(f"Preferred Drink: {customer_ctx.get('preferred_drink', 'None')}")
        
        # Recent orders
        recent_orders = customer_ctx.get('recent_orders', [])
        if recent_orders:
            user_prompt_parts.append(f"\nRecent Orders ({len(recent_orders)}):")
            for order in recent_orders[:3]:
                user_prompt_parts.append(f"  - {order['item_name']} ({order['size']}) - {order['status']}")
        
        # Active coupons
        coupons = customer_ctx.get('active_coupons', [])
        if coupons:
            user_prompt_parts.append(f"\nActive Coupons ({len(coupons)}):")
            for coupon in coupons:
                user_prompt_parts.append(f"  - {coupon['description']} (valid until {coupon['valid_until']})")
        
        user_prompt_parts.append("")
    
    # Store context
    if store_ctx:
        user_prompt_parts.append("=== NEARBY STORE ===")
        user_prompt_parts.append(f"Name: {store_ctx.get('name', 'Unknown')}")
        user_prompt_parts.append(f"Distance: {store_ctx.get('distance_m', 'Unknown')}m away")
        user_prompt_parts.append(f"Address: {store_ctx.get('address', 'Unknown')}")
        user_prompt_parts.append(f"Hours: {store_ctx.get('open_time', 'Unknown')} - {store_ctx.get('close_time', 'Unknown')}")
        user_prompt_parts.append("")
    
    # RAG context
    if rag_docs:
        user_prompt_parts.append("=== RELEVANT INFORMATION ===")
        for i, doc in enumerate(rag_docs, 1):
            user_prompt_parts.append(f"[Document {i}]")
            user_prompt_parts.append(doc.strip())
            user_prompt_parts.append("")
    
    # User message
    user_prompt_parts.append("=== CUSTOMER MESSAGE ===")
    user_prompt_parts.append(user_message)
    
    user_prompt = "\n".join(user_prompt_parts)
    
    return system_prompt, user_prompt


def process_message(user_message: str, customer_id: int) -> str:
    """
    Process a user message and generate a response.
    
    Args:
        user_message: The user's input message.
        customer_id: The current customer's ID.
    
    Returns:
        str: The assistant's response.
    """
    try:
        # Get customer and store context
        customer_ctx = get_customer_context(customer_id)
        store_ctx = get_nearest_store_for_customer(customer_id)
        
        # Mask PII in user message
        masked_message, pii_mapping = mask_text(user_message)
        
        # Mask PII in customer context
        masked_customer_ctx, customer_pii_mapping = mask_customer_context(customer_ctx)
        pii_mapping.update(customer_pii_mapping)
        
        # Retrieve relevant documents using masked message
        rag_docs = []
        try:
            rag_docs = rag_retrieve(masked_message, k=TOP_K_RAG)
        except Exception as e:
            st.warning(f"RAG retrieval unavailable: {e}")
        
        # Build prompts with masked context
        system_prompt, user_prompt = build_prompt(masked_customer_ctx, store_ctx, rag_docs, masked_message)
        
        # Call LLM
        response_masked = call_llm_with_system(system_prompt, user_prompt)
        
        # Unmask PII in response
        response = unmask_text(response_masked, pii_mapping)
        
        return response
    
    except Exception as e:
        return f"I apologize, but I encountered an error: {str(e)}\n\nPlease make sure your GROQ_API_KEY is set in the .env file."


def main():
    """Main Streamlit application."""
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "initialized" not in st.session_state:
        initialize_app()
        st.session_state.initialized = True
    if "selected_customer_id" not in st.session_state:
        st.session_state.selected_customer_id = 1
    
    # Header
    st.title("☕ Hyper-Personalized Retail Assistant")
    st.markdown("*Your smart coffee shop companion*")
    
    # Sidebar
    with st.sidebar:
        st.header("Customer Selection")
        
        # Get all customers
        all_customers = get_all_customers()
        
        # Create a searchable dropdown
        customer_options = {f"{c['name']} ({c['loyalty_level']})": c['id'] for c in all_customers}
        
        # Search box
        search_term = st.text_input("🔍 Search customer by name", placeholder="Type to search...")
        
        # Filter customers based on search
        if search_term:
            filtered_options = {k: v for k, v in customer_options.items() if search_term.lower() in k.lower()}
        else:
            filtered_options = customer_options
        
        if filtered_options:
            selected_user = st.selectbox(
                "Select Customer",
                options=list(filtered_options.keys()),
                index=0 if not hasattr(st.session_state, 'last_selection') else 
                      (list(filtered_options.keys()).index(st.session_state.last_selection) 
                       if st.session_state.last_selection in filtered_options.keys() else 0)
            )
            customer_id = filtered_options[selected_user]
            st.session_state.last_selection = selected_user
            
            # Update selected customer ID
            if st.session_state.selected_customer_id != customer_id:
                st.session_state.selected_customer_id = customer_id
                st.session_state.messages = []  # Clear chat when switching users
        else:
            st.warning("No customers found matching your search.")
            customer_id = 1
        
        st.divider()
        
        # Display customer info
        st.subheader("📋 Customer Profile")
        customer_ctx = get_customer_context(customer_id)
        if customer_ctx:
            st.write(f"**Name:** {customer_ctx['name']}")
            st.write(f"**Phone:** {customer_ctx['phone']}")
            st.write(f"**Email:** {customer_ctx['email']}")
            st.write(f"**Address:** {customer_ctx.get('address', 'N/A')}")
            st.write(f"**Loyalty:** {customer_ctx['loyalty_level']}")
            st.write(f"**Preferred:** {customer_ctx['preferred_drink']}")
            
            recent_orders = customer_ctx.get('recent_orders', [])
            if recent_orders:
                st.write(f"**Recent Orders:** {len(recent_orders)}")
                with st.expander("View Orders"):
                    for order in recent_orders[:3]:
                        st.caption(f"• {order['item_name']} ({order['size']}) - {order['status']}")
            
            coupons = customer_ctx.get('active_coupons', [])
            if coupons:
                st.write(f"**Active Coupons:** {len(coupons)}")
                with st.expander("View Coupons"):
                    for coupon in coupons:
                        st.caption(f"• {coupon['description']}")
        
        st.divider()
        
        # Display nearest store info
        st.subheader("📍 Nearest Store")
        from database import get_nearest_store_for_customer
        nearest_store = get_nearest_store_for_customer(customer_id)
        if nearest_store:
            distance = nearest_store.get('distance_m', 0)
            if distance >= 1000:
                distance_str = f"{distance/1000:.1f} km"
            else:
                distance_str = f"{int(distance)} m"
            
            st.write(f"**{nearest_store['name']}**")
            st.write(f"📏 Distance: **{distance_str}**")
            st.write(f"🕐 Hours: {nearest_store['open_time']} - {nearest_store['close_time']}")
            st.caption(f"📍 {nearest_store['address']}")
        
        st.divider()
        
        # Clear chat button
        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.rerun()
        
        st.divider()
        
        # Info
        st.caption("💡 **Try asking:**")
        st.caption("• 'I'm cold'")
        st.caption("• 'Is the store open?'")
        st.caption("• 'What's your refund policy?'")
        st.caption("• 'Where is my order?'")
        st.caption("• 'What hot drinks do you have?'")
        
        st.divider()
        
        # Privacy notice
        st.info("🔒 **Privacy Protected**: All personal information is masked before being sent to the AI model.")
        
        st.divider()
        
        # RAG update notice
        with st.expander("📚 Updating Knowledge Base"):
            st.caption("**If you change PDF files:**")
            st.caption("1. Delete the `chroma_db/` folder, OR")
            st.caption("2. Run `python rag.py` to rebuild")
            st.caption("")
            st.caption("This updates the AI's knowledge from your PDFs in `data/pdfs/`")
    
    # Chat interface
    chat_container = st.container()
    
    with chat_container:
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate and display assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = process_message(prompt, customer_id)
                st.markdown(response)
        
        # Add assistant response to chat
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Rerun to update the display
        st.rerun()


if __name__ == "__main__":
    main()
