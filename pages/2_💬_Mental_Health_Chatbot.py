import streamlit as st
import time
import json
import os
import google.generativeai as genai
import base64

# =================================================================================================
# PAGE CONFIGURATION
# =================================================================================================
st.set_page_config(page_title="Friendly Study Companion", page_icon="🌱")

# =================================================================================================
# HELPER FUNCTIONS
# =================================================================================================
def get_user_chat_dir(username):
    user_chat_dir = os.path.join("chats", username)
    if not os.path.exists(user_chat_dir):
        os.makedirs(user_chat_dir)
    return user_chat_dir

def save_chat_history(username, chat_history):
    user_chat_dir = get_user_chat_dir(username)
    file_path = os.path.join(user_chat_dir, "mental_health_chat.json")
    with open(file_path, "w") as f:
        json.dump(chat_history, f, indent=4)

def load_chat_history(username):
    user_chat_dir = get_user_chat_dir(username)
    file_path = os.path.join(user_chat_dir, "mental_health_chat.json")
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# =================================================================================================
# COLOR THEME LOGIC
# =================================================================================================
COLOR_THEMES = {
    "⚪ Light": {"primary": "#000000", "background": "#FFFFFF", "secondary_bg": "#F0F2F6", "text": "#000000"},
    "⚫ Dark": {"primary": "#FFFFFF", "background": "#3B3E42", "secondary_bg": "#1C1C1C", "text": "#FFFFFF"},
    "🔵 Blue": {"primary": "#FFFFFF", "background": "#154360", "secondary_bg": "#1F618D", "text": "#1F618D"},
    "🟢 Green": {"primary": "#FFFFFF", "background": "#145A32", "secondary_bg": "#1E8449", "text": "#1E8449"},
    "🩷 Pink": {"primary": "#FFFFFF", "background": "#880E4F", "secondary_bg": "#C2185B", "text": "#C2185B"},
    "🩵 Light Blue": {"primary": "#000000", "background": "#E1F5FE", "secondary_bg": "#B3E5FC", "text": "#01579B"},
    "💜 Lavender": {"primary": "#FFFFFF", "background": "#4A148C", "secondary_bg": "#6A1B9A", "text": "#6A1B9A"},
    "💛 Yellow": {"primary": "#000000", "background": "#FFFDE7", "secondary_bg": "#FFF9C4", "text": "#F57F17"},
}

def set_chat_background(image_path):
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        encoded = base64.b64encode(data).decode()

        css = f"""
        <style>
            .stApp {{
                background: url("data:image/png;base64,{encoded}") repeat center center fixed;
                background-size: contain;
            }}
            .stChatMessage, .st-emotion-cache-16txtl3 {{
                background: rgba(0,0,0,0.5) !important;
                border-radius: 12px;
                padding: 10px;
            }}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"Background image '{image_path}' not found. Please check the file path.")

def apply_color_theme(theme_colors):
    css = f"""
    <style>
        .st-emotion-cache-16txtl3 {{ background-color: {theme_colors["secondary_bg"]}; }}
        .stButton>button, .stDownloadButton>button {{
            background-color: {theme_colors["primary"]}; color: {theme_colors["background"]};
            border: 1px solid {theme_colors["background"]};
        }}
        h1, h2, h3, h4, h5, h6, p, li, label {{ color: {theme_colors["text"]} !important; }}
        .st-emotion-cache-16txtl3 h1, .st-emotion-cache-16txtl3 h2, .st-emotion-cache-16txtl3 h3, 
        .st-emotion-cache-16txtl3 p, .st-emotion-cache-16txtl3 b, .st-emotion-cache-16txtl3 strong {{ 
            color: {theme_colors["primary"]} !important; 
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# =================================================================================================
# SIDEBAR STYLING
# =================================================================================================
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #FFFFFF, #16213e, #0f3460);
        color: white;
        border-radius: 20px;
        padding: 20px;
    }
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] h4 {
        color: #ffffff;
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
    }
    [data-testid="stSidebar"] button {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: white;
        border-radius: 12px;
        padding: 10px 15px;
        font-weight: 500;
        margin-bottom: 10px;
        transition: all 0.3s ease-in-out;
    }
    [data-testid="stSidebar"] button:hover {
        background: linear-gradient(90deg, #00c6ff, #0072ff);
        color: white;
        transform: scale(1.05);
    }
</style>
""", unsafe_allow_html=True)

# =================================================================================================
# THEME SELECTOR
# =================================================================================================
if "selected_theme_emoji" not in st.session_state:
    st.session_state.selected_theme_emoji = "⚪ Light"

st.sidebar.write("Choose a theme:")
cols = st.sidebar.columns(len(COLOR_THEMES))
col_index = 0
for emoji_and_name, colors in COLOR_THEMES.items():
    with cols[col_index]:
        btn_label = emoji_and_name.split(" ")[0]
        if st.button(btn_label, use_container_width=True, key=f"theme_{emoji_and_name}"):
            st.session_state.selected_theme_emoji = emoji_and_name
            st.rerun()
    col_index = (col_index + 1) % len(cols)

selected_theme_colors = COLOR_THEMES.get(st.session_state.selected_theme_emoji, COLOR_THEMES["⚪ Light"])
apply_color_theme(selected_theme_colors)
set_chat_background("night.jpg")

# =================================================================================================
# MAIN APP
# =================================================================================================
st.title("🌱 Your Friendly Study Companion")

# --- Check if user is logged in ---
if not st.session_state.get("logged_in", False):
    st.warning("Please log in from the Home page to use the application.")
    st.stop()
username = st.session_state.get("username", "default_user").strip()

# --- Gemini API Configuration ---
model = None
try:
    genai.configure(api_key=st.secrets.get("GEMINI_API_KEY", None))
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except Exception:
    st.error("Gemini API not configured. This feature is currently disabled.")
    st.stop()

# --- CHATBOT PERSONA ---
SYSTEM_PROMPT = """
You are a friendly, empathetic, and supportive AI companion for students. Your name is 'Pebble'.
Your purpose is to be a safe space for students to talk about their study-related stress, anxieties, and mental health challenges.
- Listen carefully and validate their feelings.
- Offer gentle, constructive advice and coping strategies (like the Pomodoro Technique, mindfulness exercises, or breaking down large tasks).
- Always be encouraging and positive.
- NEVER claim to be a real therapist or a replacement for professional help.
- If the user's problem seems serious or they mention severe distress, you MUST include the following disclaimer in your response: 
"I'm here to listen, but I'm an AI. If you're feeling overwhelmed, please consider talking to a trusted adult or a mental health professional. You are not alone."
"""

# --- Load history ---
if "mh_chat_history" not in st.session_state:
    st.session_state.mh_chat_history = load_chat_history(username)

# --- Layout Split ---
col_left, col_right = st.columns([2, 1])

# ---------------- LEFT COLUMN: Pebble Chat ----------------
with col_left:
    st.write("A safe space to talk about study stress and well-being.")
    st.divider()

    # Show old messages
    for message in st.session_state.mh_chat_history:
        avatar_icon = "🌱" if message["role"] == 'assistant' else "😊"
        with st.chat_message(message["role"], avatar=avatar_icon):
            st.markdown(message["parts"])

    # Welcome if empty
    if not st.session_state.mh_chat_history:
        welcome_message = "Hello! I'm Pebble, your friendly study companion. What's on your mind today? I'm here to listen."
        st.session_state.mh_chat_history.append({"role": "assistant", "parts": welcome_message})
        with st.chat_message("assistant", avatar="🌱"):
            st.markdown(welcome_message)
        save_chat_history(username, st.session_state.mh_chat_history)

    # User input
    if user_prompt := st.chat_input("Share your thoughts here..."):
        st.session_state.mh_chat_history.append({"role": "user", "parts": user_prompt})
        with st.chat_message("user", avatar="😊"):
            st.markdown(user_prompt)

        with st.chat_message("assistant", avatar="🌱"):
            with st.spinner("Pebble is thinking..."):
                full_history = [{"role": "user", "parts": SYSTEM_PROMPT}] + st.session_state.mh_chat_history
                chat = model.start_chat(history=full_history)
                response = chat.send_message(user_prompt)
                response_text = response.text
                st.markdown(response_text)

        st.session_state.mh_chat_history.append({"role": "assistant", "parts": response_text})
        save_chat_history(username, st.session_state.mh_chat_history)

# ---------------- RIGHT COLUMN: Extra Panel ----------------
with col_right:
    st.subheader("🗓️ Mood & Tools")

    mood = st.radio("How are you feeling today?", ["😊 Good", "😐 Okay", "😞 Bad"])
    if st.button("Save Mood"):
        st.success(f"Mood saved: {mood}")

    st.divider()

    st.subheader("🎮 Relax a bit")
    game_choice = st.radio("Play a game: ", ["Sudoku"])

    if game_choice == "Chess":
        st.markdown(
            """
            <iframe src="https://www.chess.com/play/computer"
            width="100%" height="500px" style="border:none;"></iframe>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <iframe src="https://sudoku.com"
            width="100%" height="500px" style="border:none;"></iframe>
            """,
            unsafe_allow_html=True
        )
