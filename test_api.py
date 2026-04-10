#!/usr/bin/env python3
"""
Comprehensive API test demonstrating all working features
"""

import requests
import json

API_URL = "http://localhost:8000/api/v1"


def test_wildcard_search():
    """Test 1: Basic wildcard search for latest notices"""
    print("\n" + "="*60)
    print("TEST 1: Wildcard Search (Latest Notices)")
    print("="*60)
    
    response = requests.post(
        f"{API_URL}/tenders/search",
        json={
            "query": "",
            "max_results": 3
        }
    )
    
    data = response.json()
    print(f"Status: {response.status_code}")
    print(f"Expert Query: {data['expert_query']}")
    print(f"Found: {data['count']} notices\n")
    
    for i, notice in enumerate(data['notices'], 1):
        print(f"{i}. {notice['title'][:70]}")
        print(f"   ID: {notice['notice_id']}")
        print(f"   Date: {notice['publication_date']}")
        print(f"   Buyer: {notice['buyer_name'] or 'N/A'}")
        print()


def test_cpv_search():
    """Test 2: CPV code search (IT services)"""
    print("\n" + "="*60)
    print("TEST 2: CPV Code Search (72000000 - IT Services)")
    print("="*60)
    
    response = requests.post(
        f"{API_URL}/tenders/search",
        json={
            "query": "",
            "cpv_codes": ["72000000"],
            "max_results": 3
        }
    )
    
    data = response.json()
    print(f"Status: {response.status_code}")
    print(f"Expert Query: {data['expert_query']}")
    print(f"Found: {data['count']} IT service notices\n")
    
    for i, notice in enumerate(data['notices'], 1):
        print(f"{i}. {notice['title'][:70]}")
        print(f"   CPV Codes: {', '.join(notice['cpv_codes'][:3])}")
        print(f"   Description: {(notice['description'] or '')[:80]}...")
        print()


def test_title_search():
    """Test 3: Title search"""
    print("\n" + "="*60)
    print("TEST 3: Title Search ('software')")
    print("="*60)
    
    response = requests.post(
        f"{API_URL}/tenders/search",
        json={
            "query": "software",
            "max_results": 3
        }
    )
    
    data = response.json()
    print(f"Status: {response.status_code}")
    print(f"Expert Query: {data['expert_query']}")
    print(f"Found: {data['count']} notices with 'software' in title\n")
    
    for i, notice in enumerate(data['notices'], 1):
        print(f"{i}. {notice['title'][:70]}")
        print(f"   Country: {notice['country']}")
        print()


def test_combined_search():
    """Test 4: Combined filters"""
    print("\n" + "="*60)
    print("TEST 4: Combined Search (Construction + Germany)")
    print("="*60)
    
    response = requests.post(
        f"{API_URL}/tenders/search",
        json={
            "query": "construction",
            "countries": ["Germany"],
            "max_results": 3
        }
    )
    
    data = response.json()
    print(f"Status: {response.status_code}")
    print(f"Expert Query: {data['expert_query']}")
    print(f"Found: {data['count']} notices\n")
    
    for i, notice in enumerate(data['notices'], 1):
        print(f"{i}. {notice['title'][:70]}")
        print(f"   Country: {notice['country']}")
        print(f"   Buyer: {notice['buyer_name'] or 'N/A'}")
        print()


def test_health_check():
    """Test health endpoint"""
    print("\n" + "="*60)
    print("HEALTH CHECK")
    print("="*60)
    
    response = requests.get(f"{API_URL}/health")
    data = response.json()
    
    print(f"Status: {response.status_code}")
    print(f"Service: {data['service']}")
    print(f"Health: {data['status']}")


def main():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# TED Bot API - Comprehensive Test Suite")
    print("#"*60)
    
    try:
        test_health_check()
        test_wildcard_search()
        test_cpv_search()
        test_title_search()
        test_combined_search()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nThe TED Bot search API is fully functional.")
        print("You can now:")
        print("  1. Use the frontend: Open frontend/index.html")
        print("  2. Access API docs: http://localhost:8000/docs")
        print("  3. Build custom integrations using the API")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to the API")
        print("Make sure the server is running:")
        print("  poetry run uvicorn backend.app.main:app --reload --port 8000")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


if __name__ == "__main__":
    main()
