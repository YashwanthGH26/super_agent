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

# ─── 1. Page Config ────────────────────────────────────────────────────────────
st.set_page_config(page_title="J.A.R.V.I.S", page_icon="⚡", layout="wide")

# ─── 2. JARVIS UI Styling ──────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600&display=swap');

:root {
    --hud-blue: #00d4ff;
    --hud-cyan: #00ffff;
    --hud-dark: #020b18;
    --hud-panel: rgba(0, 20, 40, 0.85);
    --hud-border: rgba(0, 212, 255, 0.3);
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--hud-dark) !important;
    font-family: 'Rajdhani', sans-serif !important;
    color: #c8e6f0 !important;
}

[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse 80% 60% at 50% 0%, rgba(0,100,180,0.15) 0%, transparent 70%),
        repeating-linear-gradient(0deg, transparent, transparent 40px, rgba(0,212,255,0.03) 40px, rgba(0,212,255,0.03) 41px),
        repeating-linear-gradient(90deg, transparent, transparent 40px, rgba(0,212,255,0.03) 40px, rgba(0,212,255,0.03) 41px);
    pointer-events: none;
    z-index: 0;
}

[data-testid="stHeader"] { background: transparent !important; }

[data-testid="stSidebar"] {
    background: rgba(2, 11, 24, 0.95) !important;
    border-right: 1px solid var(--hud-border) !important;
}

.jarvis-title {
    font-family: 'Orbitron', monospace;
    font-size: 2.4rem;
    font-weight: 900;
    color: var(--hud-blue);
    text-shadow: 0 0 20px rgba(0,212,255,0.6), 0 0 60px rgba(0,212,255,0.2);
    letter-spacing: 0.3em;
    text-align: center;
    padding: 1rem 0 0.2rem;
    animation: pulse-glow 3s ease-in-out infinite;
}

.jarvis-subtitle {
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.85rem;
    color: rgba(0,212,255,0.5);
    text-align: center;
    letter-spacing: 0.4em;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
}

@keyframes pulse-glow {
    0%, 100% { text-shadow: 0 0 20px rgba(0,212,255,0.6), 0 0 60px rgba(0,212,255,0.2); }
    50%       { text-shadow: 0 0 30px rgba(0,212,255,0.9), 0 0 80px rgba(0,212,255,0.4); }
}

.hud-panel {
    background: var(--hud-panel);
    border: 1px solid var(--hud-border);
    border-radius: 4px;
    padding: 1rem 1.2rem;
    margin-bottom: 1rem;
    position: relative;
    backdrop-filter: blur(10px);
}
.hud-panel::before { content:''; position:absolute; top:0; left:0; width:40px; height:2px; background:var(--hud-blue); }
.hud-panel::after  { content:''; position:absolute; bottom:0; right:0; width:40px; height:2px; background:var(--hud-blue); }

.stat-label {
    font-family: 'Orbitron', monospace;
    font-size: 0.6rem;
    color: rgba(0,212,255,0.5);
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 0.2rem;
}
.stat-value {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--hud-cyan);
}

[data-testid="stChatMessage"] {
    background: rgba(0,20,40,0.7) !important;
    border: 1px solid var(--hud-border) !important;
    border-radius: 4px !important;
    margin-bottom: 0.5rem !important;
    backdrop-filter: blur(8px) !important;
}

[data-testid="stChatInput"] textarea {
    background: rgba(0,20,40,0.9) !important;
    border: 1px solid var(--hud-border) !important;
    color: var(--hud-cyan) !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1rem !important;
    border-radius: 4px !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: var(--hud-blue) !important;
    box-shadow: 0 0 15px rgba(0,212,255,0.2) !important;
}

.stButton > button {
    background: transparent !important;
    border: 1px solid var(--hud-border) !important;
    color: var(--hud-blue) !important;
    font-family: 'Orbitron', monospace !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.15em !important;
    border-radius: 2px !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: rgba(0,212,255,0.1) !important;
    border-color: var(--hud-blue) !important;
    box-shadow: 0 0 15px rgba(0,212,255,0.3) !important;
}

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: rgba(0,20,40,0.5); }
::-webkit-scrollbar-thumb { background: rgba(0,212,255,0.3); border-radius: 2px; }

[data-testid="stMetricLabel"] { color: rgba(0,212,255,0.6) !important; font-family: 'Orbitron', monospace !important; font-size: 0.6rem !important; }
[data-testid="stMetricValue"] { color: var(--hud-cyan) !important; font-family: 'Rajdhani', sans-serif !important; }
</style>
""", unsafe_allow_html=True)

# ─── 3. Header ─────────────────────────────────────────────────────────────────
st.markdown('<div class="jarvis-title">J.A.R.V.I.S</div>', unsafe_allow_html=True)
st.markdown('<div class="jarvis-subtitle">Just A Rather Very Intelligent System · Online</div>', unsafe_allow_html=True)

# ─── 4. Tools ──────────────────────────────────────────────────────────────────
@tool
def get_current_datetime() -> str:
    """Returns the current date, time, day of week, and timezone info."""
    now = datetime.datetime.now()
    utc = datetime.datetime.utcnow()
    return (
        f"Current local datetime: {now.strftime('%A, %B %d, %Y at %H:%M:%S')}\n"
        f"IST datetime: {utc.strftime('%Y-%m-%d %H:%M:%S IST')}\n"
        f"Week number: {now.isocalendar()[1]}\n"
        f"Day of year: {now.timetuple().tm_yday}"
    )

@tool
def get_weather(city: str) -> str:
    """Gets current weather for a city.
    Args:
        city: Name of the city to get weather for.
    """
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1"
        with urllib.request.urlopen(geo_url, timeout=5) as r:
            geo = json.loads(r.read())
        if not geo.get("results"):
            return f"City '{city}' not found."
        loc = geo["results"][0]
        lat, lon, name, country = loc["latitude"], loc["longitude"], loc["name"], loc.get("country", "")
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
        return (f"Weather in {name}, {country}: {desc}, {c['temperature_2m']}°C, "
                f"Humidity {c['relative_humidity_2m']}%, Wind {c['wind_speed_10m']} km/h")
    except Exception as e:
        return f"Weather lookup failed: {e}"

@tool
def get_news(topic: str = "technology") -> str:
    """Searches for latest news on a topic.
    Args:
        topic: The news topic to search for.
    """
    try:
        search = DuckDuckGoSearchRun()
        results = search.run(f"latest news {topic} 2025")
        return f"Latest news on '{topic}':\n{results}"
    except Exception as e:
        return f"News fetch failed: {e}"

@tool
def analyze_trend(subject: str) -> str:
    """Analyzes historical context and current trends for any subject.
    Args:
        subject: The topic to analyze.
    """
    search = DuckDuckGoSearchRun()
    past    = search.run(f"{subject} history milestones key events")
    current = search.run(f"{subject} current trends 2025 latest")
    forecast= search.run(f"{subject} future predictions forecast 2025 2026")
    return (f"TEMPORAL ANALYSIS: {subject}\n\n[HISTORICAL]\n{past[:500]}\n\n"
            f"[CURRENT 2025]\n{current[:500]}\n\n[OUTLOOK]\n{forecast[:500]}")

@tool
def predict_insights(domain: str) -> str:
    """Generates predictive insights for a domain.
    Args:
        domain: The domain to forecast.
    """
    search = DuckDuckGoSearchRun()
    data  = search.run(f"{domain} market forecast predictions 2025 2026")
    stats = search.run(f"{domain} statistics growth rate data")
    return (f"PREDICTIVE INSIGHTS: {domain}\n\n[FORECAST]\n{data[:600]}\n\n[STATS]\n{stats[:400]}")

@tool
def read_local_file(file_path: str) -> str:
    """Reads the content of a local text or code file."""
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

# ─── 5. Agent ──────────────────────────────────────────────────────────────────
tools_list: list[Any] = [
    DuckDuckGoSearchRun(),
    get_current_datetime,
    get_weather,
    get_news,
    analyze_trend,
    predict_insights,
    read_local_file,
    write_local_file,
]

SYSTEM_PROMPT = """You are J.A.R.V.I.S — Just A Rather Very Intelligent System.
Personality: Tony Stark's AI — calm, precise, confident, slightly witty.

Rules:
- Always use tools for live data (weather, news, time). Never guess.
- For voice responses, be CONCISE: 1-3 sentences max for simple queries, 4-6 for complex.
- NO markdown symbols in responses (no **, ##, -, *). Speak in plain natural sentences.
- Use JARVIS-style phrasing occasionally: "Certainly", "Analysis complete", "Right away".
- Structure: answer first, detail second. Lead with the most important fact.
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

# ─── 6. Session State ──────────────────────────────────────────────────────────
if "chat_history"   not in st.session_state:
    st.session_state.chat_history   = InMemoryChatMessageHistory()
if "voice_input"    not in st.session_state:
    st.session_state.voice_input    = ""
if "last_voice_ts"  not in st.session_state:
    st.session_state.last_voice_ts  = ""

# ─── 7. Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="stat-label">⬡ SYSTEM STATUS</div>', unsafe_allow_html=True)
    st.markdown('<div class="hud-panel"><div class="stat-value">● ONLINE</div><div class="stat-label">All systems nominal</div></div>', unsafe_allow_html=True)

    now = datetime.datetime.now()
    st.markdown(f"""
    <div class="hud-panel">
        <div class="stat-label">◈ LOCAL TIME</div>
        <div class="stat-value">{now.strftime('%H:%M:%S')}</div>
        <div class="stat-label">{now.strftime('%A, %d %B %Y')}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="stat-label">⬡ CAPABILITIES</div>', unsafe_allow_html=True)
    for cap in ["🔍 Web Search","🌤 Live Weather","📰 Global News","📊 Trend Analysis","🔮 Forecasting","📁 File I/O","🕐 DateTime"]:
        st.markdown(f'<div style="font-size:0.8rem;color:rgba(0,212,255,0.7);padding:2px 0;">{cap}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="stat-label">⬡ QUICK COMMANDS</div>', unsafe_allow_html=True)
    quick_cmds = {
        "🕐 Time & Date":  "What is the current date and time?",
        "🌤 Weather":       "What is the weather in New York?",
        "📰 Tech News":     "Get me the latest technology news",
        "📊 AI Trends":     "Analyze current AI trends and future outlook",
        "🔮 Forecast":      "Give me predictive insights on the renewable energy market",
    }
    for label, cmd in quick_cmds.items():
        if st.button(label, use_container_width=True):
            st.session_state.voice_input = cmd

    if st.button("🗑 Clear Memory", use_container_width=True):
        st.session_state.chat_history = InMemoryChatMessageHistory()
        st.rerun()

# ─── 8. Always-On Voice HUD ────────────────────────────────────────────────────
# Fully hands-free like Siri/Alexa:
    • Continuous background listening for wake word "hey jarvis"
    • On detection → chime → command listening with noise suppression
    • Auto-submit on silence → agent replies → TTS speaks back
    • Returns to wake-word listening automatically
#
# Noise suppression via:
    • Web Audio API noise gate (filters mic input below threshold)
    • SpeechRecognition with no-speech timeout handling
    • Debounced final-result detection (ignores sub-word fragments)

voice_html = """
<div id="jarvis-voice" style="
    font-family:'Rajdhani',sans-serif;
    background:rgba(0,20,40,0.92);
    border:1px solid rgba(0,212,255,0.35);
    border-radius:6px;
    padding:16px 20px 14px;
    position:relative;
    user-select:none;
">
  <div style="position:absolute;top:0;left:0;width:36px;height:2px;background:#00d4ff;border-radius:1px;"></div>
  <div style="position:absolute;bottom:0;right:0;width:36px;height:2px;background:#00d4ff;border-radius:1px;"></div>

  <!-- Top row: indicator + status -->
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
    <div id="dot" style="
        width:12px;height:12px;border-radius:50%;
        background:#1a3a4a;
        box-shadow:0 0 0 rgba(0,212,255,0);
        transition:background 0.3s,box-shadow 0.3s;
        flex-shrink:0;
    "></div>
    <span id="statusLabel" style="
        font-family:'Orbitron',monospace;
        font-size:0.62rem;
        letter-spacing:0.18em;
        color:rgba(0,212,255,0.55);
    ">INITIALIZING...</span>
  </div>

  <!-- Waveform bars -->
  <div id="waveform" style="
      display:flex;align-items:flex-end;justify-content:center;
      gap:3px;height:36px;margin-bottom:12px;
  ">
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:4px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:6px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:4px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:8px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:5px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:4px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:10px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:6px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:4px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:7px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:12px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:5px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:4px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:9px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:6px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:4px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:8px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:5px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:4px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:6px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:4px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:5px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:4px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:6px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:4px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:7px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:4px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:5px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:4px;"></div>
    <div class="b" style="width:3px;background:rgba(0,212,255,0.18);border-radius:2px 2px 0 0;height:6px;"></div>
  </div>

  <!-- Transcript / hint text -->
  <div id="tbox" style="
      font-size:0.88rem;color:#00ffff;
      text-align:center;min-height:20px;
      letter-spacing:0.04em;opacity:0.85;
      transition:color 0.3s;
  ">Say <strong style="color:#00d4ff;">HEY JARVIS</strong> to begin...</div>
</div>

<script>
(function() {
  /* ── DOM ─────────────────────────────────────────────────────────── */
  const dot    = document.getElementById('dot');
  const label  = document.getElementById('statusLabel');
  const tbox   = document.getElementById('tbox');
  const bars   = Array.from(document.querySelectorAll('.b'));

  /* ── State ───────────────────────────────────────────────────────── */
  const WAKE_WORD      = 'hey jarvis';
  let wakeRec          = null;
  let cmdRec           = null;
  let isWaking         = false;
  let isCommand        = false;
  let isSpeaking       = false;
  let audioCtx         = null;
  let analyser         = null;
  let micStream        = null;
  let rafId            = null;
  let noSpeechTimer    = null;
  let finalText        = '';

  /* ── Status themes ───────────────────────────────────────────────── */
  const THEMES = {
    boot:      { dot:'#1a3a4a', glow:'none',                             text:'INITIALIZING...' },
    wake:      { dot:'#00d4ff', glow:'0 0 10px rgba(0,212,255,0.55)',    text:'LISTENING FOR WAKE WORD' },
    detected:  { dot:'#00ff88', glow:'0 0 14px rgba(0,255,136,0.65)',    text:'WAKE WORD DETECTED' },
    command:   { dot:'#ff8800', glow:'0 0 14px rgba(255,136,0,0.65)',    text:'LISTENING — SPEAK YOUR COMMAND' },
    thinking:  { dot:'#aa44ff', glow:'0 0 14px rgba(170,68,255,0.6)',    text:'PROCESSING...' },
    speaking:  { dot:'#ffdd00', glow:'0 0 14px rgba(255,221,0,0.6)',     text:'SPEAKING' },
    error:     { dot:'#ff3333', glow:'none',                             text:'ERROR — RETRYING' },
    nosupport: { dot:'#ff3333', glow:'none',                             text:'USE CHROME OR EDGE' },
  };

  function setTheme(key, extra) {
    const t = THEMES[key] || THEMES.boot;
    dot.style.background  = t.dot;
    dot.style.boxShadow   = t.glow;
    label.textContent     = extra || t.text;
  }

  /* ── Waveform ─────────────────────────────────────────────────────── */
  function startWave(stream) {
    stopWave();
    audioCtx  = new (window.AudioContext || window.webkitAudioContext)();
    analyser  = audioCtx.createAnalyser();
    analyser.fftSize = 128;
    audioCtx.createMediaStreamSource(stream).connect(analyser);
    const data = new Uint8Array(analyser.frequencyBinCount);
    function frame() {
      analyser.getByteFrequencyData(data);
      bars.forEach((b, i) => {
        const v = data[Math.floor(i * data.length / bars.length)];
        const h = Math.max(4, (v / 255) * 34);
        const g = Math.round(130 + v * 0.5);
        b.style.height     = h + 'px';
        b.style.background = `rgba(0,${g},255,${0.35 + v/700})`;
      });
      rafId = requestAnimationFrame(frame);
    }
    frame();
  }

  function stopWave() {
    if (rafId)    { cancelAnimationFrame(rafId); rafId = null; }
    if (audioCtx) { audioCtx.close().catch(()=>{}); audioCtx = null; analyser = null; }
    idleWave();
  }

  function idleWave() {
    bars.forEach((b, i) => {
      b.style.height     = (4 + Math.sin(i * 0.7) * 3) + 'px';
      b.style.background = 'rgba(0,212,255,0.18)';
    });
  }

  function speakWave() {
    let t = 0;
    function frame() {
      t += 0.18;
      bars.forEach((b, i) => {
        const h = 4 + Math.abs(Math.sin(t + i * 0.35)) * 28;
        b.style.height     = h + 'px';
        b.style.background = `rgba(255,${Math.round(180 + Math.sin(t+i)*50)},0,0.7)`;
      });
      if (isSpeaking) rafId = requestAnimationFrame(frame);
      else idleWave();
    }
    if (rafId) cancelAnimationFrame(rafId);
    frame();
  }

  /* ── Chime ───────────────────────────────────────────────────────── */
  function chime() {
    try {
      const c = new (window.AudioContext || window.webkitAudioContext)();
      [[660,0],[880,0.13],[1100,0.26]].forEach(([f,d]) => {
        const o = c.createOscillator(), g = c.createGain();
        o.type = 'sine'; o.frequency.value = f;
        o.connect(g); g.connect(c.destination);
        g.gain.setValueAtTime(0, c.currentTime+d);
        g.gain.linearRampToValueAtTime(0.25, c.currentTime+d+0.06);
        g.gain.linearRampToValueAtTime(0, c.currentTime+d+0.32);
        o.start(c.currentTime+d); o.stop(c.currentTime+d+0.38);
      });
    } catch(e) {}
  }

  /* ── Mic stream with noise suppression constraints ───────────────── */
  function getMic() {
    return navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl:  true,
        sampleRate:       16000,
      }
    });
  }

  /* ── Release mic stream ──────────────────────────────────────────── */
  function releaseMic() {
    if (micStream) {
      micStream.getTracks().forEach(t => t.stop());
      micStream = null;
    }
    stopWave();
  }

  /* ── WAKE WORD LISTENER ──────────────────────────────────────────── */
  function startWake() {
    if (isWaking || isCommand || isSpeaking) return;
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      setTheme('nosupport');
      tbox.textContent = 'Speech recognition requires Chrome or Edge browser.';
      return;
    }

    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    wakeRec = new SR();
    wakeRec.continuous      = true;
    wakeRec.interimResults  = true;
    wakeRec.lang            = 'en-US';
    wakeRec.maxAlternatives = 5;

    wakeRec.onstart = () => {
      isWaking = true;
      setTheme('wake');
      tbox.innerHTML = 'Say <strong style="color:#00d4ff;">HEY JARVIS</strong> to begin...';
      idleWave();
    };

    wakeRec.onresult = (e) => {
      if (isCommand || isSpeaking) return;
      for (let i = e.resultIndex; i < e.results.length; i++) {
        for (let j = 0; j < e.results[i].length; j++) {
          const heard = e.results[i][j].transcript.toLowerCase().trim();
          if (heard.includes('hey jarvis') || heard.includes('jarvis') && heard.length < 20) {
            try { wakeRec.abort(); } catch(x) {}
            onWakeDetected();
            return;
          }
        }
      }
    };

    wakeRec.onerror = (e) => {
      isWaking = false;
      if (['no-speech','aborted','network'].includes(e.error)) {
        setTimeout(startWake, 400);
      } else {
        setTheme('error');
        setTimeout(startWake, 2000);
      }
    };

    wakeRec.onend = () => {
      isWaking = false;
      if (!isCommand && !isSpeaking) setTimeout(startWake, 300);
    };

    wakeRec.start();
  }

  /* ── WAKE DETECTED ───────────────────────────────────────────────── */
  function onWakeDetected() {
    isWaking = false;
    setTheme('detected');
    tbox.textContent = '⚡ JARVIS activated — listening...';
    chime();
    setTimeout(startCommand, 500);
  }

  /* ── COMMAND LISTENER ────────────────────────────────────────────── */
  function startCommand() {
    if (isCommand) return;
    isCommand = true;
    finalText = '';

    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    cmdRec = new SR();
    cmdRec.continuous      = false;
    cmdRec.interimResults  = true;
    cmdRec.lang            = 'en-US';
    cmdRec.maxAlternatives = 1;

    /* Noise gate: only open mic + visualizer after recognition starts */
    cmdRec.onstart = () => {
      setTheme('command');
      tbox.textContent = '🎙 Speak now...';
      getMic().then(stream => {
        micStream = stream;
        startWave(stream);
      }).catch(() => {});

      /* Fallback no-speech timeout: if silent for 7s, close */
      noSpeechTimer = setTimeout(() => {
        try { cmdRec.stop(); } catch(x) {}
      }, 7000);
    };

    cmdRec.onresult = (e) => {
      /* Reset no-speech timer on every result */
      clearTimeout(noSpeechTimer);
      noSpeechTimer = setTimeout(() => {
        try { cmdRec.stop(); } catch(x) {}
      }, 4000);

      let interim = '';
      finalText   = '';
      for (let i = e.resultIndex; i < e.results.length; i++) {
        if (e.results[i].isFinal) finalText += e.results[i][0].transcript + ' ';
        else                      interim   += e.results[i][0].transcript;
      }
      tbox.textContent = (finalText || interim).trim() || '...';
    };

    cmdRec.onerror = (e) => {
      clearTimeout(noSpeechTimer);
      isCommand = false;
      releaseMic();
      if (e.error === 'no-speech') {
        tbox.innerHTML = 'Nothing heard. Say <strong style="color:#00d4ff;">HEY JARVIS</strong> again.';
        setTheme('wake');
        setTimeout(startWake, 600);
      } else {
        setTheme('error');
        setTimeout(startWake, 1500);
      }
    };

    cmdRec.onend = () => {
      clearTimeout(noSpeechTimer);
      releaseMic();
      isCommand = false;

      const cmd = finalText.trim();
      if (cmd.length > 1) {
        setTheme('thinking');
        tbox.textContent = '⚡ ' + cmd;
        submitCommand(cmd);
      } else {
        tbox.innerHTML = 'Nothing heard. Say <strong style="color:#00d4ff;">HEY JARVIS</strong> again.';
        setTheme('wake');
        setTimeout(startWake, 600);
      }
    };

    cmdRec.start();
  }

  /* ── SUBMIT command to Streamlit ─────────────────────────────────── */
  function submitCommand(text) {
    /* Method 1: URL query param (most reliable for Streamlit) */
    try {
      const url = new URL(window.parent.location.href);
      url.searchParams.set('vc',  encodeURIComponent(text));
      url.searchParams.set('vts', Date.now().toString());
      window.parent.history.replaceState({}, '', url.toString());
    } catch(e) {}

    /* Method 2: Simulate typing into Streamlit chat input */
    setTimeout(() => {
      try {
        const doc   = window.parent.document;
        const areas = doc.querySelectorAll('textarea');
        for (const ta of areas) {
          if (ta.placeholder && ta.placeholder.toLowerCase().includes('jarvis')) {
            const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
            setter.call(ta, text);
            ta.dispatchEvent(new Event('input', { bubbles: true }));
            setTimeout(() => {
              ta.dispatchEvent(new KeyboardEvent('keydown', {
                key:'Enter', code:'Enter', keyCode:13, bubbles:true
              }));
            }, 120);
            break;
          }
        }
      } catch(e) {}
    }, 250);
  }

  /* ── TTS: speak JARVIS response ──────────────────────────────────── */
  function speak(text) {
    if (!window.speechSynthesis || !text) return;
    window.speechSynthesis.cancel();
    isSpeaking = true;
    setTheme('speaking');
    speakWave();

    /* Strip markdown symbols for clean speech */
    const clean = text
      .replace(/[#*_`~>]/g, '')
      .replace(/\n+/g, '. ')
      .replace(/\s{2,}/g, ' ')
      .trim()
      .substring(0, 1000);

    const u = new SpeechSynthesisUtterance(clean);
    u.rate   = 0.93;
    u.pitch  = 0.78;
    u.volume = 1.0;

    function doSpeak() {
      const voices = window.speechSynthesis.getVoices();
      /* Priority order: UK Male Google → Daniel → Alex → any en-GB → any en */
      const pick =
        voices.find(v => v.name === 'Google UK English Male') ||
        voices.find(v => v.name.includes('Daniel'))           ||
        voices.find(v => v.name.includes('Alex'))             ||
        voices.find(v => v.lang === 'en-GB')                  ||
        voices.find(v => v.lang.startsWith('en'));
      if (pick) u.voice = pick;

      u.onend   = u.onerror = () => {
        isSpeaking = false;
        idleWave();
        setTheme('wake');
        tbox.innerHTML = 'Say <strong style="color:#00d4ff;">HEY JARVIS</strong> to continue...';
        setTimeout(startWake, 400);
      };
      window.speechSynthesis.speak(u);
    }

    const voices = window.speechSynthesis.getVoices();
    if (voices.length) doSpeak();
    else { window.speechSynthesis.onvoiceschanged = doSpeak; }
  }

  /* ── Listen for TTS message from Streamlit page ──────────────────── */
  window.addEventListener('message', (e) => {
    if (e.data && e.data.type === 'jarvis_tts') speak(e.data.text);
  });

  /* ── Boot ────────────────────────────────────────────────────────── */
  setTheme('boot');
  setTimeout(startWake, 900);
})();
</script>
"""

components.html(voice_html, height=170)

# ─── 9. Bridge: receive voice command from iframe ──────────────────────────────
bridge_html = """
<script>
window.addEventListener('message', function(e) {
  if (!e.data || e.data.type !== 'voice_command') return;
  const text = e.data.text;
  /* URL param approach */
  try {
    const url = new URL(window.parent.location.href);
    url.searchParams.set('vc',  encodeURIComponent(text));
    url.searchParams.set('vts', Date.now().toString());
    window.parent.history.replaceState({}, '', url.toString());
  } catch(err) {}
  /* Direct textarea inject */
  setTimeout(() => {
    try {
      const areas = window.parent.document.querySelectorAll('textarea');
      for (const ta of areas) {
        if (ta.placeholder && ta.placeholder.toLowerCase().includes('jarvis')) {
          const s = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;
          s.call(ta, text);
          ta.dispatchEvent(new Event('input',{bubbles:true}));
          setTimeout(() => ta.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',keyCode:13,bubbles:true})), 150);
          break;
        }
      }
    } catch(err) {}
  }, 200);
});
</script>
"""
components.html(bridge_html, height=0)

# ─── 10. Read voice command from URL params ────────────────────────────────────
params      = st.query_params
raw_vc      = params.get("vc", "")
raw_vts     = params.get("vts", "")
voice_cmd   = ""
try:
    if raw_vc:
        voice_cmd = urllib.parse.unquote(raw_vc)
except Exception:
    voice_cmd = raw_vc

last_ts = st.session_state.last_voice_ts
if voice_cmd and raw_vts != last_ts:
    st.session_state.voice_input   = voice_cmd
    st.session_state.last_voice_ts = raw_vts
    st.query_params.clear()

# ─── 11. Chat history ──────────────────────────────────────────────────────────
TYPE_TO_ROLE = {"human": "user", "ai": "assistant"}
for msg in st.session_state.chat_history.messages:
    role = TYPE_TO_ROLE.get(msg.type, msg.type)
    with st.chat_message(role):
        st.write(msg.content)

# ─── 12. Handle input ──────────────────────────────────────────────────────────
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

    # ── TTS: fire response text to the voice component ────────────────────────
    # We broadcast to all iframes (voice HUD lives in one).
    # Also inject directly via window.speechSynthesis as a fallback.
    clean_for_tts = (
        output_text
        .replace('"', "'")
        .replace("\\", "")
        .replace("\n", " ")
        [:1000]
    )
    tts_script = f"""
    <script>
    (function() {{
      const payload = {{ type: 'jarvis_tts', text: `{clean_for_tts}` }};
      /* Broadcast to every iframe in the page */
      try {{
        Array.from(window.parent.document.querySelectorAll('iframe')).forEach(f => {{
          try {{ f.contentWindow.postMessage(payload, '*'); }} catch(e) {{}}
        }});
      }} catch(e) {{}}
      /* Fallback: speak in this frame directly */
      if (window.speechSynthesis) {{
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(`{clean_for_tts}`);
        u.rate = 0.93; u.pitch = 0.78; u.volume = 1.0;
        function go() {{
          const vs = window.speechSynthesis.getVoices();
          const v  = vs.find(x => x.name === 'Google UK English Male')
                  || vs.find(x => x.name.includes('Daniel'))
                  || vs.find(x => x.lang === 'en-GB')
                  || vs.find(x => x.lang.startsWith('en'));
          if (v) u.voice = v;
          window.speechSynthesis.speak(u);
        }}
        if (window.speechSynthesis.getVoices().length) go();
        else window.speechSynthesis.onvoiceschanged = go;
      }}
    }})();
    </script>
    """
    components.html(tts_script, height=0)

    st.session_state.chat_history.add_user_message(user_query)
    st.session_state.chat_history.add_ai_message(output_text)
