import os
import base64
import re
import json

import streamlit as st
from openai import AssistantEventHandler
from tools import TOOL_MAP
from typing_extensions import override
from dotenv import load_dotenv
from pyairtable import Api
import time
import uuid
import requests
import extra_streamlit_components as stx
from datetime import datetime, timedelta
from langfuse import Langfuse

# Add these to your existing environment variable loading
BASE_ID = os.environ.get('BASE_ID')
USER_TABLE_NAME = 'Users'
CHAT_TABLE_NAME = 'Chat History'
AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY')

# Initialize Airtable API
try:
    airtable = Api(AIRTABLE_API_KEY)
except Exception as e:
    st.error(f"Error initializing Airtable API: {str(e)}")
    st.stop()

enabled_file_upload_message = os.environ.get(
    "ENABLED_FILE_UPLOAD_MESSAGE", "Upload a file"
)

# Define your pages using st.Page with actual icons
# flowise = st.Page("pages_section/1_DA_Learning_Assistant.py", 
#                         title="Chat with DALA", 
#                         icon="📝")

message = st.Page("pages_section/2_DA_Learning_Home.py", 
                        title="Home and Info", 
                        icon="🏠")

feedback = st.Page("pages_section/3_DA_Learning_Feedback.py", 
                        title="Report Error", 
                        icon="📊")

flowise_template = st.Page("pages_section/4_Flowise_Template.py", 
                         title="Flowise Chat", 
                         icon="💬")

# flowise_embed = st.Page("pages_section/5_Flowise_Embed.py", 
#                         title="Flowise Embed", 
#                         icon="🔗")

# Initialize Langfuse client
langfuse = Langfuse(
    public_key=os.environ.get("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.environ.get("LANGFUSE_SECRET_KEY"),
    host=os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")
)

def generate_session_id():
    return str(uuid.uuid4())

def get_user(username):
    try:
        table = airtable.table(BASE_ID, USER_TABLE_NAME)
        records = table.all(formula=f"{{Username}} = '{username}'")
        return records[0] if records else None
    except Exception as e:
        st.error(f"Error getting user: {str(e)}")
        return None

def get_student_id(username):
    try:
        table = airtable.table(BASE_ID, USER_TABLE_NAME)
        records = table.all(formula=f"{{Username}} = '{username}'")
        if records:
            return records[0]['fields'].get('StudentID')
        else:
            return None
    except Exception as e:
        st.error(f"Error getting user: {str(e)}")
        return None

def verify_password(stored_password, provided_password):
    return stored_password == provided_password

if "tool_call" not in st.session_state:
    st.session_state.tool_calls = []

if "chat_log" not in st.session_state:
    st.session_state.chat_log = []

if "in_progress" not in st.session_state:
    st.session_state.in_progress = False

def disable_form():
    st.session_state.in_progress = True

def reset_chat():
    current_page = st.session_state.get('current_page', 'Unknown Page')
    if current_page in st.session_state.page_chat_logs:
        st.session_state.page_chat_logs[current_page] = []
    st.session_state.in_progress = False

def save_chat_history(session_id, username, user_input, response_json):
    try:
        # Serialize the full response JSON to a string
        response_json_str = json.dumps(response_json)

        table = airtable.table(BASE_ID, CHAT_TABLE_NAME)
        table.create({
            "Timestamp": int(time.time()),
            "SessionID": session_id,
            "ResponseJSON": response_json_str, # Store the full response JSON as a string
            "Username": username,
            "UserInput": user_input
        })
    except Exception as e:
        st.error(f"Error saving chat history: {str(e)}")
        
def generate_custom_api_response(api_url, headers, question):
    # Retrieve the session ID directly from the session state
    session_id = st.session_state.get('flowise_session_id', None)

    # Create the payload for the API request
    payload = {
        "question": question,
        "streaming": False,  # Assuming the API supports streaming
        "overrideConfig": {
            "sessionId": session_id  # Directly use the session ID from session state
        }
    }

    # Send the request to the custom API endpoint
    response = requests.post(api_url, json=payload, headers=headers)

    # Return the response content as JSON if status is 200 OK
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error {response.status_code}: {response.text}")
        return None

def load_flowise_chat_screen(api_url, headers, assistant_title, assistant_message):
    def get_current_page():
        return st.session_state.get('current_page', 'Flowise Chat')

    def initialize_chat_logs(current_page):
        if 'page_chat_logs' not in st.session_state:
            st.session_state.page_chat_logs = {}
        if current_page not in st.session_state.page_chat_logs:
            st.session_state.page_chat_logs[current_page] = []

    def display_chat_log(current_page):
        for chat in st.session_state.page_chat_logs[current_page]:
            with st.chat_message(chat["name"]):
                st.markdown(chat["msg"], True)

    def update_session_id_if_needed(response_json):
        if 'sessionId' in response_json and st.session_state.get('flowise_session_id') is None:
            st.session_state['flowise_session_id'] = response_json['sessionId']

    def process_user_input(user_msg, current_page):
        st.session_state.in_progress = True

        # Display user message
        with st.chat_message("user"):
            st.markdown(user_msg, True)

        # Save user message to chat log
        st.session_state.page_chat_logs[current_page].append({"name": "user", "msg": user_msg})

        # Retrieve session-related variables
        session_id = st.session_state.get('flowise_session_id', None)
        username = st.session_state.get('username', 'Unknown User')

        # Display spinner while waiting for both API response and Airtable save
        with st.spinner("AI is thinking..."):
            # Get API response
            response_json = generate_custom_api_response(api_url, headers, user_msg)

            if response_json:
                update_session_id_if_needed(response_json)

                flowise_reply = response_json.get('text', "No response received.")

                # Show AI response with "default" name for the default style (yellow bubble)
                with st.chat_message("🤖"):
                    st.markdown(flowise_reply, True)

                # Save AI reply to chat log
                st.session_state.page_chat_logs[current_page].append({"name": "🤖", "msg": flowise_reply})

                # Call save_chat_history to log the interaction (inside spinner)
                try:
                    save_chat_history(
                        session_id=session_id,
                        username=username,
                        user_input=user_msg,
                        response_json=response_json
                    )
                except Exception as e:
                    st.error(f"Error saving chat history: {str(e)}")

        st.session_state.in_progress = False
        st.rerun()

    # Main Logic Execution
    current_page = get_current_page()

    # # Initialize UI Components
    # st.sidebar.file_uploader(
    #     "Upload a file if needed (txt, pdf, json)",  
    #     type=["txt", "pdf", "json"],
    #     disabled=st.session_state.get('in_progress', False),
    # )

    initialize_chat_logs(current_page)

    st.title(assistant_title or "")
    st.info(assistant_message)
    st.write("Halo, bisa perkenalkan namamu?")  

    display_chat_log(current_page)

    user_msg = st.chat_input("Message", disabled=st.session_state.get('in_progress', False))

    if user_msg:
        process_user_input(user_msg, current_page)

def get_cookie_manager():
    return stx.CookieManager()

def set_auth_cookie(cookie_manager, username):
    # Set cookie to expire in 7 days
    expiry = (datetime.now() + timedelta(days=7)).timestamp()
    # Convert the float timestamp to a datetime object
    expiry = datetime.fromtimestamp(expiry)
    cookie_manager.set('auth_token', f"{username}|{expiry}", expires_at=expiry)

def get_auth_cookie(cookie_manager):
    auth_token = cookie_manager.get('auth_token')
    if auth_token:
        try:
            username, expiry = auth_token.split('|')
            if float(expiry) > datetime.now().timestamp():
                return username
        except:
            pass
    return None

def login():
    cookie_manager = get_cookie_manager()
    
    # Check if user is already logged in via cookie
    auth_username = get_auth_cookie(cookie_manager)
    if auth_username:
        st.session_state['logged_in'] = True
        st.session_state['username'] = auth_username
        # Clear existing messages to force reload from Langfuse
        if 'messages' in st.session_state:
            del st.session_state.messages
        if 'flowise_session_id' in st.session_state:
            del st.session_state.flowise_session_id
        return
    
    st.title("DALA RevoU")
    st.markdown("For login, use the registered email in RevoU with your phone number with format `081xxx` as password")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = get_user(username)
        if user:
            if 'Password' in user['fields']:
                if verify_password(user['fields']['Password'], password):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    # Set auth cookie
                    set_auth_cookie(cookie_manager, username)
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid password")
            else:
                st.error("User record does not contain a password field")
        else:
            st.error("User not found")

def logout():
    cookie_manager = get_cookie_manager()
    
    # Check if cookie exists before deleting
    if 'auth_token' in cookie_manager.cookies:
        cookie_manager.delete('auth_token')
    
    # Clear session state
    st.session_state.clear()
    st.rerun()

def get_current_page_name(pg):
    if pg and hasattr(pg, 'title'):
        st.session_state['current_page'] = pg.title
        return pg.title
    return "Unknown Page"

def main():
    st.logo("https://cdn.prod.website-files.com/61af164800e38c4f53c60b4e/61af164800e38c11efc60b6d_RevoU.svg")
    st.set_page_config(page_title="Revo Assistant")

    # Initialize session state
    if "page_thread_ids" not in st.session_state:
        st.session_state.page_thread_ids = {}
    if "page_chat_logs" not in st.session_state:
        st.session_state.page_chat_logs = {}
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []
    if 'session_id' not in st.session_state:
        st.session_state['session_id'] = generate_session_id()
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = "Home"
    if 'in_progress' not in st.session_state:
        st.session_state.in_progress = False
    if 'flowise_session_id' not in st.session_state:
        st.session_state.flowise_session_id = None
        
    if st.session_state['logged_in']:
        pg = st.navigation({
            "Flowise": [message, flowise_template, feedback],
            "Logout": [st.Page(logout, title="Logout", icon="🚪")]
        })
    else:
        pg = st.navigation([st.Page(login, title="Login", icon="🔑")])

    # Set the current page in session state
    if pg and hasattr(pg, 'title'):
        st.session_state['current_page'] = pg.title
    else:
        st.session_state['current_page'] = "Unknown Page"

    # Main content
    if not st.session_state['logged_in']:
        login()
    else:        
        pg.run()
        
if __name__ == "__main__":
    main()
