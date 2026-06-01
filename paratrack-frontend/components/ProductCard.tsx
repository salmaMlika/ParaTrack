"use client";
import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

// ──────────────────────────────────────────────────────────────
// Types
// ──────────────────────────────────────────────────────────────
interface Offer {
  source: string;
  price: string;
  price_val: number;
  link: string;
  image_url: string;
  stock: string;
}

interface Product {
  titleA?: string;
  name?: string;
  offers?: Offer[];
  min_price?: number;
  max_price?: number;
  saving_pct?: number;
  best_source?: string;
  image_url?: string;
  // legacy flat format
  source?: string;
  price_siteA?: string;
  link_siteA?: string;
  source_siteB?: string;
  price_siteB?: string;
  link_siteB?: string;
  similarity?: number;
  id?: number;
}

// ──────────────────────────────────────────────────────────────
// Prédiction Prophet
// ──────────────────────────────────────────────────────────────
function PricePredictionBadge({ title, source }: { title: string; source: string }) {
  const [pred, setPred]       = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [open, setOpen]       = useState(false);

  async function fetchPred() {
    if (pred || loading) { setOpen(o => !o); return; }
    setLoading(true);
    setOpen(true);
    try {
      const res  = await fetch(`${API}/products/predict?title=${encodeURIComponent(title)}&source=${encodeURIComponent(source)}`);
      setPred(await res.json());
    } catch {
      setPred({ decision: "❌ Serveur indisponible", current_price: null, predicted_price: null });
    } finally {
      setLoading(false);
    }
  }

  const isGood   = pred?.decision?.startsWith("🟢");
  const isWait   = pred?.decision?.startsWith("🔴");
  const noData   = pred?.decision?.startsWith("Pas assez");
  const bgColor  = isGood ? "#f0faf4" : isWait ? "#fff5f5" : "#faf7f2";
  const bdColor  = isGood ? "#b7e4c7" : isWait ? "#fecaca" : "#e8e0d6";
  const txtColor = isGood ? "#2d6a4f" : isWait ? "#e63946" : "#c9a84c";

  return (
    <div style={{ margin: "0 20px 6px" }}>
      <button
        onClick={fetchPred}
        style={{
          display: "flex", alignItems: "center", gap: 6, width: "100%",
          background: "none", border: "1.5px dashed #e8e0d6",
          borderRadius: 8, padding: "6px 12px", cursor: "pointer",
          fontSize: 12, color: "#6b6b6b", fontFamily: "inherit", transition: "all 0.18s",
        }}
        onMouseEnter={e => { e.currentTarget.style.borderColor = "#2d6a4f"; e.currentTarget.style.color = "#2d6a4f"; }}
        onMouseLeave={e => { e.currentTarget.style.borderColor = "#e8e0d6"; e.currentTarget.style.color = "#6b6b6b"; }}
      >
        <span>📈</span>
        <span style={{ fontWeight: 600 }}>Prédiction du prix sur 7 jours</span>
        <span style={{ marginLeft: "auto" }}>{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div style={{
          marginTop: 6, padding: "12px 14px",
          background: bgColor, border: `1.5px solid ${bdColor}`,
          borderRadius: 10, fontSize: 13,
        }}>
          {loading ? (
            <span style={{ color: "#aaa" }}>Analyse en cours…</span>
          ) : noData ? (
            <span style={{ color: "#aaa", fontSize: 12 }}>
              Pas encore assez d'historique — revenez dans quelques jours 📅
            </span>
          ) : pred ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <div style={{ fontWeight: 700, color: txtColor }}>{pred.decision}</div>
              {pred.current_price && pred.predicted_price && (
                <div style={{ display: "flex", gap: 16, fontSize: 12, color: "#6b6b6b" }}>
                  <span>Actuel : <b style={{ color: "#1a1a1a" }}>{pred.current_price} DT</b></span>
                  <span>Dans 7j : <b style={{ color: txtColor }}>{pred.predicted_price} DT</b></span>
                </div>
              )}
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}

// ──────────────────────────────────────────────────────────────
// Alerte prix
// ──────────────────────────────────────────────────────────────
function AlertSubscribe({ productId, title }: { productId: number; title: string }) {
  const [open, setOpen]       = useState(false);
  const [email, setEmail]     = useState("");
  const [threshold, setThreshold] = useState(5);
  const [status, setStatus]   = useState<"idle" | "loading" | "ok" | "error">("idle");

  async function subscribe() {
    if (!email.includes("@")) return;
    setStatus("loading");
    try {
      const res = await fetch(`${API}/api/alerts/subscribe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, product_id: productId, threshold }),
      });
      const data = await res.json();
      setStatus(data.status === "ok" ? "ok" : "error");
    } catch {
      setStatus("error");
    }
  }

  return (
    <div style={{ margin: "0 20px 14px" }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          display: "flex", alignItems: "center", gap: 6, width: "100%",
          background: "none", border: "1.5px dashed #e8e0d6",
          borderRadius: 8, padding: "6px 12px", cursor: "pointer",
          fontSize: 12, color: "#6b6b6b", fontFamily: "inherit", transition: "all 0.18s",
        }}
        onMouseEnter={e => { e.currentTarget.style.borderColor = "#c9a84c"; e.currentTarget.style.color = "#c9a84c"; }}
        onMouseLeave={e => { e.currentTarget.style.borderColor = "#e8e0d6"; e.currentTarget.style.color = "#6b6b6b"; }}
      >
        <span>🔔</span>
        <span style={{ fontWeight: 600 }}>M'alerter si le prix baisse</span>
        <span style={{ marginLeft: "auto" }}>{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div style={{
          marginTop: 6, padding: "14px",
          background: "#fffdf7", border: "1.5px solid #f0e8c8",
          borderRadius: 10,
        }}>
          {status === "ok" ? (
            <div style={{ color: "#2d6a4f", fontWeight: 600, fontSize: 13 }}>
              ✅ Alerte créée ! Vous serez notifié à {email}
            </div>
          ) : (
            <>
              <div style={{ fontSize: 12, color: "#6b6b6b", marginBottom: 10 }}>
                Recevez un email dès que le prix baisse de{" "}
                <select
                  value={threshold}
                  onChange={e => setThreshold(Number(e.target.value))}
                  style={{
                    border: "1.5px solid #e8e0d6", borderRadius: 6,
                    padding: "2px 6px", fontSize: 12, fontFamily: "inherit",
                    background: "white", cursor: "pointer",
                  }}
                >
                  <option value={3}>3%</option>
                  <option value={5}>5%</option>
                  <option value={10}>10%</option>
                  <option value={15}>15%</option>
                </select>
                {" "}ou plus
              </div>

              <div style={{ display: "flex", gap: 8 }}>
                <input
                  type="email"
                  placeholder="votre@email.com"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && subscribe()}
                  style={{
                    flex: 1, padding: "8px 12px",
                    border: "1.5px solid #e8e0d6", borderRadius: 8,
                    fontSize: 13, fontFamily: "inherit", outline: "none",
                    background: "white",
                  }}
                />
                <button
                  onClick={subscribe}
                  disabled={status === "loading" || !email.includes("@")}
                  style={{
                    padding: "8px 16px", background: "#c9a84c", color: "white",
                    border: "none", borderRadius: 8, fontSize: 13,
                    fontWeight: 600, cursor: "pointer", fontFamily: "inherit",
                    opacity: status === "loading" ? 0.6 : 1,
                  }}
                >
                  {status === "loading" ? "…" : "Alerter"}
                </button>
              </div>

              {status === "error" && (
                <div style={{ color: "#e63946", fontSize: 12, marginTop: 6 }}>
                  ❌ Erreur — vérifiez votre email et réessayez
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

// ──────────────────────────────────────────────────────────────
// ProductCard principal
// ──────────────────────────────────────────────────────────────
export default function ProductCard({ product }: { product: Product }) {
  if (!product) return null;

  const parseTnd = (p: string) => parseFloat(p?.replace(/[^\d.,]/g, "").replace(",", ".")) || 0;

  // Support format groupé (nouveau) et flat (legacy)
  let offers: Offer[] = [];
  if (product.offers && Array.isArray(product.offers)) {
    offers = product.offers;
  } else {
    if (product.source || product.price_siteA) {
      offers.push({
        source: product.source || "Pharmacie",
        price:  product.price_siteA || "N/A",
        price_val: parseTnd(product.price_siteA || "0"),
        link:   product.link_siteA || "#",
        image_url: "",
        stock: "available",
      });
    }
    if (product.source_siteB && product.price_siteB) {
      offers.push({
        source: product.source_siteB,
        price:  product.price_siteB,
        price_val: parseTnd(product.price_siteB),
        link:   product.link_siteB || "#",
        image_url: "",
        stock: "available",
      });
    }
  }

  const prices   = offers.map(o => o.price_val || parseTnd(o.price)).filter(Boolean);
  const minPrice = prices.length ? Math.min(...prices) : 0;
  const saving   = product.saving_pct || (prices.length > 1
    ? Math.round(((Math.max(...prices) - minPrice) / Math.max(...prices)) * 100)
    : 0);

  const title      = product.titleA || product.name || "Produit";
  const bestSource = product.best_source || offers[0]?.source || "";
  const productId  = product.id || 0;

  return (
    <div className="product-card">
      {/* Header */}
      <div className="product-header">
        <div style={{ display: "flex", alignItems: "center", gap: 10, flex: 1, minWidth: 0 }}>
          {product.image_url && (
            <img
              src={product.image_url}
              alt={title}
              style={{ width: 44, height: 44, objectFit: "contain", borderRadius: 8, flexShrink: 0 }}
              onError={e => { (e.target as HTMLImageElement).style.display = "none"; }}
            />
          )}
          <div className="product-title" style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {title}
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexShrink: 0 }}>
          {saving > 0 && (
            <span className="offer-saving">−{saving}%</span>
          )}
          {offers.length > 1 && (
            <span className="product-badge">{offers.length} offres</span>
          )}
        </div>
      </div>

      {/* Offres */}
      {offers.map((offer, i) => {
        const priceVal = offer.price_val || parseTnd(offer.price);
        const isBest   = priceVal === minPrice && prices.length > 1;
        return (
          <a
            key={i}
            href={offer.link || "#"}
            target="_blank"
            rel="noopener noreferrer"
            className={`offer${isBest ? " best" : ""}`}
          >
            <span className="offer-rank">{i + 1}</span>
            <span className="offer-source">{offer.source}</span>
            {offer.stock === "out of stock" && (
              <span style={{ fontSize: 10, color: "#e63946", background: "#fff0f0", padding: "2px 6px", borderRadius: 10 }}>
                Indisponible
              </span>
            )}
            <span className="offer-price">{offer.price}</span>
            <span className="offer-link">Voir →</span>
          </a>
        );
      })}

      {/* Prédiction + Alerte */}
      <div style={{ padding: "10px 0 0", borderTop: "1.5px solid #f5f0ea" }}>
        <PricePredictionBadge title={title} source={bestSource} />
        {productId > 0 && <AlertSubscribe productId={productId} title={title} />}
      </div>
    </div>
  );
}