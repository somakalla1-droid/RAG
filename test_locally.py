#!/usr/bin/env python3
"""
Simple local testing script for Single-URL RAG System
Run this to verify everything works before submission
"""

import os
import sys

# Add rag-chatbot to path
sys.path.insert(0, '/Users/somakalla/Desktop/IK/Assignment-1/RAG/rag-chatbot')

def test_imports():
    """Test 1: Verify all imports work"""
    print("\n" + "="*60)
    print("TEST 1: Checking Imports")
    print("="*60)
    try:
        from src.rag_pipeline_single_url import SingleURLRAG
        print("✅ SingleURLRAG imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_api_key():
    """Test 2: Check API key is set"""
    print("\n" + "="*60)
    print("TEST 2: Checking OpenAI API Key")
    print("="*60)
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        print(f"✅ API key found: {api_key[:20]}...{api_key[-10:]}")
        return True
    else:
        print("❌ OPENAI_API_KEY not set")
        print("\n📝 How to fix:")
        print("   Option 1 (Recommended):")
        print("     export OPENAI_API_KEY='your-api-key'")
        print("     python3 test_locally.py")
        print("\n   Option 2 (Edit this file):")
        print("     Replace api_key = os.getenv('OPENAI_API_KEY')")
        print("     with: api_key = 'your-api-key'")
        return False

def test_rag_system():
    """Test 3: Full RAG pipeline test"""
    print("\n" + "="*60)
    print("TEST 3: Testing RAG Pipeline")
    print("="*60)
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Skipped (API key not set)")
        return False
    
    try:
        from src.rag_pipeline_single_url import SingleURLRAG
        
        # Create RAG instance
        print("Creating RAG instance...")
        rag = SingleURLRAG(openai_api_key=api_key)
        print("✅ Instance created")
        
        # Test with a simple URL
        test_url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
        print(f"\nLoading URL: {test_url}")
        
        rag.initialize_from_url(test_url)
        print("✅ URL loaded and processed successfully!")
        
        # Test query
        print("\nTesting query...")
        question = "What is Python?"
        answer = rag.query(question)
        print(f"Question: {question}")
        print(f"Answer: {answer[:200]}...\n")
        print("✅ Query successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "█"*60)
    print("  LOCAL TESTING SCRIPT - Single-URL RAG System")
    print("█"*60)
    
    results = {
        "Imports": test_imports(),
        "API Key": test_api_key(),
        "RAG Pipeline": test_rag_system()
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Ready for submission!")
    else:
        print("⚠️  Some tests failed - See details above")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
