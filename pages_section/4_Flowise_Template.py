import os
import streamlit as st
from flowise import Flowise, PredictionData
import json
from datetime import datetime
from langfuse import Langfuse
from functools import lru_cache

# Flowise app base url
base_url = os.environ.get('FLOWISE_BASE_URL')
api_key = os.environ.get("FLOWISE_API_KEY")

# Langfuse setup
langfuse = Langfuse(
    public_key=os.environ.get("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.environ.get("LANGFUSE_SECRET_KEY"),
    host=os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")
)

# Chatflow/Agentflow ID
flow_id = os.environ.get("FLOW_ID")

# Show title and description
st.title("DALA")
st.write("Data Analytics Learning Assistant")

# Create Flowise client
client = Flowise(base_url)  
if api_key:
    client.api_key = api_key

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_latest_session_id(username: str) -> str:
    """
    Get the latest session ID for a user from Langfuse
    """
    try:
        # Get traces for the user without order parameter
        traces = langfuse.get_traces(
            user_id=username,
            limit=1
        )
        if traces and len(traces) > 0:
            return traces[0].session_id
        return None
    except Exception as e:
        st.error(f"Error getting latest session ID: {str(e)}")
        return None

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_session_chat_history(username: str, session_id: str):
    """
    Retrieve chat history from Langfuse for a specific session
    """
    try:
        # Get traces for the specific session without order parameter
        traces = langfuse.get_traces(
            user_id=username,
            session_id=session_id
        )
        
        # Sort traces by timestamp if needed
        traces = sorted(traces, key=lambda x: x.timestamp if hasattr(x, 'timestamp') else 0)
        
        messages = []
        for trace in traces:
            # Extract generations from trace
            for generation in trace.generations:
                if generation.input and generation.output:
                    # Add user message
                    messages.append({
                        "role": "user",
                        "content": generation.input
                    })
                    # Add assistant message
                    messages.append({
                        "role": "assistant",
                        "content": generation.output
                    })
        
        return messages
    except Exception as e:
        st.error(f"Error loading chat history from Langfuse: {str(e)}")
        return []

# Initialize chat messages with history from Langfuse
if "messages" not in st.session_state:
    username = st.session_state.get('username')
    if username:
        # Get latest session ID
        latest_session_id = get_latest_session_id(username)
        if latest_session_id:
            # Store the session ID for future use
            st.session_state['flowise_session_id'] = latest_session_id
            # Get chat history for this session
            st.session_state.messages = get_session_chat_history(username, latest_session_id)
        else:
            st.session_state.messages = []
    else:
        st.session_state.messages = []

# Display the existing chat messages via `st.chat_message`.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def generate_response(prompt: str):
    completion = client.create_prediction(
        PredictionData(
            chatflowId=flow_id,
            question=prompt,
            overrideConfig={
                "sessionId": st.session_state.get('flowise_session_id'),  # Use existing session ID if available
                "analytics": {
                    "langFuse": {  
                        "userId": st.session_state['username']
                    }
                }
            },
            streaming=True
        )
    )

    for chunk in completion:
        parsed_chunk = json.loads(chunk)
        if parsed_chunk['event'] == 'token' and parsed_chunk['data'] != '':
            yield str(parsed_chunk['data'])

# Create a chat input field
if prompt := st.chat_input("What is up?"):
    # If we don't have a session ID yet, this must be a new session
    if 'flowise_session_id' not in st.session_state:
        # The first message will create a new session in Flowise
        st.session_state.messages = []  # Start fresh for new session
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Stream the response
    response = ""
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        for chunk in generate_response(prompt):
            response += chunk
            response_placeholder.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})

# Move file uploader to sidebar
with st.sidebar:
    st.divider()
    # Add file uploader widget with size limit (1MB = 1048576 bytes)
    MAX_FILE_SIZE = 1048576  # 1MB in bytes

    uploaded_file = st.file_uploader(
        "Upload a file (Max 1MB)", 
        type=["txt", "pdf", "csv", "json"],
        help="Upload your document to chat about its contents",
    )

    # Handle uploaded file
    if uploaded_file is not None:
        # Check file size
        if uploaded_file.size > MAX_FILE_SIZE:
            st.error(f"File is too large! Maximum size is 1MB. Your file is {uploaded_file.size / 1048576:.2f}MB")
        else:
            # Display file details
            file_details = {
                "Filename": uploaded_file.name,
                "File size": f"{uploaded_file.size / 1024:.2f} KB",
                "File type": uploaded_file.type
            }
            st.write("File Details:", file_details)
            
            # Store in session state
            if "uploaded_files" not in st.session_state:
                st.session_state.uploaded_files = []
            st.session_state.uploaded_files.append(uploaded_file)