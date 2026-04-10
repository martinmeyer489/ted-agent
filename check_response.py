"""Quick test to see what fields are actually returned"""
import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.services.ted_client import get_ted_client


async def check_response_structure():
    client = get_ted_client()
    result = await client.search_notices(
        "ND=*", 
        ["ND", "notice-title", "country-origin", "publication-date", "classification-cpv"]
    )
    
    if result.get("notices"):
        print("Sample notice structure:")
        print(json.dumps(result["notices"][0], indent=2))
    
    print(f"\n\nTotal fields in first notice: {len(result['notices'][0].keys())}")
    print("Available keys:", list(result["notices"][0].keys()))


if __name__ == "__main__":
    asyncio.run(check_response_structure())
