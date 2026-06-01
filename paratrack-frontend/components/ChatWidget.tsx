"use client";
import { useState, useRef, useEffect } from "react";
import { sendChatMessage } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  type?: "text" | "skin_result" | "image";
  imageUrl?: string;
  skinResult?: SkinResult;
}

interface SkinResult {
  skin_issue: string;
  confidence: number;
  scores: Record<string, number>;
}

const QUICK_PROMPTS = ["Meilleur hydratant visage", "Solaire SPF50 pas cher", "Comparer Avène vs La Roche"];

const SKIN_API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

// Labels en français pour les classes du modèle
const ISSUE_LABELS: Record<string, { fr: string; emoji: string; color: string }> = {
  acne:          { fr: "Acné",           emoji: "🔴", color: "#e63946" },
  eczema:        { fr: "Eczéma",         emoji: "🟠", color: "#f4a261" },
  rosacea:       { fr: "Rosacée",        emoji: "🌸", color: "#e07c9b" },
  psoriasis:     { fr: "Psoriasis",      emoji: "🟡", color: "#f4d03f" },
  normal:        { fr: "Peau normale",   emoji: "✅", color: "#52b788" },
  dry:           { fr: "Peau sèche",     emoji: "🏜️", color: "#c9a84c" },
  oily:          { fr: "Peau grasse",    emoji: "💧", color: "#4ea8de" },
  hyperpigmentation: { fr: "Hyperpigmentation", emoji: "🟤", color: "#8d6e63" },
};

function getLabel(key: string) {
  const k = key.toLowerCase();
  return ISSUE_LABELS[k] ?? { fr: key, emoji: "🔬", color: "#888" };
}

function SkinResultCard({ result }: { result: SkinResult }) {
  const label = getLabel(result.skin_issue);
  const top3 = Object.entries(result.scores)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 3);

  return (
    <div style={{
      background: "white", borderRadius: 12, padding: "12px 14px",
      border: "1.5px solid #e8e0d6", marginTop: 4, width: "100%"
    }}>
      {/* Résultat principal */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
        <span style={{ fontSize: 22 }}>{label.emoji}</span>
        <div>
          <div style={{ fontWeight: 700, fontSize: 14, color: label.color }}>{label.fr}</div>
          <div style={{ fontSize: 11, color: "#888" }}>
            Confiance : {(result.confidence * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Top 3 barres */}
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {top3.map(([cls, score]) => {
          const l = getLabel(cls);
          return (
            <div key={cls}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 2 }}>
                <span style={{ color: "#555" }}>{l.emoji} {l.fr}</span>
                <span style={{ fontWeight: 600, color: l.color }}>{(score * 100).toFixed(1)}%</span>
              </div>
              <div style={{ height: 5, background: "#f0ebe4", borderRadius: 4 }}>
                <div style={{
                  height: "100%", borderRadius: 4,
                  width: `${score * 100}%`,
                  background: l.color,
                  transition: "width 0.5s ease"
                }} />
              </div>
            </div>
          );
        })}
      </div>

      <div style={{
        marginTop: 10, fontSize: 10, color: "#aaa",
        borderTop: "1px solid #f0ebe4", paddingTop: 8
      }}>
        ⚠️ Outil d'aide — consultez un dermatologue
      </div>
    </div>
  );
}

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Bonjour ! 👋 Je peux vous aider à trouver le meilleur prix, comparer des produits, ou **analyser un problème de peau** 📷" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [skinLoading, setSkinLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, open]);

  // Ouvre le chat depuis le bouton CTA skin de la page
  useEffect(() => {
    const handler = () => {
      setOpen(true);
      setTimeout(() => fileInputRef.current?.click(), 400);
    };
    window.addEventListener("paratrack:openchat", handler);
    return () => window.removeEventListener("paratrack:openchat", handler);
  }, []);

  async function sendMessage(text?: string) {
    const msg = text || input.trim();
    if (!msg || loading) return;
    setInput("");
    const newMessages: Message[] = [...messages, { role: "user", content: msg }];
    setMessages(newMessages);
    setLoading(true);
    try {
      const data = await sendChatMessage(msg);
      setMessages([...newMessages, { role: "assistant", content: data.reply }]);
    } catch {
      setMessages([...newMessages, { role: "assistant", content: "Erreur, réessayez." }]);
    } finally {
      setLoading(false);
    }
  }

  async function handleSkinImage(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = ""; // reset pour re-upload possible

    const imageUrl = URL.createObjectURL(file);

    // Message utilisateur avec aperçu
    const userMsg: Message = {
      role: "user",
      content: "Analysez cette photo de ma peau",
      type: "image",
      imageUrl,
    };
    const withUser = [...messages, userMsg];
    setMessages(withUser);
    setSkinLoading(true);

    try {
      const formData = new FormData();
      formData.append("image", file);

      const res = await fetch(`${SKIN_API}/api/skin/analyze`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Erreur serveur");
      const result: SkinResult = await res.json();

      const label = getLabel(result.skin_issue);
      const assistantMsg: Message = {
        role: "assistant",
        content: `Voici l'analyse de votre photo — détection : **${label.fr}** (${(result.confidence * 100).toFixed(1)}%)`,
        type: "skin_result",
        skinResult: result,
      };
      setMessages([...withUser, assistantMsg]);
    } catch (err) {
      setMessages([...withUser, {
        role: "assistant",
        content: "❌ Impossible d'analyser l'image. Vérifiez que le serveur skin est démarré.",
      }]);
    } finally {
      setSkinLoading(false);
    }
  }

  return (
    <>
      <style>{`
        .chat-fab {
          position: fixed; bottom: 24px; right: 24px;
          width: 56px; height: 56px; border-radius: 50%;
          background: #2d6a4f; border: none; cursor: pointer;
          display: flex; align-items: center; justify-content: center;
          box-shadow: 0 4px 18px rgba(45,106,79,0.35); z-index: 1000;
          transition: transform 0.2s, box-shadow 0.2s;
        }
        .chat-fab:hover { transform: scale(1.06); box-shadow: 0 6px 24px rgba(45,106,79,0.45); }
        .chat-window {
          position: fixed; bottom: 92px; right: 24px;
          width: 360px; height: 530px; background: #faf7f2;
          border-radius: 18px; box-shadow: 0 20px 48px rgba(0,0,0,0.13);
          display: flex; flex-direction: column; overflow: hidden; z-index: 1000;
          border: 1.5px solid #e8e0d6;
          animation: slideUp 0.22s ease-out;
        }
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .chat-header {
          padding: 14px 16px; background: #2d6a4f;
          display: flex; justify-content: space-between; align-items: center;
          flex-shrink: 0;
        }
        .chat-header-info { display: flex; align-items: center; gap: 10px; }
        .chat-avatar {
          width: 34px; height: 34px; border-radius: 50%;
          background: rgba(255,255,255,0.18);
          display: flex; align-items: center; justify-content: center; font-size: 16px;
        }
        .chat-header h3 { font-size: 14px; font-weight: 600; margin: 0; color: white; }
        .chat-header p { font-size: 10px; color: #b7e4c7; margin: 2px 0 0; }
        .chat-close-btn {
          background: rgba(255,255,255,0.15); border: none; font-size: 14px;
          cursor: pointer; color: white; border-radius: 50%;
          width: 26px; height: 26px; display: flex; align-items: center; justify-content: center;
          transition: background 0.15s;
        }
        .chat-close-btn:hover { background: rgba(255,255,255,0.25); }
        .chat-messages {
          flex: 1; overflow-y: auto; padding: 14px 12px;
          display: flex; flex-direction: column; gap: 10px;
        }
        .msg-row { display: flex; flex-direction: column; }
        .msg-row.user { align-items: flex-end; }
        .msg-row.assistant { align-items: flex-start; }
        .message {
          max-width: 84%; padding: 9px 13px; border-radius: 14px;
          font-size: 13px; line-height: 1.45;
        }
        .message.user {
          background: #2d6a4f; color: white; border-bottom-right-radius: 4px;
        }
        .message.assistant {
          background: white; color: #1a1a1a;
          border: 1.5px solid #e8e0d6; border-bottom-left-radius: 4px;
        }
        .msg-image {
          max-width: 160px; border-radius: 10px; overflow: hidden;
          border: 2px solid #2d6a4f; margin-bottom: 4px;
        }
        .msg-image img { width: 100%; display: block; }
        .quick-chips {
          padding: 8px 12px; display: flex; gap: 6px; flex-wrap: wrap;
          border-top: 1.5px solid #e8e0d6; background: white; flex-shrink: 0;
        }
        .quick-chips button {
          padding: 4px 11px; background: #d8f3dc; border: none;
          border-radius: 20px; font-size: 11px; cursor: pointer;
          color: #2d6a4f; font-weight: 600; transition: background 0.15s;
        }
        .quick-chips button:hover { background: #b7e4c7; }
        .chat-toolbar {
          display: flex; gap: 8px; padding: 10px 12px;
          border-top: 1.5px solid #e8e0d6; background: white; flex-shrink: 0;
          align-items: center;
        }
        .chat-toolbar input[type="text"] {
          flex: 1; padding: 8px 12px; border: 1.5px solid #e8e0d6;
          border-radius: 10px; font-size: 13px; outline: none;
          font-family: inherit; background: #faf7f2; transition: border-color 0.2s;
        }
        .chat-toolbar input[type="text"]:focus { border-color: #2d6a4f; }
        .btn-send {
          padding: 8px 14px; background: #2d6a4f; color: white;
          border: none; border-radius: 10px; cursor: pointer;
          font-size: 13px; font-weight: 600; transition: background 0.2s;
          white-space: nowrap;
        }
        .btn-send:hover { background: #1e4d38; }
        .btn-send:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn-skin {
          width: 36px; height: 36px; border-radius: 10px;
          background: #d8f3dc; border: 1.5px solid #b7e4c7;
          cursor: pointer; display: flex; align-items: center;
          justify-content: center; font-size: 17px;
          transition: background 0.15s; flex-shrink: 0;
          position: relative;
        }
        .btn-skin:hover { background: #b7e4c7; }
        .btn-skin.loading { animation: pulse 1s infinite; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
        .skin-tooltip {
          position: absolute; bottom: 42px; left: 50%;
          transform: translateX(-50%);
          background: #1a1a1a; color: white; font-size: 10px;
          padding: 4px 8px; border-radius: 6px; white-space: nowrap;
          pointer-events: none; opacity: 0; transition: opacity 0.2s;
        }
        .btn-skin:hover .skin-tooltip { opacity: 1; }
        @media (max-width: 480px) {
          .chat-window { width: calc(100vw - 32px); right: 16px; bottom: 80px; }
          .chat-fab { right: 16px; bottom: 16px; }
        }
      `}</style>

      {/* FAB */}
      <button className="chat-fab" onClick={() => setOpen(!open)} aria-label="Assistant">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
      </button>

      {open && (
        <div className="chat-window">
          {/* Header */}
          <div className="chat-header">
            <div className="chat-header-info">
              <div className="chat-avatar">🌿</div>
              <div>
                <h3>Assistant ParaTrack</h3>
                <p>Comparer · Conseiller · Analyser la peau</p>
              </div>
            </div>
            <button className="chat-close-btn" onClick={() => setOpen(false)}>✕</button>
          </div>

          {/* Messages */}
          <div className="chat-messages">
            {messages.map((m, i) => (
              <div key={i} className={`msg-row ${m.role}`}>
                {/* Aperçu image uploadée */}
                {m.type === "image" && m.imageUrl && (
                  <div className="msg-image">
                    <img src={m.imageUrl} alt="photo peau" />
                  </div>
                )}

                {/* Bulle texte */}
                <div className={`message ${m.role}`}>
                  {m.content}
                </div>

                {/* Carte résultat skin */}
                {m.type === "skin_result" && m.skinResult && (
                  <SkinResultCard result={m.skinResult} />
                )}
              </div>
            ))}

            {(loading || skinLoading) && (
              <div className="msg-row assistant">
                <div className="message assistant" style={{ color: "#aaa" }}>
                  {skinLoading ? "🔬 Analyse en cours..." : "•••"}
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick chips (seulement au début) */}
          {messages.length <= 1 && (
            <div className="quick-chips">
              {QUICK_PROMPTS.map(p => (
                <button key={p} onClick={() => sendMessage(p)}>{p}</button>
              ))}
            </div>
          )}

          {/* Toolbar : skin button + input + send */}
          <div className="chat-toolbar">
            {/* Bouton analyse peau */}
            <button
              className={`btn-skin${skinLoading ? " loading" : ""}`}
              onClick={() => fileInputRef.current?.click()}
              disabled={skinLoading || loading}
              title="Analyser ma peau"
            >
              {skinLoading ? "⏳" : "📷"}
              <span className="skin-tooltip">Analyser ma peau</span>
            </button>

            {/* Input fichier caché */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              capture="environment"
              style={{ display: "none" }}
              onChange={handleSkinImage}
            />

            <input
              className=""
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              placeholder="Posez votre question..."
              disabled={loading || skinLoading}
            />
            <button
              className="btn-send"
              onClick={() => sendMessage()}
              disabled={loading || skinLoading}
            >
              Envoyer
            </button>
          </div>
        </div>
      )}
    </>
  );
}