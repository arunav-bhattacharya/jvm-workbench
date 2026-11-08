/* JVM Workbench: a single-page course reader. No framework, no build step for the script.
   State lives in localStorage under one key; every read and write is guarded. */
(function () {
  "use strict";
  const C = JSON.parse(document.getElementById("course").textContent);
  const L = C.lessons;
  const T = Object.fromEntries(C.tracks.map((t, i) => [t.id, Object.assign(t, { idx: i + 1 })]));
  // parts group related tracks (course.json "sections"); without them the tracks are one flat list
  const PARTS = (C.sections || []).map((p, i) => Object.assign(p, { idx: i + 1 }));
  const partOf = {};
  PARTS.forEach((p) => p.tracks.forEach((id) => { partOf[id] = p; }));
  const trackTag = (t) => (partOf[t.id] ? `Part ${partOf[t.id].idx} · ` : "") + `Track ${pad(t.idx)}`;
  const ORDER = C.order;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const pad = (n) => String(n).padStart(2, "0");

  /* ---------------- storage ---------------- */
  const KEY = "jvmwb-v1";
  const blank = () => ({ v: 1, theme: null, code: "both", done: {}, undone: {}, paceAt: "", quiz: {}, tquiz: {}, cards: {}, explain: {}, days: {}, pace: 5, open: {}, timer: null, seenSetup: false });
  let S = blank();
  try { S = Object.assign(blank(), JSON.parse(localStorage.getItem(KEY) || "{}")); } catch (e) { /* private window or blocked storage */ }
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) { /* storage unavailable */ } };

  /* ---------------- moving progress between devices ----------------
     Progress lives in this browser. The Plan page copies it out as text and imports it on another
     device; importing merges, so nothing done on either device is lost. */
  const SYNC = ["done", "undone", "quiz", "tquiz", "cards", "days", "explain", "pace", "paceAt"];
  const syncDoc = () => Object.fromEntries(SYNC.map((k) => [k, S[k]]));
  const later = (a, b) => (!a ? b : !b ? a : a > b ? a : b);
  function mergeInto(x) {
    if (!x || typeof x !== "object") return;
    const done = {}, undone = {};
    const ids = new Set([...Object.keys(S.done), ...Object.keys(S.undone || {}), ...Object.keys(x.done || {}), ...Object.keys(x.undone || {})]);
    for (const id of ids) {
      const d = later(S.done[id], (x.done || {})[id]), u = later((S.undone || {})[id], (x.undone || {})[id]);
      if (d && (!u || d > u)) done[id] = d;
      if (u) undone[id] = u;
    }
    S.done = done; S.undone = undone;
    for (const k of ["quiz", "tquiz"]) for (const [id, v] of Object.entries(x[k] || {})) S[k][id] = Math.max(S[k][id] || 0, +v || 0);
    for (const [id, c] of Object.entries(x.cards || {})) {
      const cur = S.cards[id];
      if (!cur || (c.reps || 0) > (cur.reps || 0) || ((c.reps || 0) === (cur.reps || 0) && (c.last || 0) > (cur.last || 0))) S.cards[id] = c;
    }
    for (const [d, e] of Object.entries(x.days || {})) { const cur = S.days[d] || { l: 0, r: 0 }; S.days[d] = { l: Math.max(cur.l || 0, e.l || 0), r: Math.max(cur.r || 0, e.r || 0) }; }
    for (const [id, t] of Object.entries(x.explain || {})) if (t && !S.explain[id]) S.explain[id] = t;
    if (x.pace && (x.paceAt || "") > (S.paceAt || "")) { S.pace = x.pace; S.paceAt = x.paceAt; }
  }

  /* ---------------- dates ---------------- */
  const DAY = 864e5;
  const dayNum = (d = new Date()) => Math.floor((d.getTime() - d.getTimezoneOffset() * 60000) / DAY);
  const today = () => dayNum();
  const ymdOf = (n) => new Date(n * DAY).toISOString().slice(0, 10);
  const inDays = (n) => (n <= 0 ? "today" : n === 1 ? "tomorrow" : `in ${n} days`);
  function logDay(kind, k = 1) {
    const d = ymdOf(today());
    const e = S.days[d] || { l: 0, r: 0 };
    e[kind] = (e[kind] || 0) + k;
    S.days[d] = e;
  }

  /* ---------------- spaced repetition: FSRS-4.5, default weights, target retention 0.9 ---------------- */
  const W = [0.4872, 1.4003, 3.7145, 13.8206, 5.1618, 1.2298, 0.8975, 0.031, 1.6474, 0.1367, 1.0461, 2.1072, 0.0793, 0.3246, 1.587, 0.2272, 2.8755];
  const DECAY = -0.5, FACTOR = 19 / 81, TARGET = 0.9;
  const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
  const recall = (t, s) => Math.pow(1 + FACTOR * t / s, DECAY);
  const ivlOf = (s) => Math.max(1, Math.round((s / FACTOR) * (Math.pow(TARGET, 1 / DECAY) - 1)));
  const D0 = (g) => clamp(W[4] - (g - 3) * W[5], 1, 10);
  const nextD = (d, g) => clamp(W[7] * D0(3) + (1 - W[7]) * (d - W[6] * (g - 3)), 1, 10);
  const sUp = (d, s, r, g) => s * (Math.exp(W[8]) * (11 - d) * Math.pow(s, -W[9]) * (Math.exp(W[10] * (1 - r)) - 1) * (g === 2 ? W[15] : 1) * (g === 4 ? W[16] : 1) + 1);
  const sLapse = (d, s, r) => W[11] * Math.pow(d, -W[12]) * (Math.pow(s + 1, W[13]) - 1) * Math.exp(W[14] * (1 - r));
  function hash(s) { let h = 2166136261; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0) / 4294967296; }
  function schedule(c, g, id, dry) {
    const now = today();
    const x = Object.assign({}, c);
    if (x.s == null) { x.s = W[g - 1]; x.d = D0(g); }
    else {
      const r = recall(Math.max(0, now - x.last), x.s);
      const s = g === 1 ? Math.min(x.s, sLapse(x.d, x.s, r)) : sUp(x.d, x.s, r, g);
      x.d = nextD(x.d, g); x.s = s;
      if (g === 1) x.lapses = (x.lapses || 0) + 1;
    }
    let ivl = g === 1 ? 1 : ivlOf(x.s);
    if (ivl > 2) ivl = Math.max(2, Math.round(ivl * (0.95 + 0.1 * hash(id + ":" + now)))); // small fuzz spreads siblings apart
    x.reps = (x.reps || 0) + 1; x.last = now; x.due = now + ivl; x.ivl = ivl;
    if ((x.lapses || 0) >= 8) x.leech = true;
    if (!dry) S.cards[id] = x;
    return x;
  }
  const ivlLabel = (n) => (n < 30 ? `${n}d` : n < 365 ? `${Math.round(n / 30)}mo` : `${(n / 365).toFixed(1)}y`);
  function addCards(lid) {
    const l = L[lid]; if (!l || !l.ready) return 0;
    let n = 0;
    l.cards.forEach((_, i) => { const id = `${lid}:c${i}`; if (!S.cards[id]) { S.cards[id] = { due: today() + 1, added: today() }; n++; } });
    return n;
  }
  function addMissed(key, qi) {
    const id = `${key}:q${qi}`;
    if (!S.cards[id]) S.cards[id] = { due: today() + 1, added: today() };
  }
  function cardData(id) {
    const [key, k] = id.split(":");
    const i = +k.slice(1);
    if (k[0] === "c") { const l = L[key]; return l && l.cards && l.cards[i] ? { kind: "flash", lid: key, front: l.cards[i].front, back: l.cards[i].back } : null; }
    if (k[0] === "q") {
      if (L[key]) { const q = L[key].quiz && L[key].quiz[i]; return q ? { kind: "mcq", lid: key, q } : null; }
      const t = T[key]; const q = t && t.quiz[i]; return q ? { kind: "mcq", tid: key, q } : null;
    }
    return null;
  }
  const dueIds = () => Object.entries(S.cards).filter(([id, c]) => c.due <= today() && cardData(id)).sort((a, b) => a[1].due - b[1].due || hash(a[0]) - hash(b[0])).map(([id]) => id);
  const DAILY_CAP = 40;

  /* ---------------- progress helpers ---------------- */
  const isDone = (id) => !!S.done[id];
  const nextUp = () => ORDER.find((id) => !S.done[id]) || null;
  const doneCount = () => ORDER.filter((id) => S.done[id]).length;
  const trackDone = (t) => t.lessons.filter((id) => S.done[id]).length;
  function setDone(id, on) {
    if (on && !S.done[id]) { S.done[id] = new Date().toISOString(); const n = addCards(id); logDay("l"); save(); toast(n ? `Done. ${n} cards join your review from tomorrow.` : "Marked done."); }
    else if (!on && S.done[id]) { delete S.done[id]; S.undone[id] = new Date().toISOString(); for (const k of Object.keys(S.cards)) if (k.startsWith(id + ":c") && !S.cards[k].reps) delete S.cards[k]; save(); toast("Marked not done."); }
    render();
  }
  // the plan is counted in course weeks and days, never calendar dates: lesson k sits at
  // week floor(k / pace) + 1, day k % pace + 1, where pace is the study days per week
  const pace = () => S.pace || 5;
  const wd = (id) => { const k = ORDER.indexOf(id); return { w: Math.floor(k / pace()) + 1, d: (k % pace()) + 1 }; };
  const wdLabel = (id) => { const x = wd(id); return `Week ${x.w} · Day ${x.d}`; };
  const wdShort = (id) => { const x = wd(id); return `W${x.w} · D${x.d}`; };
  const totalWeeks = () => Math.ceil(ORDER.length / pace());
  function studiedLast7() {
    let n = 0; for (let d = today() - 6; d <= today(); d++) { const e = S.days[ymdOf(d)]; if (e && (e.l || e.r)) n++; }
    return n;
  }
  const cellState = (id) => (S.done[id] ? "done" : id === nextUp() ? "here" : "");

  /* ---------------- tiny UI helpers ---------------- */
  let toastTimer;
  function toast(msg) {
    let el = $(".toast"); if (!el) { el = document.createElement("div"); el.className = "toast"; el.setAttribute("role", "status"); document.body.appendChild(el); }
    el.textContent = msg; el.hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => (el.hidden = true), 3200);
  }
  async function copyText(text, btn) {
    try { await navigator.clipboard.writeText(text); if (btn) { btn.textContent = "Copied"; setTimeout(() => (btn.textContent = "Copy"), 1400); } }
    catch (e) { toast("Copy is blocked here. Select the text and copy it by hand."); }
  }
  const icon = {
    toc: '<svg width="16" height="16" viewBox="0 0 20 20" aria-hidden="true"><path d="M3.5 5h13M3.5 10h13M3.5 15h8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>',
    collapse: '<svg width="16" height="16" viewBox="0 0 20 20" aria-hidden="true"><path d="M8 5l5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    search: '<svg width="17" height="17" viewBox="0 0 20 20" aria-hidden="true"><circle cx="8.5" cy="8.5" r="5.5" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M12.6 12.6 17 17" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>',
    video: '<svg width="14" height="14" viewBox="0 0 20 20" aria-hidden="true"><rect x="1.5" y="4.5" width="12" height="11" rx="2.2" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M13.5 8.6 18.5 6v8l-5-2.6z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>',
    menu: '<svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true"><path d="M3 5h14M3 10h14M3 15h14" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>',
    sun: '<svg width="18" height="18" viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="3.6" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M10 1.8v2.2M10 16v2.2M1.8 10H4M16 10h2.2M4.2 4.2l1.6 1.6M14.2 14.2l1.6 1.6M4.2 15.8l1.6-1.6M14.2 5.8l1.6-1.6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>',
    moon: '<svg width="18" height="18" viewBox="0 0 20 20" aria-hidden="true"><path d="M16.5 12.4A7 7 0 0 1 7.6 3.5a7 7 0 1 0 8.9 8.9z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>',
    timer: '<svg width="18" height="18" viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="11" r="6.5" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M10 7.5V11l2.4 1.6M8 2.2h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>',
  };
  const brandMark = '<svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true">' + [0, 1, 2].map((r) => ["var(--ember)", "color-mix(in srgb, var(--ember) 65%, var(--ink))", "color-mix(in srgb, var(--ember) 35%, var(--ink))"].map((c, k) => `<circle cx="${4 + k * 7}" cy="${4 + r * 7}" r="${r === 1 && k === 1 ? 2.1 : 1.35}" fill="${c}"/>`).join("")).join("") + '<circle cx="11" cy="11" r="6" fill="none" stroke="var(--ember)" stroke-opacity=".7" stroke-width=".9"/></svg>';
  const vbadge = (id) => (L[id] && L[id].vid ? `<span class="vbadge" title="${L[id].vid === 1 ? "Has a video" : `Has ${L[id].vid} videos`}" aria-label="has a video">${icon.video}</span>` : "");
  const cells = (ids, big) => `<span class="draft" aria-hidden="true">${ids.map((id) => `<i class="cell${big ? " lg" : ""} ${cellState(id)}"></i>`).join("")}</span>`;
  function codeBox(c, title) {
    if (!c) return "";
    return `<div class="codebox"><div class="bar"><span class="nm">${esc(title || c.title || c.lang)}</span><span class="label">${esc(c.lang || "")}</span><button class="copy" data-act="copy-code">Copy</button></div>
      <pre><code>${c.html}</code></pre>${c.run ? `<div class="run"><span>$</span><code>${esc(c.run)}</code><button class="copy" data-act="copy" data-text="${esc(c.run)}">Copy</button></div>` : ""}</div>`;
  }

  // Java and Kotlin versions of one sample; html[data-code] decides which shows
  const LANGS = { java: "Java", kotlin: "Kotlin" };
  const pairBar = () => `<div class="pairbar" role="group" aria-label="Code language">${[["java", "Java"], ["kotlin", "Kotlin"], ["both", "Both"]].map(([k, v]) => `<button data-act="lang" data-lang="${k}">${v}</button>`).join("")}</div>`;
  function codePair(c, title, side) {
    if (!c) return "";
    if (!c.alt || !LANGS[c.lang] || !LANGS[c.alt.lang]) return codeBox(c, title);
    const items = [c, c.alt].sort((a) => (a.lang === "java" ? -1 : 1));
    return `<div class="pair${side ? " cols2" : ""}">${pairBar()}${items.map((x) => `<div class="pi" data-lang="${x.lang}">${codeBox(x, x === c ? title || x.title : x.title || LANGS[x.lang])}</div>`).join("")}</div>`;
  }
  function prePair(a, b) {
    if (!b || !b.html || !LANGS[a.lang] || !LANGS[b.lang]) return a.html ? `<pre class="code"><code>${a.html}</code></pre>` : "";
    const items = [a, b].sort((x) => (x.lang === "java" ? -1 : 1));
    return `<div class="pair">${pairBar()}${items.map((x) => `<div class="pi" data-lang="${x.lang}"><span class="lg">${LANGS[x.lang]}</span><pre class="code"><code>${x.html}</code></pre></div>`).join("")}</div>`;
  }
  const setCodePref = (v) => { S.code = v; document.documentElement.setAttribute("data-code", v); save(); };

  /* ---------------- frame ---------------- */
  const app = $("#app");
  let mobileOpen = false, deskOpen = true;
  const effectiveTheme = () => S.theme || "light"; // light unless the learner picks dark
  function frame() {
    const due = dueIds().length;
    app.innerHTML = `
    <header class="top">
      <button class="iconbtn" data-act="menu" aria-label="Show or hide contents">${icon.menu}</button>
      <button class="brand" data-go="home" aria-label="JVM Workbench home">${brandMark}<b>JVM <i>Workbench</i></b></button>
      <span class="spacer"></span>
      <div class="gsearch" id="gsearch-box"><span class="gs-ic">${icon.search}</span>
        <input id="gsearch" type="search" autocomplete="off" spellcheck="false" placeholder="Search everything" aria-label="Search lessons, labs, quizzes, cheat sheets and terms" aria-controls="gres" aria-expanded="false">
        <kbd class="gs-k hide-sm">/</kbd><div class="gres" id="gres" role="listbox" hidden></div></div>
      <button class="chip ${due ? "" : "quiet"}" data-go="review" title="Spaced review"><span class="dot"></span><span class="tnum">${due}</span><span class="hide-sm">&nbsp;due</span></button>
      <button class="iconbtn" data-act="timer" aria-label="Focus timer" title="35-minute focus timer">${icon.timer}</button>
      <button class="switch" data-act="theme" role="switch" aria-checked="${effectiveTheme() === "dark"}" aria-label="Dark mode" title="Dark mode"><span class="tr"></span><span class="kn"></span></button>
    </header>
    <div class="scrim ${mobileOpen ? "on" : ""}" data-act="close-menu"></div>
    <nav class="side ${(isDesk() ? !deskOpen : !mobileOpen) ? "closed" : ""}" aria-label="Contents" id="side"></nav>
    <main class="main ${isDesk() && !deskOpen ? "wide" : ""}" id="main"><div class="wrap" id="page"></div></main>
    <div id="timer-slot"></div>`;
  }
  const isDesk = () => matchMedia("(min-width: 1024px)").matches;

  const mmss = (t) => `${Math.floor(t / 60)}:${String(Math.round(t % 60)).padStart(2, "0")}`;
  /* concept videos: the Kokoro track is in the file; other narrators are separate tracks played in sync */
  const VOICE_LABEL = { "us-f": "American · female", orig: "American · female (original)", "in-m": "Indian · male" };
  const VOICE_ORDER = ["us-f", "orig", "in-m"];
  const RATES = ["0.75", "0.9", "1", "1.1", "1.25", "1.5", "2"];
  const vidVoices = (voices) => VOICE_ORDER.filter((k) => k === "orig" || (voices && voices[k]));
  const pickVoice = (voices) => { const vs = vidVoices(voices); return vs.includes(S.narrator) ? S.narrator : vs.includes("us-f") ? "us-f" : "orig"; };
  const videoFig = (v) => {
    const vs = vidVoices(v.voices), cur = pickVoice(v.voices), rate = S.vrate || "1";
    const sel = (key, label, opts) => `<label class="vpick"><span>${label}</span><select class="field" data-vset="${key}" aria-label="${label} for all videos">${opts}</select></label>`;
    return `<figure class="vid" data-voices="${esc(JSON.stringify(v.voices || {}))}">
      <video controls preload="none" playsinline poster="${v.poster}">
      <source src="${v.src}" type="video/mp4"><track kind="captions" srclang="en" label="English" src="${v.vtt}"></video>
      <figcaption><b>WATCH · ${mmss(v.secs)}</b><span class="vt">${v.title}</span><span class="vpicks">
        ${vs.length > 1 ? sel("narrator", "Voice", vs.map((k) => `<option value="${k}"${k === cur ? " selected" : ""}>${VOICE_LABEL[k]}</option>`).join("")) : ""}
        ${sel("vrate", "Speed", RATES.map((r) => `<option value="${r}"${r === rate ? " selected" : ""}>${r}×</option>`).join(""))}</span></figcaption></figure>`;
  };
  let AC = null;
  const SRCS = new WeakMap();
  // own=true plays the video's own (Kokoro) audio; own=false silences it without touching its mute button
  function ownAudio(video, own) {
    try {
      let n = SRCS.get(video);
      if (!n) {
        if (own) { video.muted = false; return true; }
        AC = AC || new (window.AudioContext || window.webkitAudioContext)();
        n = AC.createMediaElementSource(video); SRCS.set(video, n);
      }
      n.disconnect(); if (own) n.connect(AC.destination);
      if (AC && AC.resume) AC.resume().catch(() => {});
      return true;
    } catch (e) { if (!own) video.muted = true; return false; }
  }
  let liveVids = [];
  function wireVideo(fig) {
    const video = fig.querySelector("video");
    const voices = JSON.parse(fig.dataset.voices || "{}");
    const setRate = () => { const r = parseFloat(S.vrate) || 1; video.defaultPlaybackRate = r; video.playbackRate = r; video.preservesPitch = true; };
    video.addEventListener("loadedmetadata", setRate);
    let stop = null;
    const apply = () => {
      if (stop) stop(); stop = null;
      setRate();
      const voice = pickVoice(voices);
      if (voice === "orig") { if (SRCS.has(video) || video.muted) ownAudio(video, true); return; }
      const a = new Audio(); a.preload = "auto"; a.src = voices[voice];
      const sync = (force) => { if (force || Math.abs(a.currentTime - video.currentTime) > 0.25) { try { a.currentTime = video.currentTime; } catch (e) { /* not ready */ } } };
      const vol = () => { a.volume = video.volume; a.muted = video.muted && SRCS.has(video); };
      const play = () => { ownAudio(video, false); vol(); a.preservesPitch = true; a.playbackRate = video.playbackRate; sync(true); a.play().catch(() => {}); };
      const pause = () => a.pause();
      a.addEventListener("loadedmetadata", () => { if (!video.paused) sync(true); });
      const ev = [["play", play], ["pause", pause], ["ended", pause], ["seeked", () => sync(true)], ["timeupdate", () => { if (!video.paused) sync(); }],
        ["ratechange", () => { a.playbackRate = video.playbackRate; }], ["volumechange", vol], ["waiting", pause],
        ["playing", () => { if (!video.paused) { sync(true); a.play().catch(() => {}); } }]];
      ev.forEach(([k, f]) => video.addEventListener(k, f));
      if (!video.paused) play();
      stop = () => { ev.forEach(([k, f]) => video.removeEventListener(k, f)); a.pause(); a.src = ""; };
    };
    apply();
    return { apply, stop: () => { if (stop) stop(); video.pause(); } };
  }

  function sidebar(cur) {
    const curTrack = L[cur] ? L[cur].track : cur.startsWith("track-") ? cur.slice(6) : null;
    const nx = nextUp();
    const nxTrack = nx ? L[nx].track : null;
    const due = dueIds().length;
    const item = (go, label, extra = "") => `<button data-go="${go}" class="${cur === go ? "on" : ""}">${label}${extra}</button>`;
    let h = `<div class="nav">
      ${item("home", "Today")}
      ${item("review", "Review", `<span class="count tnum">${due} due</span>`)}
      ${item("practice", "Mixed practice")}
      ${item("plan", "Plan and progress")}
      ${item("sheets", "Cheat sheets")}
      ${item("glossary", "Glossary")}
      ${item("setup", "Set up the labs")}
    </div>
    <div class="navsec"><span class="label">Tracks · ${doneCount()} of ${ORDER.length} lessons done</span>
    <input class="field filter" id="lesson-filter" type="search" placeholder="Find a lesson" aria-label="Find a lesson" value="${esc(filterText)}"></div>`;
    const hereTrack = curTrack || nxTrack;
    const partOpen = (p) => filterText ? true : S.open["part-" + p.id] ?? p.tracks.includes(hereTrack);
    for (const t of C.tracks) {
      const part = partOf[t.id];
      const hits = (tid) => T[tid].lessons.some((id) => L[id].title.toLowerCase().includes(filterText.toLowerCase()));
      if (part && part.tracks[0] === t.id && (!filterText || part.tracks.some(hits))) {
        const ids = part.tracks.flatMap((tid) => T[tid].lessons);
        const pOpen = partOpen(part);
        h += `<button class="partsec" data-act="toggle-part" data-id="${part.id}" aria-expanded="${pOpen}">
          <span class="label">Part ${part.idx} · ${ids.filter(isDone).length} of ${ids.length}</span><i class="chev" aria-hidden="true"></i><b>${esc(part.title)}</b></button>`;
      }
      if (part && !partOpen(part)) continue;
      const open = filterText ? true : S.open[t.id] ?? (t.id === curTrack || (!curTrack && t.id === nxTrack));
      const shown = t.lessons.filter((id) => !filterText || L[id].title.toLowerCase().includes(filterText.toLowerCase()));
      if (filterText && !shown.length) continue;
      h += `<div class="trk"><button data-act="toggle-track" data-id="${t.id}" aria-expanded="${open}">
          <span class="tn">${pad(t.idx)}</span><span class="tt">${esc(t.title)}</span><span></span>${cells(t.lessons)}</button>
        ${open ? `<ul><li><button data-go="track-${t.id}" class="${cur === "track-" + t.id ? "on" : ""}"><span class="cell" style="visibility:hidden"></span>Track overview</button></li>
          ${shown.map((id) => `<li><button data-go="${id}" class="${cur === id ? "on" : ""}"><i class="cell ${cellState(id)}"></i><span>${esc(L[id].title)}${vbadge(id)}</span></button></li>`).join("")}</ul>` : ""}
      </div>`;
    }
    h += `<p class="label" style="padding:18px 20px 0;line-height:1.6">Progress is saved in this browser. Move it between devices from Plan and progress.</p>`;
    $("#side").innerHTML = h;
  }
  let filterText = "";

  /* ---------------- search across everything ---------------- */
  let IDX = null, idxLoading = null, gsel = 0, gres = [];
  const loadIndex = () => idxLoading || (idxLoading = fetch("search.json").then((r) => r.json()).then((d) => { IDX = d; d.forEach((e) => { e.lh = e.h.toLowerCase(); e.lx = e.x.toLowerCase(); }); return d; }).catch(() => { IDX = []; }));
  const KIND_W = { Lesson: 6, Track: 5, "Cheat sheet": 4, Lab: 3, "Worked example": 3, "Java and Kotlin": 3, "Key terms": 4, Quiz: 1, "Track quiz": 1, Drill: 2, "Go deeper": 2, "Explain it back": 1 };
  const reEsc = (w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  function mark(text, words) {
    let h = esc(text);
    words.slice().sort((x, y) => y.length - x.length).forEach((w) => { h = h.replace(new RegExp(`(${reEsc(esc(w))})`, "gi"), "\u0001$1\u0002"); });
    return h.replace(/\u0001/g, "<mark>").replace(/\u0002/g, "</mark>");
  }
  function searchAll(q) {
    const ql = q.toLowerCase().trim(), words = ql.split(/\s+/).filter(Boolean);
    if (!words.length || !IDX) return [];
    const out = [];
    for (const e of IDX) {
      if (!words.every((w) => e.lh.includes(w) || e.lx.includes(w))) continue;
      let sc = KIND_W[e.k] || 1;
      words.forEach((w) => { if (e.lh.includes(w)) sc += 12; sc += Math.min(6, e.lx.split(w).length - 1); });
      if (words.length > 1 && (e.lh.includes(ql) || e.lx.includes(ql))) sc += 20;
      if (e.lh.includes(ql)) sc += 15;
      out.push([sc, e]);
    }
    return out.sort((x, y) => y[0] - x[0]).slice(0, 40).map((x) => x[1]);
  }
  function snippet(e, words) {
    const ql = words.join(" ");
    let at = e.lx.indexOf(ql); if (at < 0) at = Math.min(...words.map((w) => e.lx.indexOf(w)).filter((i) => i >= 0).concat([0]));
    const from = Math.max(0, at - 60), text = e.x.slice(from, from + 190);
    return (from > 0 ? "… " : "") + mark(text, words) + (from + 190 < e.x.length ? " …" : "");
  }
  function gsRender() {
    const box = $("#gres"), inp = $("#gsearch"); if (!box || !inp) return;
    const q = inp.value.trim();
    if (!q) { box.hidden = true; inp.setAttribute("aria-expanded", "false"); return; }
    box.hidden = false; inp.setAttribute("aria-expanded", "true");
    if (!IDX) { box.innerHTML = `<div class="gs-empty">Loading the search index…</div>`; return; }
    const words = q.toLowerCase().split(/\s+/).filter(Boolean);
    gres = searchAll(q); gsel = Math.min(gsel, Math.max(0, gres.length - 1));
    box.innerHTML = gres.length ? `<div class="gs-count">${gres.length === 40 ? "Top 40" : gres.length} result${gres.length === 1 ? "" : "s"} · ↑↓ to move, Enter to open</div>` + gres.map((e, i) => {
      const tr = L[e.r] ? T[L[e.r].track] : T[e.r.replace(/^track-/, "")];
      const where = L[e.r] ? `${wdShort(e.r)} · ${tr ? esc(tr.title) : ""}` : (tr ? trackTag(tr) : "");
      return `<button class="gs-item ${i === gsel ? "on" : ""}" role="option" aria-selected="${i === gsel}" data-gs="${i}">
        <span class="gs-meta"><span class="gs-kind">${esc(e.k)}</span>${e.v ? `<span class="vbadge">${icon.video}</span>` : ""}<span class="gs-where">${where}</span></span>
        <span class="gs-h">${mark(e.h, words)}</span>${e.x ? `<span class="gs-x">${snippet(e, words)}</span>` : ""}</button>`;
    }).join("") : `<div class="gs-empty">Nothing matches “${esc(q)}”. Try fewer or shorter words.</div>`;
    const on = box.querySelector(".gs-item.on"); if (on) on.scrollIntoView({ block: "nearest" });
  }
  let pendingAnchor = null;
  function gsOpen(i) {
    const e = gres[i]; if (!e) return;
    pendingAnchor = e.a || null;
    const inp = $("#gsearch"); if (inp) { inp.value = ""; inp.blur(); }
    mobileOpen = false;
    go(e.r);
  }
  function jumpPending() {
    if (!pendingAnchor) return;
    const el = document.getElementById(pendingAnchor);
    if (!el) return;  // the lesson body is still loading; the next render tries again
    pendingAnchor = null;
    requestAnimationFrame(() => { el.scrollIntoView({ block: "start" }); el.classList.add("gs-flash"); setTimeout(() => el.classList.remove("gs-flash"), 1600); });
  }
  document.addEventListener("input", (ev) => { if (ev.target.id === "gsearch") { gsel = 0; if (!IDX) loadIndex().then(gsRender); gsRender(); } });
  document.addEventListener("focusin", (ev) => { if (ev.target.id === "gsearch") { loadIndex(); if (ev.target.value) gsRender(); } });
  document.addEventListener("keydown", (ev) => {
    const inp = $("#gsearch");
    if (ev.target === inp) {
      if (ev.key === "ArrowDown") { ev.preventDefault(); gsel = Math.min(gsel + 1, gres.length - 1); gsRender(); }
      else if (ev.key === "ArrowUp") { ev.preventDefault(); gsel = Math.max(gsel - 1, 0); gsRender(); }
      else if (ev.key === "Enter") { ev.preventDefault(); gsOpen(gsel); }
      else if (ev.key === "Escape") { inp.value = ""; gsRender(); inp.blur(); }
      return;
    }
    if (ev.target.closest && ev.target.closest("input,textarea,select,[contenteditable]")) return;
    if ((ev.key === "/" && !ev.metaKey && !ev.ctrlKey) || (ev.key.toLowerCase() === "k" && (ev.metaKey || ev.ctrlKey))) { ev.preventDefault(); if (inp) inp.focus(); }
  });
  document.addEventListener("mousedown", (ev) => {
    const it = ev.target.closest && ev.target.closest("[data-gs]");
    if (it) { ev.preventDefault(); gsOpen(+it.dataset.gs); return; }
    if (!ev.target.closest || !ev.target.closest("#gsearch-box")) { const box = $("#gres"); if (box) box.hidden = true; }
  });

  /* ---------------- router ---------------- */
  const route = () => (location.hash.slice(1) || "home");
  function render(keepScroll) {
    const cur = route();
    const y = scrollY;
    frame();
    sidebar(cur);
    const page = $("#page");
    let html;
    if (L[cur]) html = lessonPage(L[cur]);
    else if (cur.startsWith("track-") && T[cur.slice(6)]) html = trackPage(T[cur.slice(6)]);
    else if (cur === "review") html = reviewPage();
    else if (cur === "practice") html = practicePage();
    else if (cur === "plan") html = planPage();
    else if (cur === "sheets") html = sheetsPage();
    else if (cur === "glossary") html = glossaryPage();
    else if (cur === "setup") html = setupPage();
    else html = homePage();
    liveVids.forEach((w) => w.stop());
    page.innerHTML = html;
    page.classList.toggle("is-lesson", !!L[cur]);
    $$(".sim[data-sim]").forEach((el) => simRender(el));
    liveVids = $$("figure.vid").map(wireVideo);
    jumpPending();
    timerRender();
    if (L[cur]) watchToc();
    if (keepScroll) scrollTo(0, y);
    document.title = L[cur] ? `${L[cur].title} · JVM Workbench` : cur.startsWith("track-") && T[cur.slice(6)] ? `${T[cur.slice(6)].title} · JVM Workbench` : "JVM Workbench";
  }
  addEventListener("hashchange", () => {
    mobileOpen = false; resetPageState();
    const r = route(), tid = L[r] ? L[r].track : r.startsWith("track-") ? r.slice(6) : null;
    if (tid && partOf[tid] && S.open["part-" + partOf[tid].id] === false) { delete S.open["part-" + partOf[tid].id]; save(); }
    render(); scrollTo(0, 0);
  });
  const go = (id) => { if (route() === id) { render(); scrollTo(0, 0); } else location.hash = id; };

  /* ---------------- home ---------------- */
  function homePage() {
    const nx = nextUp();
    const due = dueIds().length;
    const l = nx ? L[nx] : null;
    const started = doneCount() > 0;
    return `
    <section class="hero">
      <div class="row" style="justify-content:space-between"><span class="label">${ORDER.length} lessons · ${C.tracks.length} tracks${PARTS.length ? ` in ${PARTS.length} parts` : ""} · about 35 minutes a day</span><span class="label">${totalWeeks()} weeks at ${pace()} days a week</span></div>
      <h1>JVM <i>Workbench</i></h1>
      <p>${esc(C.tagline)} Every lesson ends with real code to write and tests that tell you when it works.</p>
      <div class="plate-wrap">${weekPlate()}</div>
      <div class="plate-legend">
        <span><svg width="14" height="14" viewBox="-7 -7 14 14"><circle r="3.4" fill="var(--ember)"/></svg>Done</span>
        <span><svg width="18" height="18" viewBox="-9 -9 18 18"><circle r="6" fill="none" stroke="var(--ember)" stroke-width="1.2" class="pulse"/><circle r="2.2" fill="var(--ember)"/></svg>Next</span>
        <span><svg width="14" height="14" viewBox="-7 -7 14 14"><circle r="2.2" fill="var(--mark-off)"/></svg>Later</span>
        <span>One column per week, one dot per study day. Tap a dot to open that lesson.</span>
      </div>
    </section>

    <div class="sechead"><h2>Today</h2>${l ? `<span class="label">${wdLabel(l.id)} of ${totalWeeks()} weeks</span>` : ""}</div>
    <section class="today">
      <div class="panel step ${due ? "now" : ""}">
        <span class="n">1 · Review · about 10 min</span>
        <h3>${due ? `${due} card${due === 1 ? "" : "s"} due` : started ? "Nothing due" : "Your deck starts here"}</h3>
        <p class="mute" style="margin:0;font-size:15.5px">${due ? "Answer from memory first, then check. This is the part that makes lessons stick. Short on time? Do only this." : started ? "Cards come back just before you would forget them. Check again tomorrow." : "Each finished lesson adds 5 to 7 cards. They come back on a schedule, just before you would forget them."}</p>
        <div class="row">${due ? `<button class="btn hold" data-go="review">Start review</button>` : `<button class="btn ghost" data-go="practice" ${started ? "" : "disabled"}>Mixed practice</button>`}</div>
      </div>
      <div class="panel step ${!due && l ? "now" : ""}">
        <span class="n">2 · Learn and practice · about 25 min</span>
        ${l ? `<h3>${esc(l.title)}</h3>
          <span class="label">${wdLabel(l.id)} · ${esc(T[l.track].title)} · lesson ${l.n} of ${T[l.track].lessons.length}${l.minutes ? ` · ${l.minutes} min` : ""}</span>
          ${l.ready ? `<p style="margin:0;font-size:16px">${l.goal}</p>` : `<p class="mute" style="margin:0;font-size:15.5px">This lesson is still being written.</p>`}
          <div class="row"><button class="btn" data-go="${l.id}">${started ? "Open lesson" : "Start the first lesson"}</button>${!S.seenSetup ? `<button class="btn ghost" data-go="setup">Set up the labs first</button>` : ""}</div>`
        : `<h3>Every lesson is done</h3><p class="mute" style="margin:0">Keep your reviews going. Five minutes a day keeps all of it.</p>`}
      </div>
      <div class="panel step">
        <span class="n">3 · Progress</span>
        <div class="stat tnum">${doneCount()}<small>of ${ORDER.length} done</small></div>
        <div class="mute" style="font-size:15px">Studied <b class="tnum">${studiedLast7()}</b> of the last 7 days. ${l ? `You are in week <b class="tnum">${wd(l.id).w}</b> of ${totalWeeks()} at ${pace()} days a week.` : "Course finished."}</div>
        <div class="row"><button class="btn ghost sm" data-go="plan">See the plan</button></div>
      </div>
    </section>

    <div class="sechead"><h2>Tracks</h2><span class="label">Do them in order, or jump to the one you need</span></div>
    ${(PARTS.length ? PARTS : [{ idx: 0, title: "", short: "", tracks: C.tracks.map((t) => t.id) }]).map((part) => `
    ${part.idx ? `<div class="parthead"><span class="label">Part ${part.idx} · ${part.tracks.reduce((n, id) => n + T[id].lessons.length, 0)} lessons</span><h3>${esc(part.title)}</h3>${part.short ? `<p>${esc(part.short)}</p>` : ""}</div>` : ""}
    <section class="tracks">
      ${part.tracks.map((id) => T[id]).map((t) => `<button class="panel tcard" data-go="track-${t.id}">
        <span class="label">Track ${pad(t.idx)} · ${t.lessons.length} lessons · labs/${esc(t.lab)}</span>
        <h3>${esc(t.title)}</h3><p>${esc(t.short)}</p>
        ${cells(t.lessons, true)}
        <span class="foot"><span>${trackDone(t)} of ${t.lessons.length} done</span><span>${t.lessons.filter((id) => L[id].ready).length < t.lessons.length ? `${t.lessons.filter((id) => L[id].ready).length} written` : ""}</span></span>
      </button>`).join("")}
    </section>`).join("")}

    <div class="sechead"><h2>How a session works</h2></div>
    <section class="how">
      <div><b>Review first</b><span>Ten minutes of cards from earlier lessons. Recalling something just before you forget it is what moves it into long-term memory.</span></div>
      <div><b>Predict, then read</b><span>Each lesson opens with one question you answer before reading. A wrong guess still helps: you read the answer looking for it.</span></div>
      <div><b>Write the code</b><span>Short "Try it" steps in each section, then a lab with tests in the <code>labs</code> project, and a drill you write from memory.</span></div>
      <div><b>Check, then let it go</b><span>A five-question quiz with one question from an earlier lesson. Anything you miss comes back in your review deck.</span></div>
    </section>`;
  }

  // one column per course week, one row per study day; each dot is a lesson
  function weekPlate() {
    const weeks = totalWeeks(), days = pace(), sx = 36, sy = 24, x0 = 46, y0 = 30;
    const W = x0 + (weeks - 1) * sx + 20, H = y0 + (days - 1) * sy + 14;
    const nx = nextUp();
    let g = "";
    for (let w = 0; w < weeks; w++) g += `<text class="wk" x="${x0 + w * sx}" y="12" text-anchor="middle">${w + 1}</text>`;
    for (let d = 0; d < days; d++) g += `<text class="wk" x="0" y="${y0 + d * sy + 4}">D${d + 1}</text>`;
    ORDER.forEach((id, k) => {
      const x = x0 + Math.floor(k / days) * sx, y = y0 + (k % days) * sy;
      const st = S.done[id] ? "done" : id === nx ? "next" : "later";
      const mark = st === "done" ? `<circle r="4.2" fill="var(--ember)"/>` : st === "next" ? `<circle r="7.4" fill="none" stroke="var(--ember)" stroke-width="1.3" class="pulse"/><circle r="2.8" fill="var(--ember)"/>` : `<circle r="2.8" fill="var(--mark-off)"/>`;
      g += `<g transform="translate(${x} ${y})" data-go="${id}" role="link" aria-label="${wdLabel(id)}: ${esc(L[id].title)}"><title>${wdLabel(id)}: ${esc(L[id].title)}</title><circle r="11" fill="transparent"/>${mark}</g>`;
    });
    return `<svg class="plate-svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="Course plan: ${doneCount()} of ${ORDER.length} lessons done">${g}</svg>`;
  }

  /* ---------------- lesson ---------------- */
  let pageState = {};
  const resetPageState = () => { pageState = { quiz: {}, hints: {}, tab: {}, retry: {} }; };
  resetPageState();

  function lessonPage(l) {
    const t = T[l.track];
    const i = ORDER.indexOf(l.id);
    const prev = i > 0 ? L[ORDER[i - 1]] : null, next = i < ORDER.length - 1 ? L[ORDER[i + 1]] : null;
    const crumb = `<div class="crumb"><span class="label" style="color:var(--hold-ink)">${wdLabel(l.id)}</span><button data-go="track-${t.id}">${trackTag(t)} · ${esc(t.title)}</button><span class="label">Lesson ${l.n} of ${t.lessons.length}${l.minutes ? ` · about ${l.minutes} min` : ""}</span></div>`;
    if (!l.ready) return `<article class="pending lhead">${crumb}<h1>${esc(l.title)}</h1><p class="goal">This lesson is still being written. It will appear here, at the same link, when it is ready.</p></article>${pager(prev, next)}`;
    if (l.remote && !l.sections) {
      loadLesson(l);
      return `<article class="lhead">${crumb}<h1>${esc(l.title)}</h1><p class="goal">${l.goal}</p><p class="label">${l.failed ? "Couldn't load this lesson. Check your connection, then reload the page." : "Loading the lesson…"}</p></article>`;
    }
    const done = isDone(l.id);
    const toc = [];
    let h = `<div class="lgrid ${S.tocHide ? "toc-off" : ""}"><article>
      <header class="lhead">${crumb}<h1>${esc(l.title)}</h1><p class="goal">${l.goal}</p>
        <div class="donebar">${done ? `<span class="done-pill">■ Done</span><button class="btn ghost sm" data-act="undone" data-id="${l.id}">Mark not done</button>` : `<button class="btn ghost sm" data-act="done" data-id="${l.id}">Mark lesson done</button>`}
        <button class="btn ghost sm" data-act="timer">Start a 35-minute session</button></div>
      </header>`;
    if (l.warmup) {
      toc.push(["warmup", "Before you read"]);
      h += `<section class="block" id="warmup" style="margin-top:0;margin-bottom:40px"><span class="label">Before you read · guess, no score</span>${mcqCard(l.warmup, "w:" + l.id, 0, { warm: true })}</section>`;
    }
    l.sections.forEach((s, si) => {
      toc.push([`s${si}`, s.h + (s.video ? `<span class="vbadge" title="Has a video">${icon.video}</span>` : ""), pad(si + 1)]);
      h += `<section class="lsec" id="s${si}"><div class="shead"><span class="sn">${pad(si + 1)}</span><h2>${s.h}</h2></div>
        ${s.video ? videoFig(s.video) : ""}
        <div class="prose">${s.html}</div>
        ${s.figure ? `<figure class="fig"><div class="svg">${s.figure.svg}</div><figcaption><b>FIG ${pad(si + 1)}</b>${s.figure.caption}</figcaption></figure>` : ""}
        ${s.sim ? `<div class="sim" data-sim="${l.id}-${si}"></div>` : ""}
        ${si === 0 && l.analogy ? callout("analogy", "Picture it", l.analogy) : ""}
        ${si === Math.min(1, l.sections.length - 1) && l.world ? callout("world", "In your services", l.world) : ""}
        ${si === l.sections.length - 1 && l.mistake ? callout("mistake", "Common mistake", l.mistake) : ""}
        ${s.try ? tryIt(s.try) : ""}
        ${s.refs && s.refs.length ? `<div class="refs">${s.refs.map((r) => `<div><span class="kind">${esc(r.kind)}</span><a href="${esc(r.url)}" target="_blank" rel="noopener">${r.title}</a></div>`).join("")}</div>` : ""}
      </section>`;
    });
    if (l.compare) {
      toc.push(["compare", "Java and Kotlin"]);
      h += `<section class="block" id="compare"><span class="label">Java and Kotlin, side by side</span><h2>${l.compare.title}</h2>
        <div class="cmp">${codePair({ lang: "java", html: l.compare.java.html, title: l.compare.java.title, alt: { lang: "kotlin", html: l.compare.kotlin.html, title: l.compare.kotlin.title } }, l.compare.java.title, true)}
        <div class="prose">${l.compare.note}</div></div></section>`;
    }
    if (l.worked) {
      toc.push(["worked", "Worked example"]);
      h += `<section class="block" id="worked"><span class="label">Worked example</span><h2>${l.worked.title}</h2><ol class="worked">
        ${l.worked.steps.map((s, k) => `<li><div class="wn"><span>${k + 1}</span>${k < l.worked.steps.length - 1 ? "<i></i>" : ""}</div><div class="wb"><div class="prose">${s.say}</div>${s.code ? prePair({ lang: s.lang, html: s.code }, s.alt) : ""}</div></li>`).join("")}</ol></section>`;
    }
    if (l.lab) {
      toc.push(["lab", "Lab"]);
      const shown = pageState.hints[l.id] || 0;
      const lb = l.lab;
      h += `<section class="block" id="lab"><div class="lab"><span class="label">Hands-on lab · about ${lb.minutes} min · labs/${esc(t.lab)}</span><h3>${lb.title}</h3>
        <div class="files">${lb.files.map((f) => `<span>${esc(f)}</span>`).join("")}</div>
        ${codeBox({ html: esc(lb.run), lang: "bash", run: "" }, "Run the tests (from the labs folder)")}
        <ol>${lb.steps.map((s) => `<li>${s}</li>`).join("")}</ol>
        ${lb.hints.slice(0, shown).map((x, k) => `<div class="hint"><span class="label">Hint ${k + 1}</span>${x}</div>`).join("")}
        <div class="row">${shown < lb.hints.length ? `<button class="btn ghost sm" data-act="hint" data-id="${l.id}">${shown ? "Another hint" : "Stuck? Show a hint"}</button>` : ""}
        <span class="mute" style="font-size:15px"><b>Done when:</b> ${lb.done}</span></div>
        <p class="mute" style="margin:0;font-size:14.5px">The reference answer is in <code>src/solution</code> of the same package. Look only after the tests pass, or after 20 honest minutes.</p>
      </div></section>`;
    }
    if (l.drill) {
      toc.push(["drill", "From memory"]);
      h += `<section class="block" id="drill"><span class="label">Drill · from memory · ${l.drill.minutes} min</span><h2>${l.drill.title}</h2><div class="prose">${l.drill.prompt}</div>
        <details class="reveal"><summary>Show the answer</summary><div style="margin-top:10px">${codePair(l.drill.answer, "Answer")}</div></details></section>`;
    }
    if (l.recap.length) h += `<section class="block"><div class="recap"><span class="label">Remember</span><ul class="prose" style="max-width:none">${l.recap.map((r) => `<li>${r}</li>`).join("")}</ul></div></section>`;
    toc.push(["quiz", "Quiz"]);
    h += `<section class="block" id="quiz"><span class="label">Exit quiz · ${l.quiz.length} questions · ${Math.ceil(l.quiz.length * 0.8)} right marks the lesson done</span><h2>Check what stuck</h2>${quizBlock(l.quiz, l.id, "lesson")}</section>`;
    if (l.explain) {
      toc.push(["explain", "Explain it back"]);
      h += `<section class="block" id="explain"><span class="label">Explain it back</span><div class="prose"><p style="font-size:19px">${l.explain.prompt}</p></div>
        <textarea class="field" id="explain-${l.id}" rows="5" data-explain="${l.id}" placeholder="Write it in your own words. Rough is fine. It stays in this browser.">${esc(S.explain[l.id] || "")}</textarea>
        <details class="reveal"><summary>Compare with a model answer</summary><div class="call analogy" style="margin-top:10px"><div class="prose">${l.explain.answer}</div></div></details></section>`;
    }
    if (l.terms.length) {
      toc.push(["terms", "Key terms"]);
      h += `<section class="block" id="terms"><span class="label">Key terms</span><dl class="terms">${l.terms.map((x) => `<div><dt>${x.term}</dt><dd>${x.plain}</dd></div>`).join("")}</dl></section>`;
    }
    if (l.cards.length) h += `<section class="block"><span class="label">${done ? "In your review deck" : "These cards join your review deck when you finish"}</span><div class="cards-preview">${l.cards.map((c) => `<div>${c.front}</div>`).join("")}</div></section>`;
    if (l.deeper || l.sources.length) {
      toc.push(["deeper", "Go deeper"]);
      h += `<section class="block" id="deeper"><details class="reveal"><summary>Go deeper${l.deeper ? ` · optional · about ${l.deeper.minutes} min` : ""}</summary><div style="display:grid;gap:16px;margin-top:14px">
        ${l.deeper ? `<div class="prose">${l.deeper.html}</div>` : ""}
        ${l.sources.length ? `<div class="refs"><span class="label">Sources</span>${l.sources.map((s) => `<a href="${esc(s.url)}" target="_blank" rel="noopener">${s.title}</a>`).join("")}</div>` : ""}</div></details></section>`;
    }
    h += `<section class="block"><div class="score"><div><span class="label">Finished?</span><div style="font:400 24px var(--display)">${done ? "This lesson is done." : "Tick it off. The plan moves with you."}</div></div>
      ${done ? `<button class="btn ghost" data-act="undone" data-id="${l.id}">Mark not done</button>` : `<button class="btn" data-act="done" data-id="${l.id}">Mark lesson done</button>`}</div></section>`;
    h += pager(prev, next) + `</article>
      <button class="toc-open" data-act="toc-toggle" aria-label="Show the contents of this page" title="Show contents">${icon.toc}<span>Contents</span></button>
      <aside class="toc" aria-label="On this page"><div class="toc-h"><span class="label">On this page</span><button class="toc-x" data-act="toc-toggle" aria-label="Hide the contents and widen the lesson" title="Hide contents">${icon.collapse}</button></div><ul>${toc.map(([id, label, n]) => `<li data-toc="${id}"><button data-act="scroll" data-id="${id}">${n ? `<span class="label" style="margin-right:6px">${n}</span>` : ""}${label}</button></li>`).join("")}</ul></aside></div>`;
    return h;
  }
  // the web build ships lesson bodies as separate files (lessons/<id>.json); the preview inlines them
  const loading = {};
  function loadLesson(l) {
    if (loading[l.id]) return;
    loading[l.id] = fetch(`lessons/${l.id}.json`).then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then((b) => { Object.assign(l, b); if (route() === l.id) render(true); })
      .catch(() => { l.failed = true; delete loading[l.id]; if (route() === l.id) render(true); });
  }
  const callout = (kind, title, html) => `<aside class="call ${kind}"><span class="label">${title}</span><div class="prose">${html}</div></aside>`;
  function tryIt(t) {
    return `<aside class="tryit"><div class="th"><span class="label">Try it</span><b>${t.title}</b><span class="mins">${t.minutes} min</span></div>
      <ol class="prose" style="max-width:none">${t.steps.map((s) => `<li>${s}</li>`).join("")}</ol>
      ${t.code ? codePair(t.code) : ""}
      ${t.code && t.code.file ? `<span class="label" style="text-transform:none;letter-spacing:.02em">In the repo: ${esc(t.code.file)}${t.code.alt && t.code.alt.file ? ` and ${esc(t.code.alt.file)}` : ""}</span>` : ""}
      ${t.expect ? `<details class="reveal"><summary>What you should see</summary><div class="expect" style="margin-top:8px"><div class="prose">${t.expect}</div></div></details>` : ""}</aside>`;
  }
  function pager(prev, next) {
    return `<nav class="pager">${prev ? `<button data-go="${prev.id}"><span class="label">← Previous</span><b>${esc(prev.title)}</b></button>` : "<span></span>"}
      ${next ? `<button class="nx" data-go="${next.id}"><span class="label">Next · ${wdLabel(next.id)} →</span><b>${esc(next.title)}</b><span class="label">${esc(T[next.track].title)}</span></button>` : "<span></span>"}</nav>`;
  }
  let tocObs;
  function watchToc() {
    if (tocObs) tocObs.disconnect();
    const items = $$(".toc li");
    if (!items.length || !("IntersectionObserver" in window)) return;
    tocObs = new IntersectionObserver((es) => {
      const vis = es.filter((e) => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
      if (vis) items.forEach((li) => li.classList.toggle("on", li.dataset.toc === vis.target.id));
    }, { rootMargin: "-80px 0px -65% 0px" });
    items.forEach((li) => { const el = document.getElementById(li.dataset.toc); if (el) tocObs.observe(el); });
  }

  /* ---------------- quiz ---------------- */
  // key: lesson id, "t:<track>" for a track quiz, "mix" for mixed practice
  function mcqCard(q, key, qi, opt = {}) {
    const st = pageState.quiz[key] || (pageState.quiz[key] = {});
    const pick = st[qi];
    const answered = pick !== undefined;
    const src = q.from && L[q.from] ? `<span class="tag from">From: ${esc(L[q.from].title)}</span>` : "";
    return `<div class="qcard" id="q-${esc(key)}-${qi}">
      <div class="qn">${opt.num ? `<span class="label">Q${qi + 1}</span>` : ""}${src}${opt.lessonTag || ""}</div>
      <div class="q prose" style="max-width:none">${q.q}</div>
      <div class="opts" role="radiogroup" aria-label="Answers">${q.options.map((o, k) => {
        const cls = answered ? (k === q.answer ? "right" : k === pick ? "wrong" : "fade") : "";
        const state = answered ? (k === q.answer ? (k === pick ? ", your answer, right" : ", the right answer") : k === pick ? ", your answer, wrong" : "") : "";
        return `<button class="opt ${cls}" role="radio" aria-checked="${k === pick}" data-act="answer" data-key="${esc(key)}" data-qi="${qi}" data-k="${k}" ${answered ? "disabled" : ""}><span class="ring" aria-hidden="true"></span><span class="ot">${o}<span class="sr">${state}</span></span></button>`;
      }).join("")}</div>
      ${answered ? `<div class="why"><b>${pick === q.answer ? (opt.warm ? "Good guess." : "Right.") : opt.warm ? "Not quite. The right answer is marked." : "Not this one. The right answer is marked."}</b> ${q.why}${opt.warm ? " Keep it in mind as you read." : ""}</div>` : ""}
    </div>`;
  }
  function quizBlock(qs, key, kind) {
    const st = pageState.quiz[key] || (pageState.quiz[key] = {});
    const retryKey = key + ":retry";
    const n = qs.length;
    const answered = qs.filter((_, i) => st[i] !== undefined).length;
    const right = qs.filter((q, i) => st[i] === q.answer).length;
    let h = `<div class="quiz">${qs.map((q, i) => mcqCard(q, key, i, { num: true })).join("")}`;
    if (answered === n) {
      const missed = qs.map((q, i) => (st[i] !== q.answer ? i : -1)).filter((i) => i >= 0);
      const need = Math.ceil(n * 0.8);
      h += `<div class="score"><div><span class="label">Score</span><div><b class="tnum">${right} / ${n}</b></div></div>
        <div class="mute" style="max-width:46ch;font-size:15px">${missed.length ? `Missed ${missed.length}. They come back in tomorrow's review. Try them once more below while the explanation is fresh.` : "All right. Clean."}${kind === "lesson" ? (right >= need ? " The lesson is marked done." : ` You need ${need} to mark the lesson done. Reread the sections behind the ones you missed, then retake it.`) : ""}</div>
        <button class="btn ghost sm" data-act="retake" data-key="${esc(key)}">Retake</button></div>`;
      if (missed.length) {
        const rs = pageState.quiz[retryKey] || (pageState.quiz[retryKey] = {});
        h += `<span class="label">Once more, the ones you missed</span>` + missed.map((i) => mcqCard(qs[i], retryKey, i, { num: true })).join("");
        void rs;
      }
    }
    return h + "</div>";
  }
  function onAnswer(key, qi, k) {
    const base = key.replace(/:retry$/, "");
    const st = pageState.quiz[key] || (pageState.quiz[key] = {});
    if (st[qi] !== undefined) return;
    st[qi] = k;
    if (key.startsWith("w:")) return render(true);
    if (key.endsWith(":retry")) return render(true);
    let qs, cardKey;
    if (key === "mix") { const item = pageState.mix[qi]; qs = null; if (k !== item.q.answer) addMissed(item.key, item.qi); }
    else if (key.startsWith("t:")) { qs = T[key.slice(2)].quiz; cardKey = key.slice(2); }
    else { qs = L[key].quiz; cardKey = key; }
    if (qs && k !== qs[qi].answer) addMissed(cardKey, qi);
    if (qs && qs.every((_, i) => st[i] !== undefined)) {
      const right = qs.filter((q, i) => st[i] === q.answer).length;
      if (key.startsWith("t:")) { S.tquiz[cardKey] = Math.max(S.tquiz[cardKey] || 0, right); }
      else {
        S.quiz[key] = Math.max(S.quiz[key] || 0, right);
        if (right >= Math.ceil(qs.length * 0.8) && !S.done[key]) { S.done[key] = new Date().toISOString(); const n = addCards(key); logDay("l"); toast(`Lesson done. ${n} cards join your review from tomorrow.`); }
      }
    }
    save();
    void base;
    render(true);
  }

  /* ---------------- interleaving simulator ---------------- */
  const sims = {};
  function simFind(id) { const [lid, si] = [id.slice(0, id.lastIndexOf("-")), +id.slice(id.lastIndexOf("-") + 1)]; return L[lid] && L[lid].sections[si] && L[lid].sections[si].sim; }
  function simReset(id) {
    const def = simFind(id);
    sims[id] = { vars: Object.assign({}, def.vars), locks: Object.fromEntries((def.locks || []).map((k) => [k, null])), th: def.threads.map(() => ({ pc: 0, regs: {}, done: false })), log: [] };
    return sims[id];
  }
  function simBlocked(def, st, ti) {
    const t = st.th[ti]; if (t.done) return null;
    const s = def.threads[ti].steps[t.pc];
    return s.op === "lock" && st.locks[s.lock] !== null && st.locks[s.lock] !== ti ? s.lock : null;
  }
  function simStep(id, ti) {
    const def = simFind(id); const st = sims[id] || simReset(id); const t = st.th[ti];
    if (t.done || simBlocked(def, st, ti)) return;
    const s = def.threads[ti].steps[t.pc];
    let note = "";
    switch (s.op) {
      case "read": t.regs[s.reg] = st.vars[s.var]; note = `${s.reg} = ${t.regs[s.reg]}`; break;
      case "add": t.regs[s.reg] = (t.regs[s.reg] || 0) + s.n; note = `${s.reg} = ${t.regs[s.reg]}`; break;
      case "write": st.vars[s.var] = t.regs[s.reg]; note = `${s.var} = ${st.vars[s.var]}`; break;
      case "set": st.vars[s.var] = s.n; note = `${s.var} = ${s.n}`; break;
      case "lock": st.locks[s.lock] = ti; note = `holds ${s.lock}`; break;
      case "unlock": if (st.locks[s.lock] === ti) st.locks[s.lock] = null; note = `released ${s.lock}`; break;
      case "check": if (st.vars[s.var] !== s.eq) { note = `${s.var} is ${st.vars[s.var]}, skip`; t.pc = def.threads[ti].steps.length - 1; } else note = "true"; break;
      default: break;
    }
    st.log.push(`${def.threads[ti].name}: ${s.code}${note ? `  → ${note}` : ""}`);
    t.pc++; if (t.pc >= def.threads[ti].steps.length) t.done = true;
  }
  function simRender(el) {
    const id = el.dataset.sim; const def = simFind(id); if (!def) return;
    const st = sims[id] || simReset(id);
    const all = st.th.every((t) => t.done);
    const dead = !all && st.th.every((t, i) => t.done || simBlocked(def, st, i));
    const goalHit = def.goal && all && st.vars[def.goal.var] === def.goal.eq;
    let msg = "", cls = "";
    if (dead) { msg = "Deadlock. Every thread that is still running waits for a lock another thread holds. Nothing can move."; cls = "dead"; }
    else if (goalHit) { msg = def.goal.say; cls = "win"; }
    else if (all) { msg = `Finished with ${Object.entries(st.vars).map(([k, v]) => `${k} = ${v}`).join(", ")}.${def.goal ? " Reset and try another order." : ""}`; }
    else msg = def.intro;
    el.innerHTML = `<div class="simh"><span class="label">Interactive · you are the scheduler</span><b>${esc(def.title)}</b></div>
      <div class="state"><span>shared:</span>${Object.entries(st.vars).map(([k, v]) => `<span>${esc(k)} = <b>${esc(v)}</b></span>`).join("")}
        ${Object.entries(st.locks).map(([k, v]) => `<span>${esc(k)}: <b>${v === null ? "free" : esc(def.threads[v].name)}</b></span>`).join("")}</div>
      <div class="threads">${def.threads.map((t, ti) => {
        const ts = st.th[ti]; const blk = simBlocked(def, st, ti);
        return `<div class="th"><div class="tname"><span>${esc(t.name)}</span>
          <button class="btn sm ${ts.done ? "ghost" : ""}" data-act="sim-step" data-id="${id}" data-ti="${ti}" ${ts.done || blk ? "disabled" : ""}>${ts.done ? "done" : blk ? `waits for ${esc(blk)}` : "Run next line"}</button></div>
          <ol>${t.steps.map((s, k) => `<li class="${k < ts.pc ? "ran" : k === ts.pc && !ts.done ? "next" : ""}">${esc(s.code)}</li>`).join("")}</ol>
          <div class="regs">${Object.keys(ts.regs).length ? "local: " + Object.entries(ts.regs).map(([k, v]) => `${esc(k)} = ${esc(v)}`).join(", ") : ""}</div></div>`;
      }).join("")}</div>
      <div class="msg ${cls}"><span>${esc(msg)}</span><button class="btn ghost sm" data-act="sim-reset" data-id="${id}">Reset</button></div>
      ${st.log.length ? `<div class="log">${st.log.map(esc).join("<br>")}</div>` : ""}`;
  }

  /* ---------------- track ---------------- */
  function trackPage(t) {
    const best = S.tquiz[t.id];
    return `<header class="lhead"><div class="crumb"><span class="label">${trackTag(t)} · ${t.lessons.length} lessons · labs/${esc(t.lab)}</span></div>
      <h1>${esc(t.title)}</h1><p class="goal">${esc(t.short)}</p>${cells(t.lessons, true)}</header>
      ${t.intro ? `<div class="prose" style="margin-bottom:34px">${t.intro}</div>` : ""}
      <section class="block" style="margin-top:0"><span class="label">Lessons</span><div class="plan-list">
        ${t.lessons.map((id) => { const l = L[id]; return `<div class="pr"><span class="d">${wdShort(id)}</span><i class="cell ${cellState(id)}"></i><button data-go="${id}">${esc(l.title)}${vbadge(id)}${l.ready ? "" : ' <span class="label">being written</span>'}</button><span class="label">${S.quiz[id] != null ? `quiz ${S.quiz[id]}/5` : ""}</span></div>`; }).join("")}
      </div></section>
      ${t.cheatsheet ? `<section class="block"><span class="label">Cheat sheet</span><h2>The track on one page</h2><div class="prose" style="max-width:none">${t.cheatsheet}</div></section>` : ""}
      ${t.recap.length ? `<section class="block"><div class="recap"><span class="label">Remember from this track</span><ul class="prose" style="max-width:none">${t.recap.map((r) => `<li>${r}</li>`).join("")}</ul></div></section>` : ""}
      ${t.quiz.length ? `<section class="block"><span class="label">Track quiz · ${t.quiz.length} questions${best != null ? ` · best ${best}/${t.quiz.length}` : ""}</span><h2>Mix it all together</h2><p class="mute" style="margin:0;max-width:60ch">Take it when you finish the track, and again a week later. Missed questions join your review deck.</p>${quizBlock(t.quiz, "t:" + t.id, "track")}</section>` : ""}`;
  }

  /* ---------------- review ---------------- */
  function reviewPage() {
    const ids = dueIds();
    const rs = pageState.review || (pageState.review = { queue: ids.slice(0, DAILY_CAP), i: 0, shown: false, done: 0, again: 0, pick: undefined });
    if (rs.i >= rs.queue.length) {
      const nextDue = Object.values(S.cards).filter((c) => c.due > today()).map((c) => c.due).sort((a, b) => a - b)[0];
      const total = Object.keys(S.cards).length;
      return `<div class="rv"><span class="label">Spaced review</span><h1 style="font-size:48px">${rs.done ? "Review done" : "Nothing due right now"}</h1>
        ${rs.done ? `<p class="mute">You reviewed ${rs.done} card${rs.done === 1 ? "" : "s"}${rs.again ? `, and ${rs.again} will come back tomorrow` : ""}. That is the most valuable ten minutes of the day.</p>` : ""}
        <div class="empty">${total ? `You have ${total} cards in your deck. ${nextDue ? `The next one is due ${inDays(nextDue - today())}.` : ""} Cards come back just before you would forget them, so an empty queue is the system working.` : "Your deck is empty. Each finished lesson adds 5 to 7 cards, and every quiz question you miss joins them. They start coming back the day after."}</div>
        <div class="row">${nextUp() ? `<button class="btn" data-go="${nextUp()}">Go to the next lesson</button>` : ""}${doneCount() ? `<button class="btn ghost" data-go="practice">Mixed practice</button>` : ""}</div></div>`;
    }
    const id = rs.queue[rs.i];
    const c = S.cards[id], d = cardData(id);
    const src = d.lid ? L[d.lid] : null;
    const meta = `<div class="row" style="justify-content:space-between"><span class="label">Card ${rs.i + 1} of ${rs.queue.length}${ids.length > rs.queue.length ? ` · ${ids.length - rs.queue.length} more wait for tomorrow` : ""}</span>${src ? `<button class="tag" style="cursor:pointer;background:none" data-go="${src.id}">${esc(src.title)}</button>` : d.tid ? `<span class="tag">${esc(T[d.tid].title)} quiz</span>` : ""}</div>
      <div class="meter"><i style="width:${Math.round((rs.i / rs.queue.length) * 100)}%"></i></div>`;
    if (d.kind === "mcq") {
      const answered = rs.pick !== undefined;
      return `<div class="rv">${meta}<div class="qcard"><span class="label">A question you missed before</span><div class="q prose" style="max-width:none">${d.q.q}</div>
        <div class="opts" role="radiogroup" aria-label="Answers">${d.q.options.map((o, k) => `<button class="opt ${answered ? (k === d.q.answer ? "right" : k === rs.pick ? "wrong" : "fade") : ""}" role="radio" aria-checked="${k === rs.pick}" data-act="rv-pick" data-k="${k}" ${answered ? "disabled" : ""}><span class="ring" aria-hidden="true"></span><span class="ot">${o}${answered && k === d.q.answer ? '<span class="sr">, the right answer</span>' : ""}</span></button>`).join("")}</div>
        ${answered ? `<div class="why"><b>${rs.pick === d.q.answer ? "Right." : "Not this one. The right answer is marked."}</b> ${d.q.why}</div>` : ""}</div>
        ${answered ? `<div class="row"><button class="btn" data-act="rv-grade" data-g="${rs.pick === d.q.answer ? 3 : 1}">Next card</button></div>` : ""}</div>`;
    }
    const opts = [1, 2, 3, 4].map((g) => schedule(c, g, id, true).ivl);
    return `<div class="rv">${meta}
      <div class="flash"><div class="front">${d.front}</div>${rs.shown ? `<div class="back prose" style="max-width:none">${d.back}</div>` : ""}</div>
      ${rs.shown ? `<div class="grades">
        <button class="g1" data-act="rv-grade" data-g="1">Forgot<small>${ivlLabel(opts[0])}</small></button>
        <button data-act="rv-grade" data-g="2">Hard<small>${ivlLabel(opts[1])}</small></button>
        <button class="g3" data-act="rv-grade" data-g="3">Got it<small>${ivlLabel(opts[2])}</small></button>
        <button data-act="rv-grade" data-g="4">Easy<small>${ivlLabel(opts[3])}</small></button></div>
        <p class="mute" style="margin:0;font-size:14px">Be honest. "Got it" means you recalled it without peeking. The number is when you'll see the card again.</p>`
        : `<div class="row"><button class="btn hold" data-act="rv-show">Show answer</button><span class="mute" style="font-size:14.5px">Say or write your answer first.</span></div>`}
    </div>`;
  }
  function rvGrade(g) {
    const rs = pageState.review; const id = rs.queue[rs.i];
    schedule(S.cards[id], g, id);
    rs.done++; if (g === 1) rs.again++;
    logDay("r"); save();
    rs.i++; rs.shown = false; rs.pick = undefined;
    render(); scrollTo(0, 0);
  }

  /* ---------------- mixed practice ---------------- */
  function practicePage() {
    const doneIds = ORDER.filter((id) => S.done[id] && L[id].ready);
    if (!doneIds.length) return `<div class="rv"><span class="label">Mixed practice</span><h1 style="font-size:48px">Mixed practice</h1><div class="empty">Finish a lesson or two first. This page mixes quiz questions from everything you have finished, so you practice telling similar ideas apart.</div></div>`;
    if (!pageState.mix) {
      const pool = [];
      for (const id of doneIds) L[id].quiz.forEach((q, qi) => pool.push({ key: id, qi, q, w: 1 + (today() - dayNum(new Date(S.done[id]))) / 7 }));
      const pick = [];
      while (pick.length < Math.min(10, pool.length)) {
        const tot = pool.reduce((a, b) => a + b.w, 0); let r = Math.random() * tot;
        const k = pool.findIndex((x) => (r -= x.w) <= 0);
        pick.push(pool.splice(k < 0 ? 0 : k, 1)[0]);
      }
      pageState.mix = pick;
    }
    const st = pageState.quiz.mix || {};
    const all = pageState.mix.every((_, i) => st[i] !== undefined);
    const right = pageState.mix.filter((x, i) => st[i] === x.q.answer).length;
    return `<div class="rv" style="max-width:860px"><span class="label">Mixed practice · ${pageState.mix.length} questions from ${doneIds.length} finished lesson${doneIds.length === 1 ? "" : "s"}</span>
      <h1 style="font-size:48px">Tell similar ideas apart</h1>
      <p class="mute" style="margin:0">Questions come from all your finished lessons, older ones more often. Mixing topics feels harder than practicing one at a time. That difficulty is what helps you pick the right tool later.</p>
      <div class="quiz">${pageState.mix.map((x, i) => mcqCard(x.q, "mix", i, { num: true, lessonTag: `<span class="tag">${esc(L[x.key].title)}</span>` })).join("")}
      ${all ? `<div class="score"><div><span class="label">Score</span><div><b>${right} / ${pageState.mix.length}</b></div></div><span class="mute" style="font-size:15px">Missed questions join your review deck.</span><button class="btn" data-act="new-mix">New set</button></div>` : ""}</div></div>`;
  }

  /* ---------------- plan ---------------- */
  function planPage() {
    const nx = nextUp();
    const weeks = totalWeeks();
    let grid = "";
    for (let w = 1; w <= weeks; w++) {
      const ids = ORDER.slice((w - 1) * pace(), w * pace());
      const cur = ids.includes(nx);
      grid += `<div class="wk ${cur ? "cur" : ""}"><span class="label">Week ${w}</span><span class="wkcells">${ids.map((id) => `<button class="cell lg ${cellState(id)}" data-go="${id}" title="${wdLabel(id)}: ${esc(L[id].title)}" aria-label="${wdLabel(id)}: ${esc(L[id].title)}"></button>`).join("")}</span></div>`;
    }
    const leeches = Object.entries(S.cards).filter(([, c]) => c.leech).map(([id]) => id);
    const cardsTotal = Object.keys(S.cards).length;
    const mature = Object.values(S.cards).filter((c) => (c.ivl || 0) >= 21).length;
    const left = ORDER.length - doneCount();
    return `<header class="lhead"><span class="label">Plan and progress</span><h1>Your plan</h1>
      <p class="goal">The plan counts course weeks and days, not dates. Skip a day and nothing is "late": you pick up at the next lesson. Change how many days a week you study and the weeks rearrange around it.</p></header>
      <section class="kv" style="margin-bottom:34px">
        <div class="panel"><span class="label">Lessons done</span><div class="stat tnum">${doneCount()}<small>of ${ORDER.length}</small></div></div>
        <div class="panel"><span class="label">Current week</span><div class="stat tnum">${nx ? wd(nx).w : "Done"}<small>${nx ? `of ${weeks} · day ${wd(nx).d}` : ""}</small></div></div>
        <div class="panel"><span class="label">Still to go</span><div class="stat tnum">${Math.ceil(left / pace())}<small>weeks · ${left} lessons</small></div></div>
        <div class="panel"><span class="label">Cards in deck</span><div class="stat tnum">${cardsTotal}<small>${mature} long-term</small></div></div>
      </section>
      <section class="block" style="margin-top:0"><div class="row" style="justify-content:space-between"><span class="label">${weeks} weeks · one row per week · one cell per study day</span>
        <label class="row" style="gap:8px;font-size:15px" for="pace">Days a week <select class="field" id="pace" data-act="pace">${[3, 4, 5, 6, 7].map((n) => `<option value="${n}" ${pace() === n ? "selected" : ""}>${n}</option>`).join("")}</select></label></div>
        <div class="weeks">${grid}</div>
        <span class="mute" style="font-size:14px">Filled cells are done, the saffron cell is your next lesson. Studied ${studiedLast7()} of the last 7 days. Aim for most days, not every day: one missed day costs almost nothing.</span></section>
      ${leeches.length ? `<section class="block"><span class="label">Cards that keep slipping</span><p class="mute" style="margin:0">You've forgotten these 8 or more times. That usually means a gap in the lesson behind them. Reread the section, then keep going.</p>
        <div class="plan-list">${leeches.map((id) => { const d = cardData(id); return d ? `<div class="pr"><span class="d">card</span><i class="cell"></i><button data-go="${d.lid || "track-" + d.tid}">${d.kind === "flash" ? d.front : d.q.q}</button><span></span></div>` : ""; }).join("")}</div></section>` : ""}
      <section class="block"><span class="label">Schedule</span><div class="plan-list">
        ${Array.from({ length: weeks }, (_, k) => k + 1).map((w) => `<div class="ptrack">Week ${w}</div>` + ORDER.slice((w - 1) * pace(), w * pace()).map((id) => `<div class="pr"><span class="d">Day ${wd(id).d}</span><i class="cell ${cellState(id)}"></i><button data-go="${id}">${esc(L[id].title)} <span class="label" style="margin-left:6px">${esc(T[L[id].track].title)}</span></button><span class="label">${S.quiz[id] != null ? `quiz ${S.quiz[id]}/5` : ""}</span></div>`).join("")).join("")}
      </div></section>
      <section class="block"><span class="label">Move your progress</span><h2>Phone and laptop</h2>
        <p class="mute" style="margin:0;max-width:62ch">Progress lives in this browser. To move it, copy it here, then paste it on the other device and import. Importing merges: nothing you've done on either device is lost.</p>
        <textarea class="field" id="sync-box" rows="4" placeholder="Paste progress from another device here"></textarea>
        <div class="row"><button class="btn ghost sm" data-act="export">Copy my progress</button><button class="btn sm" data-act="import">Import pasted progress</button></div></section>`;
  }
  function importProgress(text) {
    let x; try { x = JSON.parse(text); } catch (e) { return toast("That isn't progress data. Copy it again from the other device."); }
    if (!x || typeof x !== "object" || !x.done) return toast("That isn't progress data. Copy it again from the other device.");
    mergeInto(x); save(); toast("Imported and merged."); render();
  }

  /* ---------------- reference pages ---------------- */
  function sheetsPage() {
    const have = C.tracks.filter((t) => t.cheatsheet);
    return `<header class="lhead"><span class="label">Reference</span><h1>Cheat sheets</h1><p class="goal">One page per track. Come back to these when you need the answer, not the lesson.</p></header>
      ${have.length ? have.map((t) => `<section class="sheet" id="sheet-${t.id}"><span class="label">${trackTag(t)}</span><h2>${esc(t.title)}</h2><div class="prose" style="max-width:none">${t.cheatsheet}</div></section>`).join("") : `<div class="empty">Cheat sheets appear here as tracks are written.</div>`}`;
  }
  function glossaryPage() {
    const all = [];
    for (const id of ORDER) if (L[id].ready) for (const t of L[id].terms) all.push({ t, id });
    all.sort((a, b) => a.t.term.replace(/<[^>]+>/g, "").localeCompare(b.t.term.replace(/<[^>]+>/g, ""), "en", { sensitivity: "base" }));
    const q = (pageState.gq || "").toLowerCase();
    const shown = all.filter((x) => !q || (x.t.term + " " + x.t.plain).replace(/<[^>]+>/g, "").toLowerCase().includes(q));
    return `<header class="lhead"><span class="label">Reference · ${all.length} terms</span><h1>Glossary</h1>
      <input class="field" id="gloss-filter" type="search" placeholder="Filter terms" aria-label="Filter terms" value="${esc(pageState.gq || "")}" style="max-width:420px"></header>
      <dl class="terms" style="max-width:none">${shown.map((x) => `<div><dt>${x.t.term}</dt><dd>${x.t.plain} <button class="tag" style="cursor:pointer;background:none;margin-left:4px" data-go="${x.id}">${esc(L[x.id].title)}</button></dd></div>`).join("") || `<div class="mute">No term matches.</div>`}</dl>`;
  }
  function setupPage() {
    if (!S.seenSetup) { S.seenSetup = true; save(); }
    const repo = C.repo;
    const cb = (title, src, lang = "bash") => codeBox({ html: esc(src), lang }, title);
    return `<header class="lhead"><span class="label">Before lesson one · about 15 minutes, once</span><h1>Set up the labs</h1>
      <p class="goal">Every lesson has code you run and a lab you finish. They all live in one Gradle project, so you set it up once.</p></header>
      <div class="prose" style="display:grid;gap:22px;max-width:860px">
        <section class="block" style="margin-top:0"><h2>1. Install JDK 25</h2><p>JDK 25 is the current long-term-support release. The labs compile for Java 21, so any JDK from 21 up works, but 25 lets you run every example in the lessons. SDKMAN makes switching versions painless:</p>
          ${cb("terminal", "curl -s \"https://get.sdkman.io\" | bash\nsdk install java 25-tem\njava -version")}</section>
        <section class="block"><h2>2. Get the repo</h2><p>The repo has this site's content and the <code>labs</code> folder.</p>
          ${cb("terminal", `git clone ${repo}.git\ncd jvm-workbench/labs\n./gradlew :concurrency:solutionTest`)}
          <p>The first run downloads Gradle, Kotlin and the libraries (a few minutes). <code>solutionTest</code> runs the tests against the reference answers, so everything should pass. That proves your setup works.</p></section>
        <section class="block"><h2>3. Open it in IntelliJ IDEA</h2><p>Open the <code>labs</code> folder (not the repo root) as a Gradle project. Each track is a module: <code>concurrency</code>, <code>jmm</code>, <code>executors</code>, <code>vthreads</code>, <code>generics</code>, <code>reactive</code>, <code>coroutines</code>, <code>patterns</code>. Each module has four source folders:</p>
          <div class="tablewrap"><table><thead><tr><th>Folder</th><th>What it holds</th></tr></thead><tbody>
            <tr><td><code>src/main</code></td><td>The exercises. This is where you write code.</td></tr>
            <tr><td><code>src/test</code></td><td>The tests that tell you when an exercise is done.</td></tr>
            <tr><td><code>src/demo</code></td><td>Small programs the "Try it" steps run. Edit them freely.</td></tr>
            <tr><td><code>src/solution</code></td><td>Reference answers. Same class names, same packages. Peek last.</td></tr></tbody></table></div>
          <p>Lesson <code>conc-03</code> lives in package <code>workbench.concurrency.l03</code> in every folder. The same pattern holds for every lesson.</p></section>
        <section class="block"><h2>4. The three commands you'll use</h2>
          ${cb("run one lesson's lab tests", "./gradlew :concurrency:test --tests 'workbench.concurrency.l03.*'")}
          ${cb("run a demo from a Try it step", "./gradlew :concurrency:demo -Pmain=workbench.concurrency.l03.RaceDemo")}
          ${cb("check the reference answers (should always pass)", "./gradlew :concurrency:solutionTest --tests 'workbench.concurrency.l03.*'")}
          <p>In IntelliJ you can also click the green arrow next to any test or <code>main</code>. For a Kotlin file <code>Foo.kt</code> with a top-level <code>main</code>, the class name is <code>FooKt</code>.</p></section>
        <section class="block"><h2>5. How to use the labs</h2><p>Read the failing test first. It is the spec. Then write the code, run the tests, and repeat. A deadlocked test fails after 20 seconds instead of hanging. Concurrency tests can pass by luck, so run a race fix three times before you call it done.</p></section>
        <div class="row"><button class="btn" data-go="${ORDER[0]}">Start lesson one</button></div>
      </div>`;
  }

  /* ---------------- focus timer: review 10, learn 12, practice 13 ---------------- */
  const PHASES = [["Review", 10], ["Learn", 12], ["Practice", 13]];
  const TOTAL = PHASES.reduce((a, b) => a + b[1], 0) * 60000;
  let tick;
  function elapsed() { const tm = S.timer; if (!tm) return 0; return Math.min(TOTAL, tm.acc + (tm.run ? Date.now() - tm.run : 0)); }
  function timerRender() {
    const slot = $("#timer-slot"); if (!slot) return;
    clearInterval(tick);
    if (!S.timer) { slot.innerHTML = ""; return; }
    const draw = () => {
      const e = elapsed(); const left = Math.max(0, TOTAL - e);
      let acc = 0, cur = PHASES.length - 1;
      const bars = PHASES.map(([n, m], i) => { const a = acc; acc += m * 60000; const f = clamp((e - a) / (m * 60000), 0, 1); if (e >= a && e < acc) cur = i; return { n, f, i }; });
      slot.innerHTML = `<div class="timer" role="timer"><div class="tt"><div><span class="label">${left ? `Now: ${PHASES[cur][0]}` : "Session done"}</span><div class="big tnum">${Math.floor(left / 60000)}:${pad(Math.floor((left % 60000) / 1000))}</div></div>
        <div class="row" style="gap:6px">${left ? `<button class="btn ghost sm" data-act="timer-pause">${S.timer.run ? "Pause" : "Resume"}</button>` : ""}<button class="btn ghost sm" data-act="timer-stop">Close</button></div></div>
        <div class="phases" style="grid-template-columns:${PHASES.map((p) => p[1] + "fr").join(" ")}">${bars.map((b) => `<div class="${b.i === cur && left ? "cur" : ""}"><i><b style="width:${Math.round(b.f * 100)}%"></b></i><span>${b.n} ${PHASES[b.i][1]}</span></div>`).join("")}</div></div>`;
      if (!left && S.timer.run) { S.timer.acc = TOTAL; S.timer.run = null; save(); }
    };
    draw();
    if (S.timer.run) tick = setInterval(draw, 1000);
  }

  /* ---------------- events ---------------- */
  document.addEventListener("click", (ev) => {
    const g = ev.target.closest("[data-go]");
    if (g) { ev.preventDefault(); mobileOpen = false; go(g.dataset.go); return; }
    const a = ev.target.closest("[data-act]");
    if (!a) return;
    const act = a.dataset.act, id = a.dataset.id;
    switch (act) {
      case "menu": if (isDesk()) deskOpen = !deskOpen; else mobileOpen = !mobileOpen; render(true); break;
      case "close-menu": mobileOpen = false; render(true); break;
      case "theme": S.theme = effectiveTheme() === "dark" ? "light" : "dark"; document.documentElement.setAttribute("data-theme", S.theme); save(); render(true); break;
      case "toc-toggle": {
        S.tocHide = !S.tocHide; save();
        const g = $(".lgrid"); if (g) g.classList.toggle("toc-off", !!S.tocHide);
        const f = $(S.tocHide ? ".toc-open" : ".toc-x"); if (f) f.focus({ preventScroll: true });
        break;
      }
      case "toggle-part": { const open = a.getAttribute("aria-expanded") === "true"; S.open["part-" + id] = !open; save(); sidebar(route()); break; }
      case "toggle-track": { const el = a.closest(".trk"); const open = a.getAttribute("aria-expanded") === "true"; S.open[id] = !open; save(); sidebar(route()); void el; break; }
      case "done": setDone(id, true); break;
      case "undone": setDone(id, false); break;
      case "hint": pageState.hints[id] = (pageState.hints[id] || 0) + 1; render(true); break;
      case "lang": { const top = a.getBoundingClientRect().top; setCodePref(a.dataset.lang); scrollBy(0, a.getBoundingClientRect().top - top); break; }
      case "answer": onAnswer(a.dataset.key, +a.dataset.qi, +a.dataset.k); break;
      case "retake": delete pageState.quiz[a.dataset.key]; delete pageState.quiz[a.dataset.key + ":retry"]; render(true); break;
      case "scroll": { const el = document.getElementById(id); if (el) el.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" }); break; }
      case "copy": copyText(a.dataset.text, a); break;
      case "copy-code": { const pre = a.closest(".codebox").querySelector("pre"); copyText(pre.innerText, a); break; }
      case "sim-step": simStep(id, +a.dataset.ti); simRender(a.closest(".sim")); break;
      case "sim-reset": simReset(id); simRender(a.closest(".sim")); break;
      case "rv-show": pageState.review.shown = true; render(); break;
      case "rv-pick": pageState.review.pick = +a.dataset.k; render(); break;
      case "rv-grade": rvGrade(+a.dataset.g); break;
      case "new-mix": delete pageState.mix; delete pageState.quiz.mix; render(); scrollTo(0, 0); break;
      case "export": copyText(JSON.stringify(syncDoc()), null).then(() => toast("Progress copied. Paste it on the other device.")); break;
      case "import": importProgress($("#sync-box").value); break;
      case "timer": if (!S.timer) S.timer = { acc: 0, run: Date.now() }; save(); timerRender(); break;
      case "timer-pause": if (S.timer.run) { S.timer.acc += Date.now() - S.timer.run; S.timer.run = null; } else S.timer.run = Date.now(); save(); timerRender(); break;
      case "timer-stop": S.timer = null; save(); timerRender(); break;
      default: break;
    }
  });
  document.addEventListener("change", (ev) => {
    const vset = ev.target.dataset && ev.target.dataset.vset;
    if (vset) {
      S[vset] = ev.target.value; save();
      $$(`select[data-vset="${vset}"]`).forEach((el) => { if ([...el.options].some((o) => o.value === S[vset])) el.value = S[vset]; });
      liveVids.forEach((w) => w.apply());
      return;
    }
    if (ev.target.id === "pace") { S.pace = +ev.target.value; S.paceAt = new Date().toISOString(); save(); render(true); }
  });
  let explainTimer;
  document.addEventListener("input", (ev) => {
    const t = ev.target;
    if (t.dataset && t.dataset.explain) { S.explain[t.dataset.explain] = t.value; clearTimeout(explainTimer); explainTimer = setTimeout(save, 400); }
    if (t.id === "lesson-filter") { filterText = t.value; sidebar(route()); const f = $("#lesson-filter"); f.focus(); f.setSelectionRange(f.value.length, f.value.length); }
    if (t.id === "gloss-filter") { pageState.gq = t.value; $("#page").innerHTML = glossaryPage(); const f = $("#gloss-filter"); f.focus(); f.setSelectionRange(f.value.length, f.value.length); }
  });
  addEventListener("keydown", (ev) => {
    if (ev.key === "Escape" && mobileOpen) { mobileOpen = false; render(true); }
    if (route() === "review" && pageState.review && !ev.target.closest("input,textarea,select")) {
      const rs = pageState.review;
      if (rs.i < rs.queue.length && cardData(rs.queue[rs.i]).kind === "flash") {
        if (!rs.shown && (ev.key === " " || ev.key === "Enter")) { ev.preventDefault(); rs.shown = true; render(); }
        else if (rs.shown && "1234".includes(ev.key) && ev.key.length === 1) rvGrade(+ev.key);
      }
    }
  });
  let wasDesk = isDesk();
  addEventListener("resize", () => { if (isDesk() !== wasDesk) { wasDesk = isDesk(); render(true); } });
  if (S.theme) document.documentElement.setAttribute("data-theme", S.theme);
  document.documentElement.setAttribute("data-code", S.code || "both");
  render();
  setTimeout(() => { const nx = nextUp(); if (nx && L[nx].remote && !L[nx].sections) loadLesson(L[nx]); }, 1200);
})();
