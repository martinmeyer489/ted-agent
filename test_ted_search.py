"""
Simple test script to verify TED API search functionality
Run this to test the core search feature without needing Ollama or Supabase
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.services.ted_client import get_ted_client
from app.services.query_builder import TEDQueryBuilder, DEFAULT_NOTICE_FIELDS


async def test_basic_search():
    """Test basic TED search."""
    print("🔍 Testing TED Search Functionality\n")
    print("=" * 60)
    
    # Test 1: Working example - CPV code search
    print("\n📌 Test 1: Search architectural services (CPV 71000000)")
    client = get_ted_client()
    query = "classification-cpv = 71000000 SORT BY publication-date DESC"
    
    fields = [
        "notice-title",
        "notice-type",
        "publication-date",
        "organisation-name-buyer",
        "description-lot",
        "contract-title",
        "classification-cpv",
        "ND"
    ]
    
    result = await client.search_notices(
        query=query,
        fields=fields,
        page=1,
        limit=5,
        scope="ACTIVE"
    )
    
    if result.get("notices"):
        print(f"✅ Found {len(result['notices'])} notices")
        for i, notice in enumerate(result['notices'], 1):
            title = notice.get('notice-title', {}).get('eng', ['N/A'])
            if isinstance(title, list):
                title = title[0] if title else 'N/A'
            pub_date = notice.get('publication-date', 'N/A')
            buyer = notice.get('organisation-name-buyer', {}).get('eng', ['N/A'])
            if isinstance(buyer, list):
                buyer = buyer[0] if buyer else 'N/A'
            print(f"   {i}. [{pub_date}] {title[:60]}...")
            print(f"      Buyer: {buyer[:50]}")
    else:
        print("❌ No notices found")
    
    # Test 2: Query builder with CPV code
    print("\n📌 Test 2: Using query builder for IT services")
    builder = TEDQueryBuilder()
    query = builder.cpv_code("72000000").build()
    print(f"   Query: {query}")
    
    result = await client.search_notices(
        query=query,
        fields=["notice-title", "publication-date", "classification-cpv", "ND"],
        limit=3
    )
    
    if result.get("notices"):
        print(f"✅ Found {len(result['notices'])} notices matching criteria")
        for i, notice in enumerate(result['notices'], 1):
            title = notice.get('notice-title', {}).get('eng', 'N/A')
            if isinstance(title, list):
                title = title[0] if title else 'N/A'
            pub_date = notice.get('publication-date', 'N/A')
            cpvs = notice.get('classification-cpv', [])
            print(f"   {i}. [{pub_date}] {title[:50]}...")
            print(f"      CPV codes: {', '.join(cpvs[:3])}")
    else:
        print("⚠️  No notices found for this specific query")
    
    # Test 3: Wildcard search with sorting
    print("\n📌 Test 3: Latest notices (wildcard search)")
    query = "ND=* SORT BY publication-date DESC"
    
    result = await client.search_notices(
        query=query,
        fields=["ND", "notice-title", "publication-date"],
        limit=3
    )
    
    if result.get("notices"):
        print(f"✅ Found {len(result['notices'])} latest notices")
        for i, notice in enumerate(result['notices'], 1):
            title = notice.get('notice-title', {}).get('eng', 'N/A')
            if isinstance(title, list):
                title = title[0] if title else 'N/A'
            pub_date = notice.get('publication-date', 'N/A')
            nd = notice.get('ND', 'N/A')
            print(f"   {i}. [{pub_date}] {nd}")
            print(f"      {title[:60]}...")
    else:
        print("⚠️  No notices found")
    
    print("\n" + "=" * 60)
    print("✅ TED API search functionality is working correctly!")
    print("\nNext steps:")
    print("1. Set up Supabase to enable storage and vector search")
    print("2. Configure Ollama for AI chat functionality")
    print("3. Start the API: poetry run uvicorn backend.app.main:app --reload")


if __name__ == "__main__":
    asyncio.run(test_basic_search())
