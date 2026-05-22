# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S - Ultimate Voice Agent
- Smart interrupt: tap/say to stop JARVIS mid-speech
- Instant wake: always listening, one-shot command
- Music player: Deezer API (free, no auth) for global tracks
- Full UI/UX overhaul: Arc Reactor theme
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

# ─────────────────────────────────────────────────────────────
# ARC REACTOR THEME
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=Share+Tech+Mono&family=Rajdhani:wght@300;400;500;600&display=swap');

:root {
  --arc:    #00d4ff;
  --arc2:   #00aadd;
  --gold:   #f5a623;
  --gold2:  #ffcc44;
  --red:    #c0183a;
  --plasma: #8b5cf6;
  --green:  #10b981;
  --void:   #020b18;
  --deep:   #040f1e;
  --panel:  rgba(4,15,30,0.94);
  --border: rgba(0,212,255,0.2);
  --text:   #a8d4e8;
}

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
  background: var(--void) !important;
  font-family: 'Rajdhani', sans-serif !important;
  color: var(--text) !important;
  overflow-x: hidden;
}

/* Animated background grid */
[data-testid="stAppViewContainer"]::before {
  content: '';
  position: fixed; inset: 0; z-index: 0;
  background:
    radial-gradient(ellipse 60% 40% at 50% -10%, rgba(0,170,221,0.18) 0%, transparent 70%),
    radial-gradient(ellipse 30% 25% at 85% 90%, rgba(139,92,246,0.1) 0%, transparent 60%),
    radial-gradient(ellipse 25% 30% at 5%  70%, rgba(192,24,58,0.07) 0%, transparent 60%),
    repeating-linear-gradient(0deg,   transparent, transparent 44px, rgba(0,212,255,0.025) 44px, rgba(0,212,255,0.025) 45px),
    repeating-linear-gradient(90deg,  transparent, transparent 44px, rgba(0,212,255,0.025) 44px, rgba(0,212,255,0.025) 45px);
  pointer-events: none;
  animation: bg-drift 20s ease-in-out infinite alternate;
}
@keyframes bg-drift {
  0%   { opacity:0.8; }
  100% { opacity:1.0; }
}

[data-testid="stHeader"]  { background: transparent !important; border-bottom: 1px solid rgba(0,212,255,0.08) !important; }
[data-testid="stSidebar"] {
  background: rgba(2,11,24,0.98) !important;
  border-right: 1px solid rgba(0,212,255,0.15) !important;
}
[data-testid="stSidebar"] > div { padding-top: 1rem !important; }

/* ── TITLE ── */
.j-title {
  font-family: 'Orbitron', monospace;
  font-size: clamp(1.8rem, 4vw, 3rem);
  font-weight: 900;
  text-align: center;
  letter-spacing: 0.5em;
  padding: 1.5rem 0 0.3rem;
  background: linear-gradient(90deg, #00aadd 0%, #00d4ff 30%, #ffffff 50%, #00d4ff 70%, #00aadd 100%);
  background-size: 200%;
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: title-shine 4s linear infinite;
  filter: drop-shadow(0 0 30px rgba(0,212,255,0.4));
}
@keyframes title-shine {
  0%   { background-position: 200% center; }
  100% { background-position: -200% center; }
}
.j-sub {
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.72rem;
  color: rgba(0,212,255,0.4);
  text-align: center;
  letter-spacing: 0.55em;
  text-transform: uppercase;
  margin-bottom: 1.2rem;
}

/* ── PANELS ── */
.j-panel {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 0.85rem 1rem;
  margin-bottom: 0.8rem;
  position: relative;
  backdrop-filter: blur(16px);
}
.j-panel::before { content:''; position:absolute; top:0;    left:0;  width:24px; height:1px; background:var(--arc); }
.j-panel::after  { content:''; position:absolute; bottom:0; right:0; width:24px; height:1px; background:var(--arc); }

.j-label {
  font-family: 'Orbitron', monospace; font-size: 0.52rem;
  color: rgba(0,212,255,0.45); letter-spacing: 0.3em;
  text-transform: uppercase; margin-bottom: 0.3rem;
}
.j-val {
  font-family: 'Share Tech Mono', monospace; font-size: 1.05rem;
  color: var(--arc);
}

/* ── CHAT ── */
[data-testid="stChatMessage"] {
  background: rgba(4,15,30,0.85) !important;
  border: 1px solid rgba(0,212,255,0.12) !important;
  border-radius: 4px !important;
  margin-bottom: 0.5rem !important;
  backdrop-filter: blur(12px) !important;
}
[data-testid="stChatInput"] textarea {
  background: rgba(2,11,24,0.97) !important;
  border: 1px solid rgba(0,212,255,0.25) !important;
  color: var(--arc) !important;
  font-family: 'Share Tech Mono', monospace !important;
  font-size: 0.9rem !important;
  border-radius: 4px !important;
  caret-color: var(--arc);
}
[data-testid="stChatInput"] textarea:focus {
  border-color: var(--arc) !important;
  box-shadow: 0 0 20px rgba(0,212,255,0.15) !important;
}

/* ── BUTTONS ── */
.stButton > button {
  background: transparent !important;
  border: 1px solid rgba(0,212,255,0.2) !important;
  color: rgba(0,212,255,0.75) !important;
  font-family: 'Orbitron', monospace !important;
  font-size: 0.58rem !important;
  letter-spacing: 0.1em !important;
  border-radius: 3px !important;
  padding: 0.4rem 0.8rem !important;
  transition: all 0.2s !important;
}
.stButton > button:hover {
  background: rgba(0,212,255,0.07) !important;
  border-color: var(--arc) !important;
  color: var(--arc) !important;
  box-shadow: 0 0 12px rgba(0,212,255,0.2) !important;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 3px; height: 3px; }
::-webkit-scrollbar-track { background: rgba(0,0,0,0.3); }
::-webkit-scrollbar-thumb { background: rgba(0,212,255,0.25); border-radius: 2px; }

/* ── SPINNER ── */
[data-testid="stSpinner"] > div { border-color: var(--arc) transparent transparent !important; }

/* ── TAB STYLING ── */
[data-testid="stTabs"] [role="tab"] {
  font-family: 'Orbitron', monospace !important;
  font-size: 0.6rem !important;
  letter-spacing: 0.15em !important;
  color: rgba(0,212,255,0.5) !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
  color: var(--arc) !important;
  border-bottom-color: var(--arc) !important;
}

.j-cap {
  font-size: 0.78rem; color: rgba(0,212,255,0.6);
  padding: 2px 0; font-family: 'Share Tech Mono', monospace;
}

/* ── ARC REACTOR ── */
.arc-ring {
  width: 60px; height: 60px;
  border-radius: 50%;
  border: 2px solid rgba(0,212,255,0.3);
  display: flex; align-items: center; justify-content: center;
  margin: 0.5rem auto;
  position: relative;
  animation: arc-spin 8s linear infinite;
}
.arc-ring::before {
  content:'';
  position:absolute; inset:4px; border-radius:50%;
  border: 1px solid rgba(0,212,255,0.2);
  animation: arc-spin 4s linear infinite reverse;
}
.arc-core {
  width: 20px; height: 20px; border-radius: 50%;
  background: radial-gradient(circle, #00e5ff, #0088bb);
  box-shadow: 0 0 15px #00d4ff, 0 0 30px rgba(0,212,255,0.5);
  animation: core-pulse 2s ease-in-out infinite;
}
@keyframes arc-spin  { to { transform: rotate(360deg); } }
@keyframes core-pulse {
  0%,100% { box-shadow: 0 0 12px #00d4ff, 0 0 25px rgba(0,212,255,0.4); }
  50%      { box-shadow: 0 0 20px #00d4ff, 0 0 50px rgba(0,212,255,0.7); }
}

/* ── MUSIC PLAYER ── */
.music-player {
  background: linear-gradient(135deg, rgba(4,15,30,0.97), rgba(8,25,50,0.97));
  border: 1px solid rgba(0,212,255,0.2);
  border-radius: 6px;
  padding: 1rem;
  margin-top: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────
st.markdown('<div class="j-title">J.A.R.V.I.S</div>', unsafe_allow_html=True)
st.markdown('<div class="j-sub">Just A Rather Very Intelligent System &nbsp;&middot;&nbsp; Arc Reactor Online</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# TOOLS
# ─────────────────────────────────────────────────────────────
@tool
def get_current_datetime() -> str:
    """Returns the current date, time, day of week, and timezone info."""
    now = datetime.datetime.now()
    utc = datetime.datetime.utcnow()
    return (f"Local: {now.strftime('%A, %B %d, %Y at %H:%M:%S')} | "
            f"UTC: {utc.strftime('%H:%M:%S')} | Week {now.isocalendar()[1]}")

@tool
def set_reminder(task: str, minutes: int) -> str:
    """Handles reminder/alarm requests with honest capability disclosure.
    Args:
        task: What the reminder is for.
        minutes: Minutes from now.
    """
    return (f"I appreciate the request, but I must be transparent: I cannot schedule "
            f"live notifications or alarms for '{task}' in {minutes} minutes. "
            f"My architecture is on-demand — no persistent background process exists "
            f"to fire a future alert. Please use your device's native clock or calendar.")

@tool
def get_weather(city: str) -> str:
    """Gets current weather for a city.
    Args:
        city: Name of the city.
    """
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1"
        with urllib.request.urlopen(geo_url, timeout=6) as r:
            geo = json.loads(r.read())
        if not geo.get("results"):
            return f"City '{city}' not found."
        loc = geo["results"][0]
        lat, lon, name, country = loc["latitude"], loc["longitude"], loc["name"], loc.get("country","")
        wx_url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                  f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
                  f"&temperature_unit=celsius&wind_speed_unit=kmh")
        with urllib.request.urlopen(wx_url, timeout=6) as r:
            wx = json.loads(r.read())
        c = wx["current"]
        codes = {0:"Clear sky",1:"Mainly clear",2:"Partly cloudy",3:"Overcast",
                 45:"Foggy",51:"Light drizzle",61:"Light rain",63:"Moderate rain",
                 65:"Heavy rain",71:"Light snow",80:"Rain showers",95:"Thunderstorm"}
        desc = codes.get(c["weather_code"], "Unknown")
        return (f"{name}, {country}: {desc}, {c['temperature_2m']}C, "
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
        return DuckDuckGoSearchRun().run(f"latest news {topic} 2025")
    except Exception as e:
        return f"News fetch failed: {e}"

@tool
def web_search(query: str) -> str:
    """Searches the web for any query.
    Args:
        query: Search query string.
    """
    try:
        return DuckDuckGoSearchRun().run(query)
    except Exception as e:
        return f"Search failed: {e}"

@tool
def analyze_trend(subject: str) -> str:
    """Analyzes historical context and current trends for any subject.
    Args:
        subject: Topic to analyze.
    """
    s = DuckDuckGoSearchRun()
    past = s.run(f"{subject} history milestones key events")
    curr = s.run(f"{subject} current trends 2025 latest")
    fore = s.run(f"{subject} future predictions forecast 2026")
    return (f"TEMPORAL ANALYSIS: {subject}\n[HISTORICAL]\n{past[:400]}\n"
            f"[CURRENT 2025]\n{curr[:400]}\n[OUTLOOK]\n{fore[:400]}")

@tool
def predict_insights(domain: str) -> str:
    """Generates data-driven predictive insights for a domain.
    Args:
        domain: Domain to forecast.
    """
    s = DuckDuckGoSearchRun()
    data  = s.run(f"{domain} market forecast predictions 2025 2026")
    stats = s.run(f"{domain} statistics growth rate data")
    return f"PREDICTIVE INSIGHTS: {domain}\n[FORECAST]\n{data[:500]}\n[STATS]\n{stats[:300]}"

@tool
def search_music(query: str) -> str:
    """Searches for music tracks using Deezer API.
    Args:
        query: Song, artist, or album name to search.
    """
    try:
        url = f"https://api.deezer.com/search?q={urllib.parse.quote(query)}&limit=5"
        with urllib.request.urlopen(url, timeout=6) as r:
            data = json.loads(r.read())
        tracks = data.get("data", [])
        if not tracks:
            return f"No tracks found for '{query}'."
        results = []
        for t in tracks[:5]:
            results.append(f"{t['title']} by {t['artist']['name']} (Album: {t['album']['title']})")
        return "Found tracks:\n" + "\n".join(results)
    except Exception as e:
        return f"Music search failed: {e}"

@tool
def read_local_file(file_path: str) -> str:
    """Reads content of a local text or code file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def write_local_file(file_path: str, content: str) -> str:
    """Writes content into a local text file."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Written to {file_path}"
    except Exception as e:
        return f"Error: {str(e)}"

# ─────────────────────────────────────────────────────────────
# AGENT
# ─────────────────────────────────────────────────────────────
tools_list: list[Any] = [
    DuckDuckGoSearchRun(), get_current_datetime, set_reminder,
    get_weather, get_news, web_search, analyze_trend, predict_insights,
    search_music, read_local_file, write_local_file,
]

SYSTEM_PROMPT = """You are J.A.R.V.I.S - Just A Rather Very Intelligent System.
Personality: Tony Stark's AI. Calm, precise, confident, occasionally witty.

CRITICAL RULES:
- Always use tools for live data. Never guess dates, weather, news, or music.
- Voice responses: CONCISE. 1-3 sentences for simple queries. Max 4 for complex.
- NO markdown symbols in responses. No **, ##, -, *, backticks. Plain sentences only.
- JARVIS phrases: "Certainly", "Right away", "Analysis complete", "Noted, sir".
- Lead with the answer first. Detail second. Never bury the key fact.
- Reminders/alarms: use set_reminder tool for honest capability disclosure.
- Music queries: use search_music tool then tell user what was found naturally.
"""

@st.cache_resource
def build_agent() -> Any:
    llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0.3,
                        api_key=st.secrets["ANTHROPIC_API_KEY"])
    return create_react_agent(llm, tools_list, prompt=SYSTEM_PROMPT)

agent = build_agent()

# ─────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────
defaults = {
    "chat_history":  None,
    "voice_input":   "",
    "last_voice_ts": "",
    "tts_text":      "",
    "tts_seq":       0,
    "active_tab":    "chat",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v if v is not None else InMemoryChatMessageHistory()

# ─────────────────────────────────────────────────────────────
# VOICE COMMAND FROM URL PARAMS (JS -> Python bridge)
# ─────────────────────────────────────────────────────────────
params  = st.query_params
raw_vc  = params.get("vc",  "")
raw_vts = params.get("vts", "")
try:
    voice_cmd = urllib.parse.unquote(raw_vc) if raw_vc else ""
except Exception:
    voice_cmd = raw_vc

if voice_cmd and raw_vts != st.session_state.last_voice_ts:
    st.session_state.voice_input   = voice_cmd
    st.session_state.last_voice_ts = raw_vts
    st.query_params.clear()

# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:0.5rem 0 1rem;">
      <div class="arc-ring"><div class="arc-core"></div></div>
      <div style="font-family:'Orbitron',monospace;font-size:0.55rem;color:rgba(0,212,255,0.5);letter-spacing:0.3em;margin-top:0.4rem;">ARC REACTOR ONLINE</div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="j-label">System Status</div>', unsafe_allow_html=True)
    now = datetime.datetime.now()
    st.markdown(f"""
    <div class="j-panel">
      <div class="j-val" style="color:#10b981;font-size:0.85rem;">&#9679; ALL SYSTEMS NOMINAL</div>
      <div style="font-family:'Share Tech Mono',monospace;font-size:0.7rem;color:rgba(0,212,255,0.5);margin-top:4px;">
        {now.strftime('%H:%M:%S')} &nbsp;|&nbsp; {now.strftime('%d %b %Y')}
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="j-label" style="margin-top:0.6rem;">Voice Protocol</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="j-panel" style="font-family:'Share Tech Mono',monospace;font-size:0.7rem;color:rgba(0,212,255,0.6);line-height:1.9;">
      <span style="color:#00d4ff;">HEY JARVIS</span> &rarr; activate<br>
      Speak &rarr; auto-submit<br>
      <span style="color:#f5a623;">TAP ORB</span> &rarr; interrupt speech<br>
      <span style="color:rgba(0,212,255,0.35);">Chrome / Edge only</span>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="j-label" style="margin-top:0.6rem;">Capabilities</div>', unsafe_allow_html=True)
    for cap in ["&#127925; Music Player","&#128269; Web Search","&#127780; Live Weather",
                "&#128240; Global News","&#128202; Trend Analysis","&#128302; Forecasting",
                "&#128337; Reminders","&#128336; DateTime"]:
        st.markdown(f'<div class="j-cap">{cap}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="j-label">Quick Fire</div>', unsafe_allow_html=True)
    cmds = {
        "&#128336; Date & Time":    "What is the current date and time?",
        "&#127780; Weather NYC":    "What is the weather in New York right now?",
        "&#128240; Tech News":      "Get me the latest AI and technology news",
        "&#128202; AI Trends":      "Analyze current AI trends and future outlook",
        "&#127925; Play Music":     "Search for popular songs by The Weeknd",
        "&#128337; Reminder Info":  "Set a reminder for my meeting in 30 minutes",
    }
    for label, cmd in cmds.items():
        if st.button(label, use_container_width=True):
            st.session_state.voice_input = cmd
            st.rerun()

    st.markdown("---")
    if st.button("&#128465; Clear Memory", use_container_width=True):
        st.session_state.chat_history = InMemoryChatMessageHistory()
        st.session_state.tts_text = ""
        st.session_state.tts_seq = 0
        st.rerun()

# ─────────────────────────────────────────────────────────────
# MAIN TABS
# ─────────────────────────────────────────────────────────────
tab_chat, tab_music = st.tabs(["⚡  JARVIS INTERFACE", "🎵  MUSIC STATION"])

# ═══════════════════════════════════════════
# TAB 1: CHAT + VOICE
# ═══════════════════════════════════════════
with tab_chat:

    # ── VOICE HUD ──────────────────────────────────────────────
    tts_safe = st.session_state.tts_text
    tts_seq  = st.session_state.tts_seq

    voice_html = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Share+Tech+Mono&display=swap');
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ background:transparent; overflow:hidden; }}

#jv {{
  background: linear-gradient(160deg, rgba(4,15,30,0.98) 0%, rgba(2,8,20,0.99) 100%);
  border: 1px solid rgba(0,212,255,0.22);
  border-radius: 8px;
  padding: 14px 18px 12px;
  position: relative;
  overflow: hidden;
  font-family: 'Rajdhani', sans-serif;
}}

/* Scanning top line */
#jv::before {{
  content:''; position:absolute; top:0; left:-100%; width:60%; height:1px;
  background: linear-gradient(90deg, transparent, #00d4ff, transparent);
  animation: scan 4s linear infinite;
}}
@keyframes scan {{ to {{ left:200%; }} }}

/* Corner brackets */
.c {{ position:absolute; width:10px; height:10px; border-color:rgba(0,212,255,0.5); border-style:solid; }}
.tl {{ top:0; left:0;   border-width:1px 0 0 1px; }}
.tr {{ top:0; right:0;  border-width:1px 1px 0 0; }}
.bl {{ bottom:0; left:0;  border-width:0 0 1px 1px; }}
.br {{ bottom:0; right:0; border-width:0 1px 1px 0; }}

/* Status row */
#row {{ display:flex; align-items:center; gap:12px; margin-bottom:10px; }}

/* ORB - clickable to interrupt */
#orb {{
  width:18px; height:18px; border-radius:50%; flex-shrink:0;
  background: #0a1a2a;
  box-shadow: 0 0 0 rgba(0,212,255,0);
  transition: background 0.25s, box-shadow 0.3s, transform 0.15s;
  cursor: pointer;
  position: relative;
}}
#orb::after {{
  content:''; position:absolute; inset:-5px; border-radius:50%;
  border: 1px solid rgba(0,212,255,0.15);
  animation: orb-ring 2.5s ease-in-out infinite;
}}
@keyframes orb-ring {{
  0%,100% {{ transform:scale(1); opacity:0.3; }}
  50%      {{ transform:scale(1.4); opacity:0.08; }}
}}
#orb:hover {{ transform: scale(1.15); }}
#orb:active {{ transform: scale(0.9); }}

#status {{
  font-family:'Orbitron',monospace; font-size:0.58rem;
  letter-spacing:0.2em; color:rgba(0,212,255,0.45); flex:1;
}}
#interrupt-hint {{
  font-family:'Share Tech Mono',monospace; font-size:0.6rem;
  color:rgba(0,212,255,0.25); white-space:nowrap;
}}

/* Waveform */
#wave {{
  display:flex; align-items:flex-end; justify-content:center;
  gap:2px; height:38px; margin-bottom:10px;
}}
.b {{ width:3px; border-radius:2px 2px 0 0; background:rgba(0,212,255,0.15); transition:height 0.07s,background 0.1s; }}

/* Transcript */
#tbox {{
  font-family:'Share Tech Mono',monospace; font-size:0.82rem;
  color:#00d4ff; text-align:center; min-height:20px;
  letter-spacing:0.04em; line-height:1.4;
}}
</style>

<div id="jv">
  <div class="c tl"></div><div class="c tr"></div>
  <div class="c bl"></div><div class="c br"></div>

  <div id="row">
    <div id="orb" title="Tap to interrupt JARVIS" onclick="interrupt()"></div>
    <span id="status">ARC REACTOR INITIALIZING...</span>
    <span id="interrupt-hint">TAP ORB TO INTERRUPT</span>
  </div>

  <div id="wave">
    {''.join(['<div class="b" style="height:' + str(h) + 'px"></div>'
              for h in [4,5,4,7,4,5,9,4,5,7,11,5,4,8,13,6,4,9,5,4,6,4,5,4,7,4,6,4,5,4,7,4,5,4,8,4]])}
  </div>

  <div id="tbox">Say <strong style="color:#00ffff;">HEY JARVIS</strong> to activate</div>
</div>

<script>
(function() {{

  // ── Python TTS injection ─────────────────────────────────
  const TTS_TEXT = {json.dumps(tts_safe)};
  const TTS_SEQ  = {tts_seq};
  const SKEY     = 'jv_spoken_seq';
  let lastSeq    = parseInt(localStorage.getItem(SKEY) || '0', 10);

  // ── DOM ──────────────────────────────────────────────────
  const orb    = document.getElementById('orb');
  const status = document.getElementById('status');
  const tbox   = document.getElementById('tbox');
  const bars   = Array.from(document.querySelectorAll('.b'));

  // ── State ────────────────────────────────────────────────
  let wakeRec     = null, cmdRec = null;
  let isWaking    = false, isCommand = false, isSpeaking = false;
  let micStream   = null, audioCtx = null, rafId = null, silTimer = null;
  let finalText   = '';
  let currentUttr = null;

  // ── Themes ───────────────────────────────────────────────
  const T = {{
    boot:     {{ d:'#0a1a2a', g:'none',                              s:'ARC REACTOR INITIALIZING' }},
    wake:     {{ d:'#00d4ff', g:'0 0 14px rgba(0,212,255,0.75)',     s:'LISTENING FOR WAKE WORD' }},
    detected: {{ d:'#00ff88', g:'0 0 16px rgba(0,255,136,0.8)',      s:'WAKE DETECTED — READY' }},
    command:  {{ d:'#8b5cf6', g:'0 0 16px rgba(139,92,246,0.8)',     s:'LISTENING — SPEAK NOW' }},
    thinking: {{ d:'#f5a623', g:'0 0 16px rgba(245,166,35,0.75)',    s:'NEURAL NET PROCESSING' }},
    speaking: {{ d:'#c0183a', g:'0 0 18px rgba(192,24,58,0.85)',     s:'SPEAKING — TAP ORB TO STOP' }},
    interrupt: {{ d:'#ff6b35', g:'0 0 14px rgba(255,107,53,0.8)',    s:'INTERRUPTED — READY' }},
    error:    {{ d:'#ff3333', g:'none',                              s:'ERROR — RECOVERING' }},
    noapi:    {{ d:'#ff3333', g:'none',                              s:'USE CHROME OR EDGE' }},
  }};

  function theme(k) {{
    const t = T[k] || T.boot;
    orb.style.background = t.d;
    orb.style.boxShadow  = t.g;
    status.textContent   = t.s;
  }}

  // ── INTERRUPT ────────────────────────────────────────────
  // Called by orb click OR if user speaks while JARVIS talking
  function interrupt() {{
    if (isSpeaking) {{
      window.speechSynthesis.cancel();
      isSpeaking = false;
      theme('interrupt');
      idle();
      tbox.innerHTML = 'Interrupted. Say <strong style="color:#00ffff;">HEY JARVIS</strong> or speak...';
      setTimeout(startWake, 300);
    }}
  }}

  // ── Waveform ─────────────────────────────────────────────
  function idle() {{
    bars.forEach((b,i) => {{
      b.style.height     = (4 + Math.sin(i*0.55)*4) + 'px';
      b.style.background = 'rgba(0,212,255,0.15)';
    }});
  }}

  function startWave(stream) {{
    stopWave();
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const an = audioCtx.createAnalyser(); an.fftSize = 128;
    audioCtx.createMediaStreamSource(stream).connect(an);
    const data = new Uint8Array(an.frequencyBinCount);
    function fr() {{
      an.getByteFrequencyData(data);
      bars.forEach((b,i) => {{
        const v = data[Math.floor(i * data.length / bars.length)];
        const h = Math.max(4, (v/255)*36);
        b.style.height     = h + 'px';
        b.style.background = `rgba(139,92,246,${{0.35 + v/550}})`;
      }});
      rafId = requestAnimationFrame(fr);
    }}
    fr();
  }}

  function stopWave() {{
    if (rafId)    {{ cancelAnimationFrame(rafId); rafId = null; }}
    if (audioCtx) {{ audioCtx.close().catch(()=>{{}}); audioCtx = null; }}
    idle();
  }}

  function speakWave() {{
    let t = 0;
    function fr() {{
      t += 0.12;
      bars.forEach((b,i) => {{
        const h = 5 + Math.abs(Math.sin(t + i*0.38)) * 30;
        const rv = Math.round(192 + Math.sin(t+i*0.5)*40);
        b.style.height     = h + 'px';
        b.style.background = `rgba(${{rv}},24,58,0.8)`;
      }});
      if (isSpeaking) rafId = requestAnimationFrame(fr);
      else idle();
    }}
    if (rafId) cancelAnimationFrame(rafId);
    fr();
  }}

  // ── Chime ────────────────────────────────────────────────
  function chime() {{
    try {{
      const ctx = new (window.AudioContext||window.webkitAudioContext)();
      [[440,0],[554,0.1],[659,0.2],[880,0.3]].forEach(([f,d]) => {{
        const o=ctx.createOscillator(), g=ctx.createGain();
        o.type='sine'; o.frequency.value=f;
        o.connect(g); g.connect(ctx.destination);
        g.gain.setValueAtTime(0,ctx.currentTime+d);
        g.gain.linearRampToValueAtTime(0.18,ctx.currentTime+d+0.05);
        g.gain.linearRampToValueAtTime(0,ctx.currentTime+d+0.3);
        o.start(ctx.currentTime+d); o.stop(ctx.currentTime+d+0.35);
      }});
    }} catch(e) {{}}
  }}

  // ── TTS ──────────────────────────────────────────────────
  function speak(text) {{
    if (!window.speechSynthesis || !text || !text.trim()) return;
    window.speechSynthesis.cancel();
    isSpeaking = true;
    theme('speaking');
    speakWave();
    tbox.innerHTML = '<span style="color:#c0183a;">&#9654; SPEAKING &mdash; TAP ORB TO INTERRUPT</span>';

    const u = new SpeechSynthesisUtterance(text.trim());
    u.rate = 0.88; u.pitch = 0.72; u.volume = 1.0;
    currentUttr = u;

    function go() {{
      const vs = window.speechSynthesis.getVoices();
      const pick =
        vs.find(v => v.name === 'Google UK English Male') ||
        vs.find(v => v.name.includes('Daniel'))           ||
        vs.find(v => v.name.includes('David'))            ||
        vs.find(v => v.lang === 'en-GB')                  ||
        vs.find(v => v.lang.startsWith('en'));
      if (pick) u.voice = pick;
      u.onend = u.onerror = () => afterSpeak();
      window.speechSynthesis.speak(u);
    }}
    if (window.speechSynthesis.getVoices().length) go();
    else window.speechSynthesis.onvoiceschanged = go;
  }}

  function afterSpeak() {{
    isSpeaking = false;
    idle();
    theme('wake');
    tbox.innerHTML = 'Say <strong style="color:#00ffff;">HEY JARVIS</strong> to continue...';
    setTimeout(startWake, 400);
  }}

  // Auto-speak on new response
  if (TTS_TEXT && TTS_SEQ > 0 && TTS_SEQ !== lastSeq) {{
    localStorage.setItem(SKEY, TTS_SEQ);
    lastSeq = TTS_SEQ;
    setTimeout(() => speak(TTS_TEXT), 350);
  }}

  // ── Mic ──────────────────────────────────────────────────
  function getMic() {{
    return navigator.mediaDevices.getUserMedia({{
      audio: {{ echoCancellation:true, noiseSuppression:true, autoGainControl:true }}
    }});
  }}
  function releaseMic() {{
    if (micStream) {{ micStream.getTracks().forEach(t=>t.stop()); micStream=null; }}
    stopWave();
  }}

  // ── WAKE WORD ────────────────────────────────────────────
  function startWake() {{
    if (isWaking || isCommand || isSpeaking) return;
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {{
      theme('noapi');
      tbox.textContent = 'Speech API requires Chrome or Edge.';
      return;
    }}
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    wakeRec = new SR();
    wakeRec.continuous=true; wakeRec.interimResults=true;
    wakeRec.lang='en-US'; wakeRec.maxAlternatives=5;

    wakeRec.onstart = () => {{
      isWaking=true; theme('wake');
      tbox.innerHTML='Say <strong style="color:#00ffff;">HEY JARVIS</strong> to activate';
      idle();
    }};
    wakeRec.onresult = (e) => {{
      if (isCommand || isSpeaking) return;
      for (let i=e.resultIndex; i<e.results.length; i++) {{
        for (let j=0; j<e.results[i].length; j++) {{
          const h = e.results[i][j].transcript.toLowerCase().trim();
          // Smart detection: accept "hey jarvis", "jarvis", "ok jarvis"
          if (h.includes('hey jarvis') || h.includes('ok jarvis') ||
              (h.includes('jarvis') && h.length < 22)) {{
            try {{ wakeRec.abort(); }} catch(x) {{}}
            onWake(); return;
          }}
        }}
      }}
    }};
    wakeRec.onerror = (e) => {{
      isWaking=false;
      if (['no-speech','aborted','network'].includes(e.error)) setTimeout(startWake,500);
      else {{ theme('error'); setTimeout(startWake,2500); }}
    }};
    wakeRec.onend = () => {{
      isWaking=false;
      if (!isCommand && !isSpeaking) setTimeout(startWake,350);
    }};
    try {{ wakeRec.start(); }} catch(e) {{ setTimeout(startWake,1000); }}
  }}

  function onWake() {{
    isWaking=false; theme('detected');
    tbox.textContent='Arc Reactor activated — speak your command...';
    chime();
    setTimeout(startCmd, 550);
  }}

  // ── COMMAND LISTENER ─────────────────────────────────────
  function startCmd() {{
    if (isCommand) return;
    isCommand=true; finalText='';
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    cmdRec = new SR();
    cmdRec.continuous=false; cmdRec.interimResults=true;
    cmdRec.lang='en-US'; cmdRec.maxAlternatives=1;

    cmdRec.onstart = () => {{
      theme('command');
      tbox.textContent='Listening...';
      getMic().then(s=>{{ micStream=s; startWave(s); }}).catch(()=>{{}});
      silTimer=setTimeout(()=>{{ try{{cmdRec.stop();}}catch(x){{}} }},8000);
    }};
    cmdRec.onresult = (e) => {{
      clearTimeout(silTimer);
      silTimer=setTimeout(()=>{{ try{{cmdRec.stop();}}catch(x){{}} }},3000);
      let interim=''; finalText='';
      for (let i=e.resultIndex; i<e.results.length; i++) {{
        if (e.results[i].isFinal) finalText+=e.results[i][0].transcript+' ';
        else interim+=e.results[i][0].transcript;
      }}
      tbox.textContent=(finalText||interim).trim()||'...';
    }};
    cmdRec.onerror = (e) => {{
      clearTimeout(silTimer); isCommand=false; releaseMic();
      if (e.error==='no-speech') {{
        tbox.innerHTML='Nothing heard. Say <strong style="color:#00ffff;">HEY JARVIS</strong> again.';
        theme('wake'); setTimeout(startWake,700);
      }} else {{ theme('error'); setTimeout(startWake,1800); }}
    }};
    cmdRec.onend = () => {{
      clearTimeout(silTimer); releaseMic(); isCommand=false;
      const cmd=finalText.trim();
      if (cmd.length>1) {{
        theme('thinking'); tbox.textContent=cmd;
        submit(cmd);
      }} else {{
        tbox.innerHTML='Nothing captured. Say <strong style="color:#00ffff;">HEY JARVIS</strong>.';
        theme('wake'); setTimeout(startWake,700);
      }}
    }};
    try {{ cmdRec.start(); }} catch(e) {{ isCommand=false; setTimeout(startWake,1000); }}
  }}

  // ── SUBMIT (URL param bridge) ─────────────────────────────
  function submit(text) {{
    const enc=encodeURIComponent(text), ts=Date.now().toString();
    try {{
      const u=new URL(window.parent.location.href);
      u.searchParams.set('vc',enc); u.searchParams.set('vts',ts);
      window.parent.history.replaceState({{}}, '', u.toString());
    }} catch(e1) {{
      try {{
        const u=new URL(window.parent.location.href);
        u.searchParams.set('vc',enc); u.searchParams.set('vts',ts);
        window.parent.location.replace(u.toString());
      }} catch(e2) {{}}
    }}
  }}

  // ── BOOT ─────────────────────────────────────────────────
  theme('boot'); idle();
  setTimeout(startWake, 1000);

}})();
</script>
"""
    components.html(voice_html, height=178)

    # ── CHAT HISTORY ───────────────────────────────────────────
    TYPE_TO_ROLE = {"human": "user", "ai": "assistant"}
    for msg in st.session_state.chat_history.messages:
        role = TYPE_TO_ROLE.get(msg.type, msg.type)
        with st.chat_message(role):
            st.write(msg.content)

    # ── HANDLE INPUT ───────────────────────────────────────────
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

        # Clean and store TTS text - injected into component on next render
        clean_tts = (
            output_text
            .replace('"', " ").replace("'", " ").replace("`", " ")
            .replace("\\", " ").replace("\n", " ")
            .replace("#", " ").replace("*", " ")
            .strip()[:900]
        )
        st.session_state.tts_text = clean_tts
        st.session_state.tts_seq += 1

        st.session_state.chat_history.add_user_message(user_query)
        st.session_state.chat_history.add_ai_message(output_text)

# ═══════════════════════════════════════════
# TAB 2: MUSIC STATION
# ═══════════════════════════════════════════
with tab_music:
    music_html = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;900&family=Share+Tech+Mono&family=Rajdhani:wght@400;600&display=swap');
* { box-sizing:border-box; margin:0; padding:0; }
body { background:transparent; font-family:'Rajdhani',sans-serif; color:#a8d4e8; }

#mp {
  background: linear-gradient(160deg, rgba(4,15,30,0.98), rgba(6,0,30,0.99));
  border: 1px solid rgba(0,212,255,0.2);
  border-radius: 8px;
  padding: 20px;
  position: relative;
  overflow: hidden;
}
#mp::before {
  content:''; position:absolute; top:0; left:-100%; width:50%; height:1px;
  background: linear-gradient(90deg, transparent, #00d4ff, transparent);
  animation: scan2 5s linear infinite;
}
@keyframes scan2 { to { left:200%; } }

h2 {
  font-family:'Orbitron',monospace; font-size:0.9rem;
  color:rgba(0,212,255,0.7); letter-spacing:0.3em;
  margin-bottom:16px; text-transform:uppercase;
}

/* Search */
.srow { display:flex; gap:8px; margin-bottom:20px; }
#sq {
  flex:1; background:rgba(0,212,255,0.05);
  border:1px solid rgba(0,212,255,0.25); border-radius:4px;
  color:#00d4ff; font-family:'Share Tech Mono',monospace;
  font-size:0.88rem; padding:8px 12px; outline:none;
}
#sq:focus { border-color:#00d4ff; box-shadow:0 0 12px rgba(0,212,255,0.15); }
#sq::placeholder { color:rgba(0,212,255,0.3); }
#sbtn {
  background:rgba(0,212,255,0.08); border:1px solid rgba(0,212,255,0.3);
  color:#00d4ff; font-family:'Orbitron',monospace; font-size:0.6rem;
  letter-spacing:0.1em; padding:8px 16px; border-radius:4px;
  cursor:pointer; transition:all 0.2s; white-space:nowrap;
}
#sbtn:hover { background:rgba(0,212,255,0.15); box-shadow:0 0 10px rgba(0,212,255,0.2); }

/* Now playing */
#now-playing {
  display:none;
  background: rgba(0,212,255,0.04);
  border: 1px solid rgba(0,212,255,0.18);
  border-radius:6px; padding:14px; margin-bottom:16px;
}
#np-inner { display:flex; align-items:center; gap:14px; }
#np-art {
  width:60px; height:60px; border-radius:4px;
  object-fit:cover; flex-shrink:0;
  border:1px solid rgba(0,212,255,0.2);
  box-shadow: 0 0 16px rgba(0,212,255,0.15);
}
#np-info { flex:1; min-width:0; }
#np-title { font-family:'Orbitron',monospace; font-size:0.75rem; color:#00d4ff; letter-spacing:0.1em; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
#np-artist { font-family:'Share Tech Mono',monospace; font-size:0.72rem; color:rgba(0,212,255,0.55); margin-top:2px; }
#np-album  { font-size:0.68rem; color:rgba(0,212,255,0.35); margin-top:2px; font-style:italic; }

/* Progress */
#prog-wrap { margin-top:10px; }
#prog-bar { width:100%; height:3px; background:rgba(0,212,255,0.1); border-radius:2px; cursor:pointer; position:relative; }
#prog-fill { height:100%; background:linear-gradient(90deg,#00aadd,#00d4ff); border-radius:2px; width:0%; transition:width 0.5s linear; }
#prog-dot { position:absolute; top:-3px; width:9px; height:9px; border-radius:50%; background:#00d4ff; box-shadow:0 0 8px #00d4ff; left:0%; transform:translateX(-50%); }
#times { display:flex; justify-content:space-between; font-family:'Share Tech Mono',monospace; font-size:0.65rem; color:rgba(0,212,255,0.4); margin-top:4px; }

/* Controls */
#ctrl { display:flex; align-items:center; justify-content:center; gap:16px; margin-top:12px; }
.ctrl-btn {
  background:transparent; border:1px solid rgba(0,212,255,0.2);
  color:rgba(0,212,255,0.7); border-radius:50%;
  width:36px; height:36px; display:flex; align-items:center; justify-content:center;
  cursor:pointer; transition:all 0.2s; font-size:0.9rem;
}
.ctrl-btn:hover { background:rgba(0,212,255,0.1); border-color:#00d4ff; color:#00d4ff; box-shadow:0 0 10px rgba(0,212,255,0.2); }
#playbtn { width:44px; height:44px; font-size:1rem; border-width:2px; }
#playbtn.playing { background:rgba(0,212,255,0.12); border-color:#00d4ff; color:#00d4ff; box-shadow:0 0 15px rgba(0,212,255,0.3); }

/* Volume */
#vol-row { display:flex; align-items:center; gap:8px; margin-top:10px; }
#vol-label { font-family:'Orbitron',monospace; font-size:0.52rem; color:rgba(0,212,255,0.4); letter-spacing:0.15em; }
#vol { -webkit-appearance:none; appearance:none; flex:1; height:3px; background:rgba(0,212,255,0.15); border-radius:2px; cursor:pointer; }
#vol::-webkit-slider-thumb { -webkit-appearance:none; width:12px; height:12px; border-radius:50%; background:#00d4ff; box-shadow:0 0 6px #00d4ff; }

/* Track list */
#tracklist { display:none; }
.track {
  display:flex; align-items:center; gap:10px;
  padding:8px 10px; border-radius:4px; cursor:pointer;
  transition:background 0.15s; border-bottom:1px solid rgba(0,212,255,0.06);
}
.track:hover { background:rgba(0,212,255,0.07); }
.track.active { background:rgba(0,212,255,0.1); }
.track-num { font-family:'Share Tech Mono',monospace; font-size:0.65rem; color:rgba(0,212,255,0.3); width:20px; flex-shrink:0; }
.t-art { width:36px; height:36px; border-radius:3px; object-fit:cover; flex-shrink:0; }
.t-info { flex:1; min-width:0; }
.t-title { font-family:'Rajdhani',sans-serif; font-size:0.85rem; color:rgba(0,212,255,0.85); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.t-artist { font-family:'Share Tech Mono',monospace; font-size:0.68rem; color:rgba(0,212,255,0.45); }
.t-dur { font-family:'Share Tech Mono',monospace; font-size:0.65rem; color:rgba(0,212,255,0.35); flex-shrink:0; }

/* Waveform viz */
#wave2 { display:flex; align-items:flex-end; justify-content:center; gap:2px; height:30px; margin:10px 0 0; }
.w2b { width:3px; border-radius:2px 2px 0 0; background:rgba(0,212,255,0.15); transition:height 0.1s; }

#status-msg { font-family:'Share Tech Mono',monospace; font-size:0.72rem; color:rgba(0,212,255,0.5); text-align:center; padding:8px 0; }

/* Presets */
#presets { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:16px; }
.preset {
  background:rgba(0,212,255,0.05); border:1px solid rgba(0,212,255,0.18);
  color:rgba(0,212,255,0.65); font-family:'Share Tech Mono',monospace;
  font-size:0.68rem; padding:4px 10px; border-radius:12px;
  cursor:pointer; transition:all 0.15s;
}
.preset:hover { background:rgba(0,212,255,0.12); border-color:rgba(0,212,255,0.4); color:#00d4ff; }
</style>

<div id="mp">
  <h2>&#127925; JARVIS MUSIC STATION</h2>

  <!-- Preset genres -->
  <div id="presets">
    <span class="preset" onclick="searchMusic('top hits 2024')">&#128293; Top Hits</span>
    <span class="preset" onclick="searchMusic('electronic ambient')">&#9889; Electronic</span>
    <span class="preset" onclick="searchMusic('jazz instrumental')">&#127928; Jazz</span>
    <span class="preset" onclick="searchMusic('lo-fi hip hop beats')">&#128247; Lo-Fi</span>
    <span class="preset" onclick="searchMusic('classical piano')">&#127929; Classical</span>
    <span class="preset" onclick="searchMusic('rock anthems')">&#127928; Rock</span>
    <span class="preset" onclick="searchMusic('bollywood hits')">&#127989; Bollywood</span>
    <span class="preset" onclick="searchMusic('pop 2024')">&#11088; Pop</span>
  </div>

  <!-- Search -->
  <div class="srow">
    <input id="sq" type="text" placeholder="Search artist, song, album..." />
    <button id="sbtn" onclick="searchMusic()">&#128269; SEARCH</button>
  </div>

  <!-- Now Playing -->
  <div id="now-playing">
    <div id="np-inner">
      <img id="np-art" src="" alt="Art" />
      <div id="np-info">
        <div id="np-title">—</div>
        <div id="np-artist">—</div>
        <div id="np-album">—</div>
      </div>
    </div>
    <div id="prog-wrap">
      <div id="prog-bar" onclick="seek(event)">
        <div id="prog-fill"></div>
        <div id="prog-dot"></div>
      </div>
      <div id="times"><span id="t-cur">0:00</span><span id="t-dur">0:00</span></div>
    </div>
    <div id="vol-row">
      <span id="vol-label">VOL</span>
      <input id="vol" type="range" min="0" max="1" step="0.02" value="0.8" oninput="setVol(this.value)" />
    </div>
    <div id="ctrl">
      <button class="ctrl-btn" onclick="prevTrack()" title="Previous">&#9664;&#9664;</button>
      <button class="ctrl-btn" id="playbtn" onclick="togglePlay()" title="Play/Pause">&#9654;</button>
      <button class="ctrl-btn" onclick="nextTrack()" title="Next">&#9654;&#9654;</button>
    </div>
    <div id="wave2">
      <div class="w2b" style="height:4px"></div><div class="w2b" style="height:6px"></div>
      <div class="w2b" style="height:4px"></div><div class="w2b" style="height:8px"></div>
      <div class="w2b" style="height:5px"></div><div class="w2b" style="height:4px"></div>
      <div class="w2b" style="height:10px"></div><div class="w2b" style="height:6px"></div>
      <div class="w2b" style="height:4px"></div><div class="w2b" style="height:7px"></div>
      <div class="w2b" style="height:12px"></div><div class="w2b" style="height:5px"></div>
      <div class="w2b" style="height:4px"></div><div class="w2b" style="height:9px"></div>
      <div class="w2b" style="height:6px"></div><div class="w2b" style="height:4px"></div>
      <div class="w2b" style="height:8px"></div><div class="w2b" style="height:5px"></div>
      <div class="w2b" style="height:4px"></div><div class="w2b" style="height:6px"></div>
    </div>
  </div>

  <!-- Track list -->
  <div id="status-msg">Search for music or pick a genre above</div>
  <div id="tracklist"></div>
</div>

<script>
(function() {
  let tracks      = [];
  let currentIdx  = -1;
  let audio       = null;
  let progTimer   = null;
  let waveTimer   = null;
  const w2bars    = Array.from(document.querySelectorAll('.w2b'));

  const sq      = document.getElementById('sq');
  const status  = document.getElementById('status-msg');
  const np      = document.getElementById('now-playing');
  const tlist   = document.getElementById('tracklist');
  const playbtn = document.getElementById('playbtn');

  sq.addEventListener('keydown', e => { if(e.key==='Enter') searchMusic(); });

  window.searchMusic = function(q) {
    const query = q || sq.value.trim();
    if (!query) return;
    sq.value = query;
    status.textContent = 'Scanning Deezer database...';
    tlist.innerHTML = '';
    tlist.style.display = 'none';
    np.style.display = 'none';

    fetch(`https://api.deezer.com/search?q=${encodeURIComponent(query)}&limit=20&output=jsonp`)
      .then(() => {}) // JSONP only
      .catch(() => {});

    // Use JSONP callback approach for Deezer (no CORS on direct fetch)
    const cb = 'dz_cb_' + Date.now();
    window[cb] = function(data) {
      delete window[cb];
      document.head.removeChild(script);
      if (!data.data || data.data.length === 0) {
        status.textContent = 'No results found. Try another search.';
        return;
      }
      tracks = data.data.filter(t => t.preview); // only tracks with preview
      if (tracks.length === 0) {
        status.textContent = 'No preview available for these tracks. Try another search.';
        return;
      }
      renderTracks();
      status.textContent = '';
    };
    const script = document.createElement('script');
    script.src = `https://api.deezer.com/search?q=${encodeURIComponent(query)}&limit=20&output=jsonp&callback=${cb}`;
    script.onerror = () => {
      status.textContent = 'Search failed. Check connection.';
      delete window[cb];
    };
    document.head.appendChild(script);
  };

  function renderTracks() {
    tlist.innerHTML = '';
    tlist.style.display = 'block';
    tracks.forEach((t, i) => {
      const div = document.createElement('div');
      div.className = 'track' + (i === currentIdx ? ' active' : '');
      div.innerHTML = `
        <span class="track-num">${i+1}</span>
        <img class="t-art" src="${t.album.cover_small}" loading="lazy" />
        <div class="t-info">
          <div class="t-title">${t.title}</div>
          <div class="t-artist">${t.artist.name}</div>
        </div>
        <span class="t-dur">${fmtTime(t.duration)}</span>`;
      div.onclick = () => playTrack(i);
      tlist.appendChild(div);
    });
  }

  function playTrack(idx) {
    if (idx < 0 || idx >= tracks.length) return;
    currentIdx = idx;
    const t = tracks[idx];

    if (audio) { audio.pause(); clearInterval(progTimer); }
    audio = new Audio(t.preview);
    audio.volume = parseFloat(document.getElementById('vol').value);
    audio.crossOrigin = 'anonymous';

    audio.oncanplay = () => {
      audio.play().catch(()=>{});
      playbtn.textContent = '⏸';
      playbtn.classList.add('playing');
      startProg();
      startWave2();
    };
    audio.onended = () => {
      playbtn.textContent = '▶';
      playbtn.classList.remove('playing');
      stopWave2();
      nextTrack();
    };
    audio.onerror = () => {
      status.textContent = 'Preview unavailable. Skipping...';
      setTimeout(() => nextTrack(), 1200);
    };

    // Update now playing
    np.style.display = 'block';
    document.getElementById('np-art').src = t.album.cover_medium || t.album.cover_small;
    document.getElementById('np-title').textContent  = t.title;
    document.getElementById('np-artist').textContent = t.artist.name;
    document.getElementById('np-album').textContent  = t.album.title;
    document.getElementById('t-dur').textContent     = fmtTime(t.duration > 30 ? 30 : t.duration);

    // Highlight active
    document.querySelectorAll('.track').forEach((el,i) => {
      el.classList.toggle('active', i === idx);
    });
  }

  window.togglePlay = function() {
    if (!audio) return;
    if (audio.paused) {
      audio.play();
      playbtn.textContent = '⏸';
      playbtn.classList.add('playing');
      startWave2();
    } else {
      audio.pause();
      playbtn.textContent = '▶';
      playbtn.classList.remove('playing');
      stopWave2();
    }
  };

  window.nextTrack = function() {
    if (tracks.length === 0) return;
    playTrack((currentIdx + 1) % tracks.length);
  };
  window.prevTrack = function() {
    if (tracks.length === 0) return;
    playTrack((currentIdx - 1 + tracks.length) % tracks.length);
  };

  window.setVol = function(v) { if (audio) audio.volume = parseFloat(v); };

  window.seek = function(e) {
    if (!audio) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const pct  = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    audio.currentTime = pct * audio.duration;
  };

  function startProg() {
    clearInterval(progTimer);
    progTimer = setInterval(() => {
      if (!audio || audio.paused) return;
      const pct = (audio.currentTime / (audio.duration || 1)) * 100;
      document.getElementById('prog-fill').style.width = pct + '%';
      document.getElementById('prog-dot').style.left   = pct + '%';
      document.getElementById('t-cur').textContent = fmtTime(audio.currentTime);
    }, 500);
  }

  function startWave2() {
    clearInterval(waveTimer); let t = 0;
    waveTimer = setInterval(() => {
      t += 0.2;
      w2bars.forEach((b,i) => {
        const h = 3 + Math.abs(Math.sin(t + i*0.45)) * 24;
        b.style.height     = h + 'px';
        b.style.background = `rgba(0,${Math.round(180+Math.sin(t+i)*50)},255,0.6)`;
      });
    }, 80);
  }
  function stopWave2() {
    clearInterval(waveTimer);
    w2bars.forEach((b,i) => { b.style.height=(4+Math.sin(i*0.6)*3)+'px'; b.style.background='rgba(0,212,255,0.15)'; });
  }

  function fmtTime(s) {
    const m = Math.floor(s/60), sec = Math.floor(s%60);
    return m + ':' + String(sec).padStart(2,'0');
  }

  // Auto-load on open
  searchMusic('top global hits 2024');
})();
</script>
"""
    components.html(music_html, height=780)
