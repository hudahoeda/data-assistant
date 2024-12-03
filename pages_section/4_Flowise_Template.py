import os
import streamlit as st
from flowise import Flowise, PredictionData
import json

# Flowise app base url
base_url = os.environ.get('FLOWISE_BASE_URL')
api_key = os.environ.get("FLOWISE_API_KEY")

# Chatflow/Agentflow ID
flow_id = os.environ.get("FLOW_ID")

# Show title and description.
st.title("DALA")
st.write("Data Analytics Learning Assistant")

# Create options object with base_url
class Options:
    def __init__(self, base_url):
        self.base_url = base_url

# Create a Flowise client with options object
client = Flowise(base_url)  
if api_key:
    client.api_key = api_key

# Create a session state variable to store the chat messages. This ensures that the
# messages persist across reruns.
if "messages" not in st.session_state:
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
                "sessionId": st.session_state['session_id'],  
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
            yield str(parsed_chunk['data'])  # Yield only the new chunk

# Create a chat input field
if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Stream the response
    response = ""
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        for chunk in generate_response(prompt):
            response += chunk  # Accumulate chunks
            response_placeholder.markdown(response)  # Update placeholder with accumulated response
    
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