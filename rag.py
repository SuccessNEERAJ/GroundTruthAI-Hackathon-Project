"""
RAG (Retrieval-Augmented Generation) module.
Handles PDF/text document loading, chunking, embedding, and retrieval.
"""

import os
from typing import List
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import PyPDFLoader, TextLoader
    from sentence_transformers import SentenceTransformer
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    IMPORT_ERROR = str(e)

from config import PDF_DIR, VECTOR_STORE_DIR, CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_MODEL, TOP_K_RAG


class RAGSystem:
    """Handles document retrieval using vector similarity search."""
    
    def __init__(self):
        """Initialize the RAG system with embedding model and vector store."""
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError(f"Required dependencies not available: {IMPORT_ERROR}")
        
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        self.client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
        self.collection_name = "retail_knowledge"
        
    def build_vector_store(self) -> None:
        """
        Build the vector store from PDF and text files in the PDF_DIR.
        Loads documents, splits into chunks, creates embeddings, and stores in ChromaDB.
        """
        print(f"Building vector store from documents in {PDF_DIR}...")
        
        # Create PDF directory if it doesn't exist
        os.makedirs(PDF_DIR, exist_ok=True)
        
        # Load documents
        documents = []
        pdf_path = Path(PDF_DIR)
        
        # Check if directory has any files
        files = list(pdf_path.glob("*.pdf")) + list(pdf_path.glob("*.txt"))
        if not files:
            print(f"⚠ Warning: No PDF or TXT files found in {PDF_DIR}")
            print("Creating sample documents...")
            self._create_sample_documents()
            files = list(pdf_path.glob("*.txt"))
        
        for file_path in files:
            try:
                if file_path.suffix == ".pdf":
                    loader = PyPDFLoader(str(file_path))
                else:
                    loader = TextLoader(str(file_path))
                
                docs = loader.load()
                documents.extend(docs)
                print(f"  ✓ Loaded {file_path.name}")
            except Exception as e:
                print(f"  ✗ Error loading {file_path.name}: {e}")
        
        if not documents:
            print("⚠ No documents loaded. Vector store will be empty.")
            return
        
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
        )
        chunks = text_splitter.split_documents(documents)
        print(f"  ✓ Split into {len(chunks)} chunks")
        
        # Create or get collection
        try:
            self.client.delete_collection(self.collection_name)
        except:
            pass
        
        collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Add documents to collection in batches
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [doc.page_content for doc in batch]
            embeddings = self.embedding_model.encode(texts).tolist()
            ids = [f"doc_{i+j}" for j in range(len(batch))]
            metadatas = [{"source": doc.metadata.get("source", "unknown")} for doc in batch]
            
            collection.add(
                embeddings=embeddings,
                documents=texts,
                ids=ids,
                metadatas=metadatas
            )
        
        print(f"✓ Vector store built successfully with {len(chunks)} chunks")
    
    def _create_sample_documents(self) -> None:
        """Create sample text documents for demo purposes."""
        sample_docs = {
            "menu.txt": """
COFFEE SHOP MENU

Hot Drinks:
- Espresso: $3.50
- Cappuccino: $4.50
- Latte: $4.75
- Caramel Latte: $5.25
- Hot Cocoa: $4.00
- Americano: $3.75

Cold Drinks:
- Iced Coffee: $4.25
- Iced Latte: $5.00
- Cold Brew: $4.50
- Frappuccino: $5.75

Sizes: Small, Medium, Large
All drinks can be customized with milk alternatives (oat, almond, soy) for +$0.50
""",
            "store_policies.txt": """
STORE POLICIES

Operating Hours:
- Most locations: 6:00 AM - 9:00 PM
- Some locations may have extended hours
- Holiday hours may vary

Payment:
- We accept cash, credit cards, and mobile payments
- Loyalty members get 5% off all purchases

Seating:
- Free WiFi available for customers
- Seating is first-come, first-served
- Please be considerate of other customers during busy hours

Health & Safety:
- All staff members follow strict hygiene protocols
- Tables and surfaces are sanitized regularly
- Masks are optional but welcomed
""",
            "refund_faqs.txt": """
REFUND AND DELIVERY FAQs

Q: What is your refund policy?
A: If you're not satisfied with your drink, let us know within 10 minutes and we'll remake it or provide a full refund.

Q: Do you offer delivery?
A: Yes! We partner with major delivery services. Delivery is available within 3 miles of each location.

Q: How long does delivery take?
A: Typical delivery time is 20-30 minutes, depending on your location and current demand.

Q: Can I modify my order after placing it?
A: Orders can be modified within 2 minutes of placement. After that, please contact the store directly.

Q: Do you have a loyalty program?
A: Yes! Join our loyalty program to earn points on every purchase. Points can be redeemed for free drinks and discounts.

Q: What if my order is wrong?
A: Please contact us immediately. We'll remake your order or provide a refund. Customer satisfaction is our priority.
"""
        }
        
        for filename, content in sample_docs.items():
            filepath = Path(PDF_DIR) / filename
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  ✓ Created sample document: {filename}")
    
    def retrieve(self, query: str, k: int = TOP_K_RAG) -> List[str]:
        """
        Retrieve the top-k most relevant document chunks for a query.
        
        Args:
            query: The search query (should be masked if contains PII).
            k: Number of results to return.
        
        Returns:
            List[str]: List of relevant document chunks.
        """
        try:
            collection = self.client.get_collection(self.collection_name)
        except Exception as e:
            print(f"⚠ Warning: Could not load vector store: {e}")
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])[0].tolist()
        
        # Search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )
        
        if results and results["documents"]:
            return results["documents"][0]
        
        return []


# Global RAG instance
_rag_system = None


def get_rag_system() -> RAGSystem:
    """Get or create the global RAG system instance."""
    global _rag_system
    if _rag_system is None:
        _rag_system = RAGSystem()
    return _rag_system


def build_vector_store() -> None:
    """Build the vector store from documents."""
    rag = get_rag_system()
    rag.build_vector_store()


def rag_retrieve(query: str, k: int = TOP_K_RAG) -> List[str]:
    """
    Retrieve relevant document chunks for a query.
    
    Args:
        query: The search query.
        k: Number of results to return.
    
    Returns:
        List[str]: List of relevant document chunks.
    """
    rag = get_rag_system()
    return rag.retrieve(query, k)


if __name__ == "__main__":
    # Build vector store when run directly
    print("=== Building Vector Store ===")
    build_vector_store()
    
    # Test retrieval
    print("\n=== Testing Retrieval ===")
    test_queries = [
        "What hot drinks do you have?",
        "What is your refund policy?",
        "What are your store hours?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = rag_retrieve(query, k=2)
        for i, result in enumerate(results, 1):
            print(f"  Result {i}: {result[:100]}...")
