"""
VADER-based emotion detector with lightweight keyword boosts.
Priority for negative text leftover:
  fear > sadness > anger (fallback).
"""

import math
import re
from typing import Dict
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_ANALYZER = SentimentIntensityAnalyzer()
TARGETS = ["anger", "disgust", "fear", "joy", "sadness"]

# Compact keyword sets (still offline & tiny)
FEAR_RX = re.compile(
    r"\b(worry|worried|afraid|scared|fear|fearful|anxious|anxiety|nervous|panic|panicking|tense|tensed|stress|stressed|overwhelm|overwhelmed)\b",
    re.I,
)
SAD_RX = re.compile(
    r"\b(sad|down|unhappy|depress|depressed|miserable|heartbroken|lonely|gloomy|blue|tired|exhausted|burnt\s*out|burned\s*out)\b",
    re.I,
)

def _empty() -> Dict[str, float]:
    return {k: None for k in TARGETS} | {"dominant_emotion": None}

def _normalize(scores: Dict[str, float]) -> Dict[str, float]:
    total = sum(scores.values())
    if total <= 0:
        return _empty()
    norm = {k: scores[k] / total for k in TARGETS}
    dom = max(norm, key=norm.get)
    return norm | {"dominant_emotion": dom}

def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))

def _style_signals(text: str) -> Dict[str, float]:
    """No lexicon here: just punctuation/casing/elongations."""
    excls = text.count("!")
    ques  = text.count("?")

    # ALL-CAPS token ratio
    tokens = re.findall(r"[A-Za-z]+", text)
    caps_tokens = sum(
        1 for t in tokens if len(t) >= 2 and sum(ch.isupper() for ch in t) / len(t) >= 0.8
    )
    caps_ratio = (caps_tokens / len(tokens)) if tokens else 0.0

    elong = 1 if re.search(r"(.)\1{2,}", text) else 0

    anger_signal = _sigmoid(0.8 * excls + 3.0 * caps_ratio + 0.8 * elong - 1.0)
    fear_signal  = _sigmoid(0.9 * ques - 0.5 * caps_ratio - 0.2)   # yelling reduces fear
    disgust_base = 0.10  # tiny constant without word cues

    return {"anger": anger_signal, "fear": fear_signal, "disgust": disgust_base}

def emotion_detector(text_to_analyze: str) -> Dict[str, float]:
    text = (text_to_analyze or "").strip()
    if not text:
        return _empty()

    vs = _ANALYZER.polarity_scores(text)
    pos, neg, comp = vs["pos"], vs["neg"], vs["compound"]

    # Essentially neutral → None's so UI shows "Invalid text!"
    if -0.05 < comp < 0.05 and max(pos, neg) < 0.05:
        return _empty()

    sig = _style_signals(text)
    scores = {k: 0.0 for k in TARGETS}

    if comp >= 0.05:
        # Positive → joy dominates with tiny leakage
        joy = pos if pos > 0 else max(0.01, 0.05 + comp * 0.5)
        scores["joy"] = joy
        leak = 0.15 * joy
        scores["anger"]   += leak * sig["anger"]
        scores["fear"]    += leak * sig["fear"]
        scores["disgust"] += leak * 0.10
        scores["sadness"] += max(leak - (scores["anger"] + scores["fear"] + scores["disgust"]), 0.0)
    else:
        # Negative → distribute by signals, then route leftover by priority
        base_neg   = neg if neg > 0 else max(0.05, -comp * 0.4)
        anger_part = base_neg * 0.40 * sig["anger"]
        fear_part  = base_neg * 0.35 * sig["fear"]
        disgust    = base_neg * sig["disgust"]
        assigned   = anger_part + fear_part + disgust
        leftover   = max(base_neg - assigned, 0.0)

        # PRIORITY routing of leftover:
        if FEAR_RX.search(text):
            fear_part += leftover
        elif SAD_RX.search(text):
            scores["sadness"] += leftover
        else:
            anger_part += leftover  # fallback

        scores["anger"]   = anger_part
        scores["fear"]    = fear_part
        scores["disgust"] = disgust
        # sadness may have received leftover via SAD_RX; otherwise 0
        scores["joy"]     = max(0.0, pos * 0.1)  # tiny residual if mixed

    return _normalize(scores)

if __name__ == "__main__":
    tests = [
        "I am feeling tensed about work.",
        "I am extremely worried.",
        "I am infuriated about the situation.",
        "This is UNACCEPTABLE!!!",
        "Are we in danger??",
        "I feel sad and down.",
        "I am very happy today!",
    ]
    for t in tests:
        print(t, "->", emotion_detector(t))
