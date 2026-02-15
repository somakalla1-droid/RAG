# 🔧 Local Testing Guide - Before Submission

**Last Updated:** February 14, 2026  
**Status:** Step-by-step instructions for testing locally

---

## ⚡ Quick Start (5 minutes)

### Step 1: Set Your API Key
```bash
export OPENAI_API_KEY='sk-proj-YOUR_KEY_HERE'
```

### Step 2: Run Simple Test
```bash
cd /Users/somakalla/Desktop/IK/Assignment-1/RAG
python3 test_locally.py
```

### Step 3: Expected Output
```
✅ SingleURLRAG imported successfully
✅ API key found
✅ RAG Pipeline working
🎉 ALL TESTS PASSED
```

---

## 📋 Testing Options

### Option 1: Simple Test Script (⭐ RECOMMENDED)
```bash
python3 test_locally.py
```
- Takes ~30-60 seconds
- Tests: imports, API key, full pipeline
- Best for: Quick verification before submission

### Option 2: Interactive Chat (Local)
```bash
export OPENAI_API_KEY='your-key'
python3 rag-chatbot/app_single_url.py
```
- Launches Gradio interface on http://127.0.0.1:7860
- Best for: Manual testing and exploration

### Option 3: Python Script (Custom)
```python
import os
os.environ['OPENAI_API_KEY'] = 'your-key'

from rag_chatbot.src.rag_pipeline_single_url import SingleURLRAG

rag = SingleURLRAG(openai_api_key='your-key')
rag.initialize_from_url('https://en.wikipedia.org/wiki/Artificial_intelligence')
answer = rag.query('What is AI?')
print(answer)
```

### Option 4: Google Colab (✅ NO LOCAL SETUP NEEDED)
1. Open: https://github.com/somakalla1-droid/RAG
2. Click: `rag-chatbot/RAG_Single_URL_Assignment.ipynb`
3. Open in Colab button
4. Set your API key in cell 3
5. Run all cells

---

## 🐛 Troubleshooting

### Problem 1: "No module named 'openai'"
**Solution:** Install missing packages
```bash
python3 -m pip install langchain langchain-openai langchain-community langchain-text-splitters
```

### Problem 2: "OPENAI_API_KEY not set"
**Solution:** Set environment variable
```bash
export OPENAI_API_KEY='sk-proj-...'
echo $OPENAI_API_KEY  # Verify it's set
```

### Problem 3: "Module not found: src.rag_pipeline_single_url"
**Solution:** Run from correct directory
```bash
cd /Users/somakalla/Desktop/IK/Assignment-1/RAG
python3 test_locally.py
```

### Problem 4: "Connection error to OpenAI API"
**Possible causes:**
- Invalid API key
- API key doesn't have access to embeddings/chat models
- Network issue

**Solution:**
1. Check API key is correct
2. Verify in OpenAI dashboard that your account has active API access
3. Test in Google Colab instead

### Problem 5: "URL loading timeout"
**Solution:** Use a simpler/faster URL
```python
# Instead of:
url = "https://en.wikipedia.org/wiki/Artificial_intelligence"

# Try:
url = "https://raw.githubusercontent.com/somakalla1-droid/RAG/main/README.md"
```

---

## ✅ Complete Testing Checklist

### Before Submission, Verify:

- [ ] API key is set: `echo $OPENAI_API_KEY`
- [ ] Dependencies installed: `python3 test_locally.py` (no import errors)
- [ ] URL loads: Script completes without timeout
- [ ] Chunking works: See "Created X chunks" message
- [ ] Embeddings generate: See "Embeddings generated" message
- [ ] Queries work: Get answer back from LLM
- [ ] No syntax errors: Check output for exceptions

### Quick Verification
```bash
# Run this one command to test everything
cd /Users/somakalla/Desktop/IK/Assignment-1/RAG && \
export OPENAI_API_KEY='your-key' && \
python3 test_locally.py
```

---

## 📊 What Gets Tested

### Test 1: Imports
- Checks all required packages are installed
- Tests: langchain, openai, etc.

### Test 2: API Key
- Verifies OPENAI_API_KEY environment variable is set
- Shows first/last 10 chars for verification

### Test 3: Full Pipeline
- Loads Wikipedia page
- Chunks it (should see "316 chunks")
- Generates embeddings
- Answers test query

---

## 🔍 Detailed Testing

If simple test fails, try debugging step-by-step:

### Step 1: Check Imports
```python
python3 -c "from src.rag_pipeline_single_url import SingleURLRAG; print('✅ Import works')"
```

### Step 2: Check API Key
```python
import os
print(os.getenv('OPENAI_API_KEY'))  # Should show your key
```

### Step 3: Check Each Function
```python
import sys
sys.path.insert(0, '/Users/somakalla/Desktop/IK/Assignment-1/RAG/rag-chatbot')

from src.rag_pipeline_single_url import SingleURLRAG
import os

api_key = os.getenv('OPENAI_API_KEY')
rag = SingleURLRAG(openai_api_key=api_key)

# Test each step individually
print("Loading document...")
rag.load_document('https://en.wikipedia.org/wiki/Python_(programming_language)')
print(f"✅ Loaded {len(rag.documents)} documents")

print("Chunking...")
rag.chunk_document()
print(f"✅ Created {len(rag.chunks)} chunks")

print("Generating embeddings...")
rag.generate_embeddings()
print("✅ Embeddings created")

print("Setting up chain...")
rag.setup_qa_chain()
print("✅ Chain ready")

print("Testing query...")
answer = rag.query("What is this about?")
print(f"✅ Got answer: {answer[:100]}...")
```

---

## 🚀 After Successful Local Test

1. ✅ Your local environment is working
2. ✅ API key is valid
3. ✅ All components functioning
4. ✅ Ready to submit!

**Next steps:**
- Submit GitHub repository link
- Or upload Colab notebook
- Or provide all files

---

## 📞 Quick Reference

| Issue | Command |
|---|---|
| Set API key | `export OPENAI_API_KEY='sk-proj-...'` |
| Run tests | `python3 test_locally.py` |
| Check key is set | `echo $OPENAI_API_KEY` |
| Install deps | `pip3 install langchain langchain-openai` |
| Test imports | `python3 -c "from src.rag_pipeline_single_url import SingleURLRAG"` |
| Run Gradio | `python3 rag-chatbot/app_single_url.py` |

---

## ✨ Success Indicators

When working correctly, you should see:
- ✅ "Successfully loaded 1 document"
- ✅ "Created 316 chunks" (or similar number)
- ✅ "Embeddings generated"
- ✅ Answer text from query
- ✅ No error messages

**If you see all of these: Ready for submission! 🎉**

---

**Need more help?** Share:
1. The error message you're seeing
2. The command you ran
3. Your Python version: `python3 --version`
