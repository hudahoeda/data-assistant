import streamlit as st
import streamlit.components.v1 as components
import json

# Create override config as JSON string
chatflow_config = json.dumps({
    "sessionId": st.session_state['session_id'],
    "analytics": {
        "langFuse": {
            "userId": st.session_state['username']
        }
    }
})

flowise_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Flowise Chat</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body, html {{
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
        }}
        #flowise-container {{
            width: 100%;
            height: 100vh;
        }}
    </style>
</head>
<body>
    <div id="flowise-container">
        <flowise-fullchatbot></flowise-fullchatbot>
    </div>
    <script type="module">
        import Chatbot from "https://cdn.jsdelivr.net/npm/flowise-embed/dist/web.js"
        
        function initChat() {{
            const width = window.innerWidth;
            const height = window.innerHeight;
            
            Chatbot.initFull({{
                chatflowid: "2978f88d-31ba-4d0a-9f93-e1e0d24c34c2",
                apiHost: "https://flowise.revou.tech",
                chatflowConfig: {chatflow_config},
                theme: {{
                    chatWindow: {{
                        showTitle: true,
                        title: 'Flowise Bot',
                        titleAvatarSrc: 'https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/svg/google-messages.svg',
                        showAgentMessages: true,
                        welcomeMessage: 'Hello! This is custom welcome message',
                        errorMessage: 'This is a custom error message',
                        backgroundColor: "#ffffff",
                        height: height,
                        width: width,
                        fontSize: 16,
                        botMessage: {{
                            backgroundColor: "#f7f8ff",
                            textColor: "#303235",
                            showAvatar: true,
                            avatarSrc: "https://raw.githubusercontent.com/zahidkhawaja/langchain-chat-nextjs/main/public/parroticon.png"
                        }},
                        userMessage: {{
                            backgroundColor: "#3B81F6",
                            textColor: "#ffffff",
                            showAvatar: true,
                            avatarSrc: "https://raw.githubusercontent.com/zahidkhawaja/langchain-chat-nextjs/main/public/usericon.png"
                        }}
                    }}
                }}
            }})
        }}

        // Initialize on load
        initChat();

        // Update on window resize
        window.addEventListener('resize', initChat);
    </script>
</body>
</html>
"""

# Render with full width/height
components.html(flowise_html, height=1000, width=None)