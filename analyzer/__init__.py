"""Analyzer package"""
from .classifier import classify_news, classify_news_batch
from .scorer import calculate_impact_score, score_news_batch, calculate_aggregate_scores
from .political_detector import detect_political_events, PoliticalEvent
