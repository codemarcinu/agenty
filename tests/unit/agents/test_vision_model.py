#!/usr/bin/env python3
"""
Test vision model with actual image processing
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import ollama
from settings import settings

async def test_vision_model():
    """Test if vision model can process images"""
    print("🔍 Testing Vision Model with Image...")
    
    # Check if we have any test images
    test_images = list(Path("paragony").glob("*.png")) + list(Path("paragony").glob("*.jpg"))
    
    if not test_images:
        print("❌ No test images found in paragony directory")
        return False
    
    test_image = test_images[0]
    print(f"📷 Using test image: {test_image}")
    
    try:
        # Create raw ollama client for vision models
        raw_ollama_client = ollama.Client(host=settings.OLLAMA_URL)
        
        # Simple prompt to test image processing
        prompt = "What do you see in this image? Describe it briefly."
        
        response = await asyncio.to_thread(
            raw_ollama_client.chat,
            model="llava:7b",
            messages=[
                {"role": "user", "content": prompt, "images": [str(test_image)]}
            ],
            options={"temperature": 0.1, "top_p": 0.9, "num_ctx": 4096},
        )
        
        print("✅ Vision model response:")
        print(f"📝 Response: {response['message']['content']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Vision model error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_vision_model()) 