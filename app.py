import streamlit as st
import agent_core

st.set_page_config(page_title="Apex Hardware Stock Helper", page_icon="🔧")

st.title("🔧 Apex Hardware Stock Helper")
st.caption("Intelligent assistant for hardware stock lookups, restock calculations, and draft purchase orders.")
st.caption("🔒 Bring your own Gemini key. Your key stays in this browser session and is never saved or logged.")

st.sidebar.header("⚙️ Configuration")
api_key = st.sidebar.text_input(
    "Your Gemini API key",
    type="password",
    help="Get a free key at aistudio.google.com."
)

model_options = [
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-2.0-flash",
    "Custom model name..."
]
selected_model = st.sidebar.selectbox(
    "Gemini Model",
    model_options,
    index=0,
    help="Default is gemini-3.5-flash-lite. Select or type your active model."
)
if selected_model == "Custom model name...":
    model_name = st.sidebar.text_input("Enter model name", value="gemini-3.5-flash-lite")
else:
    model_name = selected_model

if st.sidebar.button("Clear chat"):
    st.session_state.pop("chat", None)
    st.session_state.pop("history", None)
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Notice & Safety:**\n"
    "- 📦 Read: hardware inventory\n"
    "- 🧮 Compute: restock & shipping cost\n"
    "- 📝 Draft: supplier inquiry note\n\n"
    "*Financial Disclaimer:* Cost calculations and draft purchase orders are for planning purposes only. "
    "This agent cannot place orders, dispatch emails, or execute payments."
)

if not api_key:
    st.info("👋 Welcome! Paste your Gemini API key in the sidebar to get started.")
    st.markdown("""
    ### What you can ask:
    - *"What hardware items are running low on stock?"*
    - *"Check stock for Rotary Hammer, calculate cost for 5 units with express shipping, and draft a PO note."*
    - *"How much would it cost to restock 10 units of Cordless Drill at $89.50 each?"*
    - *"Who supplies the safety goggles?"*
    """)
    st.stop()

if "chat" not in st.session_state:
    st.session_state.chat = []  # format: (role, text, steps, stopped)
if "history" not in st.session_state:
    st.session_state.history = []  # format: list of AnyMessage

cache_key = (api_key, model_name)
if st.session_state.get("graph_key") != cache_key:
    st.session_state.graph = agent_core.build_graph(agent_core.make_llm(api_key, model=model_name))
    st.session_state.graph_key = cache_key

for role, text, steps, stopped in st.session_state.chat:
    with st.chat_message(role):
        st.write(text)
        if steps:
            with st.expander(f"Agent steps ({len(steps)} tool call{'s' if len(steps) != 1 else ''})"):
                for number, s in enumerate(steps, 1):
                    st.markdown(f"**{number}. {s['tool']}** with `{s['args']}`")
                    st.caption(f"Result: {s['result'][:300]}")
        if stopped:
            st.warning("⚠️ The step limit stopped this run.")

question = st.chat_input("Ask about Apex Hardware stock or restock requests...")
if question:
    st.session_state.chat.append(("user", question, None, False))
    try:
        answer, steps, stopped, st.session_state.history = agent_core.run_agent(
            st.session_state.graph, st.session_state.history, question
        )
    except Exception as e:
        answer, steps, stopped = (
            f"Something went wrong ({type(e).__name__}: {e}). Check your key or selected model and try again.",
            [],
            False,
        )
    st.session_state.chat.append(("assistant", answer, steps, stopped))
    st.rerun()
