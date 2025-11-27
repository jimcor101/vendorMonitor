# Vendor Stock and News Monitoring Script

A Python script to monitor public companies that provide critical vendor services. The script fetches stock data, news headlines, and performs sentiment analysis to generate daily monitoring reports.

## Features

- Fetches stock data (close price, percent change, volume) for vendor companies
- Retrieves top 10 news articles for each company using NewsAPI
- **Dual sentiment analysis options**:
  - **VADER**: Fast, general-purpose (default, < 1 second)
  - **FinBERT**: Financial-specific, highly accurate (~30-60 seconds, CPU-compatible)
- Analyzes **full article content** (title + description + content) for better context
- Generates two CSV reports with date stamps
- **Robust error handling** with automatic retry logic (3 attempts with exponential backoff)
- **Comprehensive logging** to both console and file for debugging and audit trails
- **Graceful degradation** - continues processing even if individual vendors fail
- **Summary statistics** showing success/failure rates and error details
- Free tier available for both stock data and news APIs

## Installation

1. Install required dependencies:

```bash
pip install -r requirements.txt
```

2. Get a free NewsAPI key:
   - Visit https://newsapi.org/register
   - Sign up for a free account
   - Copy your API key from the dashboard
   - Free tier includes: 100 requests/day, 7 days of historical data

3. Set up your API key as an environment variable:

**Linux/Mac:**
```bash
export NEWSAPI_KEY='your_api_key_here'
```

**Windows (Command Prompt):**
```cmd
set NEWSAPI_KEY=your_api_key_here
```

**Windows (PowerShell):**
```powershell
$env:NEWSAPI_KEY='your_api_key_here'
```

**Permanent Setup (Recommended):**

Add to your shell profile (~/.bashrc, ~/.zshrc, or ~/.bash_profile):
```bash
export NEWSAPI_KEY='your_api_key_here'
```

Or create a `.env` file (copy from `.env.example`) and load it before running the script.

## Sentiment Analysis: VADER vs FinBERT

The script supports two sentiment analyzers:

### VADER (Default)
- ✅ **Fast**: < 1 second for all articles
- ✅ **No setup**: Works immediately
- ⚠️ **Less accurate**: ~65% accuracy on financial text
- ⚠️ **General purpose**: Not trained on financial terminology

### FinBERT (Recommended for Financial Analysis)
- ✅ **Highly accurate**: ~85% accuracy on financial text
- ✅ **Financial-specific**: Trained on 10K+ financial articles
- ✅ **CPU-compatible**: No GPU required
- ✅ **Better context**: Analyzes full article content
- ⚠️ **Slower**: ~30-60 seconds for typical analysis
- ⚠️ **First-time setup**: Downloads ~440MB model

**Quick Start with FinBERT:**
```bash
python vendor_monitor.py --analyzer finbert
```

See [FINBERT_GUIDE.md](FINBERT_GUIDE.md) for detailed comparison and usage.

## Usage

### Command-Line Options

The script accepts the following optional parameters:

```bash
python vendor_monitor.py [options]

Options:
  -h, --help            Show help message and exit
  -i, --input FILE      Input CSV file with vendor data (default: vendors.csv)
  -o, --output DIR      Output directory for CSV reports (default: script directory)
  -l, --log-path DIR    Directory for log files (default: script directory)
  -a, --analyzer METHOD Sentiment analyzer: 'vader' (fast) or 'finbert' (accurate) (default: vader)
```

### Basic Usage

Run with default settings (all files in script directory):

```bash
python vendor_monitor.py
```

This will:
- Read from `vendors.csv` in the current directory
- Write CSV reports to the script directory
- Write log file to the script directory

### Custom Input File

```bash
python vendor_monitor.py --input /path/to/custom_vendors.csv
```

### Custom Output Directory

Store reports in a specific location:

```bash
python vendor_monitor.py --output /path/to/reports
```

### Custom Log Directory

Store logs separately:

```bash
python vendor_monitor.py --log-path /var/log/vendor_monitor
```

### All Custom Paths

```bash
python vendor_monitor.py \
  --input /data/vendors.csv \
  --output /reports/daily \
  --log-path /var/log/vendor_monitor
```

### Short Form Options

```bash
python vendor_monitor.py -i vendors.csv -o ./reports -l ./logs
```

## Input Format

Create a CSV file named `vendors.csv` with the following columns:

```csv
symbol,companyname
MSFT,Microsoft Corporation
ORCL,Oracle Corporation
CRM,Salesforce Inc
```

- **symbol**: Stock ticker symbol (e.g., MSFT, ORCL)
- **companyname**: Full company name

## Output Files

The script generates two CSV files with date stamps (mmddyy format):

### 1. Stock Report: `vendorstockreport_mmddyy.csv`

Columns:
- **symbol**: Stock ticker symbol
- **companyname**: Company name
- **closeprice**: Most recent closing price
- **pctchange**: Percent change from previous day
- **volume**: Trading volume
- **sentiment**: Maximum sentiment from headlines (bullish/neutral/bearish)

### 2. Headline Report: `vendorheadlinereport_mmddyy.csv`

Columns:
- **symbol**: Stock ticker symbol
- **headline**: News headline text (or "N/A" if no headlines)
- **sentiment**: Sentiment analysis result (bullish/neutral/bearish/N/A)

### 3. Log File: `vendor_monitor_mmddyy.log`

A detailed log file is automatically generated with:
- Timestamp for each operation
- Debug information for API calls and retries
- Warning messages for failed operations
- Complete error stack traces for troubleshooting
- Summary statistics at the end

## Logging and Error Handling

The script includes comprehensive logging and error handling:

### Logging Levels

- **Console Output**: INFO level and above (clean, user-friendly messages)
- **Log File**: DEBUG level and above (detailed diagnostic information)

### Automatic Retry Logic

- **Stock Data**: 3 retry attempts with exponential backoff (1s, 2s, 4s delays)
- **News Data**: 3 retry attempts with exponential backoff
- Specific handling for rate limit errors (429) and authentication errors (401)

### Error Recovery

- **Graceful degradation**: Script continues processing other vendors if one fails
- **Detailed error reporting**: All errors are logged with context
- **Summary statistics**: Final report shows success/failure rates for easy monitoring

### Example Output

```
============================================================
Vendor Stock and News Monitoring Script
============================================================
Using NewsAPI key: 9ac0bc72...3863
Successfully initialized NewsAPI client
Output files: vendorstockreport_112626.csv, vendorheadlinereport_112626.csv
Successfully loaded 6 vendors from vendors.csv

------------------------------------------------------------
Processing vendors...
------------------------------------------------------------

[1/6] Processing MSFT - Microsoft Corporation
  Stock: $380.50 (+1.25%) Vol: 25,000,000
  News: Found 10 headlines
    [BULLISH] Microsoft announces new AI features in Azure cloud platform...
    [BULLISH] Tech giant sees strong quarterly growth...

============================================================
SUMMARY
============================================================
Total vendors processed:  6
Stock data success:       6/6
News data success:        5/6
Total headlines fetched:  47

Warnings/Errors: 1
  - SNOW: No headlines found
```

## Sentiment Analysis

The script uses VADER (Valence Aware Dictionary and sEntiment Reasoner) sentiment analysis to classify headlines:

- **Bullish**: Positive sentiment (compound score ≥ 0.05)
- **Neutral**: Neutral sentiment (-0.05 < compound score < 0.05)
- **Bearish**: Negative sentiment (compound score ≤ -0.05)
- **N/A**: No headlines available

The stock report shows the **maximum sentiment** (most positive) from all headlines for each symbol, with the ranking: bullish > neutral > bearish.

## Daily Monitoring

To run this script daily, you can:

1. **Manual execution**: Run the script each morning before market opens

2. **Cron job** (Linux/Mac):
   ```bash
   # Basic - run daily at 9:00 AM with default paths
   0 9 * * * export NEWSAPI_KEY='your_key_here' && cd /path/to/vendorai && python vendor_monitor.py

   # With custom output directories for organized storage
   0 9 * * * export NEWSAPI_KEY='your_key_here' && \
     cd /path/to/vendorai && \
     python vendor_monitor.py --output /reports/vendor/daily --log-path /var/log/vendor_monitor

   # Archive-friendly with date-based directory structure
   0 9 * * * export NEWSAPI_KEY='your_key_here' && \
     cd /path/to/vendorai && \
     python vendor_monitor.py \
       --output /reports/vendor/$(date +\%Y/\%m) \
       --log-path /var/log/vendor_monitor
   ```

3. **Task Scheduler** (Windows):
   - Create a scheduled task to run the script daily
   - Set NEWSAPI_KEY as a system environment variable
   - Use custom paths in the task action:
     ```cmd
     python C:\vendorai\vendor_monitor.py --output C:\Reports\Vendor --log-path C:\Logs\Vendor
     ```

### Benefits of Custom Paths

Using custom output and log paths helps with:
- **Organization**: Keep reports separate from code
- **Backup**: Easier to back up specific directories
- **Permissions**: Store logs in standard locations like `/var/log`
- **Archival**: Organize reports by date or month
- **Multi-environment**: Different paths for dev/test/prod

## Dependencies

- **yfinance**: Fetches stock data from Yahoo Finance (free, no API key)
- **newsapi-python**: Fetches news headlines from NewsAPI (requires free API key)
- **vaderSentiment**: Performs sentiment analysis on headlines

## Notes

- Stock data is fetched for the most recent trading day using Yahoo Finance
- News headlines are fetched using NewsAPI (free tier: 100 requests/day)
- The script fetches up to 10 headlines per symbol
- Headlines are searched by company name for better relevance
- If no headlines are available, the report shows "N/A"
- Internet connection required to fetch data

## API Rate Limits

**NewsAPI Free Tier:**
- 100 requests per day
- 7 days of historical news data
- If monitoring 5 vendors daily, you'll use ~5 requests per day
- Plan accordingly based on your vendor list size

**Yahoo Finance (yfinance):**
- No official rate limits for basic stock data
- Free, no API key required

## Troubleshooting

When encountering issues, **always check the log file** (`vendor_monitor_mmddyy.log`) for detailed error messages and stack traces.

### Common Issues

- **"NEWSAPI_KEY environment variable not set"**:
  - Make sure you've set the environment variable with your API key
  - Verify: `echo $NEWSAPI_KEY` (Linux/Mac) or `echo %NEWSAPI_KEY%` (Windows)

- **No data available**:
  - The symbol may be invalid or delisted
  - Check the log file for specific error messages
  - Verify the symbol is correct on Yahoo Finance

- **Connection errors**:
  - Check your internet connection
  - The script will automatically retry 3 times with exponential backoff
  - Check log file for retry attempts and failure reasons

- **Missing vendors.csv**:
  - Ensure the input file exists in the same directory
  - Check current directory in log file output

- **API rate limit exceeded**:
  - NewsAPI free tier is limited to 100 requests/day
  - Check the summary at the end of script execution for request counts
  - Reduce the number of vendors or upgrade your plan

- **Partial failures**:
  - The script continues processing even if individual vendors fail
  - Check the SUMMARY section at the end for failure counts
  - Review log file for specific vendor errors

### Debug Mode

For more detailed debugging, check the log file which contains:
- All API calls and responses
- Retry attempts and wait times
- Complete error stack traces
- Timing information for each operation
