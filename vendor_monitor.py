#!/usr/bin/env python3
"""
Vendor Stock and News Monitoring Script
Monitors public companies providing critical vendor services
"""

import csv
import sys
import os
import time
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import yfinance as yf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from newsapi import NewsApiClient
from newsapi.newsapi_exception import NewsAPIException

# Optional FinBERT imports (for financial sentiment analysis)
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    FINBERT_AVAILABLE = True
except ImportError:
    FINBERT_AVAILABLE = False

# Global logger instance
logger = None

# Global FinBERT model cache
finbert_model = None
finbert_tokenizer = None

# Configure logging
def setup_logging(log_path: Optional[str] = None) -> logging.Logger:
    """
    Configure logging for both console and file output

    Args:
        log_path: Directory path for log file. Defaults to script directory.

    Returns:
        Configured logger instance
    """
    date_suffix = datetime.now().strftime("%m%d%y")

    # Determine log file location
    if log_path:
        log_dir = Path(log_path)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"vendor_monitor_{date_suffix}.log"
    else:
        # Default to script directory
        script_dir = Path(__file__).parent
        log_file = script_dir / f"vendor_monitor_{date_suffix}.log"

    # Create logger
    log = logging.getLogger('VendorMonitor')
    log.setLevel(logging.DEBUG)

    # Remove existing handlers
    log.handlers = []

    # File handler - detailed logs
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(funcName)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    # Console handler - info and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)

    log.addHandler(file_handler)
    log.addHandler(console_handler)

    log.info(f"Log file: {log_file}")

    return log


def get_date_suffix() -> str:
    """Generate date suffix in mmddyy format"""
    return datetime.now().strftime("%m%d%y")


def load_finbert_model():
    """
    Lazy load FinBERT model and tokenizer (CPU-compatible)

    Returns:
        Tuple of (model, tokenizer) or (None, None) if unavailable
    """
    global finbert_model, finbert_tokenizer

    if finbert_model is not None and finbert_tokenizer is not None:
        return finbert_model, finbert_tokenizer

    if not FINBERT_AVAILABLE:
        logger.error("FinBERT dependencies not installed. Install with: pip install transformers torch")
        return None, None

    try:
        logger.info("Loading FinBERT model (ProsusAI/finbert)...")
        logger.info("First-time load will download ~440MB model. This may take a few minutes...")

        # Load model and tokenizer from HuggingFace
        finbert_tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        finbert_model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")

        # Set to eval mode and ensure CPU usage
        finbert_model.eval()
        device = torch.device("cpu")
        finbert_model.to(device)

        logger.info("✓ FinBERT model loaded successfully (running on CPU)")
        return finbert_model, finbert_tokenizer

    except Exception as e:
        logger.error(f"Failed to load FinBERT model: {e}")
        return None, None


def analyze_sentiment_finbert(text: str) -> str:
    """
    Analyze sentiment using FinBERT (financial domain-specific model)

    Args:
        text: Text to analyze (headline or article content)

    Returns:
        'bullish', 'bearish', or 'neutral'
    """
    if not text or text == "N/A":
        return "N/A"

    try:
        model, tokenizer = load_finbert_model()

        if model is None or tokenizer is None:
            logger.warning("FinBERT not available, falling back to neutral")
            return "neutral"

        # Tokenize and prepare input
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)

        # Run inference (no gradient calculation needed)
        with torch.no_grad():
            outputs = model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)

        # FinBERT outputs: [positive, negative, neutral]
        positive_score = predictions[0][0].item()
        negative_score = predictions[0][1].item()
        neutral_score = predictions[0][2].item()

        # Log scores for debugging
        logger.debug(f"FinBERT scores - Positive: {positive_score:.3f}, Negative: {negative_score:.3f}, Neutral: {neutral_score:.3f}")

        # Determine sentiment based on highest score
        max_score = max(positive_score, negative_score, neutral_score)

        if positive_score == max_score:
            return "bullish"
        elif negative_score == max_score:
            return "bearish"
        else:
            return "neutral"

    except Exception as e:
        logger.warning(f"Error analyzing sentiment with FinBERT: {e}")
        return "neutral"


def analyze_sentiment_vader(text: str, analyzer: SentimentIntensityAnalyzer) -> str:
    """
    Analyze sentiment of text using VADER sentiment analyzer

    Args:
        text: Text to analyze
        analyzer: VADER sentiment analyzer instance

    Returns:
        'bullish', 'bearish', or 'neutral'
    """
    if not text or text == "N/A":
        return "N/A"

    try:
        scores = analyzer.polarity_scores(text)
        compound = scores['compound']

        # Thresholds for sentiment classification
        if compound >= 0.05:
            return "bullish"
        elif compound <= -0.05:
            return "bearish"
        else:
            return "neutral"
    except Exception as e:
        logger.warning(f"Error analyzing sentiment for text: {e}")
        return "neutral"


def get_stock_data(symbol: str, max_retries: int = 3) -> Tuple[float, float, int]:
    """
    Fetch stock data for a given symbol with retry logic

    Args:
        symbol: Stock ticker symbol
        max_retries: Maximum number of retry attempts

    Returns:
        Tuple of (close_price, pct_change, volume)
    """
    for attempt in range(max_retries):
        try:
            logger.debug(f"Fetching stock data for {symbol} (attempt {attempt + 1}/{max_retries})")

            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")

            if hist.empty or len(hist) < 1:
                logger.warning(f"No stock data available for {symbol}")
                return (0.0, 0.0, 0)

            # Get the most recent trading day
            latest = hist.iloc[-1]
            close_price = round(latest['Close'], 2)
            volume = int(latest['Volume'])

            # Calculate percent change
            if len(hist) >= 2:
                prev_close = hist.iloc[-2]['Close']
                pct_change = round(((close_price - prev_close) / prev_close) * 100, 2)
            else:
                pct_change = 0.0
                logger.debug(f"Only one day of data available for {symbol}, using 0% change")

            logger.debug(f"Successfully fetched stock data for {symbol}: ${close_price} ({pct_change:+.2f}%)")
            return (close_price, pct_change, volume)

        except KeyError as e:
            logger.error(f"Invalid data format for {symbol}: {e}")
            return (0.0, 0.0, 0)
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed for {symbol}: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.debug(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to fetch stock data for {symbol} after {max_retries} attempts")
                return (0.0, 0.0, 0)


def get_smart_search_queries(company_name: str, symbol: str) -> List[str]:
    """
    Generate multiple search query variations for better news matching

    Args:
        company_name: Full company name
        symbol: Stock ticker symbol

    Returns:
        List of search queries to try in order
    """
    queries = []

    if company_name:
        # Remove common corporate suffixes (check longer/more specific suffixes first)
        suffixes = [
            ' Holding Corporation', ' Holding Corp.',
            ' Corporation', ' Incorporated',
            ' Holdings', ' Company', ' Limited',
            ' Corp.', ' Corp',
            ' Inc.', ' Inc',
            ' Co.', ' Co',
            ' Ltd.', ' Ltd',
            ' L.L.C.', ' LLC', ' PLC', ' Group'
        ]

        short_name = company_name
        for suffix in suffixes:
            if short_name.endswith(suffix):
                short_name = short_name[:-len(suffix)].strip()
                break

        # Try short name first (e.g., "Paylocity" instead of "Paylocity Holding Corp.")
        if short_name != company_name:
            queries.append(short_name)

        # Then try full company name
        queries.append(company_name)

        # Try combining short name with ticker
        if short_name != company_name:
            queries.append(f"{short_name} {symbol}")

    # Finally try ticker alone
    queries.append(symbol)

    return queries


def get_news_articles(newsapi: NewsApiClient, symbol: str, company_name: str,
                      max_articles: int = 10, max_retries: int = 3) -> List[Dict[str, str]]:
    """
    Fetch news articles for a given symbol using NewsAPI with retry logic and smart search

    Args:
        newsapi: NewsAPI client instance
        symbol: Stock ticker symbol
        company_name: Company name for better search results
        max_articles: Maximum number of articles to retrieve
        max_retries: Maximum number of retry attempts

    Returns:
        List of article dictionaries with 'title', 'description', and 'content'
    """
    # Generate smart search queries
    search_queries = get_smart_search_queries(company_name, symbol)

    # Define US business news domains
    us_business_domains = (
        'wsj.com,cnbc.com,bloomberg.com,reuters.com,marketwatch.com,'
        'barrons.com,ft.com,businessinsider.com,seekingalpha.com,'
        'fool.com,investors.com,finance.yahoo.com'
    )

    # Try each query until we find articles
    for query_idx, query in enumerate(search_queries):
        logger.debug(f"Trying search query {query_idx + 1}/{len(search_queries)}: '{query}'")

        # Try with US business domains first, then fallback to broader search if needed
        for use_domains in [True, False]:
            if use_domains:
                logger.debug(f"Searching US business sources for: '{query}'")
            else:
                logger.debug(f"No results from US business sources, trying broader search for: '{query}'")

            for attempt in range(max_retries):
                try:
                    logger.debug(f"Fetching news for {symbol} (attempt {attempt + 1}/{max_retries}) with query: '{query}'")

                    # Get news - prefer US business sources, fallback to broader search
                    if use_domains:
                        response = newsapi.get_everything(
                            q=query,
                            domains=us_business_domains,
                            language='en',
                            sort_by='publishedAt',
                            page_size=max_articles
                        )
                    else:
                        response = newsapi.get_everything(
                            q=query,
                            language='en',
                            sort_by='publishedAt',
                            page_size=max_articles
                        )

                    if not response or response.get('status') != 'ok':
                        logger.warning(f"Invalid response from NewsAPI for {symbol} with query '{query}'")
                        break  # Try next attempt strategy

                    articles = response.get('articles', [])

                    if not articles:
                        logger.debug(f"No articles found with query '{query}'")
                        break  # Try next attempt strategy

                    # Found articles! Process them
                    article_list = []
                    for article in articles[:max_articles]:
                        title = article.get('title', '')
                        description = article.get('description', '')
                        content = article.get('content', '')

                        # Skip removed articles
                        if title and title != '[Removed]':
                            # Combine description and content for full text analysis
                            full_text = f"{title}. {description} {content}".strip()

                            article_list.append({
                                'title': title,
                                'description': description,
                                'content': content,
                                'full_text': full_text
                            })

                    if article_list:
                        source_type = "US business sources" if use_domains else "broader search"
                        logger.info(f"Successfully fetched {len(article_list)} articles for {symbol} using query '{query}' ({source_type})")
                        return article_list
                    else:
                        logger.debug(f"All articles were removed for query '{query}'")
                        break  # Try next attempt strategy

                except NewsAPIException as e:
                    if 'rateLimited' in str(e) or '429' in str(e):
                        logger.error(f"NewsAPI rate limit exceeded for {symbol}: {e}")
                        return []
                    elif 'apiKeyInvalid' in str(e) or '401' in str(e):
                        logger.error(f"Invalid NewsAPI key: {e}")
                        raise  # Re-raise to stop execution
                    else:
                        logger.warning(f"NewsAPI error for {symbol} with query '{query}' (attempt {attempt + 1}): {e}")
                        if attempt < max_retries - 1:
                            wait_time = 2 ** attempt
                            logger.debug(f"Retrying in {wait_time} seconds...")
                            time.sleep(wait_time)
                        else:
                            logger.debug(f"Failed query '{query}' after {max_retries} attempts")
                            break  # Try next attempt strategy

                except Exception as e:
                    logger.warning(f"Unexpected error fetching news for {symbol} with query '{query}' (attempt {attempt + 1}): {e}")
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.debug(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        logger.debug(f"Failed query '{query}' after {max_retries} attempts")
                        break  # Try next attempt strategy

    # If we exhausted all queries and found nothing
    logger.info(f"No news articles found for {symbol} after trying {len(search_queries)} different search queries")
    return []


def get_max_sentiment(sentiments: List[str]) -> str:
    """
    Determine the maximum (most positive) sentiment from a list

    Ranking: bullish > neutral > bearish

    Args:
        sentiments: List of sentiment strings

    Returns:
        Maximum sentiment value
    """
    if not sentiments or all(s == "N/A" for s in sentiments):
        return "N/A"

    # Filter out N/A values
    valid_sentiments = [s for s in sentiments if s != "N/A"]

    if not valid_sentiments:
        return "N/A"

    # Priority: bullish > neutral > bearish
    if "bullish" in valid_sentiments:
        return "bullish"
    elif "neutral" in valid_sentiments:
        return "neutral"
    else:
        return "bearish"


def process_vendors(input_file: str, output_path: Optional[str] = None, analyzer: str = 'vader') -> None:
    """
    Main processing function to monitor vendors with comprehensive error handling

    Args:
        input_file: Path to vendors.csv file
        output_path: Directory path for output CSV files. Defaults to script directory.
        analyzer: Sentiment analysis method ('vader' or 'finbert')
    """
    logger.info("="*60)
    logger.info("Vendor Stock and News Monitoring Script")
    logger.info("="*60)
    logger.info(f"Sentiment analyzer: {analyzer.upper()}")

    # Statistics tracking
    stats = {
        'total_vendors': 0,
        'stock_success': 0,
        'stock_failures': 0,
        'news_success': 0,
        'news_failures': 0,
        'total_headlines': 0,
        'errors': []
    }

    # Load NewsAPI key from environment variable
    newsapi_key = os.environ.get('NEWSAPI_KEY')
    if not newsapi_key:
        logger.error("NEWSAPI_KEY environment variable not set")
        logger.error("Please set your NewsAPI key: export NEWSAPI_KEY='your_key_here'")
        logger.error("Get a free API key at: https://newsapi.org/register")
        sys.exit(1)

    logger.info(f"Using NewsAPI key: {newsapi_key[:8]}...{newsapi_key[-4:]}")

    # Initialize NewsAPI client
    try:
        newsapi = NewsApiClient(api_key=newsapi_key)
        logger.info("Successfully initialized NewsAPI client")
    except Exception as e:
        logger.error(f"Failed to initialize NewsAPI client: {e}")
        sys.exit(1)

    # Determine output file location
    date_suffix = get_date_suffix()
    if output_path:
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        stock_report_file = output_dir / f"vendorstockreport_{date_suffix}.csv"
        headline_report_file = output_dir / f"vendorheadlinereport_{date_suffix}.csv"
    else:
        # Default to script directory
        script_dir = Path(__file__).parent
        stock_report_file = script_dir / f"vendorstockreport_{date_suffix}.csv"
        headline_report_file = script_dir / f"vendorheadlinereport_{date_suffix}.csv"

    logger.info(f"Output directory: {output_path if output_path else Path(__file__).parent}")
    logger.info(f"Output files: {stock_report_file.name}, {headline_report_file.name}")

    # Initialize sentiment analyzer based on choice
    vader_analyzer = None
    if analyzer == 'vader':
        try:
            vader_analyzer = SentimentIntensityAnalyzer()
            logger.info("✓ VADER sentiment analyzer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize VADER: {e}")
            sys.exit(1)
    elif analyzer == 'finbert':
        if not FINBERT_AVAILABLE:
            logger.error("FinBERT requested but dependencies not installed")
            logger.error("Install with: pip install transformers torch sentencepiece")
            sys.exit(1)
        # FinBERT will be lazy-loaded on first use
        logger.info("FinBERT will be loaded on first analysis (may take a few minutes)")

    # Storage for data
    stock_data = []
    headline_data = []

    # Read input file
    try:
        with open(input_file, 'r') as f:
            reader = csv.DictReader(f)
            vendors = list(reader)

        if not vendors:
            logger.error(f"Input file '{input_file}' is empty or has no valid data")
            sys.exit(1)

        stats['total_vendors'] = len(vendors)
        logger.info(f"Successfully loaded {len(vendors)} vendors from {input_file}")

    except FileNotFoundError:
        logger.error(f"Input file '{input_file}' not found")
        logger.error(f"Current directory: {os.getcwd()}")
        sys.exit(1)
    except csv.Error as e:
        logger.error(f"CSV parsing error in '{input_file}': {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error reading input file '{input_file}': {e}")
        sys.exit(1)

    # Process each vendor
    logger.info("\n" + "-"*60)
    logger.info("Processing vendors...")
    logger.info("-"*60)

    for idx, vendor in enumerate(vendors, 1):
        try:
            symbol = vendor.get('symbol', '').strip().upper()
            company_name = vendor.get('companyname', '').strip()

            if not symbol:
                logger.warning(f"Skipping row {idx}: missing symbol")
                continue

            logger.info(f"\n[{idx}/{len(vendors)}] Processing {symbol} - {company_name}")

            # Get stock data
            close_price, pct_change, volume = get_stock_data(symbol)

            if close_price > 0:
                stats['stock_success'] += 1
                logger.info(f"  Stock: ${close_price} ({pct_change:+.2f}%) Vol: {volume:,}")
            else:
                stats['stock_failures'] += 1
                stats['errors'].append(f"{symbol}: No stock data available")
                logger.warning(f"  Stock: No data available")

            # Get news articles
            articles = get_news_articles(newsapi, symbol, company_name)

            # Analyze sentiment for each article
            article_sentiments = []

            if articles:
                stats['news_success'] += 1
                stats['total_headlines'] += len(articles)
                logger.info(f"  News: Found {len(articles)} articles")

                for article in articles:
                    # Use full text for analysis (title + description + content)
                    text_to_analyze = article['full_text']

                    # Analyze using the selected method
                    if analyzer == 'vader':
                        sentiment = analyze_sentiment_vader(text_to_analyze, vader_analyzer)
                    elif analyzer == 'finbert':
                        sentiment = analyze_sentiment_finbert(text_to_analyze)
                    else:
                        sentiment = "neutral"

                    article_sentiments.append(sentiment)
                    headline_data.append({
                        'symbol': symbol,
                        'headline': article['title'],
                        'sentiment': sentiment
                    })

                    # Truncate headline for display
                    display_headline = article['title'][:75] + "..." if len(article['title']) > 75 else article['title']
                    logger.info(f"    [{sentiment.upper()}] {display_headline}")
            else:
                stats['news_failures'] += 1
                stats['errors'].append(f"{symbol}: No articles found")
                article_sentiments.append("N/A")
                headline_data.append({
                    'symbol': symbol,
                    'headline': 'N/A',
                    'sentiment': 'N/A'
                })
                logger.info(f"  News: No articles available")

            # Determine max sentiment for this symbol
            max_sentiment = get_max_sentiment(article_sentiments)

            # Store stock data
            stock_data.append({
                'symbol': symbol,
                'companyname': company_name,
                'closeprice': close_price,
                'pctchange': pct_change,
                'volume': volume,
                'sentiment': max_sentiment
            })

        except KeyError as e:
            logger.error(f"Missing required field in row {idx}: {e}")
            stats['errors'].append(f"Row {idx}: Missing field {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error processing vendor {idx}: {e}")
            stats['errors'].append(f"Row {idx}: Unexpected error - {e}")
            continue

    # Write stock report
    logger.info("\n" + "-"*60)
    logger.info("Writing reports...")
    logger.info("-"*60)

    try:
        with open(stock_report_file, 'w', newline='') as f:
            fieldnames = ['symbol', 'companyname', 'closeprice', 'pctchange', 'volume', 'sentiment']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(stock_data)
        logger.info(f"✓ Stock report written: {stock_report_file} ({len(stock_data)} rows)")
    except Exception as e:
        logger.error(f"Failed to write stock report: {e}")
        stats['errors'].append(f"Failed to write stock report: {e}")

    # Write headline report
    try:
        with open(headline_report_file, 'w', newline='') as f:
            fieldnames = ['symbol', 'headline', 'sentiment']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(headline_data)
        logger.info(f"✓ Headline report written: {headline_report_file} ({len(headline_data)} rows)")
    except Exception as e:
        logger.error(f"Failed to write headline report: {e}")
        stats['errors'].append(f"Failed to write headline report: {e}")

    # Print summary statistics
    logger.info("\n" + "="*60)
    logger.info("SUMMARY")
    logger.info("="*60)
    logger.info(f"Total vendors processed:  {stats['total_vendors']}")
    logger.info(f"Stock data success:       {stats['stock_success']}/{stats['total_vendors']}")
    logger.info(f"Stock data failures:      {stats['stock_failures']}/{stats['total_vendors']}")
    logger.info(f"News data success:        {stats['news_success']}/{stats['total_vendors']}")
    logger.info(f"News data failures:       {stats['news_failures']}/{stats['total_vendors']}")
    logger.info(f"Total headlines fetched:  {stats['total_headlines']}")

    if stats['errors']:
        logger.warning(f"\nWarnings/Errors: {len(stats['errors'])}")
        for error in stats['errors'][:5]:  # Show first 5 errors
            logger.warning(f"  - {error}")
        if len(stats['errors']) > 5:
            logger.warning(f"  ... and {len(stats['errors']) - 5} more (check log file)")

    logger.info("\n" + "="*60)
    logger.info("Processing complete!")
    logger.info(f"Log file: vendor_monitor_{date_suffix}.log")
    logger.info("="*60)


def parse_arguments():
    """Parse command-line arguments"""
    # Get script directory as default
    script_dir = Path(__file__).parent

    parser = argparse.ArgumentParser(
        description='Monitor vendor company stocks and news with sentiment analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with VADER (fast, default)
  python vendor_monitor.py

  # Use FinBERT for better financial sentiment analysis (CPU-compatible)
  python vendor_monitor.py --analyzer finbert

  # Custom input file
  python vendor_monitor.py --input custom_vendors.csv

  # Custom output directory
  python vendor_monitor.py --output /path/to/reports

  # FinBERT with custom paths
  python vendor_monitor.py --analyzer finbert --output ./reports --log-path ./logs

  # All options
  python vendor_monitor.py -i vendors.csv -o ./reports -l ./logs -a finbert
        """
    )

    parser.add_argument(
        '-i', '--input',
        default='vendors.csv',
        help='Input CSV file with vendor data (default: vendors.csv in current directory)'
    )

    parser.add_argument(
        '-o', '--output',
        default=None,
        help=f'Output directory for CSV reports (default: {script_dir})'
    )

    parser.add_argument(
        '-l', '--log-path',
        default=None,
        help=f'Directory for log files (default: {script_dir})'
    )

    parser.add_argument(
        '-a', '--analyzer',
        choices=['vader', 'finbert'],
        default='vader',
        help='Sentiment analysis method: "vader" (fast, general) or "finbert" (accurate, financial-specific, requires transformers) (default: vader)'
    )

    return parser.parse_args()


def main():
    """Main entry point"""
    global logger

    # Parse command-line arguments
    args = parse_arguments()

    # Initialize logging with custom path
    logger = setup_logging(args.log_path)

    try:
        process_vendors(args.input, args.output, args.analyzer)
    except KeyboardInterrupt:
        logger.warning("\n\nProcess interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n\nUnexpected fatal error: {e}")
        logger.debug("Stack trace:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
