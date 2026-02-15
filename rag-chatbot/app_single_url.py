"""
Single-URL RAG Chatbot UI using Gradio
For assignment submission - loads from a single webpage URL
"""

import os
import gradio as gr
from src.rag_pipeline_single_url import SingleURLRAG


def create_chatbot_interface(url: str):
    """
    Create a Gradio ChatInterface for single-URL RAG system
    
    Args:
        url: Single webpage URL to load for the chatbot
    """
    
    # Initialize RAG system
    api_key = os.getenv("OPENAI_API_KEY")
    rag = SingleURLRAG(openai_api_key=api_key)
    
    print("Initializing RAG system from URL...")
    rag.initialize_from_url(url)
    
    def chat_function(message: str, history: list) -> str:
        """Process user message and return answer."""
        try:
            result = rag.query(message)
            return result
        except Exception as e:
            return f"Error: {str(e)}"
    
    # Create Gradio ChatInterface
    interface = gr.ChatInterface(
        chat_function,
        examples=[
            "What is the main topic of this document?",
            "Can you summarize the key points?",
            "What are the main concepts discussed?",
        ],
        title="Single-URL RAG Chatbot",
        description="Ask questions about the webpage content. The system will retrieve relevant information and provide conversational answers.",
    )
    
    return interface


def main():
    """
    Main function to launch the Gradio app
    
    Usage:
        1. Set your OpenAI API key: export OPENAI_API_KEY="your-key"
        2. Run: python app_single_url.py
        3. Visit the URL shown in terminal
    """
    
    # Change this URL to your target webpage
    url = "https://raw.githubusercontent.com/somakalla1-droid/RAG/main/docs/trading-platform-doc.md"
    
    print("=" * 60)
    print("SINGLE-URL RAG CHATBOT - ASSIGNMENT SUBMISSION")
    print("=" * 60)
    print(f"Loading from: {url}\n")
    
    interface = create_chatbot_interface(url)
    
    # Launch with Gradio
    interface.launch(share=False)


if __name__ == "__main__":
    main()
