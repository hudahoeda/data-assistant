import os
import streamlit as st
from flowise import Flowise, PredictionData
import json

# Flowise app base url
base_url = os.environ.get('FLOWISE_ENDPOINT')

# Chatflow/Agentflow ID
flow_id = os.environ.get("FLOW_ID", "abc")

# Show title and description.
st.title("💬 Flowise Streamlit Chat")
st.write("This is a simple chatbot that uses Flowise Python SDK")

# Create a Flowise client.
client = Flowise(base_url=base_url)

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
                "sessionId": "session1234"
            },
            streaming=True
        )
    )

    response = ""
    for chunk in completion:
        parsed_chunk = json.loads(chunk)
        if parsed_chunk['event'] == 'token' and parsed_chunk['data'] != '':
            response += str(parsed_chunk['data'])
            yield response

# Create a chat input field to allow the user to enter a message. This will display
# automatically at the bottom of the page.
if prompt := st.chat_input("What is up?"):

    # Store and display the current prompt.
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Stream the response to the chat using `st.write_stream`, then store it in 
    # session state.
    response = ""
    with st.chat_message("assistant"):
        for chunk in generate_response(prompt):
            response = chunk
            st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})