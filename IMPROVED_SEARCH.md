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

The system checks for longer/more specific suffixes first to ensure optimal stripping:

**Priority order:**
1. Holding Corporation, Holding Corp. (checked first)
2. Corporation, Incorporated, Holdings, Company, Limited
3. Corp., Inc., Co., Ltd. (checked after full words)
4. L.L.C., LLC, PLC, Group

This ordering ensures "Paylocity Holding Corp." becomes "Paylocity" (not "Paylocity Holding")

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

**PCTY (Paylocity Holding Corp.) - Success on first query:**

```
[DEBUG] Trying search query 1/4: 'Paylocity'
[DEBUG] Fetching news for PCTY (attempt 1/3) with query: 'Paylocity'
[INFO] Successfully fetched 10 articles for PCTY using query 'Paylocity'
```

Result: 10 highly relevant financial articles about Paylocity's stock performance and analyst ratings.

**If first query fails, automatic fallback:**

```
[DEBUG] Trying search query 1/4: 'ExampleCo'
[DEBUG] No articles found with query 'ExampleCo', trying next query...
[DEBUG] Trying search query 2/4: 'ExampleCo Corporation'
[INFO] Successfully fetched 5 articles for EXMP using query 'ExampleCo Corporation'
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
