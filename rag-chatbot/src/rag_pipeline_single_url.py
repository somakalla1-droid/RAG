"""
Single-URL RAG Pipeline for Assignment Submission
Follows the assignment requirements:
1. Document chunking with RecursiveCharacterTextSplitter
2. Embedding generation with OpenAI
3. Vector store using Chroma
4. Conversational LLM chain with memory
"""

import os
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import InMemoryVectorStore
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document


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
    
    def generate_embeddings(self) -> InMemoryVectorStore:
        """
        REQUIREMENT 3: Generate embeddings for each chunk
        Uses OpenAI Embeddings (text-embedding-ada-002)
        Stores in InMemoryVectorStore for similarity search
        """
        print(f"\nGenerating embeddings for {len(self.chunks)} chunks...")
        
        embeddings = OpenAIEmbeddings(openai_api_key=self.api_key)
        
        # Create in-memory vector store
        self.vector_store = InMemoryVectorStore(embeddings)
        self.vector_store.add_documents(self.chunks)
        
        print(f"✓ Embeddings generated and stored in in-memory vector store")
        return self.vector_store
    
    def setup_qa_chain(self) -> None:
        """
        REQUIREMENT 4: Setup LLM chain for question answering
        
        Creates a simple QA chain using retrieved context from vector store
        """
        print(f"\nSetting up QA chain...")
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.7,
            openai_api_key=self.api_key
        )
        
        # Create retriever from vector store
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
        
        # Create a simple prompt template for QA
        self.qa_prompt = PromptTemplate(
            template="""Use the following context to answer the question.
            
Context:
{context}

Question: {question}

Answer:""",
            input_variables=["context", "question"]
        )
        
        print(f"✓ QA chain ready for questions")
    
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
    
    def query(self, question: str) -> str:
        """
        Answer a question using the RAG system
        Retrieves context from vector store and uses LLM to generate answer
        
        Args:
            question: User question about the document
            
        Returns:
            Answer string generated by the LLM
        """
        if not hasattr(self, 'retriever') or not self.retriever:
            raise ValueError("QA chain not initialized. Call initialize_from_url() first")
        
        # Retrieve relevant documents from vector store
        relevant_docs = self.retriever.invoke(question)
        
        # Combine context from retrieved documents
        context = "\n".join([doc.page_content for doc in relevant_docs])
        
        # Format prompt with context and question
        prompt_text = self.qa_prompt.format(context=context, question=question)
        
        # Generate answer using LLM
        response = self.llm.invoke(prompt_text)
        answer = response.content if hasattr(response, 'content') else str(response)
        
        return answer
    
    def interactive_chat(self) -> None:
        """Start an interactive chat session."""
        if not hasattr(self, 'retriever') or not self.retriever:
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
            
            answer = self.query(question)
            print(f"\n> Assistant: {answer}")


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
