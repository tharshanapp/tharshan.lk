"""
RAG Engine Module for OpenGov AI Assistant
Handles vector database operations and similarity search
"""

import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ChromaDB and LangChain imports
try:
    import chromadb
    from chromadb.config import Settings
    from langchain.embeddings import HuggingFaceEmbeddings
    from langchain.docstore.document import Document
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Please install requirements: pip install -r requirements.txt")
    raise


class RAGEngine:
    """
    RAG Engine for handling vector database operations
    Manages three separate collections: FR, Procurement, ECode
    """
    
    # Category to collection mapping
    CATEGORY_COLLECTIONS = {
        "FR": "fr_db",
        "Procurement": "procurement_db",
        "ECode": "ecode_db"
    }
    
    def __init__(self, persist_directory: str = None):
        """
        Initialize the RAG Engine with ChromaDB
        
        Args:
            persist_directory: Path to persist vector database
        """
        if persist_directory is None:
            persist_directory = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                "vector_db"
            )
        
        self.persist_directory = persist_directory
        
        # Create persist directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
        # Initialize embeddings model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Cache for collection objects
        self._collections = {}
        
        # Ensure all collections exist
        self._initialize_collections()
    
    def _initialize_collections(self):
        """Initialize all category collections if they don't exist"""
        for collection_name in self.CATEGORY_COLLECTIONS.values():
            try:
                self.client.get_collection(name=collection_name)
            except Exception:
                # Collection doesn't exist, create it
                self.client.create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
    
    def get_collection(self, category: str):
        """
        Get or create a collection for the specified category
        
        Args:
            category: Category name (FR, Procurement, ECode)
            
        Returns:
            ChromaDB collection object
        """
        if category not in self.CATEGORY_COLLECTIONS:
            raise ValueError(f"Invalid category: {category}")
        
        collection_name = self.CATEGORY_COLLECTIONS[category]
        
        if collection_name not in self._collections:
            self._collections[collection_name] = self.client.get_collection(
                name=collection_name
            )
        
        return self._collections[collection_name]
    
    def add_documents(
        self, 
        documents: List[Document], 
        category: str
    ) -> Dict[str, Any]:
        """
        Add documents to the vector database
        
        Args:
            documents: List of LangChain Document objects
            category: Category name (FR, Procurement, ECode)
            
        Returns:
            Dictionary with operation results
        """
        collection = self.get_collection(category)
        
        # Extract texts and metadata
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        
        # Generate unique IDs
        ids = [f"{category}_{i}_{doc.metadata.get('source', 'unknown')}" 
               for i, doc in enumerate(documents)]
        
        # Add to collection
        collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        return {
            "status": "success",
            "documents_added": len(documents),
            "category": category
        }
    
    def similarity_search(
        self, 
        query: str, 
        category: str, 
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents in the vector database
        
        Args:
            query: Search query text
            category: Category name (FR, Procurement, ECode)
            k: Number of results to return
            
        Returns:
            List of dictionaries containing document content and metadata
        """
        collection = self.get_collection(category)
        
        # Perform similarity search
        results = collection.query(
            query_texts=[query],
            n_results=k,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                result = {
                    'content': doc,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else 0.0
                }
                formatted_results.append(result)
        
        return formatted_results
    
    def get_collection_stats(self, category: str) -> Dict[str, Any]:
        """
        Get statistics for a collection
        
        Args:
            category: Category name
            
        Returns:
            Dictionary with collection statistics
        """
        collection = self.get_collection(category)
        
        # Get collection info
        collection_info = collection.count()
        
        return {
            "category": category,
            "document_count": collection_info,
            "collection_name": self.CATEGORY_COLLECTIONS[category]
        }
    
    def clear_collection(self, category: str) -> Dict[str, Any]:
        """
        Clear all documents from a collection
        
        Args:
            category: Category name
            
        Returns:
            Dictionary with operation results
        """
        collection_name = self.CATEGORY_COLLECTIONS[category]
        
        # Delete and recreate collection
        try:
            self.client.delete_collection(collection_name)
        except Exception:
            pass
        
        # Recreate empty collection
        self.client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Clear from cache
        if collection_name in self._collections:
            del self._collections[collection_name]
        
        return {
            "status": "success",
            "message": f"Collection {collection_name} cleared"
        }
    
    def list_all_documents(self, category: str) -> List[Dict[str, Any]]:
        """
        List all documents in a collection (for admin purposes)
        
        Args:
            category: Category name
            
        Returns:
            List of document metadata
        """
        collection = self.get_collection(category)
        
        # Get all documents
        results = collection.get(
            include=["metadatas", "documents"]
        )
        
        documents = []
        if results['metadatas']:
            for i, metadata in enumerate(results['metadatas']):
                documents.append({
                    'id': results['ids'][i],
                    'metadata': metadata,
                    'content_preview': results['documents'][i][:200] + "..." 
                                   if results['documents'][i] else ""
                })
        
        return documents


# Singleton instance for the application
_rag_engine_instance = None

def get_rag_engine() -> RAGEngine:
    """
    Get or create the singleton RAG engine instance
    
    Returns:
        RAGEngine instance
    """
    global _rag_engine_instance
    if _rag_engine_instance is None:
        _rag_engine_instance = RAGEngine()
    return _rag_engine_instance