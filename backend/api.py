import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "prophet_model"))

from flask import Flask, jsonify, request
from flask_cors import CORS
from database import (
    init_db, search_products, get_price_history,
    get_tracked_products, save_search, subscribe_alert
)
from compareprice import compare_prices
from rag_chatbot import chat_with_rag, reindex_products
from recommendations import get_recommendations
from model import run_prediction
from dotenv import load_dotenv
import requests as http_requests
import tempfile

load_dotenv()
init_db()

app = Flask(__name__)
CORS(app, origins="*")

# URL du HuggingFace Space pour le skin analyzer
SKIN_ANALYZER_URL = os.getenv("SKIN_ANALYZER_URL", "")

# Skin analyzer local (fallback si pas de HF Space configuré)
_skin_analyzer = None
def get_skin_analyzer():
    global _skin_analyzer
    if _skin_analyzer is None:
        from skin_analyzer import SkinAnalyzer
        _skin_analyzer = SkinAnalyzer("skin_issues_best.pth")
    return _skin_analyzer


# ──────────────────────────────────────────────────────────────
# Health check — requis par Render
# ──────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# ──────────────────────────────────────────────────────────────
# Produits
# ──────────────────────────────────────────────────────────────

@app.route("/products/compare", methods=["GET"])
def compare():
    query      = request.args.get("q", "")
    session_id = request.args.get("session_id", "anonymous")
    if not query:
        return jsonify([])
    save_search(session_id, query)
    return jsonify(compare_prices(query))


@app.route("/products/search", methods=["GET"])
def search():
    query = request.args.get("q", "")
    if not query:
        return jsonify([])
    return jsonify(search_products(query))


@app.route("/products/history", methods=["GET"])
def history():
    title  = request.args.get("title", "")
    source = request.args.get("source", "")
    if not title or not source:
        return jsonify([])
    return jsonify(get_price_history(title, source))


@app.route("/products/tracked", methods=["GET"])
def tracked():
    return jsonify(get_tracked_products())


# ──────────────────────────────────────────────────────────────
# Recommandations
# ──────────────────────────────────────────────────────────────

@app.route("/products/recommendations", methods=["GET"])
def recommendations():
    query = request.args.get("q", "").strip().lower()
    n     = int(request.args.get("n", 3))
    if not query:
        return jsonify([])
    return jsonify(get_recommendations(query, n=n))


# ──────────────────────────────────────────────────────────────
# Prédiction Prophet
# ──────────────────────────────────────────────────────────────

@app.route("/products/predict", methods=["GET"])
def predict_price():
    title  = request.args.get("title", "")
    source = request.args.get("source", "")
    days   = int(request.args.get("days", 7))
    if not title or not source:
        return jsonify({"error": "title et source requis"}), 400

    from database import get_connection
    conn = get_connection()
    try:
        df, forecast, decision = run_prediction(conn, title, source, days=days)
    finally:
        conn.close()

    if df is None:
        return jsonify({"decision": decision, "current_price": None,
                        "predicted_price": None, "forecast": []})

    current_price   = round(float(df["y"].iloc[-1]), 3)
    predicted_price = round(float(forecast["yhat"].iloc[-1]), 3)
    forecast_series = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(days).copy()
    forecast_series["ds"] = forecast_series["ds"].dt.strftime("%Y-%m-%d")

    return jsonify({
        "decision":        decision,
        "current_price":   current_price,
        "predicted_price": predicted_price,
        "forecast":        forecast_series.to_dict(orient="records"),
    })


# ──────────────────────────────────────────────────────────────
# Alertes
# ──────────────────────────────────────────────────────────────

@app.route("/api/alerts/subscribe", methods=["POST"])
def subscribe():
    data       = request.get_json()
    email      = data.get("email", "").strip()
    product_id = data.get("product_id")
    threshold  = float(data.get("threshold", 5.0))
    if not email or not product_id:
        return jsonify({"error": "email et product_id requis"}), 400
    try:
        subscribe_alert(email, int(product_id), threshold)
        return jsonify({"status": "ok", "message": f"Alerte créée pour {email}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────────────────────
# Chatbot RAG
# ──────────────────────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    msg  = data.get("message", "")
    if not msg:
        return jsonify({"reply": "Message vide"})
    return jsonify({"reply": chat_with_rag(msg)})


@app.route("/api/chat/reset", methods=["DELETE"])
def reset_chat():
    return jsonify({"status": "ok"})


@app.route("/api/rag/reindex", methods=["POST"])
def reindex():
    try:
        reindex_products()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────────────────────
# Skin analyzer — proxy vers HF Space ou local
# ──────────────────────────────────────────────────────────────

@app.route("/api/skin/analyze", methods=["POST"])
def analyze_skin():
    if "image" not in request.files:
        return jsonify({"error": "Aucune image reçue"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Fichier vide"}), 400

    # Si HF Space configuré → on proxy la requête
    if SKIN_ANALYZER_URL:
        try:
            resp = http_requests.post(
                f"{SKIN_ANALYZER_URL}/analyze",
                files={"image": (file.filename, file.read(), file.content_type)},
                timeout=30,
            )
            return jsonify(resp.json())
        except Exception as e:
            return jsonify({"error": f"HF Space indisponible: {str(e)}"}), 500

    # Fallback local
    suffix = os.path.splitext(file.filename)[1] or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name
    try:
        result = get_skin_analyzer().predict(tmp_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    app.run(port=5000, debug=True)