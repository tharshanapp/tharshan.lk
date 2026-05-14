"""
PDF Ingestion Script for OpenGov AI Assistant
Reads PDFs from data folders, chunks them, and stores in vector database
"""

import os
import sys
import logging
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# PDF and LangChain imports
try:
    from pypdf import PdfReader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.docstore.document import Document
except ImportError as e:
    logger.error(f"Missing dependencies: {e}")
    logger.error("Please install requirements: pip install -r requirements.txt")
    sys.exit(1)

# Import RAG engine
from rag_engine import get_rag_engine


class PDFIngester:
    """
    Handles PDF ingestion and processing for the RAG system
    """
    
    # Category folder mapping
    CATEGORY_FOLDERS = {
        "FR": "FR",
        "Procurement": "Procurement",
        "ECode": "ECode"
    }
    
    def __init__(self, data_directory: str = None):
        """
        Initialize the PDF Ingester
        
        Args:
            data_directory: Path to the data directory containing category folders
        """
        if data_directory is None:
            data_directory = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                "data"
            )
        
        self.data_directory = data_directory
        
        # Get chunk settings from environment
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", " ", ""]
        )
        
        logger.info(f"PDF Ingester initialized with chunk_size={self.chunk_size}, "
                   f"chunk_overlap={self.chunk_overlap}")
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from a PDF file with page numbers
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of dictionaries containing text and page info
        """
        pages = []
        
        try:
            reader = PdfReader(pdf_path)
            filename = os.path.basename(pdf_path)
            
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                if text.strip():  # Only add non-empty pages
                    pages.append({
                        'text': text,
                        'page': page_num,
                        'source': filename
                    })
            
            logger.info(f"Extracted {len(pages)} pages from {filename}")
            
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
        
        return pages
    
    def process_pdf(self, pdf_path: str, category: str) -> List[Document]:
        """
        Process a single PDF file into chunked documents
        
        Args:
            pdf_path: Path to the PDF file
            category: Category name (FR, Procurement, ECode)
            
        Returns:
            List of chunked Document objects
        """
        # Extract text from PDF
        pages = self.extract_text_from_pdf(pdf_path)
        
        if not pages:
            logger.warning(f"No text extracted from {pdf_path}")
            return []
        
        # Create documents with metadata
        documents = []
        for page_data in pages:
            doc = Document(
                page_content=page_data['text'],
                metadata={
                    'source': page_data['source'],
                    'page': page_data['page'],
                    'category': category,
                    'ingestion_date': datetime.now().isoformat()
                }
            )
            documents.append(doc)
        
        # Split documents into chunks
        chunks = self.text_splitter.split_documents(documents)
        
        logger.info(f"Created {len(chunks)} chunks from {os.path.basename(pdf_path)}")
        
        return chunks
    
    def ingest_folder(self, category: str) -> Dict[str, Any]:
        """
        Ingest all PDFs from a category folder
        
        Args:
            category: Category name (FR, Procurement, ECode)
            
        Returns:
            Dictionary with ingestion results
        """
        if category not in self.CATEGORY_FOLDERS:
            return {
                'status': 'error',
                'message': f'Invalid category: {category}'
            }
        
        folder_name = self.CATEGORY_FOLDERS[category]
        folder_path = os.path.join(self.data_directory, folder_name)
        
        if not os.path.exists(folder_path):
            logger.warning(f"Category folder does not exist: {folder_path}")
            os.makedirs(folder_path, exist_ok=True)
            return {
                'status': 'warning',
                'message': f'Created empty folder: {folder_path}',
                'documents_processed': 0,
                'chunks_created': 0
            }
        
        # Find all PDF files in folder
        pdf_files = [f for f in os.listdir(folder_path) 
                    if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            logger.info(f"No PDF files found in {folder_path}")
            return {
                'status': 'info',
                'message': f'No PDF files found in {folder_path}',
                'documents_processed': 0,
                'chunks_created': 0
            }
        
        # Process each PDF
        all_chunks = []
        processed_files = []
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(folder_path, pdf_file)
            logger.info(f"Processing: {pdf_file}")
            
            try:
                chunks = self.process_pdf(pdf_path, category)
                all_chunks.extend(chunks)
                processed_files.append(pdf_file)
                
            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {e}")
        
        # Add to vector database
        if all_chunks:
            rag_engine = get_rag_engine()
            result = rag_engine.add_documents(all_chunks, category)
            
            return {
                'status': 'success',
                'message': f'Processed {len(processed_files)} PDFs',
                'documents_processed': len(processed_files),
                'chunks_created': len(all_chunks),
                'files': processed_files,
                'rag_result': result
            }
        else:
            return {
                'status': 'warning',
                'message': 'No content could be processed',
                'documents_processed': 0,
                'chunks_created': 0
            }
    
    def ingest_all_categories(self) -> Dict[str, Any]:
        """
        Ingest PDFs from all category folders
        
        Returns:
            Dictionary with combined ingestion results
        """
        results = {}
        total_docs = 0
        total_chunks = 0
        
        for category in self.CATEGORY_FOLDERS.keys():
            logger.info(f"Ingesting category: {category}")
            result = self.ingest_folder(category)
            results[category] = result
            
            total_docs += result.get('documents_processed', 0)
            total_chunks += result.get('chunks_created', 0)
        
        return {
            'status': 'completed',
            'categories': results,
            'total_documents_processed': total_docs,
            'total_chunks_created': total_chunks
        }
    
    def ingest_single_file(self, file_path: str, category: str) -> Dict[str, Any]:
        """
        Ingest a single PDF file
        
        Args:
            file_path: Path to the PDF file
            category: Category name (FR, Procurement, ECode)
            
        Returns:
            Dictionary with ingestion results
        """
        if not os.path.exists(file_path):
            return {
                'status': 'error',
                'message': f'File not found: {file_path}'
            }
        
        if category not in self.CATEGORY_FOLDERS:
            return {
                'status': 'error',
                'message': f'Invalid category: {category}'
            }
        
        # Process the PDF
        chunks = self.process_pdf(file_path, category)
        
        if not chunks:
            return {
                'status': 'error',
                'message': 'No content could be extracted from PDF'
            }
        
        # Add to vector database
        rag_engine = get_rag_engine()
        result = rag_engine.add_documents(chunks, category)
        
        return {
            'status': 'success',
            'message': f'Processed {os.path.basename(file_path)}',
            'documents_processed': 1,
            'chunks_created': len(chunks),
            'file': os.path.basename(file_path),
            'rag_result': result
        }


def main():
    """
    Main function for command-line usage
    """
    print("=" * 60)
    print("OpenGov AI Assistant - PDF Ingestion Script")
    print("=" * 60)
    print()
    
    ingester = PDFIngester()
    
    # Check if specific category is provided as argument
    if len(sys.argv) > 1:
        category = sys.argv[1]
        print(f"Ingesting category: {category}")
        result = ingester.ingest_folder(category)
    else:
        print("Ingesting all categories...")
        result = ingester.ingest_all_categories()
    
    print()
    print("Ingestion Results:")
    print("-" * 40)
    print(f"Status: {result['status']}")
    print(f"Documents Processed: {result.get('total_documents_processed', result.get('documents_processed', 0))}")
    print(f"Chunks Created: {result.get('total_chunks_created', result.get('chunks_created', 0))}")
    
    if 'categories' in result:
        print()
        print("Category Details:")
        for category, cat_result in result['categories'].items():
            print(f"  {category}: {cat_result.get('documents_processed', 0)} docs, "
                  f"{cat_result.get('chunks_created', 0)} chunks")
    
    print()
    print("Ingestion completed!")


if __name__ == "__main__":
    main()