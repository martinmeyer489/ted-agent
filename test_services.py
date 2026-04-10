#!/usr/bin/env python3
"""
Quick test script to verify all services are working
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.services.ted_client import get_ted_client
from app.services.ollama_client import get_ollama_client
from app.services.supabase_client import get_supabase_client
from app.core.config import settings
from loguru import logger


async def test_ted_api():
    """Test TED API connection."""
    print("\n🔍 Testing TED API...")
    try:
        client = get_ted_client()
        result = await client.search_notices("ND=*", ["ND", "notice-title"], timeout=10)
        
        if "error" in result and not result.get("notices"):
            print(f"❌ TED API Error: {result['error']}")
            return False
        
        notice_count = len(result.get("notices", []))
        print(f"✅ TED API OK - Found {notice_count} notices")
        
        if notice_count > 0:
            sample_title = result['notices'][0].get('notice-title')
            if isinstance(sample_title, list) and sample_title:
                print(f"   Sample: {sample_title[0][:60]}...")
            else:
                print(f"   Sample: {str(sample_title)[:60]}...")
        
        return True
    except Exception as e:
        print(f"❌ TED API Failed: {str(e)}")
        return False


async def test_ollama():
    """Test Ollama Cloud connection."""
    print("\n💬 Testing Ollama Cloud...")
    try:
        client = get_ollama_client()
        messages = [
            {"role": "user", "content": "Say 'Hello' in one word."}
        ]
        
        response = await client.chat(messages, temperature=0.1)
        content = response.get("message", {}).get("content", "")
        
        print(f"✅ Ollama Cloud OK - Response: {content[:50]}")
        return True
    except Exception as e:
        print(f"❌ Ollama Cloud Failed: {str(e)}")
        return False


async def test_supabase():
    """Test Supabase connection."""
    print("\n🗄️  Testing Supabase...")
    try:
        client = get_supabase_client()
        
        # Try to query tender_notices (may be empty)
        # This will fail if tables don't exist
        result = client.client.table("tender_notices").select("count").execute()
        
        print(f"✅ Supabase OK - Connection successful")
        return True
    except Exception as e:
        print(f"⚠️  Supabase Warning: {str(e)}")
        print("   Make sure you've run database/schema.sql in Supabase SQL Editor")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("TED Bot - Service Connection Test")
    print("=" * 60)
    
    print(f"\n📋 Configuration:")
    print(f"   TED API URL: {settings.ted_api_url}")
    print(f"   Ollama URL: {settings.ollama_api_url}")
    print(f"   Supabase URL: {settings.supabase_url}")
    print(f"   Environment: {settings.environment}")
    
    results = {
        "TED API": await test_ted_api(),
        "Ollama Cloud": await test_ollama(),
        "Supabase": await test_supabase(),
    }
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    
    for service, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{service:20} {status}")
    
    all_pass = all(results.values())
    
    if all_pass:
        print("\n🎉 All services are working! You can start the application.")
        print("\nRun: ./start-dev.sh")
    else:
        print("\n⚠️  Some services failed. Please check your .env configuration.")
    
    print()


if __name__ == "__main__":
    asyncio.run(main())
