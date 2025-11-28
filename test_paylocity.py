#!/usr/bin/env python3
"""
Test script to debug Paylocity news search
"""

import os
from newsapi import NewsApiClient

# Initialize
newsapi_key = os.environ.get('NEWSAPI_KEY', '9ac0bc72401849509e687533b03f3863')
newsapi = NewsApiClient(api_key=newsapi_key)

# Test different queries
test_queries = [
    "Paylocity",
    "Paylocity Holding Corp",
    "Paylocity PCTY",
    "PCTY",
    "PCTY stock",
    "Paylocity earnings",
]

print("Testing NewsAPI queries for Paylocity (PCTY)...\n")
print("="*70)

for query in test_queries:
    print(f"\nQuery: '{query}'")
    print("-"*70)

    try:
        response = newsapi.get_everything(
            q=query,
            language='en',
            sort_by='publishedAt',
            page_size=5
        )

        total = response.get('totalResults', 0)
        articles = response.get('articles', [])

        print(f"Total results: {total}")
        print(f"Articles returned: {len(articles)}")

        if articles:
            print("\nFirst 3 headlines:")
            for i, article in enumerate(articles[:3], 1):
                title = article.get('title', 'N/A')
                print(f"  {i}. {title}")
        else:
            print("No articles found")

    except Exception as e:
        print(f"Error: {e}")

print("\n" + "="*70)
print("\nTrying with different date ranges...")
print("="*70)

# Try with last 30 days
from datetime import datetime, timedelta
from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

print(f"\nQuery: 'Paylocity' (last 30 days)")
print("-"*70)

try:
    response = newsapi.get_everything(
        q="Paylocity",
        language='en',
        from_param=from_date,
        sort_by='publishedAt',
        page_size=5
    )

    total = response.get('totalResults', 0)
    articles = response.get('articles', [])

    print(f"Total results: {total}")
    print(f"Articles returned: {len(articles)}")

    if articles:
        print("\nHeadlines:")
        for i, article in enumerate(articles[:5], 1):
            title = article.get('title', 'N/A')
            published = article.get('publishedAt', 'N/A')
            print(f"  {i}. [{published}] {title}")
    else:
        print("No articles found")

except Exception as e:
    print(f"Error: {e}")
