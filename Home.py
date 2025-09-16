import streamlit as st
import time
import base64
import json
import hashlib
from PIL import Image
from pathlib import Path


# =================================================================================================
# HELPER FUNCTIONS
# =================================================================================================
CWD = Path(__file__).resolve().parent
USERS_FILE = CWD / "users.json"
BG_IMAGE_FILE = CWD / "bg.gif"        # Login screen background
AGENT_IMAGE_FILE = CWD / "AiAgent.png"  # Login agent image
MAIN_BG_IMAGE_FILE = CWD / "M.jpg"      # Logged-in main page background


def get_base64_of_file(file_path):
    """Convert an image file to base64 string."""
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        st.warning(f"⚠️ File not found: {file_path}")
        return ""


def hash_password(password):
    """Hash a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()


def load_users():
    """Load users from JSON file."""
    if not USERS_FILE.exists():
        return {}
    with USERS_FILE.open("r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_users(users_data):
    """Save users to JSON file."""
    with USERS_FILE.open("w") as f:
        json.dump(users_data, f, indent=4)


# =================================================================================================
# PAGE CONFIGURATION & SESSION STATE
# =================================================================================================
st.set_page_config(page_title="Welcome to AI Study Buddy!", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'feature_index' not in st.session_state:
    st.session_state.feature_index = 0


# =================================================================================================
# LOGIN / SPLASH SCREEN VIEW
# =================================================================================================
if not st.session_state.logged_in:

    bg_image_base64 = get_base64_of_file(BG_IMAGE_FILE)
    agent_image_base64 = get_base64_of_file(AGENT_IMAGE_FILE)

    # --- Login screen background ---
    st.markdown(f"""
    <style>
        [data-testid="stSidebar"], header, footer {{ visibility: hidden; }}
        .stApp {{
            background-image: linear-gradient(rgba(0, 4, 40, 0.7), rgba(0, 4, 40, 0.7)), 
                              url("data:image/jpeg;base64,{bg_image_base64}");
            background-size: cover; 
            background-position: center;
        }}
        .main .block-container {{ padding-top: 5vh; }}
        h1, p, .st-emotion-cache-16txtl3 {{ color: white !important; }}
        .stTextInput > label {{ color: white !important; }}
        .stTabs [data-baseweb="tab"] p {{ color: white !important; }}
        .stTabs [data-baseweb="tab-list"] {{ justify-content: center; }}
        h1 {{ text-shadow: 2px 2px 4px black; }}
    </style>
    """, unsafe_allow_html=True)

    # --- Layout with Agent and Login/Sign-up tabs ---
    col_agent, col_auth = st.columns([1, 2])

    with col_agent:
        if agent_image_base64:
            st.markdown(
                f'<div style="text-align: center; padding-top: 50px;">'
                f'<img src="data:image/png;base64,{agent_image_base64}" alt="waving agent" width="300"></div>',
                unsafe_allow_html=True
            )

    with col_auth:
        st.title("Welcome to your AI Study Buddy! 🚀")
        st.write("Please log in or sign up to continue.")

        login_tab, signup_tab = st.tabs(["🔒 Login", "✍️ Sign Up"])

        # ---------------- LOGIN TAB ----------------
        with login_tab:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                login_button = st.form_submit_button("Login")

                if login_button:
                    username = username.strip()
                    password = password.strip()
                    users = load_users()

                    if username in users and users[username]['password_hash'] == hash_password(password):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.success("✅ Logged in successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Incorrect username or password.")

        # ---------------- SIGNUP TAB ----------------
        with signup_tab:
            with st.form("signup_form"):
                new_username = st.text_input("Choose a Username")
                new_password = st.text_input("Choose a Password", type="password")
                mobile_number = st.text_input("Mobile Number (for notifications)", placeholder="+91 1234567890")
                signup_button = st.form_submit_button("Sign Up")

                if signup_button:
                    users = load_users()
                    if new_username in users:
                        st.error("⚠️ Username already exists.")
                    elif not all([new_username, new_password, mobile_number]):
                        st.warning("⚠️ Please fill in all fields.")
                    else:
                        users[new_username] = {
                            'password_hash': hash_password(new_password),
                            'mobile_number': mobile_number
                        }
                        save_users(users)
                        st.session_state.logged_in = True
                        st.session_state.username = new_username
                        st.success("🎉 Account created! You are now logged in.")
                        time.sleep(1)
                        st.rerun()


# =================================================================================================
# MAIN APP VIEW (Shows AFTER the user is logged in)
# =================================================================================================
else:
    # ---- Page Background ----
    main_bg_base64 = get_base64_of_file(MAIN_BG_IMAGE_FILE)
    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpeg;base64,{main_bg_base64}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}
    </style>
    """, unsafe_allow_html=True)

    # ---- Features ----
    features = [
        {"title": "📚 Smart Study Planner", "desc": "Plan your daily tasks with AI assistance and stay on track."},
        {"title": "📊 Progress Charts", "desc": "Visualize completed vs pending tasks with charts."},
        {"title": "🗓️ Interactive Calendar", "desc": "Organize your schedule with an integrated calendar."},
        {"title": "🤖 AI Q&A Buddy", "desc": "Ask any question and get instant AI-powered answers."},
        {"title": "💡 Flashcards & Revision", "desc": "Quickly revise concepts with auto-generated flashcards."}
    ]

    colors = ["#2563eb", "#16a34a", "#ec4899", "#dc2626"]

    i = st.session_state.feature_index
    feature, color = features[i], colors[i % len(colors)]

    # ---- Flashcard CSS ----
    st.markdown(f"""
    <style>
    .flashcard {{
        background: linear-gradient(135deg, {color}, #1e293b);
        border-radius: 30px;
        padding: 50px;
        text-align: center;
        color: white;
        width: 50%;
        min-height: 50vh;
        margin: 2vh auto;

        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;

        box-shadow: 0px 20px 40px rgba(0,0,0,0.6), inset 0px 0px 20px rgba(255,255,255,0.2);
        transition: transform 0.8s ease, box-shadow 0.8s ease;
        transform-style: preserve-3d;
    }}

    .flashcard:hover {{
        transform: scale(1.05) rotateY(8deg) rotateX(8deg);
        box-shadow: 0px 30px 60px rgba(0,0,0,0.8), inset 0px 0px 30px rgba(255,255,255,0.3);
    }}

    .flashcard h2 {{
        font-size: 3rem;
        margin-bottom: 30px;
        text-shadow: 2px 2px 6px rgba(0,0,0,0.4);
    }}

    .flashcard p {{
        font-size: 1.5rem;
        line-height: 1.8;
        max-width: 800px;
    }}
    </style>

    <div id="flashcard" class="flashcard">
        <h2>{feature['title']}</h2>
        <p>{feature['desc']}</p>
    </div>
    """, unsafe_allow_html=True)

    # ---- Centered Skip Button ----
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("⏭️ Skip", use_container_width=True):
            if i < len(features) - 1:
                st.session_state.feature_index += 1
                st.rerun()
            else:
                st.session_state.show_dashboard = True
                st.rerun()

    # ---- Dashboard ----
    if st.session_state.get("show_dashboard", False):
      st.sidebar.success(f"👋 Welcome, {st.session_state.username}!")

      # White colored title
      st.markdown(
          "<h1 style='color: white;'>🎉 Welcome to your AI Study Buddy!</h1>",
          unsafe_allow_html=True
      )

      # White colored info text
      st.markdown(
          "<p style='color: black; font-size:18px;'>You're all set! Please choose a tool from the sidebar 👈</p>",
          unsafe_allow_html=True
      )
