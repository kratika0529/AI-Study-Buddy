import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import datetime
import os
import json

# =================================================================================================
# HELPER FUNCTION to load the user's plan
# =================================================================================================
def load_plan(username):
    """Loads a user's plan from their dedicated JSON file."""
    user_plans_dir = os.path.join("user_plans")
    user_plan_file = os.path.join(user_plans_dir, f"{username}.json")
    if not os.path.exists(user_plan_file):
        return []
    try:
        with open(user_plan_file, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# =================================================================================================
# STYLING (Inspired by your "Stats" image)
# =================================================================================================
st.set_page_config(layout="wide")

st.markdown("""
<style>
    /* --- Main Background & Text --- */
    .stApp {
        background: radial-gradient(circle, rgba(43,2,83,1) 0%, rgba(20,20,40,1) 100%);
        color: white;
    }
    /* --- Make tabs look modern --- */
    .stTabs [data-baseweb="tab-list"] {
		gap: 24px;
	}
    .stTabs [data-baseweb="tab"] {
		height: 50px;
        background-color: transparent;
		border-radius: 4px 4px 0px 0px;
		gap: 8px;
		padding-top: 10px;
		padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
  		background-color: rgba(255, 255, 255, 0.1);
	}
    /* --- General Text & Headers --- */
    h1, h2, h3, h4, h5, h6, p, li, label {
        color: white !important;
    }
    /* --- Metric styling for DONE/PENDING --- */
    .st-emotion-cache-1g6gooi { /* Targets the metric label */
        color: rgba(255, 255, 255, 0.7) !important;
        font-size: 1.2rem;
    }
    .st-emotion-cache-ocqkz7 { /* Targets the metric value */
        font-size: 3rem !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# =================================================================================================
# MAIN APP
# =================================================================================================
st.title("📈 Your Statistics")
st.write("A visual overview of your task performance.")

# --- Check if user is logged in ---
if not st.session_state.get("logged_in", False):
    st.warning("Please log in from the Home page to view your stats.")
    st.stop()

username = st.session_state.get("username", "default_user").strip()

# --- Load and Process Data ---
plan = load_plan(username)
if not plan:
    st.info("You haven't added any tasks yet. Add tasks in the 'Study Planner' to see your stats.")
    st.stop()

df = pd.DataFrame(plan)
df['date'] = pd.to_datetime(df['date'])
df['done'] = df['done'].astype(bool)

# --- Create Tabs for Different Views ---
today_tab, week_tab, performance_tab = st.tabs(["Today", "This Week", "Performance"])

# --- TODAY'S STATS ---
with today_tab:
    st.header(f"Today's Progress ({datetime.date.today().strftime('%b %d, %Y')})")
    today_df = df[df['date'].dt.date == datetime.date.today()]

    if today_df.empty:
        st.info("No tasks scheduled for today.")
    else:
        total_today = len(today_df)
        done_today = today_df['done'].sum()
        pending_today = total_today - done_today
        completion_percent = (done_today / total_today) * 100 if total_today > 0 else 0

        col1, col2 = st.columns([1, 1.5])
        with col1:
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number", value = completion_percent,
                title = {'text': "Completion", 'font': {'size': 24, 'color': 'white'}},
                number = {'suffix': "%", 'font': {'size': 50, 'color': 'white'}},
                gauge = {'axis': {'range': [None, 100]}, 'bar': {'color': "#00cc96"}, 'bgcolor': "rgba(255,255,255,0.1)"}
            ))
            fig_gauge.update_layout(paper_bgcolor = "rgba(0,0,0,0)", height=300, margin=dict(l=10, r=10, t=60, b=10))
            st.plotly_chart(fig_gauge, use_container_width=True)
        with col2:
            st.metric("✅ DONE", f"{done_today}")
            st.metric("⏳ PENDING", f"{pending_today}")
            st.metric("➕ NEW", "0") # Placeholder as in the image

# --- THIS WEEK'S STATS ---
with week_tab:
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    st.header(f"This Week's Progress ({start_of_week.strftime('%b %d')} - {end_of_week.strftime('%b %d')})")
    
    week_df = df[(df['date'].dt.date >= start_of_week) & (df['date'].dt.date <= end_of_week)]

    if week_df.empty:
        st.info("No tasks scheduled for this week.")
    else:
        total_week = len(week_df)
        done_week = week_df['done'].sum()
        pending_week = total_week - done_week
        completion_percent_week = (done_week / total_week) * 100 if total_week > 0 else 0

        col1_week, col2_week = st.columns([1, 1.5])
        with col1_week:
            fig_gauge_week = go.Figure(go.Indicator(
                mode="gauge+number", value=completion_percent_week,
                title={'text': "Completion", 'font': {'size': 24, 'color': 'white'}},
                number={'suffix': "%", 'font': {'size': 50, 'color': 'white'}},
                gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "#636efa"}}
            ))
            fig_gauge_week.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=300, margin=dict(l=10, r=10, t=60, b=10))
            st.plotly_chart(fig_gauge_week, use_container_width=True)
        with col2_week:
            st.metric("✅ DONE", f"{done_week}")
            st.metric("⏳ PENDING", f"{pending_week}")

# --- PERFORMANCE OVER TIME (YEAR) ---
with performance_tab:
    st.header("Performance Over Time")
    df_monthly = df.set_index('date').resample('ME').agg(
        completed_tasks=('done', 'sum')
    ).reset_index()
    df_monthly = df.set_index('date').groupby(pd.Grouper(freq='M')).agg(
        total_tasks=('done', 'count'),
        completed_tasks=('done', 'sum')
    ).reset_index()
    df_monthly['completion_rate'] = (df_monthly['completed_tasks'] / df_monthly['total_tasks']) * 100
    df_monthly['month'] = df_monthly['date'].dt.strftime('%Y-%m')

    if df_monthly.empty:
        st.info("Not enough data to show performance over time. Complete some tasks!")
    else:
        fig_line = px.line(
            df_monthly,
            x='month',
            y='completion_rate',
            title='Monthly Completion Rate (%)',
            markers=True,
            labels={'month': 'Month', 'completion_rate': 'Completion Rate (%)'}
        )
        fig_line.update_traces(line=dict(color='#ef553b', width=4)) # Vibrant red/orange line
        fig_line.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(255,255,255,0.05)', font_color="white",
            xaxis=dict(gridcolor='rgba(255,255,255,0.2)'), yaxis=dict(gridcolor='rgba(255,255,255,0.2)')
        )
        st.plotly_chart(fig_line, use_container_width=True)
