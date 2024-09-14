import os
import openai
import requests
import streamlit as st


st.set_page_config(
    page_title="FullstackGPT Challenge",
    page_icon="🤖",
)

st.markdown(
    """
## Hello!
            
Welcome to my FullstackGPT Portfolio!
"""
)

# GitHub 로고와 링크 추가 (사이드바 하단 중앙에 고정)
st.sidebar.markdown(
    """
    <style>
    .sidebar-footer {
        position: fixed;
        bottom: 0;
        width: 300px;
        text-align: center;
        padding-bottom: 50px;
    }
    </style>
    <div class="sidebar-footer">
        <a href="https://github.com/rafy-kim/fullstack-gpt-challenge" target="_blank">
            <img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" width="60" height="60">
        </a>
    </div>
    """,
    unsafe_allow_html=True
)

def validate_api_key(api_key):
    try:
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        # Make a simple request to OpenAI's models endpoint for validation
        response = requests.get("https://api.openai.com/v1/models", headers=headers)
        
        # Check if the response is successful (200 OK)
        if response.status_code == 200:
            return True
        else:
            return False
    except Exception as e:
        st.error(f"API Key validation failed: {str(e)}")
        return False

# Sidebar input for OpenAI API key validation
with st.sidebar:
    # Ensure the session state tracks API key validity
    if "api_key_valid" not in st.session_state:
        st.session_state["api_key_valid"] = False
    
    if not st.session_state["api_key_valid"]:
        # Input field for API key, hidden with password type
        api_key = st.text_input("Input your OpenAI API Key", type="password")
        
        if api_key:
            # Validate the API key
            if validate_api_key(api_key):
                st.session_state["api_key_valid"] = True
                os.environ["OPENAI_API_KEY"] = api_key
                st.rerun()  # Rerun the app after key validation
            else:
                st.error("Invalid API key. Please try again.")
    else:
        st.success("API key is valid!")
        

st.warning("You need to input a valid API key to access the apps.")
st.markdown(
    """
    Here are the apps I made:
        
    - [x] 📃 DocumentGPT
    - [x] ❓ QuizGPT
    """
)



