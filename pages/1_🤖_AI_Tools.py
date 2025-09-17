import streamlit as st
import datetime
import json
import time
import base64
from io import StringIO
import os
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
import google.generativeai as genai
from PIL import Image
import pandas as pd
import plotly.express as px
from streamlit_calendar import calendar

# --- Gemini AI Config ---
try:
    genai.configure(api_key=st.secrets.get("GEMINI_API_KEY", None))
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
except Exception as e:
    st.sidebar.error(f"Gemini setup failed: {e}")
    model = None

# =================================================================================================
# HELPER FUNCTIONS
# =================================================================================================
import base64
import streamlit as st

def add_bg_from_local(image_file):
    with open(image_file, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: url("data:image/png;base64,{encoded}");
            background-size: contain;
            background-repeat: repeat;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Example usage
add_bg_from_local("M.jpg")

def save_timetable(username, data):
    user_timetables_dir = os.path.join("user_timetables")
    if not os.path.exists(user_timetables_dir):
        os.makedirs(user_timetables_dir)
    file_path = os.path.join(user_timetables_dir, f"{username}.json")
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def load_timetable(username):
    user_timetables_dir = os.path.join("user_timetables")
    file_path = os.path.join(user_timetables_dir, f"{username}.json")
    today_str = str(datetime.date.today())
    time_slots = [f"{h:02d}:00" for h in range(0, 24)]
    fresh_timetable = pd.DataFrame(columns=["Activity"], index=time_slots)
    fresh_timetable["Activity"] = ""
    if not os.path.exists(file_path):
        return fresh_timetable
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            if data.get("date") == today_str:
                return pd.read_json(data["timetable_json"], orient='split')
            else:
                return fresh_timetable
    except (FileNotFoundError, json.JSONDecodeError):
        return fresh_timetable

def save_plan(username, plan_data):
    user_plans_dir = os.path.join("user_plans")
    if not os.path.exists(user_plans_dir):
        os.makedirs(user_plans_dir)
    with open(os.path.join(user_plans_dir, f"{username}.json"), "w") as f:
        json.dump(plan_data, f, indent=4)

def load_plan(username):
    user_plans_dir = os.path.join("user_plans")
    user_plan_file = os.path.join(user_plans_dir, f"{username}.json")
    if not os.path.exists(user_plan_file):
        return []
    try:
        with open(user_plan_file, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

def create_priority_chart(priority_level, plan, theme_colors):
    tasks = [t for t in plan if t.get('priority') == priority_level]
    if not tasks:
        return None
    completed = len([t for t in tasks if t.get('done', False)])
    not_completed = len(tasks) - completed
    df = pd.DataFrame({'Status': ['Completed', 'Not Completed'], 'Count': [completed, not_completed]})
    fig = px.pie(
        df,
        values='Count',
        names='Status',
        title=f'{priority_level} Priority Tasks',
        color_discrete_map={'Completed':'#007bff', 'Not Completed':'#6c757d'} 
    )
    fig.update_traces(textposition='inside', textinfo='percent+label', hole=.3)
    fig.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color=theme_colors.get("text", "black"))
    return fig

def get_user_chat_dir(username):
    user_chat_dir = os.path.join("chats", username)
    if not os.path.exists(user_chat_dir):
        os.makedirs(user_chat_dir)
    return user_chat_dir

def save_chat_history(username, chat_history, filename):
    user_chat_dir = get_user_chat_dir(username)
    with open(os.path.join(user_chat_dir, filename), "w") as f:
        json.dump(chat_history, f, indent=4)

def load_chat_history(username, filename):
    user_chat_dir = get_user_chat_dir(username)
    try:
        with open(os.path.join(user_chat_dir, filename), "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def delete_chat_history(username, filename):
    user_chat_dir = get_user_chat_dir(username)
    file_path = os.path.join(user_chat_dir, filename)
    if os.path.exists(file_path):
        os.remove(file_path)

# =================================================================================================
# COLOR THEME LOGIC
# =================================================================================================
COLOR_THEMES = {
    "⚪ Light": {"primary": "#000000", "background": "#000000", "secondary_bg": "#000000", "text": "#FFFFFF"},
    "⚫ Dark": {"primary": "#FFFFFF", "background": "#FFFFFF", "secondary_bg": "#FFFFFF", "text": "#000000"},
    "🔵 Blue": {"primary": "#FFFFFF", "background": "#1FFFFF", "secondary_bg": "#FFFFFF", "text": "#1F618D"},
    "🟢 Green": {"primary": "#FFFFFF", "background": "#145A32", "secondary_bg": "#1E8449", "text": "#1E8449"},
    "🩷 Pink": {"primary": "#FFFFFF", "background": "#880E4F", "secondary_bg": "#C2185B", "text": "#C2185B"},
    "🩵 Light Blue": {"primary": "#000000", "background": "#E1F5FE", "secondary_bg": "#B3E5FC", "text": "#01579B"},
    "💜 Lavender": {"primary": "#FFFFFF", "background": "#4A148C", "secondary_bg": "#6A1B9A", "text": "#6A1B9A"},
    "💛 Yellow": {"primary": "#000000", "background": "#FFFDE7", "secondary_bg": "#FFF9C4", "text": "#F57F17"},
}
def apply_color_theme(theme_name, theme_colors):
    css = f"""
    <style>
        .stApp {{
            background-color: {theme_colors["background"]};
            color: {theme_colors["text"]};
        }}
        .st-emotion-cache-16txtl3 {{
            background-color: {theme_colors["secondary_bg"]};
        }}
        .stButton>button, .stDownloadButton>button {{
            background-color: {theme_colors["primary"]}; 
            color: {theme_colors["background"]};
            border: 1px solid {theme_colors["background"]};
        }}
        h1, h2, h3, h4, h5, h6, p, li, label {{ 
            color: {theme_colors["text"]} !important; 
        }}
        .st-emotion-cache-16txtl3 h1, 
        .st-emotion-cache-16txtl3 h2, 
        .st-emotion-cache-16txtl3 h3, 
        .st-emotion-cache-16txtl3 p, 
        .st-emotion-cache-16txtl3 b, 
        .st-emotion-cache-16txtl3 strong {{ 
            color: {theme_colors["primary"]} !important; 
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)



if "selected_theme_emoji" not in st.session_state:
    st.session_state.selected_theme_emoji = "Pink"
st.sidebar.write("Choose a theme:")
cols = st.sidebar.columns(5)
col_index = 0
for emoji_and_name, colors in COLOR_THEMES.items():
    with cols[col_index]:
        if st.button(emoji_and_name.split(" ")[0], use_container_width=True, key=f"theme_{emoji_and_name}"):
            st.session_state.selected_theme_emoji = emoji_and_name
            st.rerun()
    col_index = (col_index + 1) % 5
selected_theme_colors = COLOR_THEMES.get(st.session_state.selected_theme_emoji, COLOR_THEMES["⚪ Light"])
# Apply the selected theme using both the name and the colors
apply_color_theme(st.session_state.selected_theme_emoji, selected_theme_colors)


# =================================================================================================
# --- MAIN APP ---
# =================================================================================================
if not st.session_state.get("logged_in", False):
    st.warning("Please log in from the Home page to use the application.")
    st.stop()
username = st.session_state.get("username", "default_user").strip()

# --- Google Calendar Config ---
service = None
try:
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    # This line now reads the credentials from Streamlit's secrets manager
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["google_credentials"], scopes=SCOPES
    )

    service = build('calendar', 'v3', credentials=creds)
    st.sidebar.success("Connected to Google Calendar.")
except Exception:
    st.sidebar.error("Google Calendar not configured for deployment.")

# --- SESSION STATE INITIALIZATION ---
if "plan" not in st.session_state:
    st.session_state.plan = load_plan(username)
if 'active_chat' not in st.session_state:
    st.session_state.active_chat = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = None

# --- SIDEBAR ---
st.sidebar.title(f"{username}'s Dashboard")
st.sidebar.subheader("Saved Conversations")
if st.sidebar.button("➕ New Chat"):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.active_chat = f"chat_{timestamp}.json"
    st.session_state.chat_history = []
    save_chat_history(username, [], st.session_state.active_chat)
    st.rerun()

try:
    user_chat_dir = get_user_chat_dir(username)
    chat_files = sorted([f for f in os.listdir(user_chat_dir) if f.endswith(".json")], reverse=True)
    for chat_file in chat_files:
        col1, col2 = st.sidebar.columns([0.8, 0.2])
        with col1:
            display_name = chat_file.replace("chat_", "").replace(".json", "").replace("_", " at ")
            if st.button(display_name, key=f"load_{chat_file}", use_container_width=True):
                st.session_state.active_chat = chat_file
                st.session_state.chat_history = load_chat_history(username, chat_file)
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"delete_{chat_file}", help=f"Delete chat {display_name}"):
                delete_chat_history(username, chat_file)
                if st.session_state.active_chat == chat_file:
                    st.session_state.active_chat = None
                    st.session_state.chat_history = []
                st.rerun()
except Exception as e:
    st.sidebar.error(f"Error loading chat files: {e}")
st.markdown("""
<style>
/* Only stretch the second column (calendar side) */
div[data-testid="stVerticalBlock"]:nth-of-type(2) {
    display: flex;
    flex-direction: column;
    height: 100vh; /* Full screen height */
}

/* Inside that column, let its content (calendar) expand */
div[data-testid="stVerticalBlock"]:nth-of-type(2) > div {
    flex: 1 1 auto;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)



# --- SIDEBAR CALENDAR ---
# Commented out the big sidebar calendar
# Add this to keep sidebar scroll
st.sidebar.markdown(
    """
    <div style="height: 800px;"></div>
    """,
    unsafe_allow_html=True
)  # Spacer to allow scrolling


# --- MAIN PAGE ---
planner_tab, assistant_tab = st.tabs(["🗓️ Study Planner", "🤖 AI Assistant"])

with planner_tab:
    st.header("Plan Your Week")
    col_left, col_right = st.columns([2 , 3])

    # LEFT COLUMN
    with col_left:
        with st.form("new_task_form", clear_on_submit=True):
            st.subheader("Add a New Study Task")
            task_date = st.date_input("Date", datetime.date.today())
            subject = st.text_input("Enter Subject")
            priority = st.selectbox("Priority", ["High", "Medium", "Low"])
            start_time = st.time_input("Start Time", datetime.time(9, 0))
            end_time = st.time_input("End Time", datetime.time(10, 0))
            submitted = st.form_submit_button("➕ Add to Plan & Calendar")

        if submitted and subject:
            new_task = {
                "date": str(task_date),
                "subject": subject,
                "priority": priority,
                "start": str(start_time),
                "end": str(end_time),
                "done": False
            }
            st.session_state.plan.append(new_task)
            save_plan(username, st.session_state.plan)

            # Google Calendar
            if service:
                start_time_str = start_time.strftime("%H:%M:%S")
                end_time_str = end_time.strftime("%H:%M:%S")
                event = {
                    'summary': f'[{priority}] Study: {subject}',
                    'start': {'dateTime': f'{task_date}T{start_time_str}', 'timeZone': 'Asia/Kolkata'},
                    'end': {'dateTime': f'{task_date}T{end_time_str}', 'timeZone': 'Asia/Kolkata'},
                    'reminders': {'useDefault': False, 'overrides': [{'method': 'popup', 'minutes': 10}]}
                }
                try:
                    service.events().insert(calendarId='primary', body=event).execute()
                    st.success(f"✅ Synced '{subject}' with Google Calendar.")
                except Exception as e:
                    st.error(f"Failed to add to Google Calendar. Error: {e}")

            st.success(f"Task '{subject}' added!")

        st.divider()
        tasks_to_display = [
            t for t in st.session_state.plan
            if t.get('date') == (st.session_state.selected_date or str(datetime.date.today()))
        ]
        st.subheader(f"📌 Today's Plan ({str(datetime.date.today())})")
        if not tasks_to_display:
            st.info("No tasks scheduled for this day.")
        else:
            for task in tasks_to_display:
                original_index = next((idx for idx, t in enumerate(st.session_state.plan) if t == task), None)
                if original_index is not None:
                    is_done = st.checkbox(
                        f"**{task['subject']}** ({task['priority']})",
                        key=f"task_{original_index}",
                        value=task.get('done', False)
                    )
                    if is_done != st.session_state.plan[original_index].get('done', False):
                        st.session_state.plan[original_index]['done'] = is_done
                        save_plan(username, st.session_state.plan)
                        st.rerun()

        # Overall Progress
        if st.session_state.plan:
            st.subheader("📊 Overall Progress (All Tasks)")
            completed_tasks = [task for task in st.session_state.plan if task.get('done', False)]
            if len(st.session_state.plan) > 0:
                st.progress(len(completed_tasks) / len(st.session_state.plan))
            st.write(f"Completed {len(completed_tasks)} / {len(st.session_state.plan)} total tasks")

        st.divider()
        st.header("🗓️ Daily Timetable")
        timetable_df = load_timetable(username)
        with st.expander("View and Edit Today's Timetable"):
            st.info("You can type directly into the 'Activity' column. Your changes are saved automatically.")
            edited_df = st.data_editor(timetable_df, use_container_width=True, height=561)
            if not edited_df.equals(timetable_df):
                today_str = str(datetime.date.today())
                timetable_json = edited_df.to_json(orient='split')
                data_to_save = {"date": today_str, "timetable_json": timetable_json}
                save_timetable(username, data_to_save)
                st.success("Timetable saved!")

    # RIGHT COLUMN
    # RIGHT COLUMN
with col_right:
    st.header("📅 Your Calendar")
    calendar_events = []
    for idx, task in enumerate(st.session_state.plan):
        # Determine color based on completion
        color = "green" if task.get("done", False) else "red"
        # Add task to calendar, only title (no start/end times)
        calendar_events.append({
            "id": str(idx),
            "title": task.get("subject"),
            "start": task.get("date"),
            "color": color
        })

    clicked_event = calendar(events=calendar_events, key=f"calendar_{len(calendar_events)}")
    if clicked_event and "event" in clicked_event:
        event_id = int(clicked_event["event"]["id"])
        task = st.session_state.plan[event_id]
        # Checkbox to toggle completion
        is_done = st.sidebar.checkbox(
            f"{task['subject']} ({task['date']})",
            value=task.get("done", False),
            key=f"calendar_task_{event_id}"
        )
        if is_done != task.get("done", False):
            st.session_state.plan[event_id]["done"] = is_done
            save_plan(username, st.session_state.plan)
            st.rerun()


# --- AI ASSISTANT TAB ---
with assistant_tab:
    st.header("Your Doubt-Solving Bestie!")
    if st.session_state.active_chat:
        st.caption(f"Continuing chat: `{st.session_state.active_chat.replace('.json', '')}`")
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["parts"])
        if model and (user_prompt := st.chat_input("What can I help you with?")):
            st.session_state.chat_history.append({"role": "user", "parts": user_prompt})
            with st.chat_message("user"):
                st.markdown(user_prompt)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    chat = model.start_chat(history=st.session_state.chat_history)
                    response = chat.send_message(user_prompt)
                    st.markdown(response.text)
            st.session_state.chat_history.append({"role": "assistant", "parts": response.text})
            save_chat_history(username, st.session_state.chat_history, st.session_state.active_chat)
    else:
        st.info("To talk to the AI, start a '➕ New Chat' from the sidebar.")

