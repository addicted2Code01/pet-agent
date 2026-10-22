import os
from typing import List, Optional
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from src.db.manager import DatabaseManager
from src.db.models import KnowledgeItem

class RAGService:
    def __init__(self, chroma_dir: str = "data/chroma"):
        self.chroma_dir = chroma_dir
        # Use a lightweight, local embedding model
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vectorstore = None
        self.db = DatabaseManager()

    def build_index_from_db(self):
        """Builds the vector index from KnowledgeItem records in the database."""
        print("Building index from Database...")
        
        # Get all knowledge items from DB
        items = self.db.get_all(KnowledgeItem)
        
        if not items:
            print("No knowledge items found in database.")
            return

        documents = []
        for item in items:
            # Create a document for each item
            content = f"Query: {item.query}\nContent: {item.content}"
            # If it has a pet, include that in the metadata/content for better retrieval
            doc = Document(
                page_content=content,
                metadata={
                    "id": item.id,
                    "category": item.category,
                    "pet_id": item.pet_id
                }
            )
            documents.append(doc)

        print(f"Creating index from {len(documents)} database records...")
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.chroma_dir
        )
        print(f"Index built and persisted to {self.chroma_dir}.")

    def load_index(self):
        """Loads an existing Chroma vector store."""
        if self.vectorstore is None:
            if os.path.exists(self.chroma_dir):
                print(f"Loading existing index from {self.chroma_dir}...")
                self.vectorstore = Chroma(
                    persist_directory=self.chroma_dir,
                    embedding_function=self.embeddings
                )
                print("Index loaded.")
            else:
                print("No existing index found.")

    def query(self, query_text: str, k: int = 3) -> List[Document]:
        """Performs a similarity search and returns the top k documents."""
        if not self.vectorstore:
            self.load_index()
            if not self.vectorstore:
                return []

        print(f"Querying RAG for: '{query_text}'")
        results = self.vectorstore.similarity_search(query_text, k=k)
        return results

    def rebuild_index(self):
        """Rebuilds the entire index from scratch."""
        # Delete old index directory to ensure a clean rebuild
        import shutil
        if os.path.exists(self.chroma_dir):
            shutil.rmtree(self.chroma_dir)
        self.build_index_from_db()
