# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S - Tony Stark Edition (Complete Rebuild)

ROOT CAUSE FIXES:
- Voice reply not working: st.markdown TTS script gets stripped by Streamlit's
  HTML sanitizer. Fix: embed TTS trigger directly inside the SAME voice iframe
  via Python f-string injection (tts_seq + tts_text). The iframe detects the
  new seq on every rerender and speaks immediately in its own window context.
- Music 30s limit: iTunes only gives 30s previews. Switched to YouTube IFrame
  API for full songs - user searches, picks, plays full tracks legally.
- Chat input white background: fixed with proper CSS selector.
- CST/IST time confirmed in tool.
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

# ================================================================
# GLOBAL CSS
# ================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=Share+Tech+Mono&family=Rajdhani:wght@300;400;500;600&display=swap');

:root {
  --arc:#00d4ff; --arc2:#00aadd; --gold:#f5a623; --gold2:#ffcc44;
  --red:#c0183a; --plasma:#8b5cf6; --green:#10b981;
  --void:#020b18; --deep:#040f1e; --panel:rgba(4,15,30,0.94);
  --border:rgba(0,212,255,0.2); --text:#a8d4e8;
}
*,*::before,*::after{box-sizing:border-box;}
html,body,[data-testid="stAppViewContainer"]{
  background:var(--void)!important;
  font-family:'Rajdhani',sans-serif!important;
  color:var(--text)!important; overflow-x:hidden;
}
[data-testid="stAppViewContainer"]::before{
  content:''; position:fixed; inset:0; z-index:0;
  background:
    radial-gradient(ellipse 60% 40% at 50% -10%,rgba(0,170,221,0.18) 0%,transparent 70%),
    radial-gradient(ellipse 30% 25% at 85% 90%,rgba(139,92,246,0.1) 0%,transparent 60%),
    radial-gradient(ellipse 25% 30% at 5% 70%,rgba(192,24,58,0.07) 0%,transparent 60%),
    repeating-linear-gradient(0deg,transparent,transparent 44px,rgba(0,212,255,0.025) 44px,rgba(0,212,255,0.025) 45px),
    repeating-linear-gradient(90deg,transparent,transparent 44px,rgba(0,212,255,0.025) 44px,rgba(0,212,255,0.025) 45px);
  pointer-events:none;
}
[data-testid="stHeader"]{background:transparent!important;border-bottom:1px solid rgba(0,212,255,0.08)!important;}
[data-testid="stSidebar"]{background:rgba(2,11,24,0.98)!important;border-right:1px solid rgba(0,212,255,0.15)!important;}
[data-testid="stSidebar"]>div{padding-top:1rem!important;}

/* TITLE */
.j-title{
  font-family:'Orbitron',monospace; font-size:clamp(1.8rem,4vw,3rem); font-weight:900;
  text-align:center; letter-spacing:0.5em; padding:1.5rem 0 0.3rem;
  background:linear-gradient(90deg,#00aadd 0%,#00d4ff 30%,#ffffff 50%,#00d4ff 70%,#00aadd 100%);
  background-size:200%; -webkit-background-clip:text; -webkit-text-fill-color:transparent;
  background-clip:text; animation:title-shine 4s linear infinite;
  filter:drop-shadow(0 0 30px rgba(0,212,255,0.4));
}
@keyframes title-shine{0%{background-position:200% center}100%{background-position:-200% center}}
.j-sub{
  font-family:'Share Tech Mono',monospace; font-size:0.72rem;
  color:rgba(0,212,255,0.4); text-align:center; letter-spacing:0.55em;
  text-transform:uppercase; margin-bottom:1.2rem;
}
/* PANELS */
.j-panel{
  background:var(--panel); border:1px solid var(--border); border-radius:4px;
  padding:0.85rem 1rem; margin-bottom:0.8rem; position:relative; backdrop-filter:blur(16px);
}
.j-panel::before{content:'';position:absolute;top:0;left:0;width:24px;height:1px;background:var(--arc);}
.j-panel::after{content:'';position:absolute;bottom:0;right:0;width:24px;height:1px;background:var(--arc);}
.j-label{font-family:'Orbitron',monospace;font-size:0.52rem;color:rgba(0,212,255,0.45);letter-spacing:0.3em;text-transform:uppercase;margin-bottom:0.3rem;}
.j-val{font-family:'Share Tech Mono',monospace;font-size:1.05rem;color:var(--arc);}
/* CHAT */
[data-testid="stChatMessage"]{
  background:rgba(4,15,30,0.85)!important; border:1px solid rgba(0,212,255,0.12)!important;
  border-radius:4px!important; margin-bottom:0.5rem!important; backdrop-filter:blur(12px)!important;
}
/* CHAT INPUT - multiple selectors to cover Streamlit versions */
[data-testid="stChatInput"],
[data-testid="stChatInput"] > div,
[data-testid="stChatInputContainer"],
[data-testid="stChatInputContainer"] > div {
  background:rgba(2,11,24,0.97)!important;
  border-color:rgba(0,212,255,0.25)!important;
}
[data-testid="stChatInput"] textarea,
textarea[data-testid="stChatInputTextArea"] {
  background:rgba(2,11,24,0.97)!important;
  border:1px solid rgba(0,212,255,0.25)!important;
  color:var(--arc)!important; font-family:'Share Tech Mono',monospace!important;
  font-size:0.9rem!important; border-radius:4px!important; caret-color:var(--arc);
}
[data-testid="stChatInput"] textarea:focus{border-color:var(--arc)!important;box-shadow:0 0 20px rgba(0,212,255,0.15)!important;}
/* Override any white backgrounds in bottom bar */
.stChatFloatingInputContainer, .stChatFloatingInputContainer > div,
section[data-testid="stBottom"], section[data-testid="stBottom"] > div {
  background:rgba(2,11,24,0.97)!important;
  border-top:1px solid rgba(0,212,255,0.1)!important;
}
/* BUTTONS */
.stButton>button{
  background:transparent!important; border:1px solid rgba(0,212,255,0.2)!important;
  color:rgba(0,212,255,0.75)!important; font-family:'Orbitron',monospace!important;
  font-size:0.58rem!important; letter-spacing:0.1em!important; border-radius:3px!important;
  padding:0.4rem 0.8rem!important; transition:all 0.2s!important;
}
.stButton>button:hover{background:rgba(0,212,255,0.07)!important;border-color:var(--arc)!important;color:var(--arc)!important;box-shadow:0 0 12px rgba(0,212,255,0.2)!important;}
::-webkit-scrollbar{width:3px;height:3px;}
::-webkit-scrollbar-track{background:rgba(0,0,0,0.3);}
::-webkit-scrollbar-thumb{background:rgba(0,212,255,0.25);border-radius:2px;}
[data-testid="stSpinner"]>div{border-color:var(--arc) transparent transparent!important;}
[data-testid="stTabs"] [role="tab"]{font-family:'Orbitron',monospace!important;font-size:0.6rem!important;letter-spacing:0.15em!important;color:rgba(0,212,255,0.5)!important;}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{color:var(--arc)!important;border-bottom-color:var(--arc)!important;}
.j-cap{font-size:0.78rem;color:rgba(0,212,255,0.6);padding:2px 0;font-family:'Share Tech Mono',monospace;}
/* ARC REACTOR */
.arc-ring{width:60px;height:60px;border-radius:50%;border:2px solid rgba(0,212,255,0.3);display:flex;align-items:center;justify-content:center;margin:0.5rem auto;position:relative;animation:arc-spin 8s linear infinite;}
.arc-ring::before{content:'';position:absolute;inset:4px;border-radius:50%;border:1px solid rgba(0,212,255,0.2);animation:arc-spin 4s linear infinite reverse;}
.arc-core{width:20px;height:20px;border-radius:50%;background:radial-gradient(circle,#00e5ff,#0088bb);box-shadow:0 0 15px #00d4ff,0 0 30px rgba(0,212,255,0.5);animation:core-pulse 2s ease-in-out infinite;}
@keyframes arc-spin{to{transform:rotate(360deg)}}
@keyframes core-pulse{0%,100%{box-shadow:0 0 12px #00d4ff,0 0 25px rgba(0,212,255,0.4)}50%{box-shadow:0 0 20px #00d4ff,0 0 50px rgba(0,212,255,0.7)}}
</style>
""", unsafe_allow_html=True)

# HEADER
st.markdown('<div class="j-title">J.A.R.V.I.S</div>', unsafe_allow_html=True)
st.markdown('<div class="j-sub">Just A Rather Very Intelligent System &nbsp;&middot;&nbsp; Arc Reactor Online</div>', unsafe_allow_html=True)

# ================================================================
# TOOLS
# ================================================================
@tool
def get_current_datetime() -> str:
    """Returns the current date and time in CST and IST timezones."""
    utc_now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    cst = utc_now - datetime.timedelta(hours=6)
    ist = utc_now + datetime.timedelta(hours=5, minutes=30)
    return (
        f"CST (Central Standard Time): {cst.strftime('%A, %B %d, %Y at %H:%M:%S')} | "
        f"IST (India Standard Time): {ist.strftime('%A, %B %d, %Y at %H:%M:%S')} | "
        f"Week {utc_now.isocalendar()[1]}, Day {utc_now.timetuple().tm_yday} of year"
    )

@tool
def set_reminder(task: str, minutes: int) -> str:
    """Handles reminder requests with honest capability disclosure.
    Args:
        task: What the reminder is for.
        minutes: Minutes from now.
    """
    return (
        f"I appreciate the request, but I must be transparent: I cannot schedule "
        f"live notifications for '{task}' in {minutes} minutes. My architecture is "
        f"on-demand with no persistent background process. Please use your device clock or calendar."
    )

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
        return (f"{name}, {country}: {codes.get(c['weather_code'],'Unknown')}, "
                f"{c['temperature_2m']} degrees Celsius, "
                f"Humidity {c['relative_humidity_2m']} percent, Wind {c['wind_speed_10m']} kmh")
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
    """Generates predictive insights for a domain.
    Args:
        domain: Domain to forecast.
    """
    s = DuckDuckGoSearchRun()
    data  = s.run(f"{domain} market forecast predictions 2025 2026")
    stats = s.run(f"{domain} statistics growth rate data")
    return f"PREDICTIVE INSIGHTS: {domain}\n[FORECAST]\n{data[:500]}\n[STATS]\n{stats[:300]}"

@tool
def search_music(query: str) -> str:
    """Searches for music using iTunes API. Returns track info for display.
    Args:
        query: Song, artist, or album name.
    """
    try:
        url = (f"https://itunes.apple.com/search?term={urllib.parse.quote(query)}"
               f"&media=music&limit=5&entity=song")
        with urllib.request.urlopen(url, timeout=6) as r:
            data = json.loads(r.read())
        results = data.get("results", [])
        if not results:
            return f"No tracks found for '{query}'."
        lines = []
        for t in results[:5]:
            lines.append(f"{t.get('trackName','?')} by {t.get('artistName','?')} "
                         f"(Album: {t.get('collectionName','?')})")
        return "Found tracks:\n" + "\n".join(lines)
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

# ================================================================
# AGENT
# ================================================================
tools_list: list[Any] = [
    DuckDuckGoSearchRun(), get_current_datetime, set_reminder,
    get_weather, get_news, web_search, analyze_trend, predict_insights,
    search_music, read_local_file, write_local_file,
]

SYSTEM_PROMPT = """You are J.A.R.V.I.S - Just A Rather Very Intelligent System.
Personality: Tony Stark's AI. Calm, precise, confident, occasionally witty.

CRITICAL RULES:
- Always use tools for live data. Never guess dates, weather, news, or music.
- Voice responses: CONCISE. Max 2-3 sentences for simple queries. Max 4 for complex.
- ZERO markdown in responses. No **, ##, -, *, backticks. Plain conversational sentences only.
- JARVIS style phrases: Certainly, Right away, Analysis complete, Noted sir, Of course.
- Lead with the direct answer first. Detail second.
- For time questions: use get_current_datetime and always give CST and IST.
- Reminders/alarms: use set_reminder tool to explain honestly.
- Music: use search_music tool, then describe what was found in one sentence.
- For Indian music (Telugu, Hindi, Tamil, Kannada): search_music fully supports it.
- Never say UTC - always convert to CST or IST before answering.
"""

@st.cache_resource
def build_agent() -> Any:
    llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0.3,
                        api_key=st.secrets["ANTHROPIC_API_KEY"])
    return create_react_agent(llm, tools_list, prompt=SYSTEM_PROMPT)

agent = build_agent()

# ================================================================
# SESSION STATE
# ================================================================
defaults = {
    "chat_history":  None,
    "voice_input":   "",
    "last_voice_ts": "",
    "tts_text":      "",
    "tts_seq":       0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v if v is not None else InMemoryChatMessageHistory()

# ================================================================
# VOICE COMMAND FROM URL PARAMS (JS -> Python bridge)
# ================================================================
params  = st.query_params
raw_vc  = params.get("vc", "")
raw_vts = params.get("vts", "")
try:
    voice_cmd = urllib.parse.unquote(raw_vc) if raw_vc else ""
except Exception:
    voice_cmd = raw_vc

if voice_cmd and raw_vts != st.session_state.last_voice_ts:
    st.session_state.voice_input   = voice_cmd
    st.session_state.last_voice_ts = raw_vts
    st.query_params.clear()

# ================================================================
# SIDEBAR
# ================================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:0.5rem 0 1rem;">
      <div class="arc-ring"><div class="arc-core"></div></div>
      <div style="font-family:'Orbitron',monospace;font-size:0.55rem;color:rgba(0,212,255,0.5);letter-spacing:0.3em;margin-top:0.4rem;">ARC REACTOR ONLINE</div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="j-label">System Status</div>', unsafe_allow_html=True)
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    ist_now = now + datetime.timedelta(hours=5, minutes=30)
    st.markdown(f"""
    <div class="j-panel">
      <div class="j-val" style="color:#10b981;font-size:0.85rem;">&#9679; ALL SYSTEMS NOMINAL</div>
      <div style="font-family:'Share Tech Mono',monospace;font-size:0.7rem;color:rgba(0,212,255,0.5);margin-top:4px;">
        IST {ist_now.strftime('%H:%M:%S')} &nbsp;|&nbsp; {ist_now.strftime('%d %b %Y')}
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="j-label" style="margin-top:0.6rem;">Voice Protocol</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="j-panel" style="font-family:'Share Tech Mono',monospace;font-size:0.7rem;color:rgba(0,212,255,0.6);line-height:1.9;">
      <span style="color:#00d4ff;">HEY JARVIS</span> &rarr; activate<br>
      Speak command &rarr; auto-submit<br>
      JARVIS speaks reply back<br>
      <span style="color:#f5a623;">TAP ORB</span> &rarr; interrupt speech<br>
      <span style="color:rgba(0,212,255,0.35);">Chrome / Edge required</span>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="j-label" style="margin-top:0.6rem;">Capabilities</div>', unsafe_allow_html=True)
    for cap in ["&#127925; Music (Full Songs)","&#128269; Web Search","&#127780; Live Weather",
                "&#128240; Global News","&#128202; Trend Analysis","&#128302; Forecasting",
                "&#128337; Reminders","&#128336; CST / IST Time"]:
        st.markdown(f'<div class="j-cap">{cap}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="j-label">Quick Fire</div>', unsafe_allow_html=True)
    cmds = {
        "&#128336; Date & Time":      "What is the current date and time?",
        "&#127780; Weather NYC":      "What is the weather in New York right now?",
        "&#128240; Tech News":        "Get me the latest AI and technology news",
        "&#128202; AI Trends":        "Analyze current AI trends and future outlook",
        "&#127925; Arijit Singh":     "Search for popular Bollywood songs by Arijit Singh",
        "&#127925; Telugu Songs":     "Search for popular Telugu songs by Sid Sriram",
        "&#128337; Reminder Info":    "Set a reminder for my meeting in 30 minutes",
    }
    for label, cmd in cmds.items():
        if st.button(label, use_container_width=True):
            st.session_state.voice_input = cmd
            st.rerun()

    st.markdown("---")
    if st.button("&#128465; Clear Memory", use_container_width=True):
        st.session_state.chat_history = InMemoryChatMessageHistory()
        st.session_state.tts_text = ""
        st.session_state.tts_seq  = 0
        st.rerun()

# ================================================================
# TABS
# ================================================================
tab_chat, tab_music = st.tabs(["⚡  JARVIS INTERFACE", "🎵  MUSIC STATION"])

# ================================================================
# TAB 1: CHAT + VOICE
# ================================================================
with tab_chat:

    tts_safe = st.session_state.tts_text
    tts_seq  = st.session_state.tts_seq

    # KEY FIX: The entire voice system - wake word, command, TTS output, ORB interrupt
    # lives in ONE single components.html() call.
    # TTS_TEXT and TTS_SEQ are injected by Python on EVERY rerender via f-string.
    # When tts_seq changes (new reply), JS detects it via localStorage comparison
    # and speaks immediately in the same iframe context - no cross-frame issues.
    # ORB interrupt calls window.speechSynthesis.cancel() in the SAME frame.
    # Voice submit navigates parent URL to trigger Streamlit rerun.

    voice_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Share+Tech+Mono&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
html,body{{background:transparent;overflow:hidden;height:185px;}}
#jv{{
  background:linear-gradient(160deg,rgba(4,15,30,0.98) 0%,rgba(2,8,20,0.99) 100%);
  border:1px solid rgba(0,212,255,0.22); border-radius:8px;
  padding:14px 18px 12px; position:relative; overflow:hidden; height:100%;
}}
#jv::before{{
  content:'';position:absolute;top:0;left:-100%;width:60%;height:1px;
  background:linear-gradient(90deg,transparent,#00d4ff,transparent);
  animation:scan 4s linear infinite;
}}
@keyframes scan{{to{{left:200%;}}}}
.c{{position:absolute;width:10px;height:10px;border-color:rgba(0,212,255,0.5);border-style:solid;}}
.tl{{top:0;left:0;border-width:1px 0 0 1px;}} .tr{{top:0;right:0;border-width:1px 1px 0 0;}}
.bl{{bottom:0;left:0;border-width:0 0 1px 1px;}} .br{{bottom:0;right:0;border-width:0 1px 1px 0;}}
#row{{display:flex;align-items:center;gap:12px;margin-bottom:10px;}}
#orb{{
  width:20px;height:20px;border-radius:50%;flex-shrink:0;
  background:#0a1a2a; box-shadow:0 0 0 rgba(0,212,255,0);
  transition:background 0.25s,box-shadow 0.3s,transform 0.15s;
  cursor:pointer; position:relative;
}}
#orb::after{{
  content:'';position:absolute;inset:-5px;border-radius:50%;
  border:1px solid rgba(0,212,255,0.15);
  animation:orb-ring 2.5s ease-in-out infinite;
}}
@keyframes orb-ring{{0%,100%{{transform:scale(1);opacity:0.3;}}50%{{transform:scale(1.4);opacity:0.08;}}}}
#orb:hover{{transform:scale(1.15);cursor:pointer;}} #orb:active{{transform:scale(0.9);}}
#status{{font-family:'Orbitron',monospace;font-size:0.58rem;letter-spacing:0.2em;color:rgba(0,212,255,0.45);flex:1;}}
#hint{{font-family:'Share Tech Mono',monospace;font-size:0.6rem;color:rgba(0,212,255,0.25);white-space:nowrap;}}
#wave{{display:flex;align-items:flex-end;justify-content:center;gap:2px;height:40px;margin-bottom:10px;}}
.b{{width:3px;border-radius:2px 2px 0 0;background:rgba(0,212,255,0.15);transition:height 0.07s,background 0.1s;}}
#tbox{{
  font-family:'Share Tech Mono',monospace;font-size:0.82rem;color:#00d4ff;
  text-align:center;min-height:20px;letter-spacing:0.04em;line-height:1.4;
  padding:2px 4px;
}}
</style>
</head>
<body>
<div id="jv">
  <div class="c tl"></div><div class="c tr"></div>
  <div class="c bl"></div><div class="c br"></div>
  <div id="row">
    <div id="orb" onclick="orbInterrupt()" title="Tap to interrupt JARVIS"></div>
    <span id="status">ARC REACTOR INITIALIZING...</span>
    <span id="hint">TAP ORB TO INTERRUPT</span>
  </div>
  <div id="wave">
    {''.join(['<div class="b" style="height:' + str(h) + 'px"></div>'
              for h in [4,5,4,7,4,5,9,4,5,7,11,5,4,8,13,6,4,9,5,4,6,4,5,4,7,4,6,4,5,4,7,4,5,4,8,4]])}
  </div>
  <div id="tbox">Say <strong style="color:#00ffff;">HEY JARVIS</strong> to activate</div>
</div>

<script>
// ── INJECTED BY PYTHON ON EVERY RENDER ─────────────────────────
const TTS_TEXT = {json.dumps(tts_safe)};
const TTS_SEQ  = {tts_seq};

// ── DOM ─────────────────────────────────────────────────────────
const orb    = document.getElementById('orb');
const status = document.getElementById('status');
const tbox   = document.getElementById('tbox');
const bars   = Array.from(document.querySelectorAll('.b'));

// ── STATE ───────────────────────────────────────────────────────
let wakeRec=null, cmdRec=null;
let isWaking=false, isCommand=false, isSpeaking=false;
let micStream=null, audioCtx=null, rafId=null, silTimer=null;
let finalText='';

// ── THEMES ──────────────────────────────────────────────────────
const T = {{
  boot:     {{d:'#0a1a2a', g:'none',                            s:'ARC REACTOR INITIALIZING'}},
  wake:     {{d:'#00d4ff', g:'0 0 14px rgba(0,212,255,0.75)',   s:'LISTENING FOR WAKE WORD'}},
  detected: {{d:'#00ff88', g:'0 0 16px rgba(0,255,136,0.8)',    s:'WAKE DETECTED'}},
  command:  {{d:'#8b5cf6', g:'0 0 16px rgba(139,92,246,0.8)',   s:'LISTENING - SPEAK NOW'}},
  thinking: {{d:'#f5a623', g:'0 0 16px rgba(245,166,35,0.75)',  s:'NEURAL NET PROCESSING'}},
  speaking: {{d:'#c0183a', g:'0 0 18px rgba(192,24,58,0.85)',   s:'SPEAKING - TAP ORB TO STOP'}},
  interrupt:{{d:'#ff6b35', g:'0 0 14px rgba(255,107,53,0.8)',   s:'INTERRUPTED'}},
  error:    {{d:'#ff3333', g:'none',                            s:'ERROR - RETRYING'}},
  noapi:    {{d:'#ff3333', g:'none',                            s:'CHROME OR EDGE REQUIRED'}},
}};
function theme(k) {{
  const t=T[k]||T.boot;
  orb.style.background=t.d; orb.style.boxShadow=t.g; status.textContent=t.s;
}}

// ── WAVEFORM ────────────────────────────────────────────────────
function idle() {{
  bars.forEach((b,i)=>{{b.style.height=(4+Math.sin(i*0.55)*4)+'px';b.style.background='rgba(0,212,255,0.15)';}});
}}
function liveWave(stream) {{
  stopWave();
  audioCtx=new (window.AudioContext||window.webkitAudioContext)();
  const an=audioCtx.createAnalyser(); an.fftSize=128;
  audioCtx.createMediaStreamSource(stream).connect(an);
  const data=new Uint8Array(an.frequencyBinCount);
  (function fr() {{
    an.getByteFrequencyData(data);
    bars.forEach((b,i)=>{{
      const v=data[Math.floor(i*data.length/bars.length)];
      b.style.height=Math.max(4,(v/255)*36)+'px';
      b.style.background='rgba(139,92,246,'+(0.35+v/550)+')';
    }});
    rafId=requestAnimationFrame(fr);
  }})();
}}
function speakWave() {{
  let t=0;
  if(rafId) cancelAnimationFrame(rafId);
  (function fr() {{
    t+=0.12;
    bars.forEach((b,i)=>{{
      b.style.height=(5+Math.abs(Math.sin(t+i*0.38))*30)+'px';
      b.style.background='rgba('+(Math.round(192+Math.sin(t+i*0.5)*40))+',24,58,0.8)';
    }});
    if(isSpeaking) rafId=requestAnimationFrame(fr); else idle();
  }})();
}}
function stopWave() {{
  if(rafId){{cancelAnimationFrame(rafId);rafId=null;}}
  if(audioCtx){{audioCtx.close().catch(()=>{{}});audioCtx=null;}}
  idle();
}}

// ── CHIME ───────────────────────────────────────────────────────
function chime() {{
  try {{
    const ctx=new (window.AudioContext||window.webkitAudioContext)();
    [[440,0],[554,0.1],[659,0.2],[880,0.3]].forEach(function(fd) {{
      const o=ctx.createOscillator(),g=ctx.createGain();
      o.type='sine'; o.frequency.value=fd[0];
      o.connect(g); g.connect(ctx.destination);
      g.gain.setValueAtTime(0,ctx.currentTime+fd[1]);
      g.gain.linearRampToValueAtTime(0.18,ctx.currentTime+fd[1]+0.05);
      g.gain.linearRampToValueAtTime(0,ctx.currentTime+fd[1]+0.3);
      o.start(ctx.currentTime+fd[1]); o.stop(ctx.currentTime+fd[1]+0.35);
    }});
  }} catch(e) {{}}
}}

// ── TTS (runs in THIS iframe - same frame as ORB, so cancel() works) ──
function speak(text) {{
  if(!window.speechSynthesis || !text || !text.trim()) return;
  window.speechSynthesis.cancel();
  isSpeaking=true;
  theme('speaking'); speakWave();
  tbox.innerHTML='<span style="color:#c0183a;">&#9654; SPEAKING &mdash; TAP ORB TO STOP</span>';

  const u=new SpeechSynthesisUtterance(text.trim());
  u.rate=0.88; u.pitch=0.72; u.volume=1.0;

  function go() {{
    const vs=window.speechSynthesis.getVoices();
    const pick=
      vs.find(function(v){{return v.name==='Google UK English Male';}}) ||
      vs.find(function(v){{return v.name.includes('Daniel');}}) ||
      vs.find(function(v){{return v.name.includes('David');}}) ||
      vs.find(function(v){{return v.lang==='en-GB';}}) ||
      vs.find(function(v){{return v.lang.startsWith('en');}});
    if(pick) u.voice=pick;
    u.onend=u.onerror=function() {{
      isSpeaking=false; idle(); theme('wake');
      tbox.innerHTML='Say <strong style="color:#00ffff;">HEY JARVIS</strong> to continue...';
      setTimeout(startWake,400);
    }};
    window.speechSynthesis.speak(u);
  }}

  if(window.speechSynthesis.getVoices().length) go();
  else window.speechSynthesis.onvoiceschanged=go;
}}

// ── ORB INTERRUPT - cancel in same frame ─────────────────────────
window.orbInterrupt=function() {{
  if(isSpeaking) {{
    window.speechSynthesis.cancel();
    isSpeaking=false;
    stopWave(); theme('interrupt');
    tbox.innerHTML='Interrupted. Say <strong style="color:#00ffff;">HEY JARVIS</strong>...';
    setTimeout(startWake,400);
  }}
}};

// ── AUTO-SPEAK: detect new TTS via localStorage seq comparison ───
(function checkTTS() {{
  const SKEY='jv_tts_seq';
  const lastSeq=parseInt(localStorage.getItem(SKEY)||'0',10);
  if(TTS_TEXT && TTS_SEQ>0 && TTS_SEQ!==lastSeq) {{
    localStorage.setItem(SKEY, TTS_SEQ);
    setTimeout(function(){{speak(TTS_TEXT);}}, 300);
  }}
}})();

// ── MIC ─────────────────────────────────────────────────────────
function getMic() {{
  return navigator.mediaDevices.getUserMedia({{
    audio:{{echoCancellation:true,noiseSuppression:true,autoGainControl:true}}
  }});
}}
function releaseMic() {{
  if(micStream){{micStream.getTracks().forEach(function(t){{t.stop();}});micStream=null;}}
  stopWave();
}}

// ── WAKE WORD LISTENER ──────────────────────────────────────────
function startWake() {{
  if(isWaking||isCommand||isSpeaking) return;
  if(!('webkitSpeechRecognition' in window)&&!('SpeechRecognition' in window)) {{
    theme('noapi'); tbox.textContent='Speech API requires Chrome or Edge.'; return;
  }}
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  wakeRec=new SR();
  wakeRec.continuous=true; wakeRec.interimResults=true;
  wakeRec.lang='en-US'; wakeRec.maxAlternatives=5;

  wakeRec.onstart=function() {{
    isWaking=true; theme('wake');
    tbox.innerHTML='Say <strong style="color:#00ffff;">HEY JARVIS</strong> to activate';
    idle();
  }};
  wakeRec.onresult=function(e) {{
    if(isCommand||isSpeaking) return;
    for(var i=e.resultIndex;i<e.results.length;i++) {{
      for(var j=0;j<e.results[i].length;j++) {{
        var h=e.results[i][j].transcript.toLowerCase().trim();
        if(h.includes('hey jarvis')||h.includes('ok jarvis')||
           (h.includes('jarvis')&&h.length<22)) {{
          try{{wakeRec.abort();}}catch(x){{}}
          onWake(); return;
        }}
      }}
    }}
  }};
  wakeRec.onerror=function(e) {{
    isWaking=false;
    if(['no-speech','aborted','network'].indexOf(e.error)>=0) setTimeout(startWake,500);
    else{{theme('error');setTimeout(startWake,2500);}}
  }};
  wakeRec.onend=function() {{
    isWaking=false;
    if(!isCommand&&!isSpeaking) setTimeout(startWake,350);
  }};
  try{{wakeRec.start();}}catch(e){{setTimeout(startWake,1000);}}
}}

function onWake() {{
  isWaking=false; theme('detected');
  tbox.textContent='Arc Reactor activated - speak your command...';
  chime(); setTimeout(startCmd,550);
}}

// ── COMMAND LISTENER ────────────────────────────────────────────
function startCmd() {{
  if(isCommand) return;
  isCommand=true; finalText='';
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  cmdRec=new SR();
  cmdRec.continuous=false; cmdRec.interimResults=true;
  cmdRec.lang='en-US'; cmdRec.maxAlternatives=1;

  cmdRec.onstart=function() {{
    theme('command'); tbox.textContent='Listening - speak now...';
    getMic().then(function(s){{micStream=s;liveWave(s);}}).catch(function(){{}});
    silTimer=setTimeout(function(){{try{{cmdRec.stop();}}catch(x){{}}}},8000);
  }};
  cmdRec.onresult=function(e) {{
    clearTimeout(silTimer);
    silTimer=setTimeout(function(){{try{{cmdRec.stop();}}catch(x){{}}}},3000);
    var interim=''; finalText='';
    for(var i=e.resultIndex;i<e.results.length;i++) {{
      if(e.results[i].isFinal) finalText+=e.results[i][0].transcript+' ';
      else interim+=e.results[i][0].transcript;
    }}
    tbox.textContent=(finalText||interim).trim()||'...';
  }};
  cmdRec.onerror=function(e) {{
    clearTimeout(silTimer); isCommand=false; releaseMic();
    if(e.error==='no-speech') {{
      tbox.innerHTML='Nothing heard. Say <strong style="color:#00ffff;">HEY JARVIS</strong> again.';
      theme('wake'); setTimeout(startWake,700);
    }} else {{theme('error');setTimeout(startWake,1800);}}
  }};
  cmdRec.onend=function() {{
    clearTimeout(silTimer); releaseMic(); isCommand=false;
    var cmd=finalText.trim();
    if(cmd.length>1) {{
      theme('thinking'); tbox.textContent=cmd;
      submitCmd(cmd);
    }} else {{
      tbox.innerHTML='Nothing captured. Say <strong style="color:#00ffff;">HEY JARVIS</strong>.';
      theme('wake'); setTimeout(startWake,700);
    }}
  }};
  try{{cmdRec.start();}}catch(e){{isCommand=false;setTimeout(startWake,1000);}}
}}

// ── SUBMIT: navigate parent URL -> Streamlit detects ?vc= and reruns ──
function submitCmd(text) {{
  var enc=encodeURIComponent(text), ts=Date.now().toString();
  try {{
    var u=new URL(window.parent.location.href);
    u.searchParams.set('vc',enc); u.searchParams.set('vts',ts);
    window.parent.location.href=u.toString();
  }} catch(e1) {{
    try {{
      var u2=new URL(window.location.href);
      u2.searchParams.set('vc',enc); u2.searchParams.set('vts',ts);
      window.location.href=u2.toString();
    }} catch(e2) {{}}
  }}
}}

// ── BOOT ────────────────────────────────────────────────────────
theme('boot'); idle();
setTimeout(startWake,1000);
</script>
</body>
</html>"""

    components.html(voice_html, height=195, scrolling=False)

    # ── CHAT HISTORY ──────────────────────────────────────────────
    TYPE_TO_ROLE = {"human": "user", "ai": "assistant"}
    for msg in st.session_state.chat_history.messages:
        role = TYPE_TO_ROLE.get(msg.type, msg.type)
        with st.chat_message(role):
            st.write(msg.content)

    # ── HANDLE INPUT ──────────────────────────────────────────────
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

        # Clean for TTS - remove ALL symbols that break speech
        clean_tts = (
            output_text
            .replace('"', " ").replace("'", " ").replace("`", " ")
            .replace("\\", " ").replace("\n", ". ").replace("\r", " ")
            .replace("#", " ").replace("*", " ").replace("_", " ")
            .replace("|", ", ").replace("[", "").replace("]", "")
            .replace("(", "").replace(")", "").replace("{", "").replace("}", "")
            .strip()
        )
        # Collapse multiple spaces
        import re
        clean_tts = re.sub(r'\s+', ' ', clean_tts)[:900]

        st.session_state.tts_text = clean_tts
        st.session_state.tts_seq += 1

        st.session_state.chat_history.add_user_message(user_query)
        st.session_state.chat_history.add_ai_message(output_text)

# ================================================================
# TAB 2: MUSIC STATION
# Full songs via YouTube IFrame API (no 30s limit, all languages)
# User searches -> results appear -> click to play full song in player
# ================================================================
with tab_music:
    music_html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;900&family=Share+Tech+Mono&family=Rajdhani:wght@400;600&display=swap');
*{box-sizing:border-box;margin:0;padding:0;}
html,body{background:transparent;font-family:'Rajdhani',sans-serif;color:#a8d4e8;height:100%;}

#mp{
  background:linear-gradient(160deg,rgba(4,15,30,0.98),rgba(6,0,30,0.99));
  border:1px solid rgba(0,212,255,0.2); border-radius:8px;
  padding:18px 20px; position:relative; overflow:hidden;
}
#mp::before{
  content:'';position:absolute;top:0;left:-100%;width:50%;height:1px;
  background:linear-gradient(90deg,transparent,#00d4ff,transparent);
  animation:scan2 5s linear infinite;
}
@keyframes scan2{to{left:200%;}}
.corn{position:absolute;width:10px;height:10px;border-color:rgba(0,212,255,0.4);border-style:solid;}
.tl{top:0;left:0;border-width:1px 0 0 1px;}.tr{top:0;right:0;border-width:1px 1px 0 0;}
.bl{bottom:0;left:0;border-width:0 0 1px 1px;}.br{bottom:0;right:0;border-width:0 1px 1px 0;}

h2{font-family:'Orbitron',monospace;font-size:0.85rem;color:rgba(0,212,255,0.7);letter-spacing:0.3em;margin-bottom:4px;text-transform:uppercase;}
.api-note{font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:rgba(0,212,255,0.35);margin-bottom:14px;}

/* PLAYER */
#player-wrap{
  background:rgba(0,0,0,0.4);border:1px solid rgba(0,212,255,0.15);
  border-radius:6px;margin-bottom:14px;overflow:hidden;
  display:none; position:relative;
}
#yt-player{width:100%;height:220px;display:block;}
#np-bar{
  display:flex;align-items:center;gap:10px;padding:10px 14px;
  background:rgba(0,212,255,0.04);border-top:1px solid rgba(0,212,255,0.1);
}
#np-title{
  font-family:'Share Tech Mono',monospace;font-size:0.78rem;
  color:#00d4ff;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}
#np-badge{
  font-family:'Orbitron',monospace;font-size:0.5rem;letter-spacing:0.15em;
  color:rgba(0,212,255,0.5);background:rgba(0,212,255,0.08);
  border:1px solid rgba(0,212,255,0.2);border-radius:2px;padding:2px 6px;white-space:nowrap;
}

/* SEARCH */
.srow{display:flex;gap:8px;margin-bottom:14px;}
#sq{
  flex:1;background:rgba(0,212,255,0.05);border:1px solid rgba(0,212,255,0.25);
  border-radius:4px;color:#00d4ff;font-family:'Share Tech Mono',monospace;
  font-size:0.88rem;padding:8px 12px;outline:none;
}
#sq:focus{border-color:#00d4ff;box-shadow:0 0 12px rgba(0,212,255,0.15);}
#sq::placeholder{color:rgba(0,212,255,0.3);}
#sbtn{
  background:rgba(0,212,255,0.08);border:1px solid rgba(0,212,255,0.3);
  color:#00d4ff;font-family:'Orbitron',monospace;font-size:0.6rem;
  letter-spacing:0.1em;padding:8px 14px;border-radius:4px;cursor:pointer;transition:all 0.2s;
}
#sbtn:hover{background:rgba(0,212,255,0.15);box-shadow:0 0 10px rgba(0,212,255,0.2);}

/* PRESETS */
#presets{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:14px;}
.preset{
  background:rgba(0,212,255,0.05);border:1px solid rgba(0,212,255,0.18);
  color:rgba(0,212,255,0.65);font-family:'Share Tech Mono',monospace;
  font-size:0.67rem;padding:4px 9px;border-radius:12px;cursor:pointer;transition:all 0.15s;
}
.preset:hover{background:rgba(0,212,255,0.12);border-color:rgba(0,212,255,0.4);color:#00d4ff;}

/* RESULTS */
#status-msg{font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:rgba(0,212,255,0.5);text-align:center;padding:8px 0;}
#results{display:none;}
.ritem{
  display:flex;align-items:center;gap:10px;padding:7px 8px;border-radius:4px;
  cursor:pointer;transition:background 0.15s;border-bottom:1px solid rgba(0,212,255,0.06);
}
.ritem:hover{background:rgba(0,212,255,0.08);}
.ritem.active{background:rgba(0,212,255,0.12);border-left:2px solid #00d4ff;}
.rthumb{width:48px;height:36px;border-radius:3px;object-fit:cover;flex-shrink:0;background:rgba(0,0,0,0.4);}
.rinfo{flex:1;min-width:0;}
.rtitle{font-family:'Rajdhani',sans-serif;font-size:0.85rem;color:rgba(0,212,255,0.85);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.rchan{font-family:'Share Tech Mono',monospace;font-size:0.65rem;color:rgba(0,212,255,0.45);}
.rdur{font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:rgba(0,212,255,0.35);flex-shrink:0;}
.play-icon{width:28px;height:28px;border:1px solid rgba(0,212,255,0.3);border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;color:rgba(0,212,255,0.6);font-size:0.7rem;transition:all 0.15s;}
.ritem:hover .play-icon{background:rgba(0,212,255,0.1);color:#00d4ff;border-color:#00d4ff;}
</style>
</head>
<body>
<div id="mp">
  <div class="corn tl"></div><div class="corn tr"></div>
  <div class="corn bl"></div><div class="corn br"></div>

  <h2>&#127925; JARVIS MUSIC STATION</h2>
  <div class="api-note">Full songs via YouTube &mdash; All languages including Telugu, Hindi, Tamil, Kannada, Global</div>

  <!-- YouTube Player -->
  <div id="player-wrap">
    <div id="yt-player"></div>
    <div id="np-bar">
      <span id="np-title">No track selected</span>
      <span id="np-badge">&#9654; PLAYING</span>
    </div>
  </div>

  <!-- Genre Presets -->
  <div id="presets">
    <span class="preset" onclick="doSearch('top hits songs 2024')">&#128293; Top Hits</span>
    <span class="preset" onclick="doSearch('Arijit Singh best songs')">&#127988; Arijit Singh</span>
    <span class="preset" onclick="doSearch('Sid Sriram Telugu songs')">&#127873; Telugu</span>
    <span class="preset" onclick="doSearch('Anirudh Ravichander Tamil hits')">&#9733; Tamil</span>
    <span class="preset" onclick="doSearch('Kannada songs hits 2024')">&#127774; Kannada</span>
    <span class="preset" onclick="doSearch('AR Rahman best songs')">&#127775; AR Rahman</span>
    <span class="preset" onclick="doSearch('SPB SP Balasubrahmanyam songs')">&#9654; SPB Hits</span>
    <span class="preset" onclick="doSearch('lo-fi hip hop music')">&#128247; Lo-Fi</span>
    <span class="preset" onclick="doSearch('jazz instrumental music')">&#127928; Jazz</span>
    <span class="preset" onclick="doSearch('The Weeknd best songs')">&#11088; The Weeknd</span>
    <span class="preset" onclick="doSearch('classical piano music')">&#127929; Classical</span>
    <span class="preset" onclick="doSearch('electronic music 2024')">&#9889; Electronic</span>
  </div>

  <!-- Search -->
  <div class="srow">
    <input id="sq" type="text" placeholder="Search any song, artist, album, language..." />
    <button id="sbtn" onclick="doSearch()">&#128269; SEARCH</button>
  </div>

  <div id="status-msg">Search for music or tap a genre above to start</div>
  <div id="results"></div>
</div>

<!-- YouTube IFrame API -->
<script src="https://www.youtube.com/iframe_api"></script>
<script>
(function() {
  var ytPlayer = null;
  var ytReady  = false;
  var pendingId = null;
  var currentIdx = -1;
  var videoList  = [];

  var sq       = document.getElementById('sq');
  var statusEl = document.getElementById('status-msg');
  var resultsEl= document.getElementById('results');
  var playerWrap=document.getElementById('player-wrap');
  var npTitle  = document.getElementById('np-title');

  sq.addEventListener('keydown', function(e){ if(e.key==='Enter') doSearch(); });

  // YouTube IFrame API ready callback
  window.onYouTubeIframeAPIReady = function() {
    ytReady = true;
    ytPlayer = new YT.Player('yt-player', {
      height: '220',
      width:  '100%',
      playerVars: {
        autoplay: 0, controls: 1, rel: 0,
        modestbranding: 1, fs: 1, iv_load_policy: 3
      },
      events: {
        onReady: function() {
          if(pendingId) { playVideo(pendingId, pendingId); pendingId=null; }
        },
        onStateChange: function(e) {
          if(e.data === YT.PlayerState.ENDED) {
            // Auto next
            if(currentIdx+1 < videoList.length) {
              currentIdx++;
              var v=videoList[currentIdx];
              playVideo(v.id, v.title);
              highlightActive();
            }
          }
        }
      }
    });
  };

  function playVideo(videoId, title) {
    playerWrap.style.display = 'block';
    npTitle.textContent = title || 'Playing...';
    if(ytReady && ytPlayer && ytPlayer.loadVideoById) {
      ytPlayer.loadVideoById(videoId);
    } else {
      pendingId = videoId;
    }
  }

  function highlightActive() {
    Array.from(resultsEl.querySelectorAll('.ritem')).forEach(function(el, i) {
      el.classList.toggle('active', i === currentIdx);
    });
  }

  // YouTube Data API v3 - free, CORS-open for search
  window.doSearch = function(q) {
    var query = q || sq.value.trim();
    if(!query) return;
    sq.value = query;
    statusEl.textContent = 'Scanning YouTube catalog...';
    resultsEl.innerHTML = ''; resultsEl.style.display='none';

    // Use YouTube oEmbed + noembed as a free search proxy
    // Primary: invidious public API (open source YouTube frontend, no key needed)
    var apis = [
      'https://invidious.io.lol/api/v1/search?q='+encodeURIComponent(query)+'&type=video&page=1',
      'https://yt.dragongoaway.net/api/v1/search?q='+encodeURIComponent(query)+'&type=video&page=1',
      'https://invidious.privacydev.net/api/v1/search?q='+encodeURIComponent(query)+'&type=video&page=1'
    ];

    tryApi(apis, 0, query);
  };

  function tryApi(apis, idx, query) {
    if(idx >= apis.length) {
      // All failed - show fallback search link
      statusEl.textContent = '';
      resultsEl.style.display = 'block';
      resultsEl.innerHTML =
        '<div style="text-align:center;padding:20px;font-family:Share Tech Mono,monospace;font-size:0.75rem;color:rgba(0,212,255,0.5);">' +
        'Direct YouTube search: <br><br>' +
        '<a href="https://www.youtube.com/results?search_query='+encodeURIComponent(query)+'" ' +
        'target="_blank" style="color:#00d4ff;text-decoration:none;font-size:0.85rem;">&#128269; Open YouTube: '+query+'</a>' +
        '<br><br><span style="font-size:0.65rem;color:rgba(0,212,255,0.35);">Tip: Copy the video ID and paste below to play directly</span>' +
        '<br><br><div style="display:flex;gap:8px;justify-content:center;margin-top:8px;">' +
        '<input id="vidid" placeholder="Paste YouTube video ID..." style="background:rgba(0,212,255,0.05);border:1px solid rgba(0,212,255,0.3);border-radius:4px;color:#00d4ff;font-family:Share Tech Mono,monospace;font-size:0.8rem;padding:6px 10px;outline:none;width:200px;"/>' +
        '<button onclick="playDirectId()" style="background:rgba(0,212,255,0.1);border:1px solid rgba(0,212,255,0.3);color:#00d4ff;font-family:Orbitron,monospace;font-size:0.55rem;letter-spacing:0.1em;padding:6px 12px;border-radius:4px;cursor:pointer;">PLAY</button>' +
        '</div></div>';
      return;
    }

    fetch(apis[idx])
      .then(function(r){ return r.json(); })
      .then(function(data){
        var videos = Array.isArray(data) ? data : (data.videos || data.items || []);
        var filtered = videos.filter(function(v){
          return (v.type==='video'||v.videoId||v.id) && (v.title||v.snippet);
        }).slice(0,15);

        if(filtered.length === 0) { tryApi(apis, idx+1, query); return; }

        videoList = filtered.map(function(v){
          var vid = v.videoId || (v.id && v.id.videoId) || v.id || '';
          var title = v.title || (v.snippet && v.snippet.title) || 'Unknown';
          var chan = v.author || v.authorId || (v.snippet&&v.snippet.channelTitle) || '';
          var dur = v.lengthSeconds ? fmtSec(parseInt(v.lengthSeconds)) : '';
          var thumb = v.videoThumbnails
            ? (v.videoThumbnails[2]||v.videoThumbnails[0]||{}).url||''
            : (v.snippet&&v.snippet.thumbnails&&(v.snippet.thumbnails.medium||v.snippet.thumbnails.default||{}).url)||
              'https://img.youtube.com/vi/'+vid+'/mqdefault.jpg';
          return {id:vid, title:title, channel:chan, dur:dur, thumb:thumb};
        });

        renderResults();
        statusEl.textContent = '';
      })
      .catch(function(){ tryApi(apis, idx+1, query); });
  }

  function renderResults() {
    resultsEl.innerHTML = ''; resultsEl.style.display='block';
    videoList.forEach(function(v, i) {
      var div=document.createElement('div');
      div.className='ritem'+(i===currentIdx?' active':'');
      div.innerHTML=
        '<img class="rthumb" src="'+v.thumb+'" onerror="this.src=\'https://img.youtube.com/vi/'+v.id+'/mqdefault.jpg\'" loading="lazy"/>'+
        '<div class="rinfo">'+
          '<div class="rtitle">'+escHtml(v.title)+'</div>'+
          '<div class="rchan">'+escHtml(v.channel)+'</div>'+
        '</div>'+
        (v.dur?'<span class="rdur">'+v.dur+'</span>':'')+
        '<div class="play-icon">&#9654;</div>';
      div.onclick=(function(idx){ return function(){
        currentIdx=idx; playVideo(videoList[idx].id, videoList[idx].title); highlightActive();
      };})(i);
      resultsEl.appendChild(div);
    });
  }

  window.playDirectId=function(){
    var id=(document.getElementById('vidid')||{}).value||'';
    id=id.trim();
    if(!id) return;
    // Extract ID from full URL if pasted
    var m=id.match(/(?:v=|youtu\.be\/|embed\/)([a-zA-Z0-9_-]{11})/);
    if(m) id=m[1];
    if(id.length===11) playVideo(id, 'Custom video');
  };

  function fmtSec(s){
    var h=Math.floor(s/3600),m=Math.floor((s%3600)/60),sec=s%60;
    if(h>0) return h+':'+pad(m)+':'+pad(sec);
    return m+':'+pad(sec);
  }
  function pad(n){return n<10?'0'+n:String(n);}
  function escHtml(t){
    return String(t||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  // Auto-load default
  window.doSearch('Arijit Singh best Bollywood songs');
})();
</script>
</body>
</html>"""
    components.html(music_html, height=860, scrolling=True)
