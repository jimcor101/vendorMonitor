# Quick Start Guide

Get up and running in 5 minutes!

## Step 1: Get Your NewsAPI Key

1. Go to https://newsapi.org/register
2. Sign up for a free account
3. Copy your API key from the dashboard

## Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 3: Set Your API Key

**Mac/Linux:**
```bash
export NEWSAPI_KEY='paste_your_key_here'
```

**Windows (PowerShell):**
```powershell
$env:NEWSAPI_KEY='paste_your_key_here'
```

## Step 4: Run the Script

**Basic usage:**
```bash
python vendor_monitor.py
```

**With custom output directory:**
```bash
python vendor_monitor.py --output ./reports
```

**View all options:**
```bash
python vendor_monitor.py --help
```

### Command-Line Options

- `-i, --input FILE` - Input CSV file (default: vendors.csv)
- `-o, --output DIR` - Output directory for CSV reports (default: script directory)
- `-l, --log-path DIR` - Directory for log files (default: script directory)

## What You'll Get

Three files with today's date:
- `vendorstockreport_mmddyy.csv` - Stock prices and sentiment summary
- `vendorheadlinereport_mmddyy.csv` - Individual headlines with sentiment
- `vendor_monitor_mmddyy.log` - Detailed log file

## Example Output

```
Processing 5 vendors...

Processing MSFT - Microsoft Corporation...
  - Microsoft announces new AI features in Azure... [bullish]
  - Microsoft stock reaches new high on cloud growth... [bullish]
  - Tech giant expands data center operations... [neutral]

Processing ORCL - Oracle Corporation...
  - Oracle reports strong quarterly earnings... [bullish]
  - Database company sees increased cloud adoption... [bullish]

...

Writing stock report to vendorstockreport_112626.csv...
Writing headline report to vendorheadlinereport_112626.csv...

Processing complete!
```

## Customizing Your Vendor List

Edit `vendors.csv` to add or remove companies:

```csv
symbol,companyname
MSFT,Microsoft Corporation
ORCL,Oracle Corporation
CRM,Salesforce Inc
SNOW,Snowflake Inc
```

## Daily Automation

To run automatically every day, add a cron job (Mac/Linux):

```bash
0 9 * * * export NEWSAPI_KEY='your_key' && cd /path/to/vendorai && python vendor_monitor.py
```

This runs at 9 AM daily. Adjust the time as needed.

## Troubleshooting

**"NEWSAPI_KEY environment variable not set"**
- Make sure you ran the export command in the same terminal window
- For permanent setup, add the export to your ~/.bashrc or ~/.zshrc file

**"No headlines available"**
- The company name might be too generic. Try adjusting the company name in vendors.csv
- NewsAPI might not have recent news for smaller companies

**Rate limit errors**
- Free tier is 100 requests/day
- Each vendor uses 1 request
- If you have many vendors, consider spreading checks throughout the day

## Need Help?

Check the full README.md for more detailed documentation and troubleshooting tips.
