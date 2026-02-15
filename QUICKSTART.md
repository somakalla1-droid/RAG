# Quick Start Guide - Single-URL RAG Assignment

## 🚀 Get Started in 3 Minutes

### Option 1: Google Colab (No Setup Required) ⭐ RECOMMENDED

1. **Open the notebook**:
   - Navigate to: `RAG_Single_URL_Assignment.ipynb`
   - Click "Open in Colab" (or upload to Colab)

2. **Run the cells**:
   ```
   Cell 1: Install dependencies (!pip install ...)
   Cell 2: Import libraries
   Cell 3: Enter your OpenAI API key
   Cell 4-7: Run through requirements 1-4
   Cell 8-9: Test with sample queries
   Cell 10: Launch Gradio UI
   ```

3. **Ask questions**:
   - Use the Gradio chat interface
   - Share the public link with others

---

### Option 2: Local Python CLI

**Prerequisites**:
```bash
python3 --version  # Need Python 3.9+
export OPENAI_API_KEY="sk-..."
```

**Installation**:
```bash
cd /Users/somakalla/Desktop/IK/Assignment-1/RAG/rag-chatbot
pip install -r requirements.txt
```

**Run the chatbot**:
```bash
python -m src.rag_pipeline_single_url
```

**Example interaction**:
```
> You: What is this document about?
> Assistant: The document discusses...

> You: Tell me more about security
> Assistant: Regarding the security aspects mentioned...

> You: exit
```

---

### Option 3: Local Web UI with Gradio

**Run the web app**:
```bash
cd /Users/somakalla/Desktop/IK/Assignment-1/RAG/rag-chatbot
export OPENAI_API_KEY="sk-..."
python app_single_url.py
```

**Access the UI**:
- Open browser to `http://localhost:7860`
- Chat with the bot
- No public link in local mode

---

## 📋 What You Get

### ✅ Requirement 1: Document Chunking
```
Input: Single webpage URL
↓
RecursiveCharacterTextSplitter (1000 chars, 200 overlap)
↓
Output: 6-120+ semantic chunks
```

### ✅ Requirement 2: Embeddings
```
Input: Text chunks
↓
OpenAI (text-embedding-ada-002)
↓
Output: Semantic vectors for each chunk
```

### ✅ Requirement 3: Vector Store
```
Input: Embedding vectors
↓
Chroma DB (local, persistent)
↓
Output: Indexed, searchable vector database
```

### ✅ Requirement 4: LLM Chain
```
User Question
   ↓
Query embedding
   ↓
Semantic search (top 3 chunks)
   ↓
ChatOpenAI (gpt-3.5-turbo)
   ↓
Answer with context
```

### ✅ Extra: Conversational Memory
```
Your first question → System remembers context
Your follow-up question → System uses previous context
→ Proper multi-turn conversation!
```

---

## 🔑 Getting Your OpenAI API Key

1. Visit: https://platform.openai.com/api-keys
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key
5. In Colab: Enter when prompted
6. In CLI: `export OPENAI_API_KEY="sk-..."`

---

## 📝 Sample Queries to Try

```
"What is the main topic?"
"Can you summarize this?"
"What are the key concepts?"
"Tell me more about [specific topic]"
"How does [feature] work?"
```

---

## 🎯 Change the URL

To use a different webpage:

**Colab**:
```python
# In Cell 4 (Step 4), change:
url = "https://your-website.com/page"
```

**CLI**:
```python
# Edit src/rag_pipeline_single_url.py, change line ~270:
url = "https://your-website.com/page"
```

---

## 🐛 Troubleshooting

### "OpenAI API key not found"
→ Make sure you set the environment variable or entered it in Colab

### "Module not found: chromadb"
→ Run: `pip install chromadb`

### "Timeout loading URL"
→ Make sure the URL is accessible (try in browser first)

### "Connection refused" (Gradio)
→ Another app is using port 7860. Restart or kill the process

---

## 📊 What's Happening Behind the Scenes

```
┌─────────────────────────────────────────────┐
│         Your Question: "What is X?"         │
└────────────────┬────────────────────────────┘
                 ↓
    ┌────────────────────────────┐
    │  1. Generate embedding     │
    │     of your question       │
    └────────────┬───────────────┘
                 ↓
    ┌────────────────────────────┐
    │  2. Search vector store    │
    │     for similar content    │
    │     (top 3 chunks)         │
    └────────────┬───────────────┘
                 ↓
    ┌────────────────────────────┐
    │  3. Create context prompt: │
    │     "Here's what I found:" │
    │     [Chunk 1]              │
    │     [Chunk 2]              │
    │     [Chunk 3]              │
    │     "Now answer: What is X?"
    └────────────┬───────────────┘
                 ↓
    ┌────────────────────────────┐
    │  4. Send to ChatOpenAI     │
    │     (gpt-3.5-turbo)        │
    └────────────┬───────────────┘
                 ↓
┌─────────────────────────────────────────────┐
│    Your Answer: "[Context-grounded      │
│     response based on document]"            │
└─────────────────────────────────────────────┘
```

---

## 📈 Expected Performance

| Metric | Expected |
|--------|----------|
| Loading webpage | 2-5 seconds |
| Chunking document | <1 second |
| Generating embeddings | 5-10 seconds |
| Setting up LLM chain | 2-3 seconds |
| Answering a question | 2-5 seconds |

**Total initialization**: ~15-25 seconds (first time only)  
**Per question**: ~3 seconds

---

## 💡 Pro Tips

1. **Longer documents**: May take longer to chunk and embed, but answer quality improves
2. **Better questions**: More specific questions → better answers
3. **Cost optimization**: Embeddings are cheaper than multiple LLM calls
4. **Reusability**: Vector store persists, no need to re-embed on restart

---

## 📚 Full Documentation

- **Detailed requirements**: See `ASSIGNMENT_SUBMISSION.md`
- **Test results**: See `TEST_REPORT.md`
- **API reference**: See docstrings in `src/rag_pipeline_single_url.py`

---

## ✅ Ready to Submit?

Check this list:
- [ ] Opened Colab notebook
- [ ] Set OpenAI API key
- [ ] Ran through all cells
- [ ] Tested with sample queries
- [ ] Launched Gradio UI
- [ ] All working! 🎉

---

**Questions?** Check the troubleshooting section above or refer to detailed documentation.

**Happy coding!** 🚀
