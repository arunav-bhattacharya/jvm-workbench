// JVM Workbench worker. Every page and file needs a signed-in Google account on ALLOWED_EMAILS,
// except the sign-in page itself and its cover art.
//   GET  /login                 sign-in page (Google button)                     public
//   GET  /api/config            { clientId }                                     public
//   POST /api/session           body { credential: <Google ID token> } -> session cookie if the email is enrolled
//   POST /api/logout            clears the session cookie
//   GET  /api/me                { name, email, picture }                         signed in
//   GET  /api/progress          the learner's saved progress                     signed in
//   PUT  /api/progress          merges the sent progress into the saved copy and returns the result
// KV keys are prefixed "jvmwb:" so this course can share a namespace with another course.
const JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs";
const ISSUERS = ["https://accounts.google.com", "accounts.google.com"];
const COOKIE = "jvmwb_s", DAYS = 30, MAX_BYTES = 512 * 1024, PREFIX = "jvmwb:";
const isPublicAsset = (path) => path.startsWith("/fonts/"); // the sign-in page needs the fonts
let jwksCache = { at: 0, keys: [] }, hmacKey = null;

const enc = new TextEncoder(), dec = new TextDecoder();
const b64u = (bytes) => btoa(String.fromCharCode(...new Uint8Array(bytes))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const unb64u = (s) => Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/").padEnd(Math.ceil(s.length / 4) * 4, "=")), (c) => c.charCodeAt(0));
const json = (data, status = 200, headers = {}) => new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json", "cache-control": "no-store", ...headers } });
export const enrolled = (env, email) => (env.ALLOWED_EMAILS || "").toLowerCase().split(/[\s,]+/).filter(Boolean).includes((email || "").toLowerCase());

async function googleKeys() {
  if (Date.now() - jwksCache.at < 3600_000 && jwksCache.keys.length) return jwksCache.keys;
  const { keys } = await (await fetch(JWKS_URL)).json();
  jwksCache = { at: Date.now(), keys };
  return keys;
}
async function verifyGoogle(token, clientId) {
  const p = (token || "").split(".");
  if (p.length !== 3) throw new Error("bad token");
  const head = JSON.parse(dec.decode(unb64u(p[0]))), body = JSON.parse(dec.decode(unb64u(p[1])));
  if (head.alg !== "RS256") throw new Error("bad alg");
  const jwk = (await googleKeys()).find((k) => k.kid === head.kid);
  if (!jwk) throw new Error("unknown key");
  const key = await crypto.subtle.importKey("jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);
  if (!(await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, unb64u(p[2]), enc.encode(p[0] + "." + p[1])))) throw new Error("bad signature");
  if (body.aud !== clientId || !ISSUERS.includes(body.iss) || !(body.exp > Date.now() / 1000 - 60) || !body.sub || body.email_verified === false) throw new Error("bad claims");
  return body;
}
async function key(env) { // signs session cookies; made once and kept in KV
  if (hmacKey) return hmacKey;
  let raw = await env.PROGRESS.get(PREFIX + "cfg:session-key");
  if (!raw) { raw = b64u(crypto.getRandomValues(new Uint8Array(32))); await env.PROGRESS.put(PREFIX + "cfg:session-key", raw); }
  hmacKey = await crypto.subtle.importKey("raw", unb64u(raw), { name: "HMAC", hash: "SHA-256" }, false, ["sign", "verify"]);
  return hmacKey;
}
async function makeCookie(env, who) {
  const payload = b64u(enc.encode(JSON.stringify({ ...who, exp: Math.floor(Date.now() / 1000) + DAYS * 86400 })));
  const sig = b64u(await crypto.subtle.sign("HMAC", await key(env), enc.encode(payload)));
  return `${COOKIE}=${payload}.${sig}; Path=/; Max-Age=${DAYS * 86400}; HttpOnly; Secure; SameSite=Lax`;
}
async function session(request, env) {
  const m = (request.headers.get("cookie") || "").match(new RegExp(`(?:^|; )${COOKIE}=([^;]+)`));
  if (!m) return null;
  const [payload, sig] = m[1].split(".");
  if (!payload || !sig) return null;
  try {
    if (!(await crypto.subtle.verify("HMAC", await key(env), unb64u(sig), enc.encode(payload)))) return null;
    const s = JSON.parse(dec.decode(unb64u(payload)));
    if (!(s.exp > Date.now() / 1000) || !enrolled(env, s.email)) return null; // taken off the list -> signed out
    return s;
  } catch { return null; }
}

/* Progress merge, the same rules as the page uses: later done/undone event wins, best quiz score,
   the card copy with more reviews, the larger daily count, the non-empty explanation, the later pace. */
const later = (a, b) => (!a ? b : !b ? a : a > b ? a : b);
export function merge(a, b) {
  a = a && typeof a === "object" ? a : {}; b = b && typeof b === "object" ? b : {};
  const out = { done: {}, undone: {}, quiz: {}, tquiz: {}, cards: {}, days: {}, explain: {} };
  const ids = new Set([...Object.keys(a.done || {}), ...Object.keys(b.done || {}), ...Object.keys(a.undone || {}), ...Object.keys(b.undone || {})]);
  for (const id of ids) {
    const d = later((a.done || {})[id], (b.done || {})[id]), u = later((a.undone || {})[id], (b.undone || {})[id]);
    if (d && (!u || d > u)) out.done[id] = d;
    if (u) out.undone[id] = u;
  }
  for (const k of ["quiz", "tquiz"]) for (const src of [a[k] || {}, b[k] || {}]) for (const [id, v] of Object.entries(src)) out[k][id] = Math.max(out[k][id] || 0, +v || 0);
  for (const src of [a.cards || {}, b.cards || {}]) for (const [id, c] of Object.entries(src)) {
    const cur = out.cards[id];
    if (!cur || (c.reps || 0) > (cur.reps || 0) || ((c.reps || 0) === (cur.reps || 0) && (c.last || 0) > (cur.last || 0))) out.cards[id] = c;
  }
  for (const src of [a.days || {}, b.days || {}]) for (const [d, e] of Object.entries(src)) {
    const cur = out.days[d] || { l: 0, r: 0 };
    out.days[d] = { l: Math.max(cur.l || 0, e.l || 0), r: Math.max(cur.r || 0, e.r || 0) };
  }
  for (const src of [b.explain || {}, a.explain || {}]) for (const [id, t] of Object.entries(src)) if (t) out.explain[id] = t;
  const pa = a.paceAt || "", pb = b.paceAt || "";
  const pick = pb > pa ? b : a;
  if (pick.pace) { out.pace = pick.pace; out.paceAt = pick.paceAt || ""; }
  return out;
}

const LOGIN = (clientId) => `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Sign in · JVM Workbench</title>
<style>
@font-face{font-family:'Instrument Serif';font-style:normal;font-weight:400;font-display:swap;src:url(/fonts/instrument-serif-400.woff2) format('woff2')}
@font-face{font-family:'Instrument Serif';font-style:italic;font-weight:400;font-display:swap;src:url(/fonts/instrument-serif-400i.woff2) format('woff2')}
@font-face{font-family:'Newsreader';font-style:normal;font-weight:400;font-display:swap;src:url(/fonts/newsreader-400.woff2) format('woff2')}
@font-face{font-family:'Inter';font-style:normal;font-weight:600;font-display:swap;src:url(/fonts/inter-600.woff2) format('woff2')}
:root{color-scheme:light;--ink:#fcfcfb;--fg:#23262e;--mute:#575b66;--faint:#8b909b;--ember:#1f5fc4;--gold:#1a4a96;--bad:#b5303a;--rule:#e2e5eb}
:root.dark{color-scheme:dark;--ink:#0b1220;--fg:#e4e9f3;--mute:#a3b0c6;--faint:#6f7e98;--ember:#5b9bff;--gold:#8ec5ff;--bad:#f07a86;--rule:#24324f}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;display:grid;place-items:center;background:var(--ink);color:var(--fg);font:400 20px/1.46 "Newsreader",Georgia,serif;padding:24px max(16px,env(safe-area-inset-left,0px))}
.card{width:100%;max-width:440px;display:grid;gap:18px;justify-items:center;text-align:center}
.label{font:600 13px -apple-system,BlinkMacSystemFont,"SF Pro Text","Inter",system-ui,sans-serif;color:var(--mute)}
h1{font:400 56px/1.02 "Instrument Serif",Georgia,serif;margin:0}h1 i{color:var(--gold)}
p{margin:0;color:var(--mute);max-width:34ch}
.rule{width:100%;border-top:1px solid var(--rule)}
#g{min-height:44px;display:grid;place-items:center}
.msg{min-height:1.5em;font:15px -apple-system,BlinkMacSystemFont,"Inter",system-ui,sans-serif;color:var(--mute)}.msg.bad{color:var(--bad)}
</style>
<script>try{if((JSON.parse(localStorage.getItem('jvmwb-v1')||'{}').theme)==='dark')document.documentElement.className='dark'}catch(e){}</script>
</head><body><main class="card">
<svg width="44" height="44" viewBox="0 0 22 22" aria-hidden="true"><g fill="var(--ember)"><circle cx="4" cy="4" r="1.35"/><circle cx="4" cy="11" r="1.35"/><circle cx="4" cy="18" r="1.35"/><circle cx="11" cy="11" r="2.1"/></g><g fill="var(--ember)" fill-opacity=".6"><circle cx="11" cy="4" r="1.35"/><circle cx="11" cy="18" r="1.35"/></g><g fill="var(--ember)" fill-opacity=".3"><circle cx="18" cy="4" r="1.35"/><circle cx="18" cy="11" r="1.35"/><circle cx="18" cy="18" r="1.35"/></g><circle cx="11" cy="11" r="6" fill="none" stroke="var(--ember)" stroke-opacity=".7" stroke-width=".9"/></svg>
<span class="label">Concurrency, generics and patterns in Java and Kotlin</span>
<h1>JVM <i>Workbench</i></h1>
<div class="rule"></div>
<p>Sign in with your enrolled Google account. Your progress follows you between devices.</p>
<div id="g"></div><div class="msg" id="msg" role="status">Loading Google sign-in…</div>
</main>
<script>
var msg=document.getElementById('msg');
function say(t,bad){msg.textContent=t;msg.className='msg'+(bad?' bad':'');}
async function done(r){say('Checking your account…');
 var x=await fetch('/api/session',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({credential:r.credential})});
 if(x.ok){var n=new URLSearchParams(location.search).get('next')||'/';if(n.charAt(0)!=='/'||n.charAt(1)==='/')n='/';location.replace(n+location.hash);}
 else say(x.status===403?'This Google account is not enrolled. Ask the course owner to add it.':'Sign-in failed. Please try again.',true);}
function start(){
 var light=document.documentElement.className!=='dark';
 google.accounts.id.initialize({client_id:${JSON.stringify(clientId)},callback:done,auto_select:true,itp_support:true});
 google.accounts.id.renderButton(document.getElementById('g'),{theme:light?'outline':'filled_black',size:'large',shape:'pill',text:'signin_with',width:260});
 google.accounts.id.prompt();
 setTimeout(function(){if(document.querySelector('#g iframe, #g div[role=button]'))say('');else say('Google sign-in did not load. If this site was set up just now, add its address to the Google client\\'s authorized JavaScript origins, then try again.',true);},5000);}
</script>
<script src="https://accounts.google.com/gsi/client" async defer onload="start()" onerror="say('Could not reach Google. Check your connection and reload.',true)"></script>
</body></html>`;

export default {
  async fetch(request, env) {
    const url = new URL(request.url), path = url.pathname;
    const clientId = env.GOOGLE_CLIENT_ID || "";
    // public: the sign-in page, its art, and the sign-in API
    if (path === "/login") return new Response(LOGIN(clientId), { headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" } });
    if (isPublicAsset(path)) return env.ASSETS.fetch(request);
    if (path === "/api/config") return json({ clientId });
    if (path === "/api/session" && request.method === "POST") {
      let who;
      try { const { credential } = await request.json(); who = await verifyGoogle(credential, clientId); }
      catch { return json({ error: "sign in again" }, 401); }
      if (!enrolled(env, who.email)) return json({ error: "not enrolled" }, 403);
      const cookie = await makeCookie(env, { sub: who.sub, email: who.email, name: who.given_name || who.name || "", picture: who.picture || "" });
      return json({ ok: true }, 200, { "set-cookie": cookie });
    }
    if (path === "/api/logout") return json({ ok: true }, 200, { "set-cookie": `${COOKIE}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax` });

    // everything else needs an enrolled, signed-in learner
    const s = await session(request, env);
    if (!s) {
      if (path.startsWith("/api/") || path.endsWith(".json")) return json({ error: "sign in" }, 401);
      return new Response(null, { status: 302, headers: { location: "/login?next=" + encodeURIComponent(path + url.search), "cache-control": "no-store" } });
    }
    if (path === "/api/me") return json({ name: s.name, email: s.email, picture: s.picture });
    if (path === "/api/progress") {
      const k = PREFIX + "u:" + s.sub;
      if (request.method === "GET") return json((await env.PROGRESS.get(k, "json")) || {});
      if (request.method === "PUT") {
        const text = await request.text();
        if (text.length > MAX_BYTES) return json({ error: "too large" }, 413);
        let data; try { data = JSON.parse(text); } catch { return json({ error: "bad json" }, 400); }
        if (typeof data !== "object" || data === null || Array.isArray(data)) return json({ error: "bad shape" }, 400);
        const merged = merge((await env.PROGRESS.get(k, "json")) || {}, data);
        await env.PROGRESS.put(k, JSON.stringify({ ...merged, email: s.email, savedAt: new Date().toISOString() }));
        return json(merged);
      }
      return json({ error: "method not allowed" }, 405);
    }
    if (path.startsWith("/api/")) return json({ error: "not found" }, 404);
    const res = await env.ASSETS.fetch(request);
    const out = new Response(res.body, res);
    out.headers.set("cache-control", "private, no-cache");
    return out;
  },
};
