System Design Document: AI Study Buddy

Author: Kratika Singh
Project: AI Agent Prototype for Software Engineer Internship

1. Introduction & System Concept
1.1. The Problem: The Modern Student's Dilemma

The modern university student faces a multitude of challenges:

Managing a complex schedule of classes and assignments

Comprehending difficult subjects

Dealing with stress and mental overhead

The manual task selected for automation is holistic student management, which encompasses not just academic planning but also learning assistance and personal well-being.

1.2. The Solution: AI Study Buddy

AI Study Buddy is a comprehensive, multi-page web application designed to be an all-in-one AI agent for students.

Goes beyond a simple task planner

Acts as a centralized hub for academic + personal life

Can reason about queries, plan schedules, and execute tasks by integrating with external services

1.3. Originality and Social Impact

The originality of this project lies in its integrated approach: combining several specialized AI functions into one cohesive user experience.

Key social impacts:

Mental Health Chatbot → addresses student stress & well-being

Secure Document Locker → ensures privacy & security of academic/personal files

This makes the tool supportive of the student as a whole person, not just academically.

2. System Architecture
2.1. Framework Choice: Streamlit

Why Streamlit?

Acts as both backend and frontend

Generates UI directly from Python code

Rapid prototyping with no need for React/Flask split

Great for projects where AI and backend logic are the focus

2.2. Application Flow

Landing & Authentication (Home.py) → secure login/signup page

Multi-Page Container (pages/) → Streamlit sidebar navigation

Feature Pages → Planner, Assistants, Document Locker, Stats (each in a separate .py file)

📌 Example flow:

User → Home.py (Login) → Main App (Sidebar) → Planner / Assistant / Locker / Stats

3. Data Design & Persistence
3.1. Backend Style: Serverless & File-Based

State managed per user session (via Streamlit)

Persistent storage = file-based JSON system

Chosen for simplicity, robustness, and no database setup overhead

3.2. Data Models
Data Type	Storage Location	Purpose
Users	users.json	Stores usernames, hashed passwords, mobiles
Study Plans	user_plans/<username>.json	User’s task lists
Timetables	user_timetables/<username>.json	Daily timetable (resets daily)
Chats	chats/<username>/mental_health_chat.json	Saves chatbot conversations
Documents	user_documents/<username>/...	Encrypted document storage

Encryption handled using cryptography library.

4. Component Breakdown
4.1. Authentication (Home.py)

Secure signup/login

hashlib for password hashing

Uses st.session_state to manage user sessions

4.2. AI Study Planner (pages/1_Study_Planner.py)

Create/edit tasks with dates, times, and priorities

Interactive progress tracking (lists, bars, pie charts)

Google Calendar API integration for real-world execution

Daily timetable view for scheduling

4.3. AI Assistants (pages/2_AI_Assistant.py)

Powered by Google Gemini API

Handles multimodal reasoning (text + images)

Can save, load, and delete chat histories

4.4. Secure Document Locker (pages/3_Document_Locker.py)

Encrypted vault for user documents

Password-based encryption with cryptography

Ensures sensitive files remain secure

4.5. Stats Dashboard (pages/4_Stats.py)

Provides a data-driven overview of performance

Uses Plotly Express for interactive charts (pie, bar, gauge)

Helps students track productivity visually

5. Chosen Technologies & Justification
Technology	Component	Why Chosen
Python	Entire App	AI/ML ecosystem, simple syntax
Streamlit	Frontend & Backend	All-in-one framework for rapid prototyping
Google Gemini API	AI Assistant	State-of-the-art LLM for reasoning & multimodal tasks
Google Calendar API	Study Planner	External tool integration, enables execution
Pandas	Stats & Timetable	Easy data manipulation
Plotly Express	Dashboards	Beautiful interactive charts
cryptography	Document Locker	Secure encryption
JSON Storage	Data Persistence	Simple, human-readable, no DB setup required
6. Future Improvements

Upgrade from JSON → SQL/NoSQL database for scalability

Role-based authentication (admin, student)

Mobile app integration for notifications

Expand wellness tools (journaling, guided meditation)

✅ This document is GitHub-ready:

Uses proper headings & tables

Easy to read in Markdown renderers

No leftover [cite_start] markers

Includes diagrams placeholders
