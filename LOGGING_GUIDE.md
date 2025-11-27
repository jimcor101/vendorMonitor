# Logging and Error Handling Guide

This document explains the robust logging and error handling features added to the Vendor Monitoring Script.

## Features Overview

### 1. Dual-Level Logging

The script implements a sophisticated logging system with two output streams:

**Console Output (INFO level):**
- Clean, user-friendly messages
- Progress indicators
- Summary statistics
- Critical errors and warnings

**Log File (DEBUG level):**
- Detailed diagnostic information
- All API calls and responses
- Retry attempts with timing
- Complete stack traces
- Timestamps for every operation

### 2. Automatic Log Files

Every run creates a dated log file: `vendor_monitor_mmddyy.log`

Example: `vendor_monitor_112626.log` for November 26, 2026

## Retry Logic

### Stock Data (yfinance)
- **Attempts**: 3 retries
- **Backoff**: Exponential (1s, 2s, 4s)
- **Errors Handled**: Network timeouts, connection errors, malformed data

### News Data (NewsAPI)
- **Attempts**: 3 retries
- **Backoff**: Exponential (1s, 2s, 4s)
- **Special Handling**:
  - Rate limit errors (429): Immediate stop, no retry
  - Auth errors (401): Fatal error, script stops
  - Network errors: Retry with backoff

## Error Recovery

### Graceful Degradation
The script never stops on individual vendor failures. If one vendor's data is unavailable:
- Error is logged
- Script continues to next vendor
- Failed vendor shows in error summary

### Error Statistics
At the end of each run, you get a summary:
```
SUMMARY
============================================================
Total vendors processed:  6
Stock data success:       6/6
Stock data failures:      0/6
News data success:        5/6
News data failures:       1/6
Total headlines fetched:  47

Warnings/Errors: 1
  - SNOW: No headlines found
```

## Log File Format

### Log Entry Structure
```
2026-11-26 09:15:23 - INFO - process_vendors - [1/6] Processing MSFT - Microsoft Corporation
2026-11-26 09:15:23 - DEBUG - get_stock_data - Fetching stock data for MSFT (attempt 1/3)
2026-11-26 09:15:24 - DEBUG - get_stock_data - Successfully fetched stock data for MSFT: $380.50 (+1.25%)
```

Each log entry contains:
- **Timestamp**: Exact time of operation
- **Level**: INFO, DEBUG, WARNING, ERROR
- **Function**: Which function generated the log
- **Message**: Description of the operation

## Using Logs for Monitoring

### Daily Monitoring Checklist

1. **Run the script**:
   ```bash
   export NEWSAPI_KEY='your_key_here'
   python vendor_monitor.py
   ```

2. **Check console output** for immediate feedback:
   - Did all vendors process successfully?
   - Any warnings or errors?
   - Summary statistics acceptable?

3. **Review log file if issues exist**:
   ```bash
   tail -50 vendor_monitor_112626.log
   ```

4. **Search for errors**:
   ```bash
   grep ERROR vendor_monitor_112626.log
   grep WARNING vendor_monitor_112626.log
   ```

### Common Log Patterns

**Successful Processing:**
```
INFO - Successfully loaded 6 vendors from vendors.csv
DEBUG - Successfully fetched stock data for MSFT: $380.50 (+1.25%)
DEBUG - Successfully fetched 10 headlines for MSFT
```

**Network Issues (Auto-Retry):**
```
WARNING - Attempt 1 failed for ORCL: Connection timeout
DEBUG - Retrying in 1 seconds...
DEBUG - Fetching stock data for ORCL (attempt 2/3)
DEBUG - Successfully fetched stock data for ORCL: $125.30 (-0.50%)
```

**Rate Limit Hit:**
```
ERROR - NewsAPI rate limit exceeded for SNOW: 429 Too Many Requests
WARNING - SNOW: No headlines found
```

**Fatal Errors:**
```
ERROR - Invalid NewsAPI key: 401 Unauthorized
ERROR - Failed to initialize NewsAPI client
```

## Debugging Tips

### Issue: Script runs but some vendors have no data

**Steps:**
1. Check summary section for success rates
2. Open log file and search for vendor symbol: `grep "SYMBOL" vendor_monitor_*.log`
3. Look for WARNING or ERROR entries for that vendor
4. Check if it's a data issue or API issue

### Issue: Script is slow

**Steps:**
1. Check log for retry attempts: `grep "Retrying" vendor_monitor_*.log`
2. Multiple retries indicate network issues
3. Consider increasing timeout or checking internet connection

### Issue: Partial failures happening regularly

**Steps:**
1. Review the errors list in summary
2. Check if same vendors fail consistently
3. Possible causes:
   - Invalid ticker symbols
   - Delisted companies
   - Company name too generic for news search
   - API rate limits

## Automation and Monitoring

### Cron Job Setup with Logging

```bash
# Run daily at 9 AM and keep logs
0 9 * * * export NEWSAPI_KEY='your_key' && \
  cd /path/to/vendorai && \
  python vendor_monitor.py >> cron_output.log 2>&1
```

### Log Rotation

Keep your logs organized:
```bash
# Archive old logs (weekly)
0 0 * * 0 cd /path/to/vendorai && \
  tar -czf logs_archive_$(date +%Y%m%d).tar.gz vendor_monitor_*.log && \
  find . -name "vendor_monitor_*.log" -mtime +7 -delete
```

### Email Alerts on Failures

```bash
# Send email if errors detected
0 9 * * * export NEWSAPI_KEY='your_key' && \
  cd /path/to/vendorai && \
  python vendor_monitor.py && \
  grep -q "ERROR" vendor_monitor_$(date +%m%d%y).log && \
  echo "Errors detected in vendor monitoring" | mail -s "Vendor Monitor Alert" you@example.com
```

## API Key Security

The script masks your API key in logs:
```
INFO - Using NewsAPI key: 9ac0bc72...3863
```

Only the first 8 and last 4 characters are shown for security.

## Performance Metrics

The log file contains timing information useful for performance analysis:
- Time to fetch stock data per vendor
- Time to fetch news per vendor
- Total script execution time
- Retry delays and their impact

## Best Practices

1. **Always check the summary** before leaving the script output
2. **Review log files weekly** for patterns of failures
3. **Archive logs older than 30 days** to save space
4. **Monitor API usage** through the headlines fetched count
5. **Set up alerts** for critical errors in production environments

## Example Full Log Snippet

```
2026-11-26 09:15:20 - INFO - setup_logging - Logging initialized
2026-11-26 09:15:20 - INFO - process_vendors - ============================================================
2026-11-26 09:15:20 - INFO - process_vendors - Vendor Stock and News Monitoring Script
2026-11-26 09:15:20 - INFO - process_vendors - ============================================================
2026-11-26 09:15:20 - INFO - process_vendors - Using NewsAPI key: 9ac0bc72...3863
2026-11-26 09:15:20 - INFO - process_vendors - Successfully initialized NewsAPI client
2026-11-26 09:15:20 - INFO - process_vendors - Successfully loaded 6 vendors from vendors.csv
2026-11-26 09:15:20 - INFO - process_vendors - [1/6] Processing MSFT - Microsoft Corporation
2026-11-26 09:15:20 - DEBUG - get_stock_data - Fetching stock data for MSFT (attempt 1/3)
2026-11-26 09:15:21 - DEBUG - get_stock_data - Successfully fetched stock data for MSFT: $380.50 (+1.25%)
2026-11-26 09:15:21 - INFO - process_vendors - Stock: $380.50 (+1.25%) Vol: 25,000,000
2026-11-26 09:15:21 - DEBUG - get_news_headlines - Fetching news for MSFT (attempt 1/3) with query: 'Microsoft Corporation'
2026-11-26 09:15:22 - DEBUG - get_news_headlines - Successfully fetched 10 headlines for MSFT
2026-11-26 09:15:22 - INFO - process_vendors - News: Found 10 headlines
2026-11-26 09:15:22 - INFO - process_vendors - [BULLISH] Microsoft announces new AI features...
```

This detailed logging ensures you always know what's happening with your vendor monitoring system!
