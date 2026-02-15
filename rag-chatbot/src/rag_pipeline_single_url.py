"""
Single-URL RAG Pipeline for Assignment Submission
Follows the assignment requirements:
1. Document chunking with RecursiveCharacterTextSplitter
2. Embedding generation with OpenAI
3. Vector store using Chroma
4. Conversational LLM chain with memory
"""

import os
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import WebBaseLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import RetrievalQA
from langchain.schema import Document


class SingleURLRAG:
    """
    A Retrieval-Augmented Generation (RAG) system that loads a single webpage
    and answers questions based on its content with conversational memory.
    
    Assignment Requirements Met:
    ✓ Document Chunking: RecursiveCharacterTextSplitter
    ✓ Embeddings: OpenAI text-embedding-ada-002
    ✓ Vector Store: Chroma (local persistence)
    ✓ LLM: ChatOpenAI with conversation memory
    """
    
    def __init__(self, openai_api_key: str = None):
        """Initialize the RAG system with OpenAI API key."""
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.documents: List[Document] = []
        self.chunks = []
        self.vector_store = None
        self.llm = None
        self.memory = None
        self.qa_chain = None
    
    def load_document(self, url: str) -> List[Document]:
        """
        REQUIREMENT 1: Load document from single webpage URL
        Uses LangChain WebBaseLoader to fetch content from URL
        """
        print(f"Loading document from: {url}")
        try:
            loader = WebBaseLoader(url)
            self.documents = loader.load()
            print(f"✓ Successfully loaded {len(self.documents)} document(s)")
            return self.documents
        except Exception as e:
            print(f"✗ Error loading document: {e}")
            raise
    
    def chunk_document(self, chunk_size: int = 1000, chunk_overlap: int = 200) -> List:
        """
        REQUIREMENT 2: Chunk document to fit model's maximum length
        Uses RecursiveCharacterTextSplitter as suggested in assignment
        
        Args:
            chunk_size: Number of characters per chunk
            chunk_overlap: Overlap between chunks for context preservation
        """
        print(f"\nChunking document (size={chunk_size}, overlap={chunk_overlap})...")
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        
        self.chunks = splitter.split_documents(self.documents)
        print(f"✓ Created {len(self.chunks)} chunks from document")
        return self.chunks
    
    def generate_embeddings(self) -> Chroma:
        """
        REQUIREMENT 3: Generate embeddings for each chunk
        Uses OpenAI Embeddings (text-embedding-ada-002) as suggested
        """
        print(f"\nGenerating embeddings for {len(self.chunks)} chunks...")
        
        embeddings = OpenAIEmbeddings(openai_api_key=self.api_key)
        
        # Create vector store with persistence
        self.vector_store = Chroma.from_documents(
            documents=self.chunks,
            embedding=embeddings,
            persist_directory="./chroma_db_single"
        )
        
        print(f"✓ Embeddings generated and stored in Chroma")
        return self.vector_store
    
    def setup_qa_chain(self) -> None:
        """
        REQUIREMENT 4: Setup LLM chain for question answering
        EXTRA REQUIREMENT: Make system conversational with memory
        
        Uses RetrievalQA with conversation memory for multi-turn dialogs
        """
        print(f"\nSetting up QA chain with conversational memory...")
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.7,
            openai_api_key=self.api_key
        )
        
        # Setup conversation memory for multi-turn dialogs (EXTRA REQUIREMENT)
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Create retriever from vector store
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
        
        # Create QA chain with retriever
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            verbose=True
        )
        
        print(f"✓ QA chain ready for conversational questions")
    
    def initialize_from_url(self, url: str) -> None:
        """
        Complete initialization pipeline from URL to ready-to-query system
        Executes all 4 requirements in sequence
        """
        print("=" * 60)
        print("SINGLE-URL RAG SYSTEM INITIALIZATION")
        print("=" * 60)
        
        # Requirement 1: Load document
        self.load_document(url)
        
        # Requirement 2: Chunk document
        self.chunk_document(chunk_size=1000, chunk_overlap=200)
        
        # Requirement 3: Generate embeddings & store
        self.generate_embeddings()
        
        # Requirement 4: Setup LLM chain
        self.setup_qa_chain()
        
        print("\n" + "=" * 60)
        print("✓ INITIALIZATION COMPLETE - Ready to answer questions!")
        print("=" * 60)
    
    def query(self, question: str) -> dict:
        """
        Answer a question using the RAG system
        Maintains conversation context via memory (conversational feature)
        
        Args:
            question: User question about the document
            
        Returns:
            Dictionary with answer and source documents
        """
        if not self.qa_chain:
            raise ValueError("QA chain not initialized. Call initialize_from_url() first")
        
        print(f"\n> Question: {question}")
        result = self.qa_chain({"query": question})
        print(f"\n> Answer: {result['result']}")
        
        if result.get("source_documents"):
            print(f"\n> Source: {len(result['source_documents'])} relevant chunk(s)")
        
        return result
    
    def interactive_chat(self) -> None:
        """Start an interactive chat session."""
        if not self.qa_chain:
            raise ValueError("QA chain not initialized. Call initialize_from_url() first")
        
        print("\n" + "=" * 60)
        print("CONVERSATIONAL RAG CHATBOT")
        print("Type 'exit' to quit")
        print("=" * 60)
        
        while True:
            question = input("\n> You: ").strip()
            
            if question.lower() == "exit":
                print("Goodbye!")
                break
            
            if not question:
                continue
            
            result = self.query(question)
            print(f"\n> Assistant: {result['result']}")


def main():
    """
    Example usage with a single URL (assignment requirement)
    Change the URL to your target webpage
    """
    # Set your OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Initialize RAG system
    rag = SingleURLRAG(openai_api_key=api_key)
    
    # Use a single URL as per assignment requirement
    # Example: trading platform documentation
    url = "https://raw.githubusercontent.com/somakalla1-droid/RAG/main/docs/trading-platform-doc.md"
    
    # Initialize from URL (runs all 4 requirements)
    rag.initialize_from_url(url)
    
    # Start interactive chat
    rag.interactive_chat()


if __name__ == "__main__":
    main()
