#!/usr/bin/env python3
"""Test VADER sentiment on FISV headlines"""
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

headlines = [
    "Cramer's Lighting Round: Don't buy Fiserv",
    "Fiserv's lone bear sounded alarm long before stock's plunge",
    "Fiserv attracted hot money ahead of 44% stock-price nosedive",
    "Fiserv stock craters 44%, on pace for worst day ever after company slashes guidance"
]

print("VADER Sentiment Analysis for FISV Headlines:\n")
sentiments = []

for headline in headlines:
    scores = analyzer.polarity_scores(headline)
    compound = scores['compound']

    if compound >= 0.05:
        sentiment = 'BULLISH'
    elif compound <= -0.05:
        sentiment = 'BEARISH'
    else:
        sentiment = 'NEUTRAL'

    sentiments.append(sentiment.lower())
    print(f'{sentiment}: {headline}')
    print(f'  Compound: {compound:.3f}\n')

print(f"Sentiments: {sentiments}")
print(f"Bullish: {sentiments.count('bullish')}, Bearish: {sentiments.count('bearish')}, Neutral: {sentiments.count('neutral')}")
