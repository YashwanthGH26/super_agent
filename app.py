import os
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

# ─── 2. JARVIS UI Styling ───────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600&display=swap');

:root {
    --hud-blue: #00d4ff;
    --hud-cyan: #00ffff;
    --hud-orange: #ff6b00;
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
    50% { text-shadow: 0 0 30px rgba(0,212,255,0.9), 0 0 80px rgba(0,212,255,0.4), 0 0 120px rgba(0,212,255,0.1); }
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

.hud-panel::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 40px; height: 2px;
    background: var(--hud-blue);
}

.hud-panel::after {
    content: '';
    position: absolute;
    bottom: 0; right: 0;
    width: 40px; height: 2px;
    background: var(--hud-blue);
}

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

[data-testid="stMetric"] {
    background: rgba(0,20,40,0.6) !important;
    border: 1px solid var(--hud-border) !important;
    border-radius: 4px !important;
    padding: 0.5rem !important;
}

[data-testid="stMetricLabel"] { color: rgba(0,212,255,0.6) !important; font-family: 'Orbitron', monospace !important; font-size: 0.6rem !important; }
[data-testid="stMetricValue"] { color: var(--hud-cyan) !important; font-family: 'Rajdhani', sans-serif !important; }
</style>
""", unsafe_allow_html=True)

# ─── 3. Header ─────────────────────────────────────────────────────────────────
st.markdown('<div class="jarvis-title">J.A.R.V.I.S</div>', unsafe_allow_html=True)
st.markdown('<div class="jarvis-subtitle">Just A Rather Very Intelligent System · Online</div>', unsafe_allow_html=True)

# ─── 4. Real-Time Data Tools ───────────────────────────────────────────────────
@tool
def get_current_datetime() -> str:
    """Returns the current date, time, day of week, and timezone info."""
    now = datetime.datetime.now()
    utc = datetime.datetime.utcnow()
    return (
        f"Current local datetime: {now.strftime('%A, %B %d, %Y at %H:%M:%S')}\n"
        f"UTC datetime: {utc.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        f"Week number: {now.isocalendar()[1]}\n"
        f"Day of year: {now.timetuple().tm_yday}"
    )

@tool
def get_weather(city: str) -> str:
    """Gets current weather for a city using the open-meteo geocoding and weather APIs.
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
                 63:"Moderate rain",65:"Heavy rain",71:"Light snow",80:"Rain showers",
                 95:"Thunderstorm"}
        desc = codes.get(c["weather_code"], f"Code {c['weather_code']}")
        return (
            f"Weather in {name}, {country}:\n"
            f"Condition: {desc}\n"
            f"Temperature: {c['temperature_2m']}°C\n"
            f"Humidity: {c['relative_humidity_2m']}%\n"
            f"Wind speed: {c['wind_speed_10m']} km/h"
        )
    except Exception as e:
        return f"Weather lookup failed: {e}"

@tool
def get_news(topic: str = "technology") -> str:
    """Searches for latest news on a topic using DuckDuckGo.
    Args:
        topic: The news topic to search for (e.g., 'AI', 'economy', 'space').
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
    past = search.run(f"{subject} history milestones key events")
    current = search.run(f"{subject} current trends 2025 latest")
    forecast = search.run(f"{subject} future predictions forecast 2025 2026")
    return (
        f"TEMPORAL ANALYSIS: {subject}\n\n"
        f"[HISTORICAL CONTEXT]\n{past[:600]}\n\n"
        f"[CURRENT STATE (2025)]\n{current[:600]}\n\n"
        f"[FUTURE OUTLOOK]\n{forecast[:600]}"
    )

@tool
def predict_insights(domain: str) -> str:
    """Generates data-driven predictive insights and forecasts for a domain.
    Args:
        domain: The domain to forecast.
    """
    search = DuckDuckGoSearchRun()
    data = search.run(f"{domain} market forecast predictions expert analysis 2025 2026")
    stats = search.run(f"{domain} statistics growth rate data trends")
    return (
        f"PREDICTIVE INSIGHTS: {domain}\n\n"
        f"[FORECAST DATA]\n{data[:700]}\n\n"
        f"[STATISTICAL TRENDS]\n{stats[:500]}"
    )

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

# ─── 5. Build Agent ────────────────────────────────────────────────────────────
tools: list[Any] = [
    DuckDuckGoSearchRun(),
    get_current_datetime,
    get_weather,
    get_news,
    analyze_trend,
    predict_insights,
    read_local_file,
    write_local_file,
]

SYSTEM_PROMPT = """You are J.A.R.V.I.S — Just A Rather Very Intelligent System. You are a sophisticated, JARVIS-like AI assistant with the personality of Tony Stark's AI: calm, precise, slightly witty, highly capable.

You have access to the following capabilities:
- Real-time date and time information
- Live weather data for any city worldwide
- Global news retrieval on any topic
- Temporal analysis: historical context + current trends + future forecasting
- Predictive insights and data-driven forecasting
- Web search for any query
- Local file reading and writing

Behavioral guidelines:
- Speak with confident precision. Be concise but comprehensive.
- When answering time-sensitive questions, always fetch live data — never guess.
- For trend/forecast questions, use analyze_trend or predict_insights tools.
- Occasionally use subtle JARVIS-style phrasing: "Certainly, sir/ma'am", "Analysis complete", "Running diagnostics", etc.
- Structure complex responses with clear sections.
- Keep responses conversational and not too long when voice is being used — aim for 2-3 sentences for simple queries.
- If you write a file, confirm the exact filename.
"""

@st.cache_resource
def build_agent() -> Any:
    llm = ChatAnthropic(
        model="claude-sonnet-4-5",
        temperature=0.3,
        api_key=st.secrets["ANTHROPIC_API_KEY"],
    )
    return create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)

agent = build_agent()

# ─── 6. Session State ──────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = InMemoryChatMessageHistory()
if "voice_input" not in st.session_state:
    st.session_state.voice_input = ""
if "tts_enabled" not in st.session_state:
    st.session_state.tts_enabled = True
if "wake_word_enabled" not in st.session_state:
    st.session_state.wake_word_enabled = True
if "wake_word" not in st.session_state:
    st.session_state.wake_word = "hey jarvis"
if "pending_tts" not in st.session_state:
    st.session_state.pending_tts = ""

# ─── 7. Sidebar HUD ────────────────────────────────────────────────────────────
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

    st.markdown('<div class="stat-label">⬡ VOICE SETTINGS</div>', unsafe_allow_html=True)
    st.session_state.tts_enabled = st.toggle("Voice Output (TTS)", value=st.session_state.tts_enabled)
    st.session_state.wake_word_enabled = st.toggle("Always-On Wake Word", value=st.session_state.wake_word_enabled)

    wake_word_input = st.text_input(
        "Wake Word / Phrase",
        value=st.session_state.wake_word,
        help="Say this phrase to activate JARVIS hands-free (e.g. 'hey jarvis', 'ok jarvis')"
    )
    if wake_word_input:
        st.session_state.wake_word = wake_word_input.lower().strip()

    st.markdown('<div class="stat-label">⬡ CAPABILITIES</div>', unsafe_allow_html=True)
    caps = ["🔍 Web Search", "🌤 Live Weather", "📰 Global News", "📊 Trend Analysis", "🔮 Forecasting", "📁 File I/O", "🕐 DateTime"]
    for c in caps:
        st.markdown(f'<div style="font-size:0.8rem;color:rgba(0,212,255,0.7);padding:2px 0;">{c}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="stat-label">⬡ QUICK COMMANDS</div>', unsafe_allow_html=True)
    quick_cmds = {
        "🕐 Time & Date": "What's the current date and time?",
        "🌤 Weather": "What's the weather in New York?",
        "📰 Tech News": "Get me the latest technology news",
        "📊 AI Trends": "Analyze current AI trends and future outlook",
        "🔮 Forecast": "Give me predictive insights on the renewable energy market",
    }
    for label, cmd in quick_cmds.items():
        if st.button(label, use_container_width=True):
            st.session_state.voice_input = cmd

    if st.button("🗑 Clear Memory", use_container_width=True):
        st.session_state.chat_history = InMemoryChatMessageHistory()
        st.rerun()

# ─── 8. Always-On Voice Component (Wake Word + Full Loop) ─────────────────────
#
# This component does exactly what Alexa/real JARVIS does:
#  1. Continuously listens in the background for the wake word
#  2. On detection → plays a chime → starts actively listening for the command
#  3. After silence → auto-submits the command to Streamlit via postMessage
#  4. TTS speaks the response back (injected after agent replies)
#
voice_component = f"""
<div id="voice-hud" style="
    font-family: 'Rajdhani', sans-serif;
    background: rgba(0,20,40,0.9);
    border: 1px solid rgba(0,212,255,0.3);
    border-radius: 4px;
    padding: 14px 16px;
    margin-bottom: 10px;
    position: relative;
">
    <!-- Corner accents -->
    <div style="position:absolute;top:0;left:0;width:30px;height:2px;background:#00d4ff;"></div>
    <div style="position:absolute;bottom:0;right:0;width:30px;height:2px;background:#00d4ff;"></div>

    <!-- Status Row -->
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
        <div style="display:flex;align-items:center;gap:10px;">
            <div id="statusDot" style="width:10px;height:10px;border-radius:50%;background:#555;box-shadow:0 0 0px #555;transition:all 0.3s;"></div>
            <span id="statusText" style="font-family:'Orbitron',monospace;font-size:0.65rem;letter-spacing:0.15em;color:rgba(0,212,255,0.6);">INITIALIZING...</span>
        </div>
        <div style="display:flex;gap:8px;">
            <button id="toggleWakeBtn" onclick="toggleWakeWord()" style="
                background:transparent;border:1px solid rgba(0,212,255,0.4);color:#00d4ff;
                font-family:'Orbitron',monospace;font-size:0.55rem;letter-spacing:0.1em;
                padding:5px 12px;border-radius:2px;cursor:pointer;transition:all 0.2s;
            ">⬡ WAKE WORD: ON</button>
            <button id="manualMicBtn" onclick="manualListen()" style="
                background:transparent;border:1px solid rgba(0,212,255,0.4);color:#00d4ff;
                font-family:'Orbitron',monospace;font-size:0.55rem;letter-spacing:0.1em;
                padding:5px 12px;border-radius:2px;cursor:pointer;transition:all 0.2s;
            ">🎙 SPEAK</button>
        </div>
    </div>

    <!-- Waveform visualizer -->
    <div id="waveform" style="display:flex;align-items:center;justify-content:center;gap:3px;height:28px;margin-bottom:10px;">
        {"".join([f'<div class="wave-bar" id="bar{i}" style="width:3px;height:4px;background:rgba(0,212,255,0.3);border-radius:2px;transition:height 0.1s;"></div>' for i in range(24)])}
    </div>

    <!-- Transcript display -->
    <div id="transcriptBox" style="
        font-size:0.9rem;color:#00ffff;
        min-height:22px;text-align:center;
        letter-spacing:0.05em;opacity:0.8;
    ">Say <span style="color:#00d4ff;font-weight:600;">"{st.session_state.wake_word.upper()}"</span> to begin...</div>
</div>

<script>
// ── Config ──────────────────────────────────────────────────────────────────
const WAKE_WORD = "{st.session_state.wake_word}";
const WAKE_ENABLED_DEFAULT = {"true" if st.session_state.wake_word_enabled else "false"};
const TTS_ENABLED = {"true" if st.session_state.tts_enabled else "false"};

// ── State ────────────────────────────────────────────────────────────────────
let wakeEnabled = WAKE_ENABLED_DEFAULT;
let wakeRecognition = null;
let commandRecognition = null;
let isWakeListening = false;
let isCommandListening = false;
let animFrame = null;
let audioCtx = null;
let analyser = null;
let mediaStream = null;

// ── DOM refs ─────────────────────────────────────────────────────────────────
const dot        = document.getElementById('statusDot');
const statusTxt  = document.getElementById('statusText');
const transcript = document.getElementById('transcriptBox');
const wakeBtn    = document.getElementById('toggleWakeBtn');
const micBtn     = document.getElementById('manualMicBtn');
const bars       = document.querySelectorAll('.wave-bar');

// ── Utility: set status ───────────────────────────────────────────────────────
function setStatus(state, text) {{
    const styles = {{
        idle:      {{ color:'#444',   shadow:'none',                          label:'STANDBY' }},
        wake:      {{ color:'#00d4ff',shadow:'0 0 8px rgba(0,212,255,0.5)',   label:'LISTENING FOR WAKE WORD' }},
        activated: {{ color:'#00ff88',shadow:'0 0 12px rgba(0,255,136,0.6)', label:'WAKE DETECTED' }},
        command:   {{ color:'#ff6b00',shadow:'0 0 12px rgba(255,107,0,0.6)', label:'LISTENING...' }},
        thinking:  {{ color:'#aa00ff',shadow:'0 0 12px rgba(170,0,255,0.5)', label:'PROCESSING' }},
        speaking:  {{ color:'#ffdd00',shadow:'0 0 12px rgba(255,221,0,0.5)', label:'SPEAKING' }},
        error:     {{ color:'#ff4444',shadow:'none',                          label:'ERROR' }},
    }};
    const s = styles[state] || styles.idle;
    dot.style.background  = s.color;
    dot.style.boxShadow   = s.shadow;
    statusTxt.textContent = text || s.label;
}}

// ── Waveform animation ────────────────────────────────────────────────────────
function startWaveAnimation(stream) {{
    if (!stream) {{ idleWave(); return; }}
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 64;
    const src = audioCtx.createMediaStreamSource(stream);
    src.connect(analyser);
    const dataArr = new Uint8Array(analyser.frequencyBinCount);
    function draw() {{
        analyser.getByteFrequencyData(dataArr);
        bars.forEach((bar, i) => {{
            const val = dataArr[i % dataArr.length];
            const h = Math.max(4, (val / 255) * 28);
            bar.style.height = h + 'px';
            bar.style.background = `rgba(0,${{Math.round(150 + val/2)}},255,${{0.4 + val/500}})`;
        }});
        animFrame = requestAnimationFrame(draw);
    }}
    draw();
}}

function stopWaveAnimation() {{
    if (animFrame) cancelAnimationFrame(animFrame);
    if (audioCtx) {{ audioCtx.close(); audioCtx = null; analyser = null; }}
    idleWave();
}}

function idleWave() {{
    bars.forEach((bar, i) => {{
        bar.style.height = (4 + Math.sin(i * 0.8) * 3) + 'px';
        bar.style.background = 'rgba(0,212,255,0.2)';
    }});
}}

// ── Chime on wake detection ───────────────────────────────────────────────────
function playChime() {{
    try {{
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        [[880, 0], [1100, 0.12], [1320, 0.24]].forEach(([freq, delay]) => {{
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain); gain.connect(ctx.destination);
            osc.frequency.value = freq;
            osc.type = 'sine';
            gain.gain.setValueAtTime(0, ctx.currentTime + delay);
            gain.gain.linearRampToValueAtTime(0.3, ctx.currentTime + delay + 0.05);
            gain.gain.linearRampToValueAtTime(0, ctx.currentTime + delay + 0.3);
            osc.start(ctx.currentTime + delay);
            osc.stop(ctx.currentTime + delay + 0.35);
        }});
    }} catch(e) {{}}
}}

// ── Wake word listener (always running in background) ────────────────────────
function startWakeWordListener() {{
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {{
        setStatus('error', 'SPEECH API NOT SUPPORTED — USE CHROME/EDGE');
        return;
    }}
    if (isWakeListening) return;

    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    wakeRecognition = new SR();
    wakeRecognition.continuous = true;
    wakeRecognition.interimResults = true;
    wakeRecognition.lang = 'en-US';
    wakeRecognition.maxAlternatives = 3;

    wakeRecognition.onstart = () => {{
        isWakeListening = true;
        setStatus('wake');
        transcript.innerHTML = 'Say <span style="color:#00d4ff;font-weight:600;">"' + WAKE_WORD.toUpperCase() + '"</span> to begin...';
        idleWave();
    }};

    wakeRecognition.onresult = (e) => {{
        if (isCommandListening) return;
        for (let i = e.resultIndex; i < e.results.length; i++) {{
            for (let j = 0; j < e.results[i].length; j++) {{
                const said = e.results[i][j].transcript.toLowerCase().trim();
                if (said.includes(WAKE_WORD)) {{
                    wakeRecognition.stop();
                    onWakeWordDetected();
                    return;
                }}
            }}
        }}
    }};

    wakeRecognition.onerror = (e) => {{
        isWakeListening = false;
        if (e.error === 'no-speech' || e.error === 'aborted') {{
            if (wakeEnabled) setTimeout(startWakeWordListener, 300);
        }} else {{
            setStatus('error', 'MIC ERROR: ' + e.error.toUpperCase());
        }}
    }};

    wakeRecognition.onend = () => {{
        isWakeListening = false;
        if (wakeEnabled && !isCommandListening) {{
            setTimeout(startWakeWordListener, 300);
        }}
    }};

    wakeRecognition.start();
}}

function stopWakeWordListener() {{
    wakeEnabled = false;
    isWakeListening = false;
    if (wakeRecognition) {{ try {{ wakeRecognition.stop(); }} catch(e) {{}} }}
    setStatus('idle', 'WAKE WORD OFF');
    transcript.textContent = 'Wake word disabled. Use SPEAK button.';
}}

// ── Wake word detected → start command listener ───────────────────────────────
function onWakeWordDetected() {{
    setStatus('activated', 'WAKE WORD DETECTED');
    transcript.textContent = '⚡ JARVIS activated — listening for command...';
    playChime();
    setTimeout(() => startCommandListener(), 400);
}}

// ── Command listener (after wake word) ───────────────────────────────────────
function startCommandListener() {{
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) return;
    isCommandListening = true;

    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    commandRecognition = new SR();
    commandRecognition.continuous = false;
    commandRecognition.interimResults = true;
    commandRecognition.lang = 'en-US';
    commandRecognition.maxAlternatives = 1;

    commandRecognition.onstart = () => {{
        setStatus('command', 'LISTENING — SPEAK YOUR COMMAND');
        transcript.textContent = '🎙 Speak now...';
        // Try to get audio stream for waveform
        navigator.mediaDevices.getUserMedia({{ audio: true }})
            .then(stream => {{ mediaStream = stream; startWaveAnimation(stream); }})
            .catch(() => {{ idleWave(); }});
    }};

    let finalText = '';
    commandRecognition.onresult = (e) => {{
        let interim = '';
        finalText = '';
        for (let i = e.resultIndex; i < e.results.length; i++) {{
            if (e.results[i].isFinal) finalText += e.results[i][0].transcript;
            else interim += e.results[i][0].transcript;
        }}
        transcript.textContent = finalText || interim || '...';
    }};

    commandRecognition.onerror = (e) => {{
        isCommandListening = false;
        stopWaveAnimation();
        if (mediaStream) {{ mediaStream.getTracks().forEach(t => t.stop()); mediaStream = null; }}
        setStatus('error', 'COMMAND ERROR: ' + e.error.toUpperCase());
        if (wakeEnabled) setTimeout(startWakeWordListener, 1000);
    }};

    commandRecognition.onend = () => {{
        stopWaveAnimation();
        if (mediaStream) {{ mediaStream.getTracks().forEach(t => t.stop()); mediaStream = null; }}
        isCommandListening = false;

        if (finalText && finalText.trim().length > 1) {{
            setStatus('thinking', 'PROCESSING COMMAND');
            transcript.textContent = '⚡ ' + finalText;
            // Submit to Streamlit
            window.parent.postMessage({{ type: 'voice_command', text: finalText.trim() }}, '*');
        }} else {{
            transcript.innerHTML = 'No command detected. Say <span style="color:#00d4ff;">"' + WAKE_WORD.toUpperCase() + '"</span> again.';
            if (wakeEnabled) setTimeout(startWakeWordListener, 500);
        }}
    }};

    commandRecognition.start();
}}

// ── Manual mic button (no wake word needed) ───────────────────────────────────
function manualListen() {{
    if (isCommandListening) {{
        if (commandRecognition) commandRecognition.stop();
        return;
    }}
    if (isWakeListening) {{
        try {{ wakeRecognition.stop(); }} catch(e) {{}}
        isWakeListening = false;
    }}
    onWakeWordDetected();
}}

// ── Toggle wake word on/off ───────────────────────────────────────────────────
function toggleWakeWord() {{
    if (wakeEnabled) {{
        stopWakeWordListener();
        wakeBtn.textContent = '⬡ WAKE WORD: OFF';
        wakeBtn.style.color = 'rgba(0,212,255,0.4)';
    }} else {{
        wakeEnabled = true;
        wakeBtn.textContent = '⬡ WAKE WORD: ON';
        wakeBtn.style.color = '#00d4ff';
        startWakeWordListener();
    }}
}}

// ── Listen for TTS trigger from Streamlit ────────────────────────────────────
window.addEventListener('message', (e) => {{
    if (e.data && e.data.type === 'jarvis_speak' && TTS_ENABLED) {{
        speakText(e.data.text);
    }}
}});

function speakText(text) {{
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    setStatus('speaking', 'SPEAKING');
    const clean = text.replace(/[#*_`]/g, '').substring(0, 900);
    const u = new SpeechSynthesisUtterance(clean);
    u.rate = 0.92;
    u.pitch = 0.8;
    u.volume = 1.0;

    // Pick best voice — prefer deep/British voices
    function trySpeak() {{
        const voices = window.speechSynthesis.getVoices();
        const preferred = voices.find(v =>
            v.name.includes('Google UK English Male') ||
            v.name.includes('Daniel') ||
            v.name.includes('Alex') ||
            v.name.includes('Google UK')
        ) || voices.find(v => v.lang === 'en-GB' && v.name.toLowerCase().includes('male'))
          || voices.find(v => v.lang.startsWith('en'));
        if (preferred) u.voice = preferred;
        u.onend = () => {{
            setStatus('wake');
            if (wakeEnabled) startWakeWordListener();
        }};
        window.speechSynthesis.speak(u);
    }}

    if (window.speechSynthesis.getVoices().length) trySpeak();
    else window.speechSynthesis.onvoiceschanged = trySpeak;
}}

// ── Init ─────────────────────────────────────────────────────────────────────
idleWave();
if (WAKE_ENABLED_DEFAULT) {{
    setTimeout(startWakeWordListener, 800);
}} else {{
    setStatus('idle', 'WAKE WORD OFF — USE SPEAK BUTTON');
    transcript.textContent = 'Wake word disabled. Press SPEAK to talk.';
}}
</script>
"""

components.html(voice_component, height=160)

# ─── 9. Handle postMessage from voice component ─────────────────────────────────
# Streamlit doesn't natively receive postMessage, so we use a hidden JS bridge
# that stores the voice command in sessionStorage and a query param trick.
# The cleanest approach for Streamlit: a text_input that gets auto-populated
# by a JS component, plus st.query_params for the bridge.

bridge_component = """
<script>
window.addEventListener('message', function(e) {
    if (e.data && e.data.type === 'voice_command') {
        const text = e.data.text;
        // Write to a hidden input that Streamlit can read via query_params
        const url = new URL(window.parent.location.href);
        url.searchParams.set('voice_cmd', text);
        url.searchParams.set('voice_ts', Date.now());
        window.parent.history.replaceState({}, '', url.toString());
        // Also trigger a Streamlit rerun by simulating the chat input
        // Find the chat input textarea and fill it
        setTimeout(() => {
            const inputs = window.parent.document.querySelectorAll('textarea');
            for (const inp of inputs) {
                if (inp.placeholder && inp.placeholder.includes('J.A.R.V.I.S')) {
                    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
                    nativeInputValueSetter.call(inp, text);
                    inp.dispatchEvent(new Event('input', { bubbles: true }));
                    setTimeout(() => {
                        inp.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true }));
                    }, 100);
                    break;
                }
            }
        }, 200);
    }
});
</script>
"""
components.html(bridge_component, height=0)

# ─── 10. Read voice command from query params ──────────────────────────────────
params = st.query_params
voice_cmd_from_url = params.get("voice_cmd", "")
voice_ts = params.get("voice_ts", "")

# Deduplicate: only use if timestamp is new
last_ts = st.session_state.get("last_voice_ts", "")
if voice_cmd_from_url and voice_ts != last_ts:
    st.session_state.voice_input = voice_cmd_from_url
    st.session_state.last_voice_ts = voice_ts
    # Clear from URL
    st.query_params.clear()

# ─── 11. Render Chat History ────────────────────────────────────────────────────
TYPE_TO_ROLE: dict[str, str] = {"human": "user", "ai": "assistant"}
for message in st.session_state.chat_history.messages:
    role = TYPE_TO_ROLE.get(message.type, message.type)
    with st.chat_message(role):
        st.write(message.content)

# ─── 12. Handle Input (text, quick command, or voice) ───────────────────────────
user_query = st.chat_input("Interface with J.A.R.V.I.S...")

# Inject quick command or voice command
if st.session_state.voice_input and not user_query:
    user_query = st.session_state.voice_input
    st.session_state.voice_input = ""

if user_query:
    with st.chat_message("user"):
        st.write(user_query)

    typed_history: list[HumanMessage | AIMessage] = [
        HumanMessage(content=str(m.content)) if m.type == "human"
        else AIMessage(content=str(m.content))
        for m in st.session_state.chat_history.messages
    ]
    typed_history.append(HumanMessage(content=user_query))

    with st.spinner("⚡ Processing..."):
        result: dict[str, Any] = agent.invoke({"messages": typed_history})
        output_text: str = str(result["messages"][-1].content)

    with st.chat_message("assistant"):
        st.write(output_text)

    # TTS: send text to the voice component via JS injection
    if st.session_state.tts_enabled:
        clean_tts = output_text.replace('"', "'").replace('\n', ' ').replace('\\', '').replace('`', '')[:900]
        tts_bridge = f"""
        <script>
        (function() {{
            // Post to parent frames (the voice component iframes listen for this)
            const iframes = window.parent.document.querySelectorAll('iframe');
            iframes.forEach(iframe => {{
                try {{
                    iframe.contentWindow.postMessage({{type:'jarvis_speak', text:"{clean_tts}"}}, '*');
                }} catch(e) {{}}
            }});
            // Also speak directly if in top frame context
            if (window.speechSynthesis) {{
                window.speechSynthesis.cancel();
                const u = new SpeechSynthesisUtterance("{clean_tts}");
                u.rate = 0.92; u.pitch = 0.8; u.volume = 1.0;
                const voices = window.speechSynthesis.getVoices();
                const preferred = voices.find(v => v.name.includes('Google UK English Male') || v.name.includes('Daniel'));
                if (preferred) u.voice = preferred;
                window.speechSynthesis.speak(u);
            }}
        }})();
        </script>
        """
        components.html(tts_bridge, height=0)

    st.session_state.chat_history.add_user_message(user_query)
    st.session_state.chat_history.add_ai_message(output_text)
