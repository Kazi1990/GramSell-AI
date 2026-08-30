"use client";

import { useEffect, useRef, useState } from "react";
import { createUserWithEmailAndPassword, onAuthStateChanged, signInWithEmailAndPassword, signOut, updateProfile, User } from "firebase/auth";
import { firebaseAuth, firebaseConfigured } from "./firebase";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "";
const agents = [
  ["memory", "Memory", "Context"],
  ["insight", "Insight", "Analyze"],
  ["guide", "Guide", "Options"],
  ["decision", "Decision", "Judge"],
  ["action", "Action", "Execute"]
];
const config: Record<string, { languages: string[]; currency: string; payment: string }> = {
  BD: { languages: ["auto", "bn"], currency: "BDT", payment: "Local provider" },
  IN: { languages: ["auto", "hi"], currency: "INR", payment: "Local provider" },
  ZA: { languages: ["auto", "af", "zu", "xh", "st", "en"], currency: "ZAR", payment: "Local provider" }
};
const languageLabels: Record<string, string> = {
  auto: "Auto-detect (any language)", bn: "Bangla", hi: "Hindi", en: "English",
  af: "Afrikaans", zu: "Zulu", xh: "Xhosa", st: "Sesotho"
};

type AgentState = "idle" | "running" | "completed";

export default function Home() {
  const [sellerId, setSellerId] = useState("");
  const [authToken, setAuthToken] = useState("");
  const [firebaseUser, setFirebaseUser] = useState<User | null>(null);
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
  const [financials, setFinancials] = useState<any>(null);
  const [paymentOrderId, setPaymentOrderId] = useState("");
  const [paymentTranscript, setPaymentTranscript] = useState("");
  const [paymentListening, setPaymentListening] = useState(false);
  const [paymentProvider, setPaymentProvider] = useState(config.BD.payment);
  const [paymentDestination, setPaymentDestination] = useState("");
  const [paymentInfo, setPaymentInfo] = useState<any>(null);
  const [forecast, setForecast] = useState<any[]>([]);
  const [forecastBusy, setForecastBusy] = useState(false);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    if (firebaseConfigured && firebaseAuth) {
      return onAuthStateChanged(firebaseAuth, async user => {
        setFirebaseUser(user);
        if (!user) {
          setAuthToken("");
          setSellerId("");
          return;
        }
        const token = await user.getIdToken();
        setAuthToken(token);
        const profile = {
          display_name: user.displayName || user.email?.split("@")[0] || "Seller",
          country,
          language,
          currency: config[country].currency
        };
        const response = await fetch(`${API}/api/auth/firebase-session`, {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
          body: JSON.stringify(profile)
        });
        if (response.ok) {
          const data = await response.json();
          setSellerId(String(data.seller_id));
          if (data.country && config[data.country]) setCountry(data.country);
          if (data.language) setLanguage(data.language);
          await loadFinancials(String(data.seller_id), token);
        }
      });
    }
    const token = sessionStorage.getItem("gramsell_token");
    if (token) setAuthToken(token);
  }, []);

  function authHeaders(): HeadersInit {
    return authToken ? { Authorization: `Bearer ${authToken}` } : {};
  }

  async function authenticate() {
    setError(""); setAuthBusy(true);
    try {
      if (firebaseConfigured && firebaseAuth) {
        const credential = authMode === "login"
          ? await signInWithEmailAndPassword(firebaseAuth, email, password)
          : await createUserWithEmailAndPassword(firebaseAuth, email, password);
        if (authMode === "register" && displayName.trim()) {
          await updateProfile(credential.user, { displayName: displayName.trim() });
        }
        const token = await credential.user.getIdToken(true);
        setFirebaseUser(credential.user);
        setAuthToken(token);
        const response = await fetch(`${API}/api/auth/firebase-session`, {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
          body: JSON.stringify({
            display_name: displayName.trim() || credential.user.displayName || email.split("@")[0],
            country,
            language,
            currency: config[country].currency
          })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Seller profile could not be created.");
        setSellerId(String(data.seller_id));
        if (data.country && config[data.country]) setCountry(data.country);
        if (data.language) setLanguage(data.language);
      } else {
        const endpoint = authMode === "login" ? "/api/auth/login" : "/api/auth/register";
        const payload = authMode === "login"
          ? { email, password }
          : { display_name: displayName, email, password, country, language, currency: config[country].currency };
        const response = await fetch(`${API}${endpoint}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Authentication failed.");
        setAuthToken(data.access_token);
        setSellerId(String(data.seller_id));
        await loadFinancials(String(data.seller_id), data.access_token);
        if (typeof window !== "undefined") sessionStorage.setItem("gramsell_token", data.access_token);
      }
    } catch (err) { setError(err instanceof Error ? err.message : "Authentication failed."); }
    finally { setAuthBusy(false); }
  }

  async function logout() {
    if (firebaseAuth && firebaseUser) await signOut(firebaseAuth);
    setFirebaseUser(null);
    setAuthToken(""); setSellerId("");
    if (typeof window !== "undefined") sessionStorage.removeItem("gramsell_token");
  }

  function changeCountry(value: string) {
    setCountry(value);
    setLanguage(config[value].languages[0]);
    setPaymentProvider(value === "BD" ? "bkash" : value === "IN" ? "upi" : "eft");
    setPaymentDestination("");
    setPaymentInfo(null);
  }

  async function configurePayment() {
    if (!authToken || !sellerId || !paymentProvider || !paymentDestination.trim()) {
      setError("Payment provider and real seller destination are required.");
      return;
    }
    const response = await fetch(`${API}/api/integrations/seller/${sellerId}/payment`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ provider: paymentProvider, destination: paymentDestination.trim() })
    });
    const data = await response.json();
    if (!response.ok) { setError(data.detail || "Payment destination could not be saved."); return; }
    setPaymentInfo(data);
    setError("");
  }

  async function loadForecast() {
    setForecastBusy(true);
    try {
      const response = await fetch(`${API}/api/weather/seller/${sellerId}/forecast?language=${encodeURIComponent(language)}&days=10`, { headers: authHeaders() });
      const data = await response.json();
      if (!response.ok || !data.available) throw new Error(data.reason || "Weather forecast is unavailable.");
      setForecast(data.days || []);
    } catch (err) { setError(err instanceof Error ? err.message : "Weather forecast failed."); }
    finally { setForecastBusy(false); }
  }

  async function loadFinancials(id: string, token: string) {
    const response = await fetch(`${API}/api/orders/seller/${id}/summary`, { headers: { Authorization: `Bearer ${token}` } });
    if (response.ok) setFinancials(await response.json());
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
        method: "POST", headers: { "Content-Type": "application/json", ...authHeaders() },
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


  function speakPaymentPrompt() {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    const text = language === "bn" ? "\u09aa\u09c7\u09ae\u09c7\u09a8\u09cd\u099f \u09aa\u09c7\u09af\u09bc\u09c7\u099b\u09c7\u09a8? \u09a8\u09bf\u09b6\u09cd\u099a\u09bf\u09a4 \u0995\u09b0\u09a4\u09c7 \u09b9\u09cd\u09af\u09be\u0981 \u09ac\u09b2\u09c1\u09a8\u0964" : language === "hi" ? "\u092d\u0941\u0917\u0924\u093e\u0928 \u092a\u094d\u0930\u093e\u092a\u094d\u0924 \u0939\u0941\u0906? \u092a\u0941\u0937\u094d\u091f\u093f \u0915\u0930\u0928\u0947 \u0915\u0947 \u0932\u093f\u090f \u0939\u093e\u0901 \u0915\u0939\u0947\u0902\u0964" : "Payment received? Please say yes to confirm.";
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = language === "bn" ? "bn-BD" : language === "hi" ? "hi-IN" : "en-US";
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  }

  async function confirmPaymentByVoice() {
    if (!authToken || !paymentOrderId) { setError("Enter an order ID before payment confirmation."); return; }
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) { setError("Voice recording is not supported by this browser."); return; }
    speakPaymentPrompt();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks: Blob[] = [];
      recorder.ondataavailable = event => { if (event.data.size > 0) chunks.push(event.data); };
      recorder.onstop = async () => {
        stream.getTracks().forEach(track => track.stop());
        setPaymentListening(false);
        const blob = new Blob(chunks, { type: recorder.mimeType || "audio/webm" });
        const form = new FormData();
        form.append("audio", blob, "payment-confirmation.webm");
        try {
          const transcription = await fetch(`${API}/api/media/speech/transcribe?language=${encodeURIComponent(language)}&seller_id=${encodeURIComponent(sellerId)}`, { method: "POST", headers: authHeaders(), body: form });
          const transcriptData = await transcription.json();
          if (!transcription.ok) throw new Error(transcriptData.detail || "Payment confirmation speech failed.");
          setPaymentTranscript(transcriptData.transcript);
          const confirmation = await fetch(`${API}/api/orders/${encodeURIComponent(paymentOrderId)}/payment/seller-confirm`, { method: "POST", headers: { "Content-Type": "application/json", ...authHeaders() }, body: JSON.stringify({ transcript: transcriptData.transcript, source: "voice" }) });
          const confirmationData = await confirmation.json();
          if (!confirmation.ok) throw new Error(confirmationData.detail || "Seller confirmation was not accepted.");
          setError(confirmationData.provider_verification_required ? "Seller confirmation recorded. Provider verification is still required before revenue is realized." : "Payment confirmation recorded.");
          await loadFinancials(sellerId, authToken);
        } catch (err) { setError(err instanceof Error ? err.message : "Payment confirmation failed."); }
      };
      recorder.onstart = () => setPaymentListening(true);
      recorder.start();
      window.setTimeout(() => recorder.state === "recording" && recorder.stop(), 4000);
    } catch { setPaymentListening(false); setError("Microphone access was not available."); }
  }

  return (
    <main className="page">
      <header className="topbar"><div className="brand">GramSell <span>AI</span></div><div className="topbarRight"><div className="statusPill"><i /> Live Intelligence</div>{authToken ? <button className="authButton" onClick={logout}>Sign out</button> : null}</div></header>
      <section className="content">
        {!authToken && <section className="card authCard"><div className="cardHeader"><div><h2>{authMode === "login" ? "Seller sign in" : "Create seller account"}</h2><p>{firebaseConfigured ? "Firebase Authentication protects your account." : "Local development authentication is active."}</p></div><div className="liveDot"><i /> Protected</div></div><div className="authGrid">{authMode === "register" && <div className="field"><label>Display name</label><input value={displayName} onChange={e => setDisplayName(e.target.value)} /></div>}<div className="field"><label>Email</label><input type="email" value={email} onChange={e => setEmail(e.target.value)} autoComplete="email" /></div><div className="field"><label>Password</label><input type="password" value={password} onChange={e => setPassword(e.target.value)} autoComplete={authMode === "login" ? "current-password" : "new-password"} /></div></div><div className="actions"><button className="primary" onClick={authenticate} disabled={authBusy}>{authBusy ? "Working..." : authMode === "login" ? "Sign in" : "Create account"}</button><button className="secondary" onClick={() => setAuthMode(authMode === "login" ? "register" : "login")}>{authMode === "login" ? "Create account" : "Back to sign in"}</button></div></section>}

        <div className="hero"><div><div className="eyebrow">REAL-TIME RURAL BUSINESS INTELLIGENCE</div><h1>One business team.<br /><span>Every product.</span></h1><p>Voice, image and text flow through grounded business intelligence. Real data only.</p></div><div className="heroOrb"><div className="orbCore" /></div></div>
        <div className="grid">
          <div className={`card mainCard ${!authToken ? "locked" : ""}`}>
            <div className="cardHeader"><div><h2>Seller workspace</h2><p>Give the agents a real business request.</p></div><div className="liveDot"><i /> Secure</div></div>
            <div className="agents">{agents.map(([id, name, role]) => { const state = agentStates[id] || "idle"; return <div className={`agent ${state}`} key={id}><div className="agentLight" /><div className="agentGlyph">{name.slice(0,1)}</div><strong>{name}</strong><span>{state === "running" ? "Working" : state === "completed" ? "Done" : role}</span></div>; })}</div>
            <div className="stack workspace">
              <div className="row"><div className="field"><label>Seller ID</label><input value={sellerId} readOnly inputMode="numeric" /></div><div className="field"><label>Country</label><select value={country} onChange={e => changeCountry(e.target.value)}><option value="BD">Bangladesh</option><option value="IN">India</option><option value="ZA">South Africa</option></select></div></div>
              <div className="row"><div className="field"><label>Language</label><select value={language} onChange={e => setLanguage(e.target.value)}>{config[country].languages.map(item => <option value={item} key={item}>{languageLabels[item] || item}</option>)}</select></div><div className="field"><label>Currency</label><input value={config[country].currency} readOnly /></div></div>
              <div className="field"><label>Business request</label><textarea value={message} onChange={e => setMessage(e.target.value)} placeholder="Speak, type, or add a product image..." /></div>
              <div className="actions"><button type="button" className={`secondary ${listening ? "active" : ""}`} onClick={startVoiceInput} disabled={transcribing}>{listening ? "Stop listening" : transcribing ? "Transcribing..." : "Speak"}</button><label className="secondary upload">{analyzingImage ? "Analyzing..." : "Add image"}<input type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={e => { const file = e.target.files?.[0]; if (file) analyzeImage(file); e.currentTarget.value = ""; }} /></label><button className="primary" onClick={runAgents} disabled={busy}>{busy ? "Agents working..." : "Run agents"}</button></div>
              {error && <div className="error">{error}</div>}
            </div>
          </div>
          <section className="card paymentCard"><div className="cardHeader"><div><h2>Real payment destination</h2><p>Use a real seller destination for the live payment demonstration. Provider verification remains separate.</p></div><div className="liveDot"><i /> Real destination</div></div><div className="row"><div className="field"><label>Provider</label><select value={paymentProvider} onChange={e => setPaymentProvider(e.target.value)}><option value="bkash">bKash</option><option value="nagad">Nagad</option><option value="upi">UPI</option><option value="eft">EFT</option></select></div><div className="field"><label>Seller destination</label><input value={paymentDestination} onChange={e => setPaymentDestination(e.target.value)} placeholder="Enter the seller's real payment destination" /></div></div><div className="actions"><button className="secondary" onClick={configurePayment}>Save payment destination</button></div>{paymentInfo && <div className="evidenceBar"><span>{paymentInfo.provider}</span><strong>{paymentInfo.destination}</strong><small>Real destination saved. Automatic verification requires the provider's official API or webhook.</small></div>}</section>

<section className="card paymentCard"><div className="cardHeader"><div><h2>10-day weather forecast</h2><p>Google Weather API daily forecast, up to ten days.</p></div><div className="liveDot"><i /> Google Weather</div></div><div className="actions"><button className="secondary" onClick={loadForecast} disabled={forecastBusy}>{forecastBusy ? "Loading..." : "Load 10-day forecast"}</button></div>{forecast.length > 0 && <div className="financialGrid">{forecast.map((day, index) => <div key={index}><small>{day.interval?.startTime || `Day ${index + 1}`}</small><strong>{day.daytimeForecast?.weatherCondition?.description || day.weatherCondition?.description || "Forecast"}</strong><small>{day.temperature?.max?.degrees ?? "-"} / {day.temperature?.min?.degrees ?? "-"} C</small></div>)}</div>}</section>

<section className="card paymentCard"><div className="cardHeader"><div><h2>Payment confirmation</h2><p>Seller voice confirmation never creates verified revenue.</p></div><div className="liveDot"><i /> Verified only</div></div><div className="row"><div className="field"><label>Order ID</label><input value={paymentOrderId} onChange={e => setPaymentOrderId(e.target.value)} inputMode="numeric" /></div><div className="field"><label>Transcript</label><input value={paymentTranscript} readOnly /></div></div><div className="actions"><button className={`secondary ${paymentListening ? "active" : ""}`} onClick={confirmPaymentByVoice} disabled={paymentListening}>{paymentListening ? "Listening..." : "Confirm by voice"}</button></div></section>
        <aside className="card intelligenceCard"><div className="cardHeader"><div><h2>Grounded intelligence</h2><p>External evidence is used only when relevant.</p></div></div><div className="signal"><span>MARKET</span><strong>Maps Grounding</strong><small>Nearby market intelligence</small></div><div className="signal"><span>WEATHER</span><strong>Forecast-aware</strong><small>Risk planning uses available forecast evidence</small></div><div className="signal"><span>PAYMENT</span><strong>Verified only</strong><small>Provider verification required for realized revenue</small></div><div className="signal"><span>RISK</span><strong>Evidence profile</strong><small>No fabricated bank credit score</small></div></aside>
        </div>
        {authToken && financials && <section className="card financialCard"><div className="cardHeader"><div><h2>Private financials</h2><p>Seller-only values from verified records.</p></div><div className="liveDot"><i /> Private</div></div><div className="financialGrid"><div><small>Verified revenue</small><strong>{financials.currency} {financials.verified_revenue}</strong></div><div><small>Recorded cost</small><strong>{financials.currency} {financials.recorded_cost}</strong></div><div><small>Recorded expenses</small><strong>{financials.currency} {financials.recorded_expenses}</strong></div><div><small>Net profit</small><strong>{financials.currency} {financials.net_profit}</strong></div><div><small>Net margin</small><strong>{financials.net_margin_percent}%</strong></div></div></section>}
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
