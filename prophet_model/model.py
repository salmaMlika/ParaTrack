import pandas as pd
from prophet import Prophet


# ──────────────────────────────────────────────────────────────
# LOAD
# ──────────────────────────────────────────────────────────────

def load_product_data(conn, title, source):
    # PostgreSQL utilise %s au lieu de ?
    query = """
        SELECT ph.scraped_at AS ds, ph.price AS y
        FROM price_history ph
        JOIN products p ON p.id = ph.product_id
        WHERE p.title = %s AND p.source = %s
        ORDER BY ph.scraped_at ASC
    """
    
    try:
        df = pd.read_sql(query, conn, params=(title, source))

        if df.empty:
            return None

        df["ds"] = pd.to_datetime(df["ds"])

        # Nettoie le format "45.300 DT" → 45.3
        df["y"] = (
            df["y"].astype(str)
            .str.replace("DT", "", regex=False)
            .str.replace("\xa0", "", regex=False)   # espace insécable
            .str.replace(",", ".", regex=False)
            .str.strip()
        )
        df["y"] = pd.to_numeric(df["y"], errors="coerce")
        df = df.dropna()

        return df if not df.empty else None
    
    except Exception as e:
        print(f"Erreur lors du chargement des données: {e}")
        return None


# ──────────────────────────────────────────────────────────────
# TRAIN
# ──────────────────────────────────────────────────────────────

def train_model(df):
    model = Prophet(
        daily_seasonality=False,
        weekly_seasonality=False,
        yearly_seasonality=False,
        changepoint_prior_scale=0.05,   # peu de volatilité attendue sur les prix para
    )
    model.fit(df)
    return model


# ──────────────────────────────────────────────────────────────
# PREDICT
# ──────────────────────────────────────────────────────────────

def predict(model, days=7):
    future   = model.make_future_dataframe(periods=days)
    forecast = model.predict(future)
    return forecast


# ──────────────────────────────────────────────────────────────
# DECISION
# ──────────────────────────────────────────────────────────────

def get_decision(df, forecast):
    current_price = df["y"].iloc[-1]
    predicted_price = forecast["yhat"].iloc[-1]
    
    delta_pct = ((predicted_price - current_price) / current_price) * 100
    
    if delta_pct < -2:  # Prix prédit plus bas → baisse à venir
        return f"🔴 Attendre encore — prix prévu en baisse de {abs(delta_pct):.1f}%"
    elif delta_pct > 2:  # Prix prédit plus haut → hausse à venir
        return f"🟢 Acheter maintenant — prix prévu en hausse de {delta_pct:.1f}%"
    else:
        return "🟡 Prix stable — achetez quand vous voulez"


# ──────────────────────────────────────────────────────────────
# PIPELINE
# ──────────────────────────────────────────────────────────────

def run_prediction(conn, title, source, days=7):
    """
    Retourne (df, forecast, decision) ou (None, None, message_erreur).
    Nécessite au moins 5 points de données historiques.
    """
    df = load_product_data(conn, title, source)

    if df is None or len(df) < 5:
        return None, None, "Pas assez de données (minimum 5 relevés de prix requis)"

    model    = train_model(df)
    forecast = predict(model, days=days)
    decision = get_decision(df, forecast)

    return df, forecast, decision
