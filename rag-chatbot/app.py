"""
Gradio UI for Trading Platform RAG Chatbot
"""

import gradio as gr
import os
import sys
from src.rag_pipeline import TradingPlatformRAG


def create_chatbot_interface():
    """Create Gradio chat interface."""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    # Initialize RAG in background
    rag = TradingPlatformRAG(openai_api_key=api_key)
    docs_urls = [
        "https://raw.githubusercontent.com/somakalla1-droid/RAG/main/docs/trading-platform-doc.md",
        "https://raw.githubusercontent.com/somakalla1-droid/RAG/main/docs/order-validate-doc.md",
        "https://raw.githubusercontent.com/somakalla1-droid/RAG/main/docs/order-entry-doc.md",
        "https://raw.githubusercontent.com/somakalla1-droid/RAG/main/docs/order-router-doc.md",
        "https://raw.githubusercontent.com/somakalla1-droid/RAG/main/docs/fix-service-doc.md",
        "https://raw.githubusercontent.com/somakalla1-droid/RAG/main/docs/service-registry-doc.md",
    ]
    print("Initializing RAG pipeline with all service documentation...")
    rag.initialize_from_url(docs_urls)
    print("✅ RAG pipeline initialized!")
    
    def chat(message, history):
        """Chat function for Gradio."""
        response = rag.query(message)
        return response
    
    # Create Gradio interface
    demo = gr.ChatInterface(
        chat,
        examples=[
            "What are the main services in the trading platform?",
            "How does order-entry service work?",
            "What failure scenarios are documented?",
            "What are the runbook quick checks?",
            "Explain the Safeguard usage for SQL credentials."
        ],
        title="Trading Platform Documentation Chatbot",
        description="Ask questions about the trading platform architecture, services, and operations.",
        theme=gr.themes.Soft(),
    )
    
    return demo


if __name__ == "__main__":
    demo = create_chatbot_interface()
    demo.launch(share=False, server_name="0.0.0.0", server_port=7860)
