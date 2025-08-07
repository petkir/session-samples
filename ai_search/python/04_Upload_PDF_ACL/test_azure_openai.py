#!/usr/bin/env python3
"""
Quick test script to verify Azure OpenAI connection and embedding generation.
Run this script to test your Azure OpenAI configuration before running the main application.
Uses direct HTTP requests to the Azure OpenAI API.
"""
import asyncio
import sys
import os
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
import aiohttp


async def test_azure_openai_connection():
    """Test the Azure OpenAI connection and embedding generation."""
    print("🔍 Testing Azure OpenAI Configuration (Direct HTTP)")
    print("=" * 50)
    
    # Display configuration
    print(f"Endpoint URL: {settings.azure_openai_endpoint}")
    print(f"API Key: {settings.azure_openai_key[:10]}...")
    print()
    
    # Test embedding generation
    try:
        print("🧪 Testing embedding generation...")
        
        test_text = "This is a test sentence for embedding generation."
        
        # Prepare request
        headers = {
            'Content-Type': 'application/json',
            'api-key': settings.azure_openai_key
        }
        
        payload = {
            "input": test_text
        }
        
        # Make HTTP request
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                settings.azure_openai_endpoint,
                headers=headers,
                json=payload
            ) as response:
                
                print(f"HTTP Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    
                    if 'data' in result and len(result['data']) > 0:
                        embedding = result['data'][0]['embedding']
                        print(f"✅ Embedding generated successfully!")
                        print(f"   - Embedding dimensions: {len(embedding)}")
                        print(f"   - First 5 values: {embedding[:5]}")
                        print(f"   - Text: '{test_text}'")
                        
                        # Verify dimensions
                        if len(embedding) == settings.vector_dimensions:
                            print(f"✅ Embedding dimensions match configuration ({settings.vector_dimensions})")
                        else:
                            print(f"⚠️  Embedding dimensions ({len(embedding)}) don't match configuration ({settings.vector_dimensions})")
                            print("   You may need to update VECTOR_DIMENSIONS in your .env file")
                        
                        return True
                    else:
                        print("❌ No embedding data in response")
                        print(f"Response: {result}")
                        return False
                        
                else:
                    error_text = await response.text()
                    print(f"❌ HTTP Error {response.status}: {error_text}")
                    
                    if response.status == 404:
                        print("\nTroubleshooting tips for 404 error:")
                        print("1. Check that your endpoint URL is correct")
                        print("2. Verify your deployment name in the URL")
                        print("3. Ensure your Azure OpenAI resource is active")
                        print("4. Check that the API version is correct")
                    elif response.status == 401:
                        print("\nTroubleshooting tips for 401 error:")
                        print("1. Check your API key is correct")
                        print("2. Verify your API key hasn't expired")
                        print("3. Ensure you have proper permissions")
                    elif response.status == 429:
                        print("\nTroubleshooting tips for 429 error:")
                        print("1. You're hitting rate limits")
                        print("2. Wait a moment and try again")
                        print("3. Check your quota in Azure portal")
                    
                    return False
                    
    except aiohttp.ClientError as e:
        print(f"❌ HTTP Client Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check your internet connection")
        print("2. Verify the endpoint URL is accessible")
        print("3. Check firewall settings")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    try:
        success = await test_azure_openai_connection()
        
        if success:
            print("\n🎉 Azure OpenAI configuration is working correctly!")
            print("You can now run the main application: python main.py")
        else:
            print("\n❌ Azure OpenAI configuration has issues. Please check the troubleshooting tips above.")
            return 1
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
