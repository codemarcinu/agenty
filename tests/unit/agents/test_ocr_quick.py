#!/usr/bin/env python3
"""
Szybki test OCR - sprawdza tylko podstawowe funkcjonalności
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from backend.agents.ocr_agent import OCRAgent, OCRAgentInput

async def test_traditional_ocr():
    """Test tylko tradycyjnego OCR - szybszy"""
    print("🔍 Szybki test tradycyjnego OCR...")
    
    # Check if we have any test images
    test_images = list(Path("paragony").glob("*.png")) + list(Path("paragony").glob("*.jpg"))
    
    if not test_images:
        print("❌ No test images found in paragony directory")
        return False
    
    test_image = test_images[0]
    print(f"📷 Using test image: {test_image}")
    
    try:
        with open(test_image, "rb") as f:
            file_bytes = f.read()
        
        agent = OCRAgent()
        input_data = OCRAgentInput(file_bytes=file_bytes, file_type="image")
        result = await agent.process(input_data)
        
        print(f"✅ Traditional OCRAgent result: {result.success}")
        if result.success:
            print(f"📝 Extracted text length: {len(result.text or '')}")
            print(f"📝 First 200 chars: {(result.text or '')[:200]}...")
            return True
        else:
            print(f"❌ Error: {result.error}")
            return False
            
    except Exception as e:
        print(f"❌ Traditional OCRAgent error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_traditional_ocr()) 