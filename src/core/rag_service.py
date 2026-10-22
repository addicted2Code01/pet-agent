import os
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

class RAGService:
    def __init__(self, knowledge_dir: str = "knowledge", chroma_dir: str = "data/chroma"):
        self.knowledge_dir = knowledge_dir
        self.chroma_dir = chroma_dir
        # Use a lightweight, local embedding model
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vectorstore = None

    def build_index(self):
        """Loads documents, splits them, and creates a Chroma vector store."""
        print(f"Building index from {self.knowledge_dir}...")
        
        # Load all markdown/text files
        loader = DirectoryLoader(self.knowledge_dir, glob="**/*.md", loader_cls=TextLoader)
        documents = loader.load()
        
        if not documents:
            print("No documents found in knowledge directory.")
            return

        # Split documents into manageable chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        splits = text_splitter.split_documents(documents)
        print(f"Created {len(splits)} chunks from {len(documents)} documents.")

        # Create and persist the vector store
        self.vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory=self.chroma_dir
        )
        print(f"Index built and persisted to {self.chroma_dir}.")

    def load_index(self):
        """Loads an existing Chroma vector store."""
        if os.path.exists(self.chroma_dir):
            print(f"Loading existing index from {self.chroma_dir}...")
            self.vectorstore = Chroma(
                persist_directory=self.chroma_dir,
                embedding_function=self.embeddings
            )
            print("Index loaded.")
        else:
            print("No existing index found. Please run build_index() first.")

    def query(self, query_text: str, k: int = 3) -> List[Document]:
        """Performs a similarity search and returns the top k documents."""
        if not self.vectorstore:
            self.load_index()
            if not self.vectorstore:
                return []

        print(f"Querying RAG for: '{query_text}'")
        results = self.vectorstore.similarity_search(query_text, k=k)
        return results

if __name__ == "__main__":
    # Quick test
    rag = RAGService()
    rag.build_index()
    
    test_queries = [
        "Where is the heartworm pill?",
        "Where is the leash?",
        "How much Apoquel should I give?"
    ]
    
    for q in test_queries:
        print(f"\n--- Query: {q} ---")
        docs = rag.query(q)
        for i, doc in enumerate(docs):
            print(f"Result {i+1}: {doc.page_content[:200]}...")
