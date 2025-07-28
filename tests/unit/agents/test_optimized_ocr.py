#!/usr/bin/env python3
"""
Test zoptymalizowanego SpecializedOCRAgent
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from backend.agents.ocr.specialized_ocr_llm import SpecializedOCRAgent

async def test_optimized_ocr():
    """Test zoptymalizowanego OCR"""
    print("🔍 Test zoptymalizowanego SpecializedOCRAgent...")
    
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
            extracted_text = result.data.get('extracted_text', '')
            print(f"📝 Extracted text length: {len(extracted_text)}")
            print(f"📝 First 200 chars: {extracted_text[:200]}...")
            return True
        else:
            print(f"❌ Error: {result.error}")
            return False
            
    except Exception as e:
        print(f"❌ SpecializedOCRAgent error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_optimized_ocr()) 