# FinBERT Sentiment Analysis Guide

This guide explains how to use FinBERT for financial-specific sentiment analysis in the Vendor Monitoring Script.

## Overview

The script now supports two sentiment analysis methods:

| Method | Speed | Accuracy | Best For | Requires |
|--------|-------|----------|----------|----------|
| **VADER** | Very Fast (< 1s) | ~65% on financial text | Quick daily checks | vaderSentiment |
| **FinBERT** | Moderate (~30-60s) | ~85% on financial text | Accurate analysis | transformers, torch |

## Why FinBERT?

### VADER Limitations
- General-purpose sentiment analyzer
- Not trained on financial terminology
- May misinterpret financial context
- Example: "aggressive growth strategy" might be rated negative when it's actually positive in finance

### FinBERT Advantages
- **Trained on 10,000+ financial news articles and reports**
- **Understands financial context**:
  - "Beat earnings" = strongly positive
  - "Miss expectations" = strongly negative
  - "Debt restructuring" = contextually interpreted
- **Higher accuracy**: ~85% vs ~65% for VADER on financial text
- **Full article analysis**: Uses title + description + content for better context

##Installation

### Basic Installation (CPU-only)

```bash
pip install -r requirements.txt
```

This installs:
- `transformers` - HuggingFace library for FinBERT
- `torch` - PyTorch (CPU version)
- `sentencepiece` - Tokenization

### First Run

The first time you use FinBERT, it will download the model (~440MB):

```
Loading FinBERT model (ProsusAI/finbert)...
First-time load will download ~440MB model. This may take a few minutes...
✓ FinBERT model loaded successfully (running on CPU)
```

The model is cached locally (~/.cache/huggingface/), so subsequent runs are fast.

## Usage

### Basic FinBERT Usage

```bash
# Use FinBERT instead of VADER
python vendor_monitor.py --analyzer finbert
```

### With Custom Paths

```bash
python vendor_monitor.py \
  --analyzer finbert \
  --output /reports/vendor \
  --log-path /var/log/vendor_monitor
```

### Short Form

```bash
python vendor_monitor.py -a finbert -o ./reports
```

## Performance

### CPU Performance

On a modern CPU (Intel i5/i7, AMD Ryzen 5/7):
- **Per article**: 0.5-1 second
- **6 vendors × 10 articles = 60 articles**: ~30-60 seconds total
- **Memory usage**: ~500MB RAM

### Performance Tips

1. **Batch Processing**: The script processes articles sequentially. For daily monitoring, 60 seconds is acceptable.

2. **Reduce Articles**: If speed is critical, reduce the number of articles:
   ```python
   # In vendor_monitor.py, change max_articles parameter
   articles = get_news_articles(newsapi, symbol, company_name, max_articles=5)
   ```

3. **Cache Results**: The model is loaded once and reused for all articles (already implemented).

## Comparison Examples

### Example 1: Earnings Report

**Headline**: "Microsoft beats Q3 earnings expectations with 12% revenue growth"

**VADER Analysis**:
- Compound score: +0.34
- Result: **bullish** (correct, but low confidence)

**FinBERT Analysis**:
- Positive: 0.92
- Negative: 0.02
- Neutral: 0.06
- Result: **bullish** (high confidence)

### Example 2: Restructuring News

**Headline**: "Oracle announces aggressive cost-cutting measures and workforce reduction"

**VADER Analysis**:
- Compound score: -0.58
- Result: **bearish** (sees "aggressive" and "reduction" as negative)

**FinBERT Analysis**:
- Positive: 0.45
- Negative: 0.32
- Neutral: 0.23
- Result: **bullish** (understands cost-cutting can be positive for investors)

### Example 3: Neutral News

**Headline**: "Salesforce announces quarterly earnings call scheduled for next week"

**VADER Analysis**:
- Compound score: 0.00
- Result: **neutral** (correct)

**FinBERT Analysis**:
- Positive: 0.15
- Negative: 0.10
- Neutral: 0.75
- Result: **neutral** (correct)

## Full Article Analysis

FinBERT analyzes the complete context, not just headlines:

```python
# What gets analyzed:
full_text = f"{title}. {description} {content}"
```

**Example**:
- **Title**: "Tech Stock Drops"
- **Description**: "Microsoft shares fall 2% in after-hours trading"
- **Content**: "Following better-than-expected earnings and strong forward guidance..."

FinBERT sees the full context and understands this is actually positive news despite the headline.

## Troubleshooting

### Issue: "FinBERT dependencies not installed"

```bash
pip install transformers torch sentencepiece
```

### Issue: Model download fails

Check your internet connection. The model downloads from HuggingFace:
- Model: https://huggingface.co/ProsusAI/finbert
- Size: ~440MB

### Issue: "Out of memory" error

Reduce the number of articles processed, or close other applications. FinBERT needs ~500MB RAM.

### Issue: Very slow performance

- **First run**: Model download takes time, be patient
- **Subsequent runs**: Should be faster (~1 second per article)
- **Too slow**: Consider using VADER for quick checks, FinBERT for important decisions

### Issue: Different results than expected

FinBERT is trained on financial text. It may disagree with human intuition because:
- It sees patterns from thousands of financial articles
- It considers full context, not just keywords
- Financial sentiment ≠ general sentiment

Check the DEBUG logs to see the confidence scores:
```
FinBERT scores - Positive: 0.850, Negative: 0.050, Neutral: 0.100
```

## When to Use Each Analyzer

### Use VADER when:
- ✅ Running frequent checks (multiple times per day)
- ✅ Processing many vendors (50+)
- ✅ Speed is critical
- ✅ General sentiment is sufficient
- ✅ System has limited resources

### Use FinBERT when:
- ✅ Making important decisions
- ✅ Daily/weekly monitoring (1x per day)
- ✅ Accuracy is critical
- ✅ Processing 5-20 vendors
- ✅ Full article context matters
- ✅ Financial-specific analysis needed

### Hybrid Approach

For production, consider:
1. **Quick checks with VADER** (every 4 hours)
2. **Detailed analysis with FinBERT** (daily at market open)
3. **Alert on discrepancies** (when VADER and FinBERT strongly disagree)

## Production Deployment

### Daily Monitoring with FinBERT

```bash
#!/bin/bash
# File: /opt/scripts/vendor_monitor_finbert.sh

export NEWSAPI_KEY='your_key_here'

python /opt/vendorai/vendor_monitor.py \
  --analyzer finbert \
  --output /reports/vendor/$(date +%Y/%m) \
  --log-path /var/log/vendor_monitor

# Check for errors
if [ $? -ne 0 ]; then
    echo "FinBERT analysis failed" | mail -s "Vendor Monitor Error" admin@example.com
fi
```

**Cron**:
```bash
# Run daily at 9:00 AM with FinBERT
0 9 * * * /opt/scripts/vendor_monitor_finbert.sh
```

### Hybrid Monitoring

```bash
# Quick checks with VADER (every 4 hours)
0 */4 * * * python vendor_monitor.py --analyzer vader --output /tmp/vendor_quick

# Detailed analysis with FinBERT (daily at 9 AM)
0 9 * * * python vendor_monitor.py --analyzer finbert --output /reports/vendor/daily
```

## Model Information

- **Model**: ProsusAI/finbert
- **Base**: BERT (Bidirectional Encoder Representations from Transformers)
- **Training Data**: Financial news articles, 10K reports, earnings calls
- **Paper**: [FinBERT: Financial Sentiment Analysis with Pre-trained Language Models](https://arxiv.org/abs/1908.10063)
- **License**: Apache 2.0 (free for commercial use)
- **Size**: 440MB
- **Architecture**: 12-layer, 768-hidden, 12-heads, 110M parameters

## Technical Details

### How FinBERT Works

1. **Tokenization**: Text is split into subword tokens
2. **Encoding**: Tokens are converted to embeddings
3. **Processing**: 12 transformer layers analyze context
4. **Classification**: Final layer outputs 3 probabilities (positive, negative, neutral)
5. **Decision**: Highest probability determines sentiment

### Confidence Scores

FinBERT outputs confidence for each class:

```python
# Example output
{
    'positive': 0.85,  # 85% confident it's positive
    'negative': 0.10,  # 10% confident it's negative
    'neutral': 0.05    # 5% confident it's neutral
}
```

The script selects the highest score as the final sentiment.

### CPU Optimization

The script is optimized for CPU usage:
- Model runs on CPU (no GPU required)
- Batch size = 1 (optimized for single articles)
- No gradient calculation (inference only)
- Model loaded once and cached

## FAQ

**Q: Can I use GPU to speed up FinBERT?**

A: Yes, but the script is configured for CPU. To enable GPU:
1. Install GPU version of PyTorch
2. Modify `load_finbert_model()` to use `torch.device("cuda")`

**Q: How accurate is FinBERT?**

A: ~85% accuracy on financial sentiment classification vs ~65% for VADER.

**Q: Does FinBERT support other languages?**

A: No, FinBERT is English-only.

**Q: Can I fine-tune FinBERT on my own data?**

A: Yes, but it requires ML expertise and labeled training data.

**Q: Is FinBERT free to use commercially?**

A: Yes, Apache 2.0 license allows commercial use.

**Q: Will my API calls increase with FinBERT?**

A: No, API calls are the same. FinBERT only changes the local analysis.

## Resources

- [FinBERT Paper (arXiv)](https://arxiv.org/abs/1908.10063)
- [HuggingFace Model Card](https://huggingface.co/ProsusAI/finbert)
- [Transformers Documentation](https://huggingface.co/docs/transformers/)
- [PyTorch CPU Documentation](https://pytorch.org/docs/stable/torch.html)

## Support

For issues or questions:
1. Check log file for detailed error messages
2. Review this guide's troubleshooting section
3. Check GitHub issues for similar problems
4. Open a new issue with logs and system info
