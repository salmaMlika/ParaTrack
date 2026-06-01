# backend/alerts.py
"""
Système d'alertes prix intelligent.
Pipeline : scrape → Isolation Forest détecte anomalies → Resend envoie email
Fallback : si < 5 points historique → seuil % simple
"""

import os
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
from sklearn.ensemble import IsolationForest
from database import get_connection, get_active_alerts, get_previous_price

load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL     = os.getenv("FROM_EMAIL", "alerts@paratrack.tn")


# ──────────────────────────────────────────────────────────────
# PARSING
# ──────────────────────────────────────────────────────────────

def parse_price(price_str: str) -> float:
    try:
        return float(
            price_str
            .replace("DT", "").replace("dt", "")
            .replace("\xa0", "").replace(" ", "")
            .replace(",", ".")
            .strip()
        )
    except Exception:
        return 0.0


# ──────────────────────────────────────────────────────────────
# ISOLATION FOREST
# ──────────────────────────────────────────────────────────────

def load_price_history(product_id: int) -> list:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT price FROM price_history
        WHERE product_id = %s
        ORDER BY scraped_at ASC
    """, (product_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [parse_price(r[0]) for r in rows if parse_price(r[0]) > 0]


def is_anomaly_low(prices: list, current_price: float) -> bool:
    """
    True si current_price est une anomalie basse selon Isolation Forest.
    contamination=0.1 : ~10% des prix attendus comme anomalies (promos, erreurs).
    Nécessite >= 5 points.
    """
    if len(prices) < 5:
        return False

    X      = np.array(prices).reshape(-1, 1)
    model  = IsolationForest(contamination=0.1, random_state=42, n_estimators=100)
    model.fit(X)

    pred   = model.predict([[current_price]])[0]
    median = float(np.median(prices))

    # Anomalie ET en dessous de la médiane = vraie bonne affaire
    return pred == -1 and current_price < median


# ──────────────────────────────────────────────────────────────
# EMAIL — Resend
# ──────────────────────────────────────────────────────────────

def send_alert_email(email: str, product_title: str, old_price: float,
                     new_price: float, source: str, link: str, is_anomaly: bool) -> bool:
    if not RESEND_API_KEY:
        print(f"  ⚠️  RESEND_API_KEY manquante — email non envoyé à {email}")
        return False

    try:
        import resend
        resend.api_key = RESEND_API_KEY

        saving     = old_price - new_price
        saving_pct = round((saving / old_price) * 100, 1)
        badge      = "🔥 Prix inhabituellement bas détecté" if is_anomaly else f"📉 Baisse de {saving_pct}%"

        html = f"""
        <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px 24px;background:#faf7f2;border-radius:16px;">
          <div style="text-align:center;margin-bottom:24px;">
            <span style="font-size:32px;">💊</span>
            <h1 style="font-family:serif;font-size:22px;color:#1a1a1a;margin:8px 0 4px;">ParaTrack</h1>
            <p style="color:#6b6b6b;font-size:13px;margin:0;">Alerte prix</p>
          </div>

          <div style="background:white;border-radius:12px;padding:20px;border:1.5px solid #e8e0d6;margin-bottom:16px;">
            <p style="font-size:13px;color:#6b6b6b;margin:0 0 8px;">{badge}</p>
            <h2 style="font-size:16px;font-weight:700;color:#1a1a1a;margin:0 0 16px;">{product_title}</h2>

            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="text-align:center;">
                  <p style="font-size:11px;color:#aaa;margin:0 0 4px;text-transform:uppercase;">Ancien prix</p>
                  <p style="font-size:18px;font-weight:700;color:#aaa;text-decoration:line-through;margin:0;">{old_price:.3f} DT</p>
                </td>
                <td style="text-align:center;font-size:20px;color:#aaa;">→</td>
                <td style="text-align:center;">
                  <p style="font-size:11px;color:#2d6a4f;margin:0 0 4px;text-transform:uppercase;">Nouveau prix</p>
                  <p style="font-size:24px;font-weight:700;color:#2d6a4f;margin:0;">{new_price:.3f} DT</p>
                </td>
              </tr>
            </table>

            <p style="text-align:center;margin:12px 0 0;font-size:13px;color:#e63946;font-weight:600;">
              Vous économisez {saving:.3f} DT ({saving_pct}%) chez {source}
            </p>
          </div>

          <div style="text-align:center;">
            <a href="{link}" style="display:inline-block;padding:12px 28px;background:#2d6a4f;color:white;border-radius:10px;text-decoration:none;font-weight:600;font-size:14px;">
              Voir le produit →
            </a>
          </div>

          <p style="text-align:center;font-size:11px;color:#bbb;margin-top:24px;">
            ParaTrack · Comparateur parapharmacie Tunisie
          </p>
        </div>
        """

        resend.Emails.send({
            "from":    FROM_EMAIL,
            "to":      [email],
            "subject": f"📉 {product_title} − {saving_pct}% chez {source}",
            "html":    html,
        })

        print(f"  ✅ Email → {email} | {product_title} | {old_price:.2f} → {new_price:.2f} DT")
        return True

    except Exception as e:
        print(f"  ❌ Erreur Resend: {e}")
        return False


# ──────────────────────────────────────────────────────────────
# PIPELINE — appelé par le cron
# ──────────────────────────────────────────────────────────────

def run_alerts():
    print(f"\n🔔 Alertes — {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}")

    alerts = get_active_alerts()
    if not alerts:
        print("  Aucun abonnement actif")
        return

    print(f"  {len(alerts)} abonnements à vérifier")
    sent = 0

    for alert in alerts:
        product_id = alert["product_id"]
        last_price = parse_price(alert["last_price"])

        prev = get_previous_price(product_id)
        if not prev:
            continue

        prev_price = parse_price(prev[0])
        if prev_price <= 0 or last_price <= 0:
            continue

        drop_pct = ((prev_price - last_price) / prev_price) * 100
        if drop_pct <= 0:
            continue

        history = load_price_history(product_id)
        anomaly = is_anomaly_low(history, last_price)

        if drop_pct >= alert["threshold"] or anomaly:
            print(f"  🎯 {alert['title'][:40]} | {prev_price:.2f}→{last_price:.2f} DT ({drop_pct:.1f}%) anomalie={anomaly}")

            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("SELECT link FROM products WHERE id = %s", (product_id,))
            row  = cur.fetchone()
            cur.close()
            conn.close()

            if send_alert_email(
                email=alert["email"],
                product_title=alert["title"],
                old_price=prev_price,
                new_price=last_price,
                source=alert["source"],
                link=row[0] if row else "",
                is_anomaly=anomaly,
            ):
                sent += 1
        else:
            print(f"  — {alert['title'][:35]} | {drop_pct:.1f}% < seuil {alert['threshold']}%")

    print(f"✅ {sent} alertes envoyées\n")


if __name__ == "__main__":
    run_alerts()