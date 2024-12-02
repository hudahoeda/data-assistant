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
st.title("💬 Flowise Streamlit Chat")
st.write("This is a simple chatbot that uses Flowise Python SDK")

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