"""
Flask server for the offline Emotion Detection app (VADER backend).
"""

from flask import Flask, request, render_template
from EmotionDetection import emotion_detector

app = Flask(__name__)


def format_response(result: dict) -> str:
    return (
        "For the given statement, the system response is "
        f"'anger': {result.get('anger', 0)}, "
        f"'disgust': {result.get('disgust', 0)}, "
        f"'fear': {result.get('fear', 0)}, "
        f"'joy': {result.get('joy', 0)} and "
        f"'sadness': {result.get('sadness', 0)}. "
        f"The dominant emotion is {result.get('dominant_emotion')}."
    )


@app.route("/", methods=["GET"])
def home() -> str:
    return render_template("index.html")


@app.route("/emotionDetector", methods=["GET", "POST"])
def emotion_detector_route() -> str:
    text = (request.values.get("textToAnalyze") or "").strip()
    result = emotion_detector(text)
    if result["dominant_emotion"] is None:
        return "Invalid text! Please try again!"
    return format_response(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
