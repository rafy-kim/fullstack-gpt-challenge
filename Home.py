import os
import openai
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
        openai.api_key = api_key
        openai.Engine.list()  # 유효성 검사용 요청
        return True
    except openai.error.AuthenticationError:
        return False

# 사이드바에서 API 키 입력 및 검증 처리
with st.sidebar:
    # 세션 상태에서 api_key_valid를 확인하여 처리
    if "api_key_valid" not in st.session_state:
        st.session_state["api_key_valid"] = False
    
    if not st.session_state["api_key_valid"]:
        api_key = st.text_input("Input your OpenAI API Key", type="password")
        if api_key:
            if validate_api_key(api_key):
                st.session_state["api_key_valid"] = True
                os.environ["OPENAI_API_KEY"] = api_key
                st.experimental_rerun()  # 페이지 리렌더링
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



