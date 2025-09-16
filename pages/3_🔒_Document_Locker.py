import streamlit as st
import os
import time
import json
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

# =================================================================================================
# PAGE CONFIGURATION
# =================================================================================================
st.set_page_config(page_title="Secure Document Locker", page_icon="🔒", layout="wide")

# =================================================================================================
# HELPER FUNCTIONS
# =================================================================================================
def get_base64_of_bin_file(bin_file):
    """ Reads a local file and returns its Base64 encoded string. """
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

def load_users():
    """Loads the user database from the main users.json file."""
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        st.error("users.json not found or is corrupted.")
        return {}

def hash_password(password):
    """Returns the sha256 hash of a password."""
    return hashlib.sha256(password.encode()).hexdigest()

SALT = b'your_project_specific_salt_for_this_prototype'

def get_key_from_password(password, salt):
    """Derives a secure encryption key from a user's password."""
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000, backend=default_backend())
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

def get_user_doc_dir(username):
    """Returns the path to the user's specific document directory."""
    user_doc_dir = os.path.join("user_documents", username.strip())
    if not os.path.exists(user_doc_dir):
        os.makedirs(user_doc_dir)
    return user_doc_dir

# =================================================================================================
# STYLING
# =================================================================================================
# --- This new section adds your custom background image ---
bg_image_base64 = get_base64_of_bin_file("lock.jpg")
if bg_image_base64:
    st.markdown(f"""
    <style>

        .stApp {{
            background-image: linear-gradient(rgba(0, 4, 40, 0.7), rgba(0, 4, 40, 0.7)), url("data:image/jpeg;base64,{bg_image_base64}");
            background-size: contain;
            background-attachment: fixed;
        }}
        /* Make the main content container semi-transparent */
        .main .block-container {{
            background-color: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 2rem;
        }}
        /* Ensure text is white and readable */
        h1, h2, h3, p, label, .st-emotion-cache-16txtl3 {{
            color: white !important;
        }}
    </style>
    """, unsafe_allow_html=True)
# =================================================================================================

# --- MAIN APP ---
st.title("🔒 Secure Document Locker")

# (The rest of your code for the locker remains the same)
if not st.session_state.get("logged_in", False):
    st.warning("Please log in from the Home page to use the Document Locker.")
    st.stop()
# ... (rest of your existing, working locker logic)

username = st.session_state.get("username", "default_user")

if 'locker_unlocked' not in st.session_state:
    st.session_state.locker_unlocked = False
if 'fernet_key' not in st.session_state:
    st.session_state.fernet_key = None

# --- LOCK SCREEN VIEW ---
if not st.session_state.locker_unlocked:
    st.info("To access your documents, please confirm your main login password.")
    locker_password = st.text_input("Locker Password", type="password", key="locker_pass")
    
    if st.button("Unlock Locker"):
      if locker_password:
            users = load_users()
            # --- THIS IS THE SECURITY FIX ---
            # Verify the user's main login password before unlocking
            if username in users and users[username]['password_hash'] == hash_password(locker_password):
                # If correct, generate the encryption key from that same password
                key = get_key_from_password(locker_password, SALT)
                st.session_state.fernet_key = Fernet(key)
                st.session_state.locker_unlocked = True
                st.success("Locker Unlocked!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Incorrect password. Please use your main login password.")

# --- UNLOCKED VIEW ---
# --- UNLOCKED VIEW ---
else:
    st.success("Your Document Locker is unlocked.")
    if st.button("↩️ Lock and Go Back"):
        # Reset locker state
        st.session_state.locker_unlocked = False
        st.session_state.fernet_key = None

        # Show lock symbol
        st.markdown(
            """
            <div style="text-align:center; margin-top:50px;">
                <h1 style="font-size:120px;">🔒</h1>
                <h2>Your locker is now locked.</h2>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Redirect after 2 seconds to ai_tool.py
        st.markdown(
            """
            <meta http-equiv="refresh" content="2; url='/ai_tool'">
            """,
            unsafe_allow_html=True
        )

        st.stop()  # Stop further execution so only the lock screen shows

    
    # --- File Uploader ---
    st.subheader("Upload a New Document")
    uploaded_file = st.file_uploader("Choose a file to encrypt and upload", type=None, key="doc_uploader")
    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        encrypted_data = st.session_state.fernet_key.encrypt(file_bytes)
        user_doc_dir = get_user_doc_dir(username)
        file_path = os.path.join(user_doc_dir, uploaded_file.name + ".encrypted")
        with open(file_path, "wb") as f:
            f.write(encrypted_data)
        st.success(f"✅ Successfully encrypted and saved '{uploaded_file.name}'!")

    st.markdown("---")

    # --- Display and Download Encrypted Files (with new password check) ---
    st.subheader("Your Secured Documents")
    user_doc_dir = get_user_doc_dir(username)
    try:
        encrypted_files = [f for f in os.listdir(user_doc_dir) if f.endswith(".encrypted")]
        if not encrypted_files:
            st.info("Your locker is empty. Upload a document to see it here.")
        else:
            for encrypted_file in encrypted_files:
                display_name = encrypted_file.replace(".encrypted", "")
                
                # Use st.popover for the password confirmation
                with st.popover(f"Download '{display_name}'"):
                    st.write(f"Please confirm your main login password to download this file.")
                    with st.form(f"form_{encrypted_file}"):
                        locker_password = st.text_input("Your Login Password", type="password")
                        submitted = st.form_submit_button("Confirm & Prepare Download")

                        if submitted:
                            users = load_users()
                            # Verify the user's main login password
                            if username in users and users[username]['password_hash'] == hash_password(locker_password):
                                # If correct, decrypt the file and show the real download button
                                with open(os.path.join(user_doc_dir, encrypted_file), "rb") as f:
                                    encrypted_data_to_download = f.read()
                                decrypted_data = st.session_state.fernet_key.decrypt(encrypted_data_to_download)
                                
                                st.success("Password correct!")
                                st.download_button(
                                    label="Click here to Download",
                                    data=decrypted_data,
                                    file_name=display_name
                                )
                            else:
                                st.error("Incorrect password.")

    except Exception as e:
        st.error(f"Could not read document directory. Error: {e}")
