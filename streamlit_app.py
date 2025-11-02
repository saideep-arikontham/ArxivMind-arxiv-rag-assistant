import os
from typing import Dict, List

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ---- Model config ------------------------------------------------------------
RAW_MODELS = os.getenv(
    "AVAILABLE_MODELS",
    "llama3.2,moonshotai/kimi-k2-instruct-0905,deepseek-ai/deepseek-v3.1"
).split(",")

# Normalize provided list
AVAILABLE = [m.strip() for m in RAW_MODELS if m.strip()]

# Map concrete model ids to their provider label
MODEL_TO_PROVIDER = {
    "llama3.2": "Ollama (local)",
    "moonshotai/kimi-k2-instruct-0905": "NVIDIA NIM",
    "deepseek-ai/deepseek-v3.1": "NVIDIA NIM",
}

# Only show models we know how to route; if none match, fall back to all known
OPTIONS = [m for m in AVAILABLE if m in MODEL_TO_PROVIDER] or list(MODEL_TO_PROVIDER.keys())


# ---- Sidebar helpers ---------------------------------------------------------
def get_backend_url() -> str:
    """Return the configured backend URL, falling back to the env default."""
    default = os.getenv("BACKEND_URL", "http://localhost:8000")
    backend_url = st.session_state.get("backend_url", default).rstrip("/")
    input_value = st.sidebar.text_input("Backend URL", backend_url).rstrip("/")
    final_url = input_value or default
    st.session_state.backend_url = final_url
    st.sidebar.write(f"Using: `{final_url}`")
    return final_url


def get_model_choice() -> str:
    """
    Sidebar selector for the chat backend.
    Returns the provider label: 'Ollama (local)' or 'NVIDIA NIM'.
    """
    env_default = os.getenv("NVIDIA_NIM_DEFAULT_MODEL", OPTIONS[0]).strip()
    try:
        default_index = OPTIONS.index(env_default)
    except ValueError:
        default_index = 0

    # User picks a concrete model id; we translate to provider for routing
    selected_model_id = st.sidebar.selectbox(
        "Model / Provider",
        options=OPTIONS,
        index=default_index,
        help="Select which backend to send your chat to.",
    )

    provider_label = MODEL_TO_PROVIDER[selected_model_id]
    st.session_state.selected_model_id = selected_model_id
    st.session_state.selected_provider = provider_label
    return provider_label


# ---- UI helpers --------------------------------------------------------------
def render_history(messages: List[Dict[str, str]]) -> None:
    """Render the chat history in Streamlit's chat component."""
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


# ---- Networking --------------------------------------------------------------
def call_backend(backend_url: str, query: str, provider_label: str) -> str:
    """Send the prompt to the FastAPI backend and return its response string."""
    endpoint = "/chat_ollama" if provider_label == "Ollama (local)" else f"/chat_nvidia?model_name={st.session_state.get('selected_model_id','')}"
    url = f"{backend_url}{endpoint}"
    try:
        r = requests.post(url, json={"query": query}, timeout=300)
        r.raise_for_status()
        return (r.json() or {}).get("response", "")
    except requests.HTTPError as exc:
        text = exc.response.text if exc.response is not None else ""
        code = exc.response.status_code if exc.response is not None else "?"
        return f"HTTP {code} from {url}\n{text}"
    except requests.RequestException as exc:
        return f"Error contacting API at {url}: {exc}"
    except ValueError:
        return "Error: Backend returned non-JSON response."


# ---- App ---------------------------------------------------------------------
def main() -> None:
    st.set_page_config(page_title="ArxivMind Chat", page_icon="🧠")
    st.title("ArxivMind RAG Assistant")
    st.caption("Chat with the FastAPI-powered model (Ollama or NVIDIA NIM).")

    if "messages" not in st.session_state:
        st.session_state.messages = []  # type: ignore[attr-defined]

    with st.sidebar:
        backend_url = get_backend_url()
        provider_label = get_model_choice()
        picked_model = st.session_state.get("selected_model_id", "unknown")
        st.markdown(
            f"**Active backend:** `{backend_url}`  \n"
            f"**Provider:** `{provider_label}`  \n"
            f"**Model id:** `{picked_model}`"
        )

    render_history(st.session_state.messages)  # type: ignore[arg-type]

    prompt = st.chat_input("Ask a question about your research...")
    if not prompt:
        return

    # Record user message
    user_message = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_message)  # type: ignore[attr-defined]
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call selected backend
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown(f"_Querying **{provider_label}** backend..._")
        assistant_reply = call_backend(backend_url, prompt, provider_label)
        placeholder.markdown(assistant_reply or "_No response from backend._")

    # Record assistant reply
    st.session_state.messages.append(
        {"role": "assistant", "content": assistant_reply}
    )  # type: ignore[attr-defined]


if __name__ == "__main__":
    main()
