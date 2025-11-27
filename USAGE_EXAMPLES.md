# Usage Examples

This document provides practical examples of using the Vendor Monitor script with different command-line options.

## Basic Examples

### 1. Default Behavior

Run with all defaults (files in script directory):

```bash
python vendor_monitor.py
```

**Result:**
- Reads: `vendors.csv` from current directory
- Writes: CSV reports to script directory
- Writes: Log file to script directory

### 2. Custom Input File

Use a different vendor list:

```bash
python vendor_monitor.py --input /data/enterprise_vendors.csv
```

Or with short form:

```bash
python vendor_monitor.py -i /data/enterprise_vendors.csv
```

### 3. Custom Output Directory

Store reports in a specific location:

```bash
python vendor_monitor.py --output /reports/vendor/daily
```

**Result:**
- Creates: `/reports/vendor/daily/vendorstockreport_112626.csv`
- Creates: `/reports/vendor/daily/vendorheadlinereport_112626.csv`

### 4. Custom Log Directory

Store logs separately from reports:

```bash
python vendor_monitor.py --log-path /var/log/vendor_monitor
```

**Result:**
- Creates: `/var/log/vendor_monitor/vendor_monitor_112626.log`

### 5. All Custom Paths

```bash
python vendor_monitor.py \
  --input /data/vendors/critical_vendors.csv \
  --output /reports/vendor/daily \
  --log-path /var/log/vendor_monitor
```

## Production Use Cases

### Scenario 1: Centralized Reporting

**Goal:** Store all reports in a central location, separate from code.

```bash
# Directory structure:
# /opt/vendorai/         - Script location
# /reports/vendor/       - Reports location
# /var/log/vendor/       - Logs location

python /opt/vendorai/vendor_monitor.py \
  --input /opt/vendorai/vendors.csv \
  --output /reports/vendor \
  --log-path /var/log/vendor
```

**Cron job:**
```bash
0 9 * * * export NEWSAPI_KEY='your_key' && \
  python /opt/vendorai/vendor_monitor.py \
    --output /reports/vendor \
    --log-path /var/log/vendor
```

### Scenario 2: Date-Organized Archives

**Goal:** Organize reports by year and month for easy archival.

```bash
#!/bin/bash
export NEWSAPI_KEY='your_key_here'

YEAR=$(date +%Y)
MONTH=$(date +%m)
OUTPUT_DIR="/reports/vendor/${YEAR}/${MONTH}"

python vendor_monitor.py \
  --output "$OUTPUT_DIR" \
  --log-path /var/log/vendor_monitor
```

**Result structure:**
```
/reports/vendor/
├── 2024/
│   ├── 11/
│   │   ├── vendorstockreport_112626.csv
│   │   ├── vendorheadlinereport_112626.csv
│   │   ├── vendorstockreport_112726.csv
│   │   └── vendorheadlinereport_112726.csv
│   └── 12/
│       ├── vendorstockreport_120126.csv
│       └── vendorheadlinereport_120126.csv
└── 2025/
    └── 01/
```

### Scenario 3: Multiple Vendor Groups

**Goal:** Monitor different vendor groups separately.

```bash
# Critical infrastructure vendors
python vendor_monitor.py \
  --input vendors_critical.csv \
  --output /reports/vendor/critical \
  --log-path /var/log/vendor/critical

# Secondary vendors
python vendor_monitor.py \
  --input vendors_secondary.csv \
  --output /reports/vendor/secondary \
  --log-path /var/log/vendor/secondary

# Development environment vendors
python vendor_monitor.py \
  --input vendors_dev.csv \
  --output /reports/vendor/dev \
  --log-path /var/log/vendor/dev
```

### Scenario 4: Development vs Production

**Goal:** Different configurations for different environments.

**Development:**
```bash
python vendor_monitor.py \
  --input test_vendors.csv \
  --output ./dev_reports \
  --log-path ./dev_logs
```

**Production:**
```bash
python vendor_monitor.py \
  --input /etc/vendorai/vendors.csv \
  --output /var/reports/vendor \
  --log-path /var/log/vendor_monitor
```

## Automation Examples

### Example 1: Daily Monitoring with Email Alerts

```bash
#!/bin/bash
# File: /opt/scripts/vendor_monitor_daily.sh

export NEWSAPI_KEY='your_key_here'

OUTPUT_DIR="/reports/vendor/$(date +%Y/%m)"
LOG_DIR="/var/log/vendor_monitor"

python /opt/vendorai/vendor_monitor.py \
  --output "$OUTPUT_DIR" \
  --log-path "$LOG_DIR"

# Check for errors and send email
if grep -q "ERROR" "$LOG_DIR/vendor_monitor_$(date +%m%d%y).log"; then
    echo "Errors detected in vendor monitoring" | \
        mail -s "Vendor Monitor Alert - $(date +%Y-%m-%d)" admin@company.com
fi
```

**Cron:**
```bash
0 9 * * * /opt/scripts/vendor_monitor_daily.sh
```

### Example 2: Weekly Report Compilation

```bash
#!/bin/bash
# File: /opt/scripts/weekly_vendor_report.sh

export NEWSAPI_KEY='your_key_here'

WEEK_DIR="/reports/vendor/weekly/$(date +%Y_week_%V)"

# Run daily and compile into weekly directory
python /opt/vendorai/vendor_monitor.py \
  --output "$WEEK_DIR" \
  --log-path /var/log/vendor_monitor

# At end of week, create summary (run this separately)
if [ $(date +%u) -eq 7 ]; then
    echo "Creating weekly summary..."
    # Add your summary script here
fi
```

### Example 3: Backup Integration

```bash
#!/bin/bash
# File: /opt/scripts/vendor_monitor_with_backup.sh

export NEWSAPI_KEY='your_key_here'

OUTPUT_DIR="/reports/vendor"
BACKUP_DIR="/backup/vendor_reports"
DATE_STAMP=$(date +%Y%m%d)

# Run monitoring
python /opt/vendorai/vendor_monitor.py \
  --output "$OUTPUT_DIR" \
  --log-path /var/log/vendor_monitor

# Backup reports
mkdir -p "$BACKUP_DIR/$DATE_STAMP"
cp "$OUTPUT_DIR"/*$(date +%m%d%y).csv "$BACKUP_DIR/$DATE_STAMP/"

# Sync to remote backup (optional)
# rsync -av "$BACKUP_DIR/$DATE_STAMP/" backup-server:/vendor_reports/
```

## Advanced Path Management

### Relative Paths

Use relative paths for development:

```bash
# From project directory
python vendor_monitor.py --output ./reports --log-path ./logs
```

### Absolute Paths

Use absolute paths for production:

```bash
python /opt/vendorai/vendor_monitor.py \
  --output /var/reports/vendor \
  --log-path /var/log/vendor
```

### Environment Variables

Store paths in environment variables:

```bash
export NEWSAPI_KEY='your_key_here'
export VENDOR_OUTPUT_DIR='/reports/vendor'
export VENDOR_LOG_DIR='/var/log/vendor_monitor'

python vendor_monitor.py \
  --output "$VENDOR_OUTPUT_DIR" \
  --log-path "$VENDOR_LOG_DIR"
```

### Configuration File (Shell Script)

```bash
#!/bin/bash
# File: vendor_monitor_config.sh

# API Configuration
export NEWSAPI_KEY='your_key_here'

# Path Configuration
export VENDOR_INPUT_FILE='/etc/vendorai/vendors.csv'
export VENDOR_OUTPUT_DIR='/var/reports/vendor'
export VENDOR_LOG_DIR='/var/log/vendor_monitor'

# Run with configuration
python /opt/vendorai/vendor_monitor.py \
  --input "$VENDOR_INPUT_FILE" \
  --output "$VENDOR_OUTPUT_DIR" \
  --log-path "$VENDOR_LOG_DIR"
```

## Troubleshooting Path Issues

### Check Current Paths

View help to see default paths:

```bash
python vendor_monitor.py --help
```

### Verify Directory Creation

The script automatically creates directories if they don't exist:

```bash
python vendor_monitor.py --output /new/path/to/reports
# Creates /new/path/to/reports if it doesn't exist
```

### Permission Issues

If you get permission errors:

```bash
# Create directory first with proper permissions
sudo mkdir -p /var/log/vendor_monitor
sudo chown $USER:$USER /var/log/vendor_monitor

# Then run script
python vendor_monitor.py --log-path /var/log/vendor_monitor
```

### Test Configuration

Test with temporary directories first:

```bash
python vendor_monitor.py \
  --output /tmp/vendor_test \
  --log-path /tmp/vendor_test
```

## Best Practices

1. **Use absolute paths in production** - Avoid issues with working directory
2. **Separate logs from reports** - Makes cleanup and archiving easier
3. **Use date-based directories** - Helps with long-term organization
4. **Test paths before automation** - Verify permissions and access
5. **Keep configuration in scripts** - Easier to maintain and update
6. **Document your directory structure** - Helps team understand setup
7. **Regular cleanup of old files** - Prevents disk space issues

## Help and Documentation

View all options:

```bash
python vendor_monitor.py --help
```

Check version and paths:

```bash
python vendor_monitor.py --help | head -20
```

See examples directly:

```bash
python vendor_monitor.py --help | grep -A 10 "Examples:"
```
