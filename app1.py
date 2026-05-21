import os
import streamlit as st
from langchain_anthropic.chat_models import ChatAnthropic
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from typing import Any

# --- 1. System Setup ---
st.set_page_config(page_title="Super Agent", page_icon="🤖", layout="wide")
st.title("🤖 My Advanced AI Assistant")

os.environ["ANTHROPIC_API_KEY"] = "your-api-key-here"


# --- 2. Define File Tools ---
@tool
def read_local_file(file_path: str) -> str:
    """Reads the content of a local text or code file. Input must be a valid file path string."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool
def write_local_file(file_path: str, content: str) -> str:
    """Writes or overwrites content into a local text file.
    Args:
        file_path: The path of the file to write to.
        content: The text content to write into the file.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


# --- 3. Build Agent ---
tools: list[Any] = [DuckDuckGoSearchRun(), read_local_file, write_local_file]

SYSTEM_PROMPT = (
    "You are an advanced desktop assistant. You can search the web for live data, "
    "read local files, and write text/data to files on command. "
    "If you successfully write a file, confirm the exact file name to the user."
)


@st.cache_resource
def build_agent() -> Any:
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        temperature=0.3,
    )
    return create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)


agent = build_agent()

# --- 4. Initialize Session Memory ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = InMemoryChatMessageHistory()

# --- 5. Render Chat Interface ---
TYPE_TO_ROLE: dict[str, str] = {"human": "user", "ai": "assistant"}

for message in st.session_state.chat_history.messages:
    role = TYPE_TO_ROLE.get(message.type, message.type)
    with st.chat_message(role):
        st.write(message.content)

# --- 6. Handle New User Input ---
if user_query := st.chat_input("Ask me anything, or tell me to read/write a file..."):
    with st.chat_message("user"):
        st.write(user_query)

    # Build full typed message history for the agent
    typed_history: list[HumanMessage | AIMessage] = [
        HumanMessage(content=str(m.content)) if m.type == "human"
        else AIMessage(content=str(m.content))
        for m in st.session_state.chat_history.messages
    ]
    typed_history.append(HumanMessage(content=user_query))

    with st.spinner("Thinking and executing tools..."):
        result: dict[str, Any] = agent.invoke({"messages": typed_history})
        output_text: str = str(result["messages"][-1].content)

    with st.chat_message("assistant"):
        st.write(output_text)

    st.session_state.chat_history.add_user_message(user_query)
    st.session_state.chat_history.add_ai_message(output_text)
