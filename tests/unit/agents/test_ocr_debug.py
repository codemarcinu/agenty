#!/usr/bin/env python3
"""
Debug script to test OCR functionality and identify issues
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from backend.agents.ocr.specialized_ocr_llm import SpecializedOCRAgent
from backend.agents.ocr_agent import OCRAgent
from backend.core.llm_client import EnhancedLLMClient

async def test_ocr_models():
    """Test OCR models availability and functionality"""
    print("🔍 Testing OCR Models...")
    
    # Test 1: Check if Ollama is accessible
    try:
        llm_client = EnhancedLLMClient()
        response = await llm_client.chat(
            model="llava:7b",
            messages=[{"role": "user", "content": "Hello"}],
            options={"num_predict": 1}
        )
        print("✅ Ollama client is working")
        print(f"Response: {response}")
    except Exception as e:
        print(f"❌ Ollama client error: {e}")
        return False
    
    # Test 2: Test SpecializedOCRAgent with a simple image
    print("\n🔍 Testing SpecializedOCRAgent...")
    
    # Check if we have any test images
    test_images = list(Path("paragony").glob("*.png")) + list(Path("paragony").glob("*.jpg"))
    
    if not test_images:
        print("❌ No test images found in paragony directory")
        return False
    
    test_image = test_images[0]
    print(f"📷 Using test image: {test_image}")
    
    try:
        agent = SpecializedOCRAgent()
        result = await agent.process({
            "image_path": str(test_image),
            "file_type": "image"
        })
        
        print(f"✅ SpecializedOCRAgent result: {result.success}")
        if result.success:
            print(f"📝 Extracted text length: {len(result.data.get('extracted_text', ''))}")
            print(f"📝 Extracted text: {result.data.get('extracted_text', '')[:200]}...")
        else:
            print(f"❌ Error: {result.error}")
            
    except Exception as e:
        print(f"❌ SpecializedOCRAgent error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Test traditional OCRAgent as fallback
    print("\n🔍 Testing traditional OCRAgent...")
    
    try:
        with open(test_image, "rb") as f:
            file_bytes = f.read()
        
        from backend.agents.ocr_agent import OCRAgentInput
        
        agent = OCRAgent()
        input_data = OCRAgentInput(file_bytes=file_bytes, file_type="image")
        result = await agent.process(input_data)
        
        print(f"✅ Traditional OCRAgent result: {result.success}")
        if result.success:
            print(f"📝 Extracted text length: {len(result.text or '')}")
            print(f"📝 Extracted text: {(result.text or '')[:200]}...")
        else:
            print(f"❌ Error: {result.error}")
            
    except Exception as e:
        print(f"❌ Traditional OCRAgent error: {e}")
        import traceback
        traceback.print_exc()
    
    return True

if __name__ == "__main__":
    asyncio.run(test_ocr_models()) 