# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S - Streamlit Voice Agent
Fix: Single unified HTML component handles ALL voice I/O.
     st.query_params is the ONLY reliable bridge from JS -> Python in Streamlit Cloud.
     TTS text is embedded directly into the component on every rerender via f-string.
"""
import json
import datetime
import streamlit as st
import streamlit.components.v1 as components
from langchain_anthropic import ChatAnthropic
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from typing import Any
import urllib.request
import urllib.parse

st.set_page_config(page_title="J.A.R.V.I.S", page_icon="⚡", layout="wide")

# ============================================================
# THEME - Iron Blood: deep crimson + molten gold + void black
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&family=Exo+2:wght@300;400;700&display=swap');

:root {
  --j-void:    #06000f;
  --j-deep:    #0d0118;
  --j-panel:   rgba(18, 2, 35, 0.92);
  --j-gold:    #f5a623;
  --j-gold2:   #ffcc44;
  --j-crimson: #c0183a;
  --j-plasma:  #e040fb;
  --j-arc:     #00e5ff;
  --j-green:   #00ff88;
  --j-border:  rgba(245,166,35,0.25);
  --j-text:    #e8d5b0;
}

html, body, [data-testid="stAppViewContainer"] {
  background: var(--j-void) !important;
  font-family: 'Exo 2', sans-serif !important;
  color: var(--j-text) !important;
}

/* Animated hex grid background */
[data-testid="stAppViewContainer"]::before {
  content: '';
  position: fixed; inset: 0;
  background:
    radial-gradient(ellipse 70% 50% at 50% 0%,  rgba(192,24,58,0.12)  0%, transparent 60%),
    radial-gradient(ellipse 40% 30% at 80% 80%, rgba(224,64,251,0.08) 0%, transparent 50%),
    radial-gradient(ellipse 30% 40% at 10% 60%, rgba(0,229,255,0.06)  0%, transparent 50%),
    repeating-linear-gradient(60deg,  transparent, transparent 30px, rgba(245,166,35,0.015) 30px, rgba(245,166,35,0.015) 31px),
    repeating-linear-gradient(120deg, transparent, transparent 30px, rgba(245,166,35,0.015) 30px, rgba(245,166,35,0.015) 31px),
    repeating-linear-gradient(0deg,   transparent, transparent 30px, rgba(245,166,35,0.015) 30px, rgba(245,166,35,0.015) 31px);
  pointer-events: none; z-index: 0;
}

[data-testid="stHeader"]  { background: transparent !important; }
[data-testid="stSidebar"] {
  background: rgba(6,0,15,0.97) !important;
  border-right: 1px solid var(--j-border) !important;
}

/* TITLE */
.j-title {
  font-family: 'Orbitron', monospace;
  font-size: 2.6rem; font-weight: 900;
  background: linear-gradient(135deg, #f5a623 0%, #ffcc44 40%, #c0183a 70%, #e040fb 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  text-align: center; letter-spacing: 0.4em;
  padding: 1.2rem 0 0.2rem;
  filter: drop-shadow(0 0 20px rgba(245,166,35,0.5));
  animation: j-pulse 4s ease-in-out infinite;
}
.j-sub {
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.75rem; color: rgba(245,166,35,0.45);
  text-align: center; letter-spacing: 0.5em;
  text-transform: uppercase; margin-bottom: 1.8rem;
}
@keyframes j-pulse {
  0%,100% { filter: drop-shadow(0 0 15px rgba(245,166,35,0.4)); }
  50%      { filter: drop-shadow(0 0 35px rgba(245,166,35,0.8)) drop-shadow(0 0 60px rgba(192,24,58,0.3)); }
}

/* PANELS */
.j-panel {
  background: var(--j-panel);
  border: 1px solid var(--j-border);
  border-radius: 3px;
  padding: 0.9rem 1.1rem;
  margin-bottom: 0.9rem;
  position: relative;
  backdrop-filter: blur(12px);
}
.j-panel::before { content:''; position:absolute; top:0;    left:0;  width:28px; height:2px; background:var(--j-gold); }
.j-panel::after  { content:''; position:absolute; bottom:0; right:0; width:28px; height:2px; background:var(--j-crimson); }

.j-label {
  font-family: 'Orbitron', monospace; font-size: 0.55rem;
  color: rgba(245,166,35,0.5); letter-spacing: 0.25em;
  text-transform: uppercase; margin-bottom: 0.25rem;
}
.j-val {
  font-family: 'Share Tech Mono', monospace; font-size: 1rem;
  font-weight: 600; color: var(--j-gold2);
}

/* CHAT MESSAGES */
[data-testid="stChatMessage"] {
  background: rgba(18,2,35,0.8) !important;
  border: 1px solid rgba(245,166,35,0.18) !important;
  border-radius: 3px !important;
  margin-bottom: 0.5rem !important;
  backdrop-filter: blur(10px) !important;
}

/* CHAT INPUT */
[data-testid="stChatInput"] textarea {
  background: rgba(6,0,15,0.95) !important;
  border: 1px solid rgba(245,166,35,0.3) !important;
  color: var(--j-gold2) !important;
  font-family: 'Share Tech Mono', monospace !important;
  font-size: 0.95rem !important;
  border-radius: 3px !important;
}
[data-testid="stChatInput"] textarea:focus {
  border-color: var(--j-gold) !important;
  box-shadow: 0 0 20px rgba(245,166,35,0.2) !important;
}

/* BUTTONS */
.stButton > button {
  background: transparent !important;
  border: 1px solid rgba(245,166,35,0.3) !important;
  color: var(--j-gold) !important;
  font-family: 'Orbitron', monospace !important;
  font-size: 0.6rem !important;
  letter-spacing: 0.12em !important;
  border-radius: 2px !important;
  transition: all 0.2s !important;
}
.stButton > button:hover {
  background: rgba(245,166,35,0.08) !important;
  border-color: var(--j-gold) !important;
  box-shadow: 0 0 15px rgba(245,166,35,0.25) !important;
  color: var(--j-gold2) !important;
}

/* SCROLLBAR */
::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-track { background: rgba(6,0,15,0.8); }
::-webkit-scrollbar-thumb { background: rgba(245,166,35,0.3); border-radius: 2px; }

/* SPINNER */
[data-testid="stSpinner"] > div { border-color: var(--j-gold) transparent transparent !important; }

/* SIDEBAR CAPS */
[data-testid="stSidebar"] .j-cap {
  font-size: 0.78rem; color: rgba(245,166,35,0.65);
  padding: 3px 0; font-family: 'Share Tech Mono', monospace;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================
st.markdown('<div class="j-title">J.A.R.V.I.S</div>', unsafe_allow_html=True)
st.markdown('<div class="j-sub">Just A Rather Very Intelligent System &middot; Iron Protocol Active</div>', unsafe_allow_html=True)

# ============================================================
# TOOLS
# ============================================================
@tool
def get_current_datetime() -> str:
    """Returns the current date, time, day of week, and timezone info."""
    now = datetime.datetime.now()
    utc = datetime.datetime.utcnow()
    return (
        f"Current local datetime: {now.strftime('%A, %B %d, %Y at %H:%M:%S')}\n"
        f"UTC datetime: {utc.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        f"Week number: {now.isocalendar()[1]}, Day of year: {now.timetuple().tm_yday}"
    )

@tool
def set_reminder(task: str, minutes: int) -> str:
    """Acknowledges a reminder request and explains limitation.
    Args:
        task: What the reminder is for.
        minutes: Minutes from now.
    """
    return (
        f"I appreciate the request, but I must inform you that I cannot schedule "
        f"live notifications or alarms for '{task}' in {minutes} minutes. "
        f"My architecture runs on-demand — I have no persistent background process "
        f"to fire a future alert. I recommend your device's clock app or calendar for this."
    )

@tool
def get_weather(city: str) -> str:
    """Gets current weather for a city.
    Args:
        city: Name of the city.
    """
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1"
        with urllib.request.urlopen(geo_url, timeout=5) as r:
            geo = json.loads(r.read())
        if not geo.get("results"):
            return f"City '{city}' not found."
        loc = geo["results"][0]
        lat, lon, name, country = loc["latitude"], loc["longitude"], loc["name"], loc.get("country","")
        wx_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
            f"&temperature_unit=celsius&wind_speed_unit=kmh"
        )
        with urllib.request.urlopen(wx_url, timeout=5) as r:
            wx = json.loads(r.read())
        c = wx["current"]
        codes = {0:"Clear sky",1:"Mainly clear",2:"Partly cloudy",3:"Overcast",
                 45:"Foggy",48:"Icy fog",51:"Light drizzle",61:"Light rain",
                 63:"Moderate rain",65:"Heavy rain",71:"Light snow",80:"Rain showers",95:"Thunderstorm"}
        desc = codes.get(c["weather_code"], f"Code {c['weather_code']}")
        return (f"Weather in {name}, {country}: {desc}, {c['temperature_2m']}C, "
                f"Humidity {c['relative_humidity_2m']}%, Wind {c['wind_speed_10m']} kmh")
    except Exception as e:
        return f"Weather lookup failed: {e}"

@tool
def get_news(topic: str = "technology") -> str:
    """Searches for latest news on a topic.
    Args:
        topic: The news topic.
    """
    try:
        search = DuckDuckGoSearchRun()
        results = search.run(f"latest news {topic} 2025")
        return f"Latest news on '{topic}':\n{results}"
    except Exception as e:
        return f"News fetch failed: {e}"

@tool
def web_search(query: str) -> str:
    """Searches the web for any query.
    Args:
        query: Search query.
    """
    try:
        search = DuckDuckGoSearchRun()
        return search.run(query)
    except Exception as e:
        return f"Search failed: {e}"

@tool
def analyze_trend(subject: str) -> str:
    """Analyzes historical context and current trends.
    Args:
        subject: Topic to analyze.
    """
    search = DuckDuckGoSearchRun()
    past    = search.run(f"{subject} history milestones key events")
    current = search.run(f"{subject} current trends 2025 latest")
    forecast= search.run(f"{subject} future predictions forecast 2026")
    return (f"TEMPORAL ANALYSIS: {subject}\n\n[HISTORICAL]\n{past[:450]}\n\n"
            f"[CURRENT 2025]\n{current[:450]}\n\n[OUTLOOK]\n{forecast[:450]}")

@tool
def predict_insights(domain: str) -> str:
    """Generates predictive insights for a domain.
    Args:
        domain: Domain to forecast.
    """
    search = DuckDuckGoSearchRun()
    data  = search.run(f"{domain} market forecast predictions 2025 2026")
    stats = search.run(f"{domain} statistics growth rate data")
    return (f"PREDICTIVE INSIGHTS: {domain}\n\n[FORECAST]\n{data[:550]}\n\n[STATS]\n{stats[:350]}")

@tool
def read_local_file(file_path: str) -> str:
    """Reads content of a local text or code file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool
def write_local_file(file_path: str, content: str) -> str:
    """Writes content into a local text file."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

# ============================================================
# AGENT
# ============================================================
tools_list: list[Any] = [
    DuckDuckGoSearchRun(),
    get_current_datetime,
    set_reminder,
    get_weather,
    get_news,
    web_search,
    analyze_trend,
    predict_insights,
    read_local_file,
    write_local_file,
]

SYSTEM_PROMPT = """You are J.A.R.V.I.S - Just A Rather Very Intelligent System.
Personality: Tony Stark's AI. Calm, precise, confident, occasionally witty.

CRITICAL RULES:
- Always use tools for live data. Never guess dates, weather, or news.
- For voice: be CONCISE. 1-3 sentences for simple queries. Max 5 for complex.
- NO markdown: no **, ##, -, *, backticks. Plain natural sentences only.
- Use JARVIS phrases: "Certainly", "Right away", "Analysis complete", "Noted".
- Lead with the answer, then detail. Never bury the key fact.
- For reminders/alarms: use set_reminder tool, it will explain the limitation politely.
- For scheduling/notifications: explain clearly you cannot set future timed alerts.
"""

@st.cache_resource
def build_agent() -> Any:
    llm = ChatAnthropic(
        model="claude-sonnet-4-5",
        temperature=0.3,
        api_key=st.secrets["ANTHROPIC_API_KEY"],
    )
    return create_react_agent(llm, tools_list, prompt=SYSTEM_PROMPT)

agent = build_agent()

# ============================================================
# SESSION STATE
# ============================================================
for key, default in [
    ("chat_history",  None),
    ("voice_input",   ""),
    ("last_voice_ts", ""),
    ("tts_text",      ""),
    ("tts_seq",       0),
]:
    if key not in st.session_state:
        st.session_state[key] = default if default is not None else InMemoryChatMessageHistory()

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown('<div class="j-label">⬡ SYSTEM STATUS</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="j-panel">
      <div class="j-val" style="color:#00ff88;">&#9679; ONLINE</div>
      <div class="j-label">Iron protocol active &mdash; all systems nominal</div>
    </div>""", unsafe_allow_html=True)

    now = datetime.datetime.now()
    st.markdown(f"""
    <div class="j-panel">
      <div class="j-label">&#9670; LOCAL TIME</div>
      <div class="j-val">{now.strftime('%H:%M:%S')}</div>
      <div class="j-label">{now.strftime('%A, %d %B %Y')}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="j-label" style="margin-top:0.5rem;">&#9671; VOICE PROTOCOL</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="j-panel" style="font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:rgba(245,166,35,0.7);line-height:1.7;">
      Say <span style="color:#ffcc44;font-weight:bold;">HEY JARVIS</span> to activate<br>
      Speak command &rarr; auto-submit<br>
      JARVIS speaks response back<br>
      <span style="color:rgba(245,166,35,0.4);">Requires Chrome / Edge</span>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="j-label" style="margin-top:0.5rem;">&#9671; CAPABILITIES</div>', unsafe_allow_html=True)
    for cap in ["&#128269; Web Search","&#127780; Live Weather","&#128240; Global News",
                "&#128202; Trend Analysis","&#128302; Forecasting","&#128337; Reminders Info",
                "&#128193; File I/O","&#128336; DateTime"]:
        st.markdown(f'<div class="j-cap">{cap}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="j-label">&#9671; QUICK FIRE</div>', unsafe_allow_html=True)
    quick_cmds = {
        "&#128336; Date & Time":   "What is the current date and time?",
        "&#127780; Weather NYC":   "What is the weather in New York right now?",
        "&#128240; Tech News":     "Get me the latest technology news",
        "&#128202; AI Trends":     "Analyze current AI trends and the future outlook",
        "&#128302; Energy Market": "Predictive insights on the renewable energy market",
        "&#128337; Set Reminder":  "Set a reminder for my meeting in 30 minutes",
    }
    for label, cmd in quick_cmds.items():
        if st.button(label, use_container_width=True):
            st.session_state.voice_input = cmd
            st.rerun()

    if st.button("&#128465; Clear Memory", use_container_width=True):
        st.session_state.chat_history = InMemoryChatMessageHistory()
        st.session_state.tts_text = ""
        st.rerun()

# ============================================================
# READ VOICE COMMAND FROM URL PARAMS  (JS -> Python bridge)
# This is the ONLY reliable bridge on Streamlit Cloud.
# The JS component writes ?vc=...&vts=... then Streamlit detects
# the URL change on its next poll cycle and reruns.
# ============================================================
params    = st.query_params
raw_vc    = params.get("vc",  "")
raw_vts   = params.get("vts", "")
voice_cmd = ""
try:
    if raw_vc:
        voice_cmd = urllib.parse.unquote(raw_vc)
except Exception:
    voice_cmd = raw_vc

if voice_cmd and raw_vts != st.session_state.last_voice_ts:
    st.session_state.voice_input   = voice_cmd
    st.session_state.last_voice_ts = raw_vts
    st.query_params.clear()

# ============================================================
# CHAT HISTORY
# ============================================================
TYPE_TO_ROLE = {"human": "user", "ai": "assistant"}
for msg in st.session_state.chat_history.messages:
    role = TYPE_TO_ROLE.get(msg.type, msg.type)
    with st.chat_message(role):
        st.write(msg.content)

# ============================================================
# HANDLE INPUT (text or voice)
# ============================================================
user_query = st.chat_input("Interface with J.A.R.V.I.S...")

if st.session_state.voice_input and not user_query:
    user_query = st.session_state.voice_input
    st.session_state.voice_input = ""

if user_query:
    with st.chat_message("user"):
        st.write(user_query)

    history: list[HumanMessage | AIMessage] = [
        HumanMessage(content=str(m.content)) if m.type == "human"
        else AIMessage(content=str(m.content))
        for m in st.session_state.chat_history.messages
    ]
    history.append(HumanMessage(content=user_query))

    with st.spinner("⚡ Processing..."):
        result      = agent.invoke({"messages": history})
        output_text = str(result["messages"][-1].content)

    with st.chat_message("assistant"):
        st.write(output_text)

    # Store TTS text in session state - the voice component reads it on rerender
    clean_tts = (
        output_text
        .replace('"',  " ")
        .replace("'",  " ")
        .replace("`",  " ")
        .replace("\\", " ")
        .replace("\n", " ")
        .replace("#",  " ")
        .replace("*",  " ")
        .strip()[:900]
    )
    st.session_state.tts_text = clean_tts
    st.session_state.tts_seq += 1   # increment so JS knows it's a new response

    st.session_state.chat_history.add_user_message(user_query)
    st.session_state.chat_history.add_ai_message(output_text)

# ============================================================
# VOICE HUD - Single unified component
# ARCHITECTURE FIX:
#   - tts_text & tts_seq injected via Python f-string on every render
#   - JS detects new seq number -> speaks the text automatically
#   - Voice command written to window.location search params
#   - Streamlit's built-in URL polling triggers rerun
#   - No postMessage needed, no cross-iframe DOM access needed
# ============================================================
tts_text_safe = st.session_state.tts_text
tts_seq       = st.session_state.tts_seq

voice_component = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Share+Tech+Mono&display=swap');

#jv {{
  font-family: 'Exo 2', sans-serif;
  background: linear-gradient(135deg, rgba(18,2,35,0.97) 0%, rgba(6,0,15,0.99) 100%);
  border: 1px solid rgba(245,166,35,0.3);
  border-radius: 6px;
  padding: 18px 22px 16px;
  position: relative;
  user-select: none;
  overflow: hidden;
}}

/* Animated corner lines */
#jv::before {{
  content:'';
  position:absolute; top:0; left:0;
  width:0; height:2px;
  background: linear-gradient(90deg, #f5a623, #c0183a);
  animation: scan-h 3s ease-in-out infinite;
}}
#jv::after {{
  content:'';
  position:absolute; bottom:0; right:0;
  width:0; height:2px;
  background: linear-gradient(270deg, #e040fb, #f5a623);
  animation: scan-h 3s ease-in-out infinite reverse;
}}
@keyframes scan-h {{
  0%   {{ width:0; }}
  50%  {{ width:100%; }}
  100% {{ width:0; }}
}}

.jv-corner {{
  position:absolute; width:12px; height:12px;
  border-color: rgba(245,166,35,0.6);
  border-style: solid;
}}
.jv-tl {{ top:0; left:0;   border-width:2px 0 0 2px; }}
.jv-tr {{ top:0; right:0;  border-width:2px 2px 0 0; }}
.jv-bl {{ bottom:0; left:0;  border-width:0 0 2px 2px; }}
.jv-br {{ bottom:0; right:0; border-width:0 2px 2px 0; }}

#jv-row {{
  display:flex; align-items:center; gap:14px; margin-bottom:14px;
}}
#jv-dot {{
  width:14px; height:14px; border-radius:50%;
  background:#1a0a2a;
  box-shadow: 0 0 0 rgba(245,166,35,0);
  transition: background 0.3s, box-shadow 0.4s;
  flex-shrink:0;
  position:relative;
}}
#jv-dot::after {{
  content:'';
  position:absolute; inset:-4px;
  border-radius:50%;
  border: 1px solid rgba(245,166,35,0.2);
  animation: ring-pulse 2s ease-in-out infinite;
}}
@keyframes ring-pulse {{
  0%,100% {{ transform:scale(1); opacity:0.4; }}
  50%      {{ transform:scale(1.3); opacity:0.1; }}
}}
#jv-status {{
  font-family:'Orbitron',monospace;
  font-size:0.6rem; letter-spacing:0.2em;
  color:rgba(245,166,35,0.5);
  flex:1;
}}

/* Waveform */
#jv-wave {{
  display:flex; align-items:flex-end; justify-content:center;
  gap:2px; height:40px; margin-bottom:12px;
}}
.jvb {{
  width:3px; border-radius:2px 2px 0 0;
  background:rgba(245,166,35,0.2);
  transition:height 0.08s;
}}

/* Transcript */
#jv-tbox {{
  font-family:'Share Tech Mono',monospace;
  font-size:0.85rem; color:#f5a623;
  text-align:center; min-height:22px;
  letter-spacing:0.05em;
  text-shadow: 0 0 8px rgba(245,166,35,0.4);
}}
</style>

<div id="jv">
  <div class="jv-corner jv-tl"></div>
  <div class="jv-corner jv-tr"></div>
  <div class="jv-corner jv-bl"></div>
  <div class="jv-corner jv-br"></div>

  <div id="jv-row">
    <div id="jv-dot"></div>
    <span id="jv-status">INITIALIZING IRON PROTOCOL...</span>
  </div>

  <div id="jv-wave">
    {''.join(['<div class="jvb" style="height:' + str(h) + 'px;"></div>' for h in
              [4,6,4,8,5,4,10,6,4,7,12,5,4,9,14,6,4,8,5,4,6,4,5,4,6,4,7,4,5,4,6,4,8,4,5,4]])}
  </div>

  <div id="jv-tbox">Say <strong style="color:#ffcc44;">HEY JARVIS</strong> to activate...</div>
</div>

<script>
(function() {{

  // ── Python-injected TTS payload (changes on every rerender with new response) ──
  const TTS_TEXT = {json.dumps(tts_text_safe)};
  const TTS_SEQ  = {tts_seq};

  // ── Persistent seq tracking via localStorage ──────────────────────────────────
  const SPOKEN_KEY = 'jarvis_spoken_seq';
  let lastSpokenSeq = parseInt(localStorage.getItem(SPOKEN_KEY) || '0', 10);

  // ── DOM ───────────────────────────────────────────────────────────────────────
  const dot    = document.getElementById('jv-dot');
  const status = document.getElementById('jv-status');
  const tbox   = document.getElementById('jv-tbox');
  const bars   = Array.from(document.querySelectorAll('.jvb'));

  // ── State ─────────────────────────────────────────────────────────────────────
  let wakeRec       = null;
  let cmdRec        = null;
  let isWaking      = false;
  let isCommand     = false;
  let isSpeaking    = false;
  let micStream     = null;
  let audioCtx      = null;
  let rafId         = null;
  let silenceTimer  = null;
  let finalText     = '';

  // ── Themes ────────────────────────────────────────────────────────────────────
  const T = {{
    boot:     {{ d:'#1a0a2a', g:'none',                              s:'IRON PROTOCOL INITIALIZING' }},
    wake:     {{ d:'#f5a623', g:'0 0 12px rgba(245,166,35,0.7)',     s:'LISTENING FOR WAKE WORD' }},
    detected: {{ d:'#00ff88', g:'0 0 16px rgba(0,255,136,0.75)',     s:'WAKE WORD DETECTED' }},
    command:  {{ d:'#e040fb', g:'0 0 16px rgba(224,64,251,0.75)',    s:'LISTENING — SPEAK YOUR COMMAND' }},
    thinking: {{ d:'#00e5ff', g:'0 0 16px rgba(0,229,255,0.7)',      s:'NEURAL NET PROCESSING...' }},
    speaking: {{ d:'#c0183a', g:'0 0 18px rgba(192,24,58,0.8)',      s:'JARVIS SPEAKING' }},
    error:    {{ d:'#ff3333', g:'none',                              s:'SYSTEM ERROR — RECOVERING' }},
    noapi:    {{ d:'#ff3333', g:'none',                              s:'CHROME/EDGE REQUIRED' }},
  }};

  function theme(key) {{
    const t = T[key] || T.boot;
    dot.style.background = t.d;
    dot.style.boxShadow  = t.g;
    status.textContent   = t.s;
  }}

  // ── Waveform helpers ──────────────────────────────────────────────────────────
  function idle() {{
    bars.forEach((b,i) => {{
      b.style.height     = (4 + Math.sin(i*0.6)*4) + 'px';
      b.style.background = 'rgba(245,166,35,0.18)';
    }});
  }}

  function startWave(stream) {{
    stopWave();
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const analyser = audioCtx.createAnalyser();
    analyser.fftSize = 128;
    audioCtx.createMediaStreamSource(stream).connect(analyser);
    const data = new Uint8Array(analyser.frequencyBinCount);
    function frame() {{
      analyser.getByteFrequencyData(data);
      bars.forEach((b,i) => {{
        const v = data[Math.floor(i * data.length / bars.length)];
        const h = Math.max(4, (v/255)*38);
        b.style.height     = h + 'px';
        b.style.background = `rgba(224,64,251,${{0.3 + v/600}})`;
      }});
      rafId = requestAnimationFrame(frame);
    }}
    frame();
  }}

  function stopWave() {{
    if (rafId)    {{ cancelAnimationFrame(rafId); rafId = null; }}
    if (audioCtx) {{ audioCtx.close().catch(()=>{{}}); audioCtx = null; }}
    idle();
  }}

  function speakingWave() {{
    let t = 0;
    function frame() {{
      t += 0.15;
      bars.forEach((b,i) => {{
        const h = 5 + Math.abs(Math.sin(t + i*0.4)) * 32;
        b.style.height     = h + 'px';
        const r = Math.round(192 + Math.sin(t+i)*40);
        b.style.background = `rgba(${{r}},24,58,0.75)`;
      }});
      if (isSpeaking) rafId = requestAnimationFrame(frame);
      else idle();
    }}
    if (rafId) cancelAnimationFrame(rafId);
    frame();
  }}

  // ── Chime ─────────────────────────────────────────────────────────────────────
  function chime() {{
    try {{
      const c = new (window.AudioContext||window.webkitAudioContext)();
      [[528,0],[660,0.12],[792,0.24],[1056,0.36]].forEach(([f,d]) => {{
        const o=c.createOscillator(), g=c.createGain();
        o.type='sine'; o.frequency.value=f;
        o.connect(g); g.connect(c.destination);
        g.gain.setValueAtTime(0,c.currentTime+d);
        g.gain.linearRampToValueAtTime(0.2,c.currentTime+d+0.05);
        g.gain.linearRampToValueAtTime(0,c.currentTime+d+0.35);
        o.start(c.currentTime+d); o.stop(c.currentTime+d+0.4);
      }});
    }} catch(e) {{}}
  }}

  // ── TTS ───────────────────────────────────────────────────────────────────────
  function speak(text) {{
    if (!window.speechSynthesis || !text || !text.trim()) return;
    window.speechSynthesis.cancel();
    isSpeaking = true;
    theme('speaking');
    speakingWave();
    tbox.innerHTML = '<span style="color:#c0183a;">&#9654; SPEAKING...</span>';

    const u = new SpeechSynthesisUtterance(text.trim());
    u.rate = 0.9; u.pitch = 0.75; u.volume = 1.0;

    function go() {{
      const vs = window.speechSynthesis.getVoices();
      const pick =
        vs.find(v => v.name === 'Google UK English Male') ||
        vs.find(v => v.name.includes('Daniel'))           ||
        vs.find(v => v.name.includes('Alex'))             ||
        vs.find(v => v.lang === 'en-GB')                  ||
        vs.find(v => v.lang.startsWith('en-'));
      if (pick) u.voice = pick;

      u.onend = u.onerror = () => {{
        isSpeaking = false;
        idle();
        theme('wake');
        tbox.innerHTML = 'Say <strong style="color:#ffcc44;">HEY JARVIS</strong> to continue...';
        setTimeout(startWake, 500);
      }};
      window.speechSynthesis.speak(u);
    }}

    if (window.speechSynthesis.getVoices().length) go();
    else window.speechSynthesis.onvoiceschanged = go;
  }}

  // ── Auto-speak new TTS if seq changed ─────────────────────────────────────────
  // This fires when Python re-renders the component with new tts_seq
  if (TTS_TEXT && TTS_SEQ > 0 && TTS_SEQ !== lastSpokenSeq) {{
    localStorage.setItem(SPOKEN_KEY, TTS_SEQ);
    lastSpokenSeq = TTS_SEQ;
    // Small delay so component is fully painted
    setTimeout(() => speak(TTS_TEXT), 300);
  }}

  // ── getMic ────────────────────────────────────────────────────────────────────
  function getMic() {{
    return navigator.mediaDevices.getUserMedia({{
      audio: {{ echoCancellation:true, noiseSuppression:true, autoGainControl:true }}
    }});
  }}

  function releaseMic() {{
    if (micStream) {{ micStream.getTracks().forEach(t=>t.stop()); micStream=null; }}
    stopWave();
  }}

  // ── WAKE WORD LISTENER ────────────────────────────────────────────────────────
  function startWake() {{
    if (isWaking || isCommand || isSpeaking) return;
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {{
      theme('noapi');
      tbox.textContent = 'Speech API requires Chrome or Edge browser.';
      return;
    }}

    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    wakeRec = new SR();
    wakeRec.continuous=true; wakeRec.interimResults=true;
    wakeRec.lang='en-US'; wakeRec.maxAlternatives=5;

    wakeRec.onstart = () => {{
      isWaking = true;
      theme('wake');
      tbox.innerHTML = 'Say <strong style="color:#ffcc44;">HEY JARVIS</strong> to activate...';
      idle();
    }};

    wakeRec.onresult = (e) => {{
      if (isCommand || isSpeaking) return;
      for (let i=e.resultIndex; i<e.results.length; i++) {{
        for (let j=0; j<e.results[i].length; j++) {{
          const heard = e.results[i][j].transcript.toLowerCase().trim();
          if (heard.includes('hey jarvis') || (heard.includes('jarvis') && heard.length < 18)) {{
            try {{ wakeRec.abort(); }} catch(x) {{}}
            onWake();
            return;
          }}
        }}
      }}
    }};

    wakeRec.onerror = (e) => {{
      isWaking = false;
      if (['no-speech','aborted','network'].includes(e.error)) {{
        setTimeout(startWake, 500);
      }} else {{
        theme('error');
        setTimeout(startWake, 2500);
      }}
    }};

    wakeRec.onend = () => {{
      isWaking = false;
      if (!isCommand && !isSpeaking) setTimeout(startWake, 400);
    }};

    try {{ wakeRec.start(); }} catch(e) {{ setTimeout(startWake, 1000); }}
  }}

  // ── WAKE DETECTED ─────────────────────────────────────────────────────────────
  function onWake() {{
    isWaking = false;
    theme('detected');
    tbox.textContent = 'Iron Man protocol activated...';
    chime();
    setTimeout(startCmd, 600);
  }}

  // ── COMMAND LISTENER ──────────────────────────────────────────────────────────
  function startCmd() {{
    if (isCommand) return;
    isCommand = true;
    finalText = '';

    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    cmdRec = new SR();
    cmdRec.continuous=false; cmdRec.interimResults=true;
    cmdRec.lang='en-US'; cmdRec.maxAlternatives=1;

    cmdRec.onstart = () => {{
      theme('command');
      tbox.textContent = 'Speak your command...';
      getMic().then(s => {{ micStream=s; startWave(s); }}).catch(()=>{{}});
      silenceTimer = setTimeout(() => {{ try{{cmdRec.stop();}}catch(x){{}} }}, 8000);
    }};

    cmdRec.onresult = (e) => {{
      clearTimeout(silenceTimer);
      silenceTimer = setTimeout(() => {{ try{{cmdRec.stop();}}catch(x){{}} }}, 3500);
      let interim=''; finalText='';
      for (let i=e.resultIndex; i<e.results.length; i++) {{
        if (e.results[i].isFinal) finalText += e.results[i][0].transcript + ' ';
        else                      interim   += e.results[i][0].transcript;
      }}
      tbox.textContent = (finalText||interim).trim() || '...';
    }};

    cmdRec.onerror = (e) => {{
      clearTimeout(silenceTimer);
      isCommand=false; releaseMic();
      if (e.error==='no-speech') {{
        tbox.innerHTML='Nothing heard. Say <strong style="color:#ffcc44;">HEY JARVIS</strong> again.';
        theme('wake'); setTimeout(startWake,700);
      }} else {{
        theme('error'); setTimeout(startWake,1800);
      }}
    }};

    cmdRec.onend = () => {{
      clearTimeout(silenceTimer);
      releaseMic(); isCommand=false;
      const cmd = finalText.trim();
      if (cmd.length > 1) {{
        theme('thinking');
        tbox.textContent = cmd;
        submitToStreamlit(cmd);
      }} else {{
        tbox.innerHTML='Nothing captured. Say <strong style="color:#ffcc44;">HEY JARVIS</strong> again.';
        theme('wake'); setTimeout(startWake,700);
      }}
    }};

    try {{ cmdRec.start(); }} catch(e) {{ isCommand=false; setTimeout(startWake,1000); }}
  }}

  // ── SUBMIT TO STREAMLIT ───────────────────────────────────────────────────────
  // Strategy: write to the URL's query string.
  // Streamlit polls the URL every ~500ms and reruns when params change.
  // This is the ONLY sandboxing-safe method on Streamlit Cloud.
  function submitToStreamlit(text) {{
    const encoded = encodeURIComponent(text);
    const ts      = Date.now().toString();

    // Write to current window's URL (this component IS the top window inside its iframe)
    // We need to write to the PARENT window's URL
    try {{
      // This works when allow-same-origin is set (Streamlit sets it for components.html)
      const parentUrl = new URL(window.parent.location.href);
      parentUrl.searchParams.set('vc',  encoded);
      parentUrl.searchParams.set('vts', ts);
      window.parent.history.replaceState({{}}, '', parentUrl.toString());
    }} catch(err) {{
      // Fallback: navigate the parent
      try {{
        const parentUrl = new URL(window.parent.location.href);
        parentUrl.searchParams.set('vc',  encoded);
        parentUrl.searchParams.set('vts', ts);
        window.parent.location.replace(parentUrl.toString());
      }} catch(err2) {{
        // Last resort: write to own URL and hope Streamlit picks it up
        const u = new URL(window.location.href);
        u.searchParams.set('vc', encoded);
        u.searchParams.set('vts', ts);
        window.location.replace(u.toString());
      }}
    }}
  }}

  // ── BOOT ──────────────────────────────────────────────────────────────────────
  theme('boot');
  idle();

  // If TTS already set from this render, auto-speak first before starting wake
  if (TTS_TEXT && TTS_SEQ > 0 && TTS_SEQ === lastSpokenSeq) {{
    // Already spoken this seq, go straight to wake
    setTimeout(startWake, 900);
  }} else {{
    setTimeout(startWake, 900);
  }}

}})();
</script>
"""

components.html(voice_component, height=190)
