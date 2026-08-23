"use client";

import { useEffect, useRef, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const agents = [
  ["memory", "Memory", "Context"],
  ["insight", "Insight", "Analyze"],
  ["guide", "Guide", "Options"],
  ["decision", "Decision", "Judge"],
  ["action", "Action", "Execute"]
];
const config: Record<string, { languages: string[]; currency: string; payment: string }> = {
  BD: { languages: ["bn", "en"], currency: "BDT", payment: "Local provider" },
  IN: { languages: ["hi", "en"], currency: "INR", payment: "Local provider" },
  ZA: { languages: ["en", "af", "zu", "xh", "st"], currency: "ZAR", payment: "Local provider" }
};

type AgentState = "idle" | "running" | "completed";

export default function Home() {
  const [sellerId, setSellerId] = useState("");
  const [authToken, setAuthToken] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authBusy, setAuthBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [country, setCountry] = useState("BD");
  const [language, setLanguage] = useState("bn");
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");
  const [listening, setListening] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [analyzingImage, setAnalyzingImage] = useState(false);
  const [busy, setBusy] = useState(false);
  const [agentStates, setAgentStates] = useState<Record<string, AgentState>>({});
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    const token = sessionStorage.getItem("gramsell_token");
    if (token) setAuthToken(token);
  }, []);

  function authHeaders(): HeadersInit {
    return authToken ? { Authorization: `Bearer ${authToken}` } : {};
  }

  async function authenticate() {
    setError(""); setAuthBusy(true);
    try {
      const endpoint = authMode === "login" ? "/api/auth/login" : "/api/auth/register";
      const payload = authMode === "login"
        ? { email, password }
        : { display_name: displayName, email, password, country, language, currency: config[country].currency };
      const response = await fetch(`${API}${endpoint}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Authentication failed.");
      setAuthToken(data.access_token);
      setSellerId(String(data.seller_id));
      if (typeof window !== "undefined") sessionStorage.setItem("gramsell_token", data.access_token);
    } catch (err) { setError(err instanceof Error ? err.message : "Authentication failed."); }
    finally { setAuthBusy(false); }
  }

  function logout() {
    setAuthToken(""); setSellerId("");
    if (typeof window !== "undefined") sessionStorage.removeItem("gramsell_token");
  }

  function changeCountry(value: string) {
    setCountry(value);
    setLanguage(config[value].languages[0]);
  }

  async function startVoiceInput() {
    if (!authToken) { setError("Sign in before using seller tools."); return; }
    setError("");
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      setError("Voice recording is not supported by this browser."); return;
    }
    try {
      if (listening) { recorderRef.current?.stop(); return; }
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = e => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      recorder.onstart = () => setListening(true);
      recorder.onstop = async () => {
        stream.getTracks().forEach(track => track.stop()); setListening(false);
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        const form = new FormData(); form.append("audio", blob, "seller-input.webm");
        setTranscribing(true);
        try {
          const response = await fetch(`${API}/api/media/speech/transcribe?language=${encodeURIComponent(language)}`, { method: "POST", headers: authHeaders(), body: form });
          const data = await response.json(); if (!response.ok) throw new Error(data.detail || "Speech transcription failed.");
          setMessage(previous => previous ? `${previous} ${data.transcript}` : data.transcript);
        } catch (err) { setError(err instanceof Error ? err.message : "Speech transcription failed."); }
        finally { setTranscribing(false); }
      };
      recorder.start(); recorderRef.current = recorder;
    } catch { setListening(false); setError("Microphone access was not available."); }
  }

  async function analyzeImage(file: File) {
    setError(""); setAnalyzingImage(true);
    const form = new FormData(); form.append("image", file);
    try {
      const response = await fetch(`${API}/api/media/image/analyze?language=${encodeURIComponent(language)}`, { method: "POST", headers: authHeaders(), body: form });
      const data = await response.json(); if (!response.ok) throw new Error(data.detail || "Image analysis failed.");
      setResult({ image_analysis: data });
      const extracted = data.analysis?.product || data.analysis?.description;
      if (typeof extracted === "string" && extracted.trim()) setMessage(previous => previous ? `${previous}\n${extracted}` : extracted);
    } catch (err) { setError(err instanceof Error ? err.message : "Image analysis failed."); }
    finally { setAnalyzingImage(false); }
  }

  async function runAgents() {
    setError(""); setResult(null); setBusy(true);
    setAgentStates(Object.fromEntries(agents.map(([id]) => [id, "idle"])));
    if (!sellerId || !message.trim()) { setBusy(false); setError("A real seller ID and a real business request are required."); return; }
    try {
      const response = await fetch(`${API}/api/intelligence/run/stream`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ seller_id: Number(sellerId), message, country, language })
      });
      if (!response.ok || !response.body) throw new Error("Agent pipeline could not start.");
      const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = "";
      while (true) {
        const { value, done } = await reader.read(); if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split("\n\n"); buffer = chunks.pop() || "";
        for (const chunk of chunks) {
          const line = chunk.split("\n").find(item => item.startsWith("data: ")); if (!line) continue;
          const event = JSON.parse(line.slice(6));
          if (event.type === "agent") setAgentStates(previous => ({ ...previous, [event.agent]: event.status }));
          if (event.type === "complete") setResult(event);
          if (event.type === "error") throw new Error(event.detail || "Agent pipeline failed.");
        }
      }
    } catch (err) { setError(err instanceof Error ? err.message : "Agent pipeline failed."); }
    finally { setBusy(false); }
  }

  return (
    <main className="page">
      <header className="topbar"><div className="brand">GramSell <span>AI</span></div><div className="topbarRight"><div className="statusPill"><i /> Live Intelligence</div>{authToken ? <button className="authButton" onClick={logout}>Sign out</button> : null}</div></header>
      <section className="content">
        {!authToken && <section className="card authCard"><div className="cardHeader"><div><h2>{authMode === "login" ? "Seller sign in" : "Create seller account"}</h2><p>Secure access to your business workspace.</p></div><div className="liveDot"><i /> Protected</div></div><div className="authGrid">{authMode === "register" && <div className="field"><label>Display name</label><input value={displayName} onChange={e => setDisplayName(e.target.value)} /></div>}<div className="field"><label>Email</label><input type="email" value={email} onChange={e => setEmail(e.target.value)} autoComplete="email" /></div><div className="field"><label>Password</label><input type="password" value={password} onChange={e => setPassword(e.target.value)} autoComplete={authMode === "login" ? "current-password" : "new-password"} /></div></div><div className="actions"><button className="primary" onClick={authenticate} disabled={authBusy}>{authBusy ? "Working..." : authMode === "login" ? "Sign in" : "Create account"}</button><button className="secondary" onClick={() => setAuthMode(authMode === "login" ? "register" : "login")}>{authMode === "login" ? "Create account" : "Back to sign in"}</button></div></section>}

        <div className="hero"><div><div className="eyebrow">REAL-TIME RURAL BUSINESS INTELLIGENCE</div><h1>One business team.<br /><span>Every product.</span></h1><p>Voice, image and text flow through grounded business intelligence. Real data only.</p></div><div className="heroOrb"><div className="orbCore" /></div></div>
        <div className="grid">
          <div className={`card mainCard ${!authToken ? "locked" : ""}`}>
            <div className="cardHeader"><div><h2>Seller workspace</h2><p>Give the agents a real business request.</p></div><div className="liveDot"><i /> Secure</div></div>
            <div className="agents">{agents.map(([id, name, role]) => { const state = agentStates[id] || "idle"; return <div className={`agent ${state}`} key={id}><div className="agentLight" /><div className="agentGlyph">{name.slice(0,1)}</div><strong>{name}</strong><span>{state === "running" ? "Working" : state === "completed" ? "Done" : role}</span></div>; })}</div>
            <div className="stack workspace">
              <div className="row"><div className="field"><label>Seller ID</label><input value={sellerId} onChange={e => setSellerId(e.target.value)} inputMode="numeric" /></div><div className="field"><label>Country</label><select value={country} onChange={e => changeCountry(e.target.value)}><option value="BD">Bangladesh</option><option value="IN">India</option><option value="ZA">South Africa</option></select></div></div>
              <div className="row"><div className="field"><label>Language</label><select value={language} onChange={e => setLanguage(e.target.value)}>{config[country].languages.map(item => <option value={item} key={item}>{item}</option>)}</select></div><div className="field"><label>Currency</label><input value={config[country].currency} readOnly /></div></div>
              <div className="field"><label>Business request</label><textarea value={message} onChange={e => setMessage(e.target.value)} placeholder="Speak, type, or add a product image..." /></div>
              <div className="actions"><button type="button" className={`secondary ${listening ? "active" : ""}`} onClick={startVoiceInput} disabled={transcribing}>{listening ? "Stop listening" : transcribing ? "Transcribing..." : "Speak"}</button><label className="secondary upload">{analyzingImage ? "Analyzing..." : "Add image"}<input type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={e => { const file = e.target.files?.[0]; if (file) analyzeImage(file); e.currentTarget.value = ""; }} /></label><button className="primary" onClick={runAgents} disabled={busy}>{busy ? "Agents working..." : "Run agents"}</button></div>
              {error && <div className="error">{error}</div>}
            </div>
          </div>
          <aside className="card intelligenceCard"><div className="cardHeader"><div><h2>Grounded intelligence</h2><p>External evidence is used only when relevant.</p></div></div><div className="signal"><span>MARKET</span><strong>Maps Grounding</strong><small>Nearby market intelligence</small></div><div className="signal"><span>WEATHER</span><strong>Forecast-aware</strong><small>Risk planning uses available forecast evidence</small></div><div className="signal"><span>PAYMENT</span><strong>Verified only</strong><small>Provider verification required for realized revenue</small></div><div className="signal"><span>RISK</span><strong>Evidence profile</strong><small>No fabricated bank credit score</small></div></aside>
        </div>
        {result && <section className="card resultCard">
          <div className="cardHeader"><div><h2>Agent result</h2><p>{result.intent || "Business intelligence"} · {result.language || language}</p></div><div className="liveDot"><i /> Grounded</div></div>
          <div className="resultGrid">
            {agents.map(([id, name]) => {
              const output = result.agents?.[id] || {};
              const facts = Array.isArray(output.facts) ? output.facts : [];
              const recommendations = Array.isArray(output.recommendations) ? output.recommendations : [];
              const actions = Array.isArray(output.actions) ? output.actions : [];
              return <article className="resultAgent" key={id}>
                <div className="resultAgentHead"><span className="agentMiniLight" /><strong>{name}</strong><span className="resultState">completed</span></div>
                {facts.length > 0 && <div><small>Facts</small><ul>{facts.slice(0, 4).map((item: unknown, index: number) => <li key={index}>{String(item)}</li>)}</ul></div>}
                {recommendations.length > 0 && <div><small>Recommendations</small><ul>{recommendations.slice(0, 4).map((item: unknown, index: number) => <li key={index}>{String(item)}</li>)}</ul></div>}
                {actions.length > 0 && <div><small>Actions</small><ul>{actions.slice(0, 4).map((item: unknown, index: number) => <li key={index}>{typeof item === "string" ? item : JSON.stringify(item)}</li>)}</ul></div>}
                {facts.length === 0 && recommendations.length === 0 && actions.length === 0 && <p className="muted">No supported output.</p>}
              </article>;
            })}
          </div>
          <div className="evidenceBar"><span>Evidence status</span><strong>{result.grounding_summary?.nearby_market?.has_data || result.grounding_summary?.weather?.has_data ? "Grounded evidence available" : "No external evidence available"}</strong><small>Actions remain proposed until application execution succeeds.</small></div>
        </section>}
      </section>
    </main>
  );
}
