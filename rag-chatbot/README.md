# RAG Trading Platform Documentation Chatbot

A conversational RAG (Retrieval-Augmented Generation) chatbot that answers questions about the trading platform documentation using **LangChain**, **OpenAI**, and **Chroma DB**.

## Features

✅ **Document Ingestion** — Loads markdown docs from GitHub URL  
✅ **Semantic Chunking** — Splits content intelligently for better retrieval  
✅ **Vector Embeddings** — OpenAI embeddings for semantic search  
✅ **Chroma DB** — Local vector database for fast retrieval  
✅ **Conversational RAG** — Multi-turn conversation with context memory  
✅ **Gradio UI** — User-friendly web interface  
✅ **Google Colab** — Run in cloud without setup  

---

## Quick Start

### Prerequisites
- Python 3.9+
- OpenAI API key (get one at https://platform.openai.com/api-keys)

### Option 1: Local Setup

```bash
# 1. Clone and navigate
cd RAG/rag-chatbot

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

# 5. Run CLI chatbot (multi-turn conversation)
python -m src.rag_pipeline

# OR run Gradio web UI
python app.py
# Open http://localhost:7860 in browser
```

### Option 2: Google Colab (Recommended for Assignment)

1. Open the notebook in Google Colab: [RAG_Trading_Platform_Chatbot.ipynb](./RAG_Trading_Platform_Chatbot.ipynb)
2. Add your OpenAI API key when prompted
3. Run all cells
4. Chat with the Gradio interface

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│  GitHub Raw Doc URL (trading-platform-doc.md)   │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
         ┌──────────────┐
         │ WebLoader    │
         └──────┬───────┘
                │
                ▼
    ┌─────────────────────────┐
    │ RecursiveCharTextSplit  │
    │ (chunking strategy)     │
    └────────────┬────────────┘
                 │
                 ▼
       ┌──────────────────────┐
       │ OpenAI Embeddings    │
       │ (semantic vectors)   │
       └──────────┬───────────┘
                  │
                  ▼
        ┌────────────────────┐
        │ Chroma Vector DB   │
        │ (local persistence)│
        └────────────┬───────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
    ┌─────────────┐      ┌──────────────┐
    │  Retriever  │      │ Conversation │
    │  (top-k)    │      │   Memory     │
    └──────┬──────┘      └──────┬───────┘
           │                    │
           └──────────┬─────────┘
                      ▼
            ┌────────────────────┐
            │ ChatOpenAI (LLM)   │
            └────────────┬───────┘
                         │
                         ▼
               ┌──────────────────────┐
               │ Conversational Chain │
               │ (with RAG context)   │
               └────────────┬─────────┘
                            │
                    ┌───────┴────────┐
                    ▼                ▼
              ┌─────────┐      ┌──────────┐
              │ Gradio  │      │ CLI Chat │
              │   UI    │      │  Mode    │
              └─────────┘      └──────────┘
```

---

## Project Structure

```
rag-chatbot/
├── src/
│   ├── __init__.py
│   └── rag_pipeline.py        # Core RAG logic
├── app.py                      # Gradio web UI
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── RAG_Trading_Platform_Chatbot.ipynb  # Colab notebook
```

---

## Usage Examples

### Via CLI
```bash
export OPENAI_API_KEY="sk-..."
python -m src.rag_pipeline

You: What are the main services?
Chatbot: The trading platform has five key services: order-validate, order-entry, order-router, fix-service, and service-registry...

You: How does authentication work?
Chatbot: Services use multiple authentication mechanisms...
```

### Via Gradio UI
```bash
python app.py
# Navigate to http://localhost:7860
```

### Via Google Colab
- Open the `.ipynb` notebook
- Run cells in order
- Use the Gradio interface in cell output

---

## Configuration

### Environment Variables
```bash
OPENAI_API_KEY="your-key"     # Required
CHROMA_DB_PATH="./chroma_db"  # Optional (default: ./chroma_db)
```

### Customization (in `src/rag_pipeline.py`)
```python
# Chunk size and overlap
chunk_size = 1000
chunk_overlap = 200

# LLM temperature (0-1, higher = more creative)
temperature = 0.7

# Retrieval k (number of top chunks to use as context)
search_kwargs = {"k": 3}
```

---

## Features Deep Dive

### 1. Document Loading
- **WebBaseLoader** fetches markdown from GitHub URL
- Preserves formatting and structure

### 2. Semantic Chunking
- **RecursiveCharacterTextSplitter** intelligently splits on logical boundaries
- Configurable chunk size and overlap for context preservation

### 3. Vector Embeddings
- **OpenAI Embeddings API** (text-embedding-ada-002)
- Semantic understanding of content

### 4. Vector Storage
- **Chroma DB** local vector database
- Persists to disk for fast reloading
- No external service required

### 5. Retrieval-Augmented Generation
- **Conversational Retriever** finds relevant chunks
- Provides context to LLM
- LLM answers based only on retrieved chunks

### 6. Conversation Memory
- **ConversationBufferMemory** keeps chat history
- Enables multi-turn follow-up questions
- Context aware responses

---

## Testing & Validation

### Test Questions
```
Q: What are the main services in the trading platform?
Q: How does order-entry service consume messages?
Q: What certification scenarios are mentioned?
Q: What are the runbook quick checks for Safeguard?
Q: Explain the MQ cert expiry failure scenario.
```

Expected: Answers grounded in the documentation, not hallucinations.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `OPENAI_API_KEY not set` | `export OPENAI_API_KEY="sk-..."` |
| `ModuleNotFoundError: No module named 'langchain'` | `pip install -r requirements.txt` |
| `Connection error` | Check internet; verify OpenAI API key |
| `Empty responses` | Reduce `chunk_size`; increase `k` in retriever |

---

## Performance Notes

- **First run**: ~30-60s (loading, chunking, embedding, vector store creation)
- **Subsequent runs**: ~2-5s (loading from Chroma disk)
- **Query time**: ~2-3s (retrieval + LLM inference)

---

## References

- [LangChain Docs](https://python.langchain.com)
- [OpenAI API](https://platform.openai.com/docs)
- [Chroma DB](https://www.trychroma.com)
- [Gradio Docs](https://gradio.app)

---

## License

This project is part of the RAG assignment. Use and modify freely for educational purposes.

---

## Author

Built for Trading Platform Documentation RAG Assignment
