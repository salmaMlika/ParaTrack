"use client";
import { useState, useEffect, useRef } from "react";
import ProductCard from "@/components/ProductCard";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

// Génère un session_id stable pour la durée de la session browser
function getSessionId() {
  if (typeof window === "undefined") return "ssr";
  let sid = sessionStorage.getItem("paratrack_sid");
  if (!sid) { sid = crypto.randomUUID(); sessionStorage.setItem("paratrack_sid", sid); }
  return sid;
}

const SUGGESTIONS = ["SVR", "Avène", "La Roche-Posay", "Bioderma", "Vichy", "CeraVe"];

const FEATURES = [
  {
    emoji: "💰",
    title: "Comparateur de prix",
    desc: "Comparez en temps réel les prix sur 5+ pharmacies tunisiennes et économisez jusqu'à 30% sur vos achats.",
    color: "#2d6a4f",
    bg: "#d8f3dc",
  },
  {
    emoji: "🔬",
    title: "Analyse de peau IA",
    desc: "Photographiez votre peau. Notre modèle IA détecte acné, eczéma, rosacée et plus — en quelques secondes.",
    color: "#c9a84c",
    bg: "#fdf3d8",
  },
  {
    emoji: "💬",
    title: "Assistant & conseils",
    desc: "Posez vos questions à notre assistant : recommandations produits, comparaisons de marques, conseils soins.",
    color: "#4a90d9",
    bg: "#dceefb",
  },
];

const HOW_IT_WORKS = [
  { step: "01", title: "Cherchez un produit", desc: "Tapez une marque ou un soin (Avène, SPF50, hydratant...)" },
  { step: "02", title: "Comparez les prix", desc: "On affiche toutes les offres triées du moins cher au plus cher" },
  { step: "03", title: "Ou analysez votre peau", desc: "Cliquez 📷 dans le chat, prenez une photo, obtenez un diagnostic IA" },
  { step: "04", title: "Recevez des conseils", desc: "L'assistant recommande les produits adaptés à votre type de peau" },
];

export default function Home() {
  const [query, setQuery]       = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");
  const [searched, setSearched] = useState(false);
  const [recs, setRecs]         = useState<string[]>([]);
  const lastQuery               = useRef("");

  async function handleSearch(q?: string) {
    const term = q ?? query;
    if (!term.trim()) return;
    if (q) setQuery(q);
    setLoading(true);
    setError("");
    setSearched(true);
    setRecs([]);
    lastQuery.current = term.trim().toLowerCase();

    setTimeout(() => document.getElementById("results")?.scrollIntoView({ behavior: "smooth" }), 100);

    try {
      const sid = getSessionId();
      const res  = await fetch(`${API}/products/compare?q=${encodeURIComponent(term)}&session_id=${sid}`);
      const data = await res.json();
      setResults(Array.isArray(data) ? data : []);
      if (data.length === 0) setError("Aucun produit trouvé");

      // Charge les recommandations en arrière-plan
      fetchRecs(term.trim().toLowerCase());
    } catch {
      setError("Impossible de contacter le serveur");
    } finally {
      setLoading(false);
    }
  }

  async function fetchRecs(q: string) {
    try {
      const res  = await fetch(`${API}/products/recommendations?q=${encodeURIComponent(q)}&n=4`);
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) setRecs(data);
    } catch {
      // silencieux — les recs sont optionnelles
    }
  }

  return (
    <>
      <div className="topbar">
        💰 Trouvez le meilleur prix · 🔬 Analyse peau IA · 💬 Assistant disponible 24h/24
      </div>

      <header className="header">
        <div className="header-content">
          <a href="/" className="logo">Para<span>Track</span></a>
          <span className="header-badge">🇹🇳 Tunisie</span>
        </div>
      </header>

      <div className="container">
        <div className="hero">
          <div className="hero-badge">✦ Parapharmacie intelligente</div>
          <h1>
            Comparez, analysez,<br />
            <span>soignez-vous mieux</span>
          </h1>
          <p>
            Comparateur de prix · Analyse de peau IA · Assistant conseils<br />
            Tout en un, pour vos soins en Tunisie
          </p>

          <div className="search-box">
            <input
              type="text"
              className="search-input"
              placeholder="Marque ou produit (ex: SVR, Avène, CeraVe...)"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
            <button className="search-btn" onClick={() => handleSearch()} disabled={loading}>
              {loading ? "..." : "Comparer"}
            </button>
          </div>

          <div className="chips">
            {SUGGESTIONS.map(s => (
              <button key={s} className="chip" onClick={() => handleSearch(s)}>{s}</button>
            ))}
          </div>

          <div className="stats">
            <div className="stat">
              <div className="stat-value">50 200+</div>
              <div className="stat-label">Produits</div>
            </div>
            <div className="stat">
              <div className="stat-value">−30%</div>
              <div className="stat-label">Économie moy.</div>
            </div>
          </div>
        </div>

        {/* ── FEATURES ── */}
        <section className="features-section">
          <div className="section-label">Ce que fait ParaTrack</div>
          <h2 className="section-title">Plus qu'un comparateur</h2>
          <div className="features-grid">
            {FEATURES.map((f) => (
              <div className="feature-card" key={f.title}>
                <div className="feature-icon" style={{ background: f.bg, color: f.color }}>{f.emoji}</div>
                <h3 className="feature-title" style={{ color: f.color }}>{f.title}</h3>
                <p className="feature-desc">{f.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ── HOW IT WORKS ── */}
        <section className="how-section">
          <div className="section-label">Mode d'emploi</div>
          <h2 className="section-title">Comment ça marche ?</h2>
          <div className="how-grid">
            {HOW_IT_WORKS.map((h) => (
              <div className="how-card" key={h.step}>
                <div className="how-step">{h.step}</div>
                <div className="how-title">{h.title}</div>
                <div className="how-desc">{h.desc}</div>
              </div>
            ))}
          </div>
        </section>

        {/* ── SKIN CTA ── */}
        <section className="skin-cta">
          <div className="skin-cta-content">
            <div className="skin-cta-emoji">🔬</div>
            <div>
              <h3 className="skin-cta-title">Nouveau · Analyse de peau IA</h3>
              <p className="skin-cta-desc">
                Détection d'acné, eczéma, rosacée, hyperpigmentation et plus — directement depuis votre photo.
                Recommandations produits personnalisées incluses.
              </p>
            </div>
            <button
              className="skin-cta-btn"
              onClick={() => window.dispatchEvent(new CustomEvent("paratrack:openchat"))}
            >
              📷 Essayer maintenant
            </button>
          </div>
        </section>

        {/* ── RÉSULTATS ── */}
        <div id="results">
          {error && <div className="error">⚠️ {error}</div>}

          {loading && (
            <div>
              {[1, 2, 3].map(i => (
                <div key={i} className="skeleton">
                  <div className="skeleton-line" style={{ width: "45%" }} />
                  <div className="skeleton-line" style={{ width: "70%" }} />
                  <div className="skeleton-line" style={{ width: "55%" }} />
                </div>
              ))}
            </div>
          )}

          {results.length > 0 && !loading && (
            <>
              <div className="results-header">
                <span className="results-count">
                  {results.length} produit{results.length > 1 ? "s" : ""} trouvé{results.length > 1 ? "s" : ""}
                </span>
              </div>

              {results.map((product: any, i: number) => (
                <ProductCard key={i} product={product} />
              ))}

              {/* ── RECOMMANDATIONS ── */}
              {recs.length > 0 && (
                <div style={{
                  margin: "28px 0 48px",
                  padding: "20px 24px",
                  background: "white",
                  border: "1.5px solid #e8e0d6",
                  borderRadius: 16,
                }}>
                  <div style={{
                    fontSize: 11, fontWeight: 700, letterSpacing: "0.1em",
                    textTransform: "uppercase", color: "#2d6a4f", marginBottom: 12,
                  }}>
                    Les utilisateurs cherchent aussi
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                    {recs.map(r => (
                      <button
                        key={r}
                        onClick={() => handleSearch(r)}
                        style={{
                          padding: "7px 16px",
                          background: "#d8f3dc",
                          border: "1.5px solid #b7e4c7",
                          borderRadius: 20,
                          fontSize: 13,
                          fontWeight: 600,
                          cursor: "pointer",
                          color: "#2d6a4f",
                          fontFamily: "inherit",
                          transition: "all 0.15s",
                        }}
                        onMouseEnter={e => (e.currentTarget.style.background = "#b7e4c7")}
                        onMouseLeave={e => (e.currentTarget.style.background = "#d8f3dc")}
                      >
                        🔍 {r}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {searched && !loading && results.length === 0 && !error && (
            <div className="empty">
              <div className="empty-icon">🔍</div>
              <h3>Aucun résultat</h3>
              <p>Essayez un autre terme de recherche</p>
            </div>
          )}
        </div>
      </div>

      <footer className="footer">
        <div className="footer-logo">Para<span>Track</span></div>
        <div style={{ marginTop: 6, color: "var(--text-muted)" }}>
          Comparateur · Analyse peau IA · Assistant · Tunisie
        </div>
      </footer>
    </>
  );
}