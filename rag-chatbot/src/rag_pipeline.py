"""
RAG Pipeline for Trading Platform Documentation Chatbot
Uses LangChain + OpenAI + Chroma DB
"""

import requests
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
import os


class TradingPlatformRAG:
    """RAG pipeline for Trading Platform documentation."""
    
    def __init__(self, openai_api_key: str, persist_directory: str = "./chroma_db"):
        """
        Initialize RAG pipeline.
        
        Args:
            openai_api_key: OpenAI API key
            persist_directory: Path to store Chroma DB
        """
        self.openai_api_key = openai_api_key
        self.persist_directory = persist_directory
        self.vector_store = None
        self.llm = None
        self.chain = None
        self.memory = None
        
    def load_and_chunk_document(self, url: str, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Load document from URL and chunk it.
        
        Args:
            url: URL of the document to load
            chunk_size: Size of each chunk
            chunk_overlap: Overlap between chunks
            
        Returns:
            List of chunked documents
        """
        print(f"📥 Loading document from {url}...")
        loader = WebBaseLoader(url)
        documents = loader.load()
        
        print(f"📊 Chunking document (size={chunk_size}, overlap={chunk_overlap})...")
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = splitter.split_documents(documents)
        print(f"✅ Created {len(chunks)} chunks")
        
        return chunks
    
    def build_vector_store(self, chunks):
        """
        Build vector store with Chroma DB.
        
        Args:
            chunks: List of document chunks
        """
        print(f"🔤 Creating embeddings with OpenAI...")
        embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
        
        print(f"💾 Building Chroma vector store...")
        self.vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=self.persist_directory,
            collection_name="trading_platform"
        )
        print(f"✅ Vector store created at {self.persist_directory}")
    
    def setup_conversation_chain(self):
        """Setup conversational RAG chain with memory."""
        print(f"🤖 Setting up LLM and conversational chain...")
        
        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            openai_api_key=self.openai_api_key,
            temperature=0.7,
            max_tokens=500
        )
        
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
        
        self.chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=self.memory,
            verbose=True
        )
        print(f"✅ Conversational chain ready!")
    
    def query(self, question: str) -> str:
        """
        Query the RAG chain.
        
        Args:
            question: User question
            
        Returns:
            Answer from the RAG chain
        """
        if not self.chain:
            raise ValueError("Chain not initialized. Call setup_conversation_chain() first.")
        
        response = self.chain.invoke({"question": question})
        return response["answer"]
    
    def initialize_from_url(self, url: str):
        """
        Full initialization pipeline: load, chunk, embed, store.
        
        Args:
            url: URL of the document
        """
        print("🚀 Starting RAG initialization pipeline...")
        chunks = self.load_and_chunk_document(url)
        self.build_vector_store(chunks)
        self.setup_conversation_chain()
        print("✅ RAG pipeline ready for queries!")


def main():
    """Main function for local testing."""
    import sys
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set. Set it as an environment variable.")
        sys.exit(1)
    
    # Initialize RAG
    rag = TradingPlatformRAG(openai_api_key=api_key)
    
    doc_url = "https://raw.githubusercontent.com/somakalla1-droid/RAG/main/docs/trading-platform-doc.md"
    rag.initialize_from_url(doc_url)
    
    # Multi-turn conversation loop
    print("\n💬 Trading Platform Chatbot Ready! Type 'quit' to exit.\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "quit":
            print("Goodbye!")
            break
        
        if not user_input:
            continue
        
        response = rag.query(user_input)
        print(f"\nChatbot: {response}\n")


if __name__ == "__main__":
    main()
