# Improved News Search Strategy

## Problem
Companies like PCTY (Paylocity Holding Corp.) were returning no news articles because the full company name doesn't match how news articles reference the company.

## Solution
Implemented smart search with multiple fallback queries.

### Search Strategy

For "Paylocity Holding Corp." (PCTY), the system now tries in order:

1. **Short name**: "Paylocity" (strips corporate suffixes)
2. **Full name**: "Paylocity Holding Corp."
3. **Combined**: "Paylocity PCTY"
4. **Ticker**: "PCTY"

### Corporate Suffixes Removed

- Corporation, Corp., Corp
- Incorporated, Inc., Inc
- Company, Co., Co
- Limited, Ltd., Ltd
- Holdings, Holding Corporation, Holding Corp.
- LLC, L.L.C., PLC, Group

### How It Works

```python
# Example for Paylocity Holding Corp.
search_queries = [
    "Paylocity",                    # Try short name first
    "Paylocity Holding Corp.",      # Then full name
    "Paylocity PCTY",               # Then combined
    "PCTY"                          # Finally ticker
]
```

The system:
1. Tries each query in order
2. Stops when articles are found
3. Falls back to next query if no results
4. Returns empty if all queries fail

### Benefits

- **Higher success rate**: More companies will return news
- **Better relevance**: Short names match news article language
- **Automatic fallback**: No manual intervention needed
- **Detailed logging**: See which query succeeded in DEBUG logs

### Example Output

```
[DEBUG] Trying search query 1/4: 'Paylocity'
[DEBUG] Fetching news for PCTY (attempt 1/3) with query: 'Paylocity'
[INFO] Successfully fetched 10 articles for PCTY using query 'Paylocity'
```

Or if first query fails:

```
[DEBUG] Trying search query 1/4: 'Paylocity'
[DEBUG] No articles found with query 'Paylocity', trying next query...
[DEBUG] Trying search query 2/4: 'Paylocity Holding Corp.'
[INFO] Successfully fetched 5 articles for PCTY using query 'Paylocity Holding Corp.'
```

### Testing

Test with these problematic tickers:
- PCTY (Paylocity Holding Corp.) - was failing
- FI (Fiserv Corp.) - short ticker
- Companies with "Holdings" or "Group" suffixes

Run:
```bash
python3 vendor_monitor.py --analyzer vader
```

Check log file for query attempts and success rates.
