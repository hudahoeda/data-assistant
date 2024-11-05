import streamlit as st
import streamlit.components.v1 as components
import json
from streamlit_theme import st_theme

# Get theme and background color with fallback
theme = st_theme()
print(theme)
background_color = theme["backgroundColor"] if theme else "#0e1117", # Default to white

# Create chatflow config
chatflow_config = json.dumps({
    "sessionId": st.session_state.get('session_id', ''),  # Using .get() for safety
    "analytics": {
        "langFuse": {
            "userId": st.session_state.get('username', '')  # Using .get() for safety
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
            background-color: {background_color};
        }}
        #flowise-container {{
            width: 100%;
            height: 100vh;
            background-color: {background_color};
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
                        title: 'DALA',
                        titleAvatarSrc: 'https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/svg/google-messages.svg',
                        showAgentMessages: true,
                        welcomeMessage: 'Hello! This is custom welcome message',
                        errorMessage: 'This is a custom error message',
                        backgroundColor: "{background_color}",
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
                            backgroundColor: "f7f8ff",
                            textColor: "#ffffff",
                            showAvatar: true,
                            avatarSrc: "https://raw.githubusercontent.com/zahidkhawaja/langchain-chat-nextjs/main/public/usericon.png"
                        }},
                        footer: {{
                            textColor: '#ffffff',
                            text: 'Powered by',
                            company: 'RevoU',
                            companyLink: 'https://revou.co',
                        }}
                    }}
                }}
            }})
        }}

        initChat();
        window.addEventListener('resize', initChat);
    </script>
</body>
</html>
"""

components.html(flowise_html, height=1000, width=None)