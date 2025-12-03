# Hyper-Personalized Retail Support Agent

A smart, context-aware customer support chatbot that combines structured data, unstructured knowledge, and AI to deliver personalized retail experiences.

## The Problem (Real World Scenario)

Modern retail customers expect instant, personalized answers to their questions. They want to know:
- "Is this store open right now?"
- "Do you have my size in stock?"
- "Where is my order?"
- "I'm cold." → They expect a smart suggestion like "Come inside the Starbucks 50m away. We have a 10% coupon for Hot Cocoa."

**The challenge**: Most chatbots today are generic and "dumb." They provide FAQ-style answers without understanding:
- **Who** the customer is (purchase history, preferences, available coupons)
- **Where** they are (nearby stores, distances, operating hours)
- **Context** from unstructured documents (menus, policies, FAQs)

### The Coffee Shop Example

Imagine a customer standing outside a coffee shop on a cold day. They open the retail app and type: **"I'm cold."**

A typical chatbot might respond: *"Please visit our store for hot beverages."*

A **hyper-personalized agent** responds: *"Come inside the Starbucks 50m away—we're open until 9 PM! Try our Hot Cocoa (your favorite). You have a 10% discount coupon available."*

This is the experience we're building.

## Expected End Result

The final system is a **Streamlit web application** where users can chat with an intelligent retail assistant that:

- **Understands customer identity**: Pulls purchase history, loyalty status, preferred products, and active coupons from a database
- **Knows store context**: Uses real-time store data (location, distance, operating hours, inventory)
- **Leverages unstructured knowledge**: Searches through PDFs containing menus, store policies, refund FAQs, and delivery information
- **Protects privacy**: Masks personally identifiable information (PII) before sending data to the LLM and unmasks it in the response

### Example Behaviors

| User Input | Bot Response |
|------------|--------------|
| "I'm cold" | "Come inside the Starbucks 50m away—we're open until 9 PM! Try our Hot Cocoa. You have a 10% discount coupon available." |
| "Is this store open?" | "Yes! The Downtown Starbucks is open from 6 AM to 9 PM today." |
| "Where is my order?" | "Your Caramel Latte order is ready for pickup at the Downtown location." |
| "What's your refund policy?" | *[Retrieves and summarizes from refund_faqs.pdf]* |

## Technical Approach

### High-Level Architecture

```
┌─────────────────┐
│  Streamlit UI   │  ← User chats here
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│         Orchestration Layer             │
│  (streamlit_app.py)                     │
│  • Fetch customer context from DB       │
│  • Fetch store context from DB          │
│  • Mask PII in user message             │
│  • Retrieve relevant PDF snippets (RAG) │
│  • Build prompt with all context        │
│  • Call Groq LLaMA model                │
│  • Unmask PII in response               │
└─────────────────────────────────────────┘
         │
         ├──────────────┬──────────────┬──────────────┐
         ▼              ▼              ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│   SQLite DB  │ │   RAG    │ │ Masking  │ │  Groq LLaMA  │
│              │ │ (Vector  │ │  Module  │ │   API Call   │
│ • Customers  │ │  Store)  │ │          │ │              │
│ • Orders     │ │          │ │ Mask PII │ │ llama-3.3-   │
│ • Stores     │ │ PDFs:    │ │ before   │ │ 70b-         │
│ • Coupons    │ │ • Menu   │ │ LLM call │ │ versatile    │
│              │ │ • Policy │ │          │ │              │
│              │ │ • FAQs   │ │ Unmask   │ │              │
│              │ │          │ │ after    │ │              │
└──────────────┘ └──────────┘ └──────────┘ └──────────────┘
```

### Request Flow

1. **User sends message** in Streamlit chat (e.g., "I'm cold")
2. **Fetch structured context** from SQLite:
   - Customer data: recent orders, coupons, preferred drink, loyalty level
   - Store data: name, distance, open/close times, address
3. **Mask PII**: Replace phone numbers, emails, and sensitive data with placeholders
4. **RAG retrieval**: Search PDF knowledge base using the masked user message
5. **Build prompt**: Combine system instructions + customer context + store context + RAG snippets + masked user message
6. **Call Groq LLaMA**: Send prompt to `llama-3.3-70b-versatile` model via Groq API
7. **Unmask response**: Restore original PII values in the LLM's response
8. **Display**: Show the personalized answer in the chat UI

### Privacy-First Design

**Critical**: No raw PII (phone numbers, emails, names) is ever sent to the public LLM.

- **Before LLM call**: `mask_text()` replaces PII with tokens like `[PHONE_1]`, `[EMAIL_1]`
- **After LLM response**: `unmask_text()` restores the original values
- This ensures compliance with privacy regulations while maintaining personalization

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Language** | Python 3.10+ |
| **Frontend** | Streamlit |
| **Database** | SQLite |
| **Vector Store** | ChromaDB |
| **LLM Provider** | Groq API |
| **LLM Model** | `llama-3.3-70b-versatile` (Meta LLaMA) |
| **Environment Management** | `.env` file + `python-dotenv` |

### Key Libraries

- `streamlit` - Web UI framework
- `groq` - Official Groq API client
- `python-dotenv` - Load environment variables from `.env`
- `chromadb` - Vector database for RAG
- `langchain` - Document loading and text splitting
- `sentence-transformers` - Embeddings for semantic search

## Challenges & Learnings

### Key Challenges

1. **Combining structured and unstructured data**: Merging database queries (orders, coupons) with PDF content (policies, menus) into a single coherent prompt
2. **Context length management**: Deciding what information to include without exceeding token limits
3. **PII masking implementation**: Building a robust system to detect and replace sensitive information before LLM calls
4. **API integration**: Working with external LLM APIs (Groq) while handling rate limits, errors, and streaming responses
5. **RAG quality**: Ensuring vector search returns relevant snippets that actually help answer the user's question

### What You'll Learn

- **RAG fundamentals**: How to build a retrieval-augmented generation system from scratch
- **Prompt engineering**: Crafting effective prompts that combine multiple data sources
- **Security best practices**: Using environment variables and `.env` files to protect API keys
- **Privacy techniques**: Implementing PII masking/unmasking for compliance
- **Modular Python architecture**: Organizing code into clean, reusable modules
- **Streamlit development**: Building interactive chat interfaces with session state management

## Visual Proof

Once the app is running, you can capture screenshots showing:

1. **Chat interface**: User typing "I'm cold" and receiving a personalized response with store name, distance, product suggestion, and coupon information
2. **Database contents**: Console output or DB browser showing seeded customers, stores, orders, and coupons
3. **RAG in action**: Debug logs showing which PDF snippets were retrieved for a given query
4. **PII masking**: Before/after examples of text with masked phone numbers and emails

*Screenshots can be added to the `Screenshots/` folder once the application is operational.*

## How to Run

### Prerequisites

- Python 3.10 or higher
- A Groq API key (sign up at [https://console.groq.com](https://console.groq.com))

### Step-by-Step Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd <project-folder>
   ```

2. **Create and activate a virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```env
   GROQ_API_KEY=your_actual_groq_api_key_here
   ```
   
   **Important**: Never commit your `.env` file to version control. Add it to `.gitignore`.

5. **Prepare PDF knowledge base**
   
   Place your PDF files in the `data/pdfs/` directory:
   - `menu.pdf` - Product menu and descriptions
   - `store_policies.pdf` - Store policies and guidelines
   - `refund_faqs.pdf` - Refund and delivery FAQs
   
   *Note: The app will also work with `.txt` files if PDFs are not available.*

6. **Build the vector store (first-time setup)**
   
   The vector store will be built automatically on first run, or you can build it manually:
   ```bash
   python rag.py
   ```

7. **Run the Streamlit app**
   ```bash
   streamlit run streamlit_app.py
   ```

8. **Open your browser**
   
   Streamlit will automatically open `http://localhost:8501` in your browser.

### Usage

1. Select a demo user from the sidebar dropdown (e.g., "User 1 - Neeraj")
2. Type a message in the chat input (e.g., "I'm cold" or "Is the store open?")
3. Watch the AI assistant provide a personalized, context-aware response
4. Continue the conversation naturally

### Troubleshooting

- **"GROQ_API_KEY is not set"**: Make sure your `.env` file exists and contains a valid API key
- **"No such file or directory: data/pdfs"**: Create the `data/pdfs/` folder and add at least one PDF or TXT file
- **Vector store errors**: Delete the `chroma_db/` folder and restart the app to rebuild the index
- **Import errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`

## Project Structure

```
.
├── config.py              # Configuration and environment variables
├── database.py            # SQLite database setup and queries
├── rag.py                 # RAG implementation with vector store
├── masking.py             # PII masking and unmasking logic
├── llm_client.py          # Groq API client wrapper
├── streamlit_app.py       # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not in git)
├── .gitignore            # Git ignore file
├── README.md             # This file
├── data/
│   └── pdfs/             # PDF knowledge base
│       ├── menu.pdf
│       ├── store_policies.pdf
│       └── refund_faqs.pdf
├── chroma_db/            # Vector store (auto-generated)
└── hyper_support.db      # SQLite database (auto-generated)
```

## Future Enhancements

- Add real-time location tracking using GPS coordinates
- Integrate with actual inventory management systems
- Support multi-language conversations
- Add voice input/output capabilities
- Implement conversation memory across sessions
- Add analytics dashboard for support metrics
- Support multiple retail chains and brands

## License

This project is for educational and demonstration purposes.

---

Built with ☕ and 🤖 for the GroundTruth AI Hackathon
