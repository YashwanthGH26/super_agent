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

/* Chat messages */
[data-testid="stChatMessage"] {
    background: rgba(0,20,40,0.7) !important;
    border: 1px solid var(--hud-border) !important;
    border-radius: 4px !important;
    margin-bottom: 0.5rem !important;
    backdrop-filter: blur(8px) !important;
}

[data-testid="stChatMessage"][data-testid*="user"] {
    border-color: rgba(255,107,0,0.4) !important;
}

/* Chat input */
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

/* Buttons */
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

.mic-active button {
    background: rgba(255,50,50,0.15) !important;
    border-color: rgba(255,50,50,0.6) !important;
    color: #ff5050 !important;
    box-shadow: 0 0 20px rgba(255,50,50,0.3) !important;
    animation: mic-pulse 1s ease-in-out infinite !important;
}

@keyframes mic-pulse {
    0%, 100% { box-shadow: 0 0 10px rgba(255,50,50,0.3); }
    50% { box-shadow: 0 0 25px rgba(255,50,50,0.6); }
}

/* Spinner */
[data-testid="stSpinner"] { color: var(--hud-blue) !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: rgba(0,20,40,0.5); }
::-webkit-scrollbar-thumb { background: rgba(0,212,255,0.3); border-radius: 2px; }

/* Metric */
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
    """Gets current weather for a city using the open-meteo geocoding and weather APIs (no key needed).
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
    """Analyzes historical context and current trends for any subject, providing temporal insights.
    Args:
        subject: The topic to analyze (e.g., 'AI adoption', 'electric vehicles').
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
        domain: The domain to forecast (e.g., 'renewable energy market', 'AI startups').
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

# ─── 5. Import urllib.parse (needed for weather tool) ─────────────────────────
import urllib.parse

# ─── 6. Build Agent ────────────────────────────────────────────────────────────
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

# ─── 7. Session State ──────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = InMemoryChatMessageHistory()
if "listening" not in st.session_state:
    st.session_state.listening = False
if "voice_input" not in st.session_state:
    st.session_state.voice_input = ""
if "tts_enabled" not in st.session_state:
    st.session_state.tts_enabled = True

# ─── 8. Sidebar HUD ────────────────────────────────────────────────────────────
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

# ─── 9. Voice Input Component ──────────────────────────────────────────────────
voice_component = """
<div id="voice-container" style="margin-bottom:10px;">
    <button id="micBtn" onclick="toggleMic()" style="
        background: transparent;
        border: 1px solid rgba(0,212,255,0.4);
        color: #00d4ff;
        font-family: 'Orbitron', monospace;
        font-size: 0.65rem;
        letter-spacing: 0.15em;
        padding: 8px 20px;
        border-radius: 2px;
        cursor: pointer;
        width: 100%;
        transition: all 0.2s;
    ">🎙 ACTIVATE VOICE INPUT</button>
    <div id="status" style="
        font-family: 'Rajdhani', sans-serif;
        font-size: 0.8rem;
        color: rgba(0,212,255,0.5);
        margin-top:6px;
        min-height:20px;
        text-align:center;
    "></div>
    <div id="transcript" style="
        font-family: 'Rajdhani', sans-serif;
        font-size: 0.9rem;
        color: #00ffff;
        margin-top:6px;
        padding: 6px 10px;
        border: 1px solid rgba(0,212,255,0.2);
        border-radius:2px;
        min-height:30px;
        background: rgba(0,20,40,0.6);
        display:none;
    "></div>
</div>

<script>
let recognition = null;
let isListening = false;

function toggleMic() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        document.getElementById('status').innerHTML = '⚠ Speech recognition not supported. Use Chrome/Edge.';
        return;
    }
    if (isListening) {
        recognition.stop();
    } else {
        startListening();
    }
}

function startListening() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    const btn = document.getElementById('micBtn');
    const status = document.getElementById('status');
    const transcript = document.getElementById('transcript');

    recognition.onstart = () => {
        isListening = true;
        btn.innerHTML = '⏹ STOP LISTENING';
        btn.style.borderColor = 'rgba(255,50,50,0.6)';
        btn.style.color = '#ff5050';
        btn.style.boxShadow = '0 0 20px rgba(255,50,50,0.3)';
        status.innerHTML = '● Listening... speak now';
        status.style.color = '#ff5050';
        transcript.style.display = 'block';
        transcript.innerHTML = '...';
    };

    recognition.onresult = (e) => {
        let interim = '';
        let final = '';
        for (let i = e.resultIndex; i < e.results.length; i++) {
            if (e.results[i].isFinal) final += e.results[i][0].transcript;
            else interim += e.results[i][0].transcript;
        }
        transcript.innerHTML = final || interim;
        if (final) {
            // Send to Streamlit via URL hack
            window.parent.postMessage({type: 'voice_input', text: final}, '*');
        }
    };

    recognition.onerror = (e) => {
        status.innerHTML = '⚠ Error: ' + e.error;
        resetUI();
    };

    recognition.onend = () => {
        const text = transcript.innerHTML;
        if (text && text !== '...' && text !== '') {
            status.innerHTML = '✓ Voice captured — paste above or retype if needed';
            status.style.color = 'rgba(0,212,255,0.7)';
        }
        resetUI();
    };

    recognition.start();
}

function resetUI() {
    isListening = false;
    const btn = document.getElementById('micBtn');
    btn.innerHTML = '🎙 ACTIVATE VOICE INPUT';
    btn.style.borderColor = 'rgba(0,212,255,0.4)';
    btn.style.color = '#00d4ff';
    btn.style.boxShadow = 'none';
    document.getElementById('status').style.color = 'rgba(0,212,255,0.5)';
}
</script>
"""

components.html(voice_component, height=130)

# ─── 10. TTS Component ─────────────────────────────────────────────────────────
def speak_text(text: str):
    """Inject JS to speak text via Web Speech API."""
    # Clean text for TTS
    clean = text.replace('"', "'").replace('\n', ' ').replace('\\', '')[:800]
    tts_js = f"""
    <script>
    (function() {{
        if (!window.speechSynthesis) return;
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance("{clean}");
        u.rate = 0.95;
        u.pitch = 0.85;
        u.volume = 1.0;
        // Try to pick a deeper voice
        const voices = window.speechSynthesis.getVoices();
        const preferred = voices.find(v => v.name.includes('Google UK') || v.name.includes('Daniel') || v.name.includes('Alex'));
        if (preferred) u.voice = preferred;
        window.speechSynthesis.speak(u);
    }})();
    </script>
    """
    components.html(tts_js, height=0)

# ─── 11. Render Chat History ────────────────────────────────────────────────────
TYPE_TO_ROLE: dict[str, str] = {"human": "user", "ai": "assistant"}
for message in st.session_state.chat_history.messages:
    role = TYPE_TO_ROLE.get(message.type, message.type)
    with st.chat_message(role):
        st.write(message.content)

# ─── 12. Handle Input (text or quick command) ───────────────────────────────────
user_query = st.chat_input("Interface with J.A.R.V.I.S...")

# Check for quick command injection from sidebar
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

    # TTS output
    if st.session_state.tts_enabled:
        speak_text(output_text)

    st.session_state.chat_history.add_user_message(user_query)
    st.session_state.chat_history.add_ai_message(output_text)
