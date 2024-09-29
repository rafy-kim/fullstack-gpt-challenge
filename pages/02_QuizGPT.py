import time
import openai
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import CharacterTextSplitter
import streamlit as st
import os
import json
from langchain.retrievers import WikipediaRetriever
import requests


# 함수 호출을 사용합니다.
st.set_page_config(
    page_title="QuizGPT",
    page_icon="❓",
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

# def redirect(target_url):
#     st.markdown(f"""
#         <meta http-equiv="refresh" content="0; url={target_url}">
#         """, unsafe_allow_html=True)



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
        
# API 키 유효성 확인
if "api_key_valid" not in st.session_state or not st.session_state["api_key_valid"]:
    st.error("You do not have access to this page. Please provide a valid API key.")
    # time.sleep(0.5)
    # redirect("/")
    st.stop()  # 페이지 실행 중지


# 함수 정의
function = {
    "name": "create_quiz",
    "description": "function that takes a list of questions and answers and returns a quiz",
    "parameters": {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                        },
                        "answers": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "answer": {
                                        "type": "string",
                                    },
                                    "correct": {
                                        "type": "boolean",
                                    },
                                },
                                "required": ["answer", "correct"],
                            },
                        },
                    },
                    "required": ["question", "answers"],
                },
            }
        },
        "required": ["questions"],
    },
}

llm = ChatOpenAI(
    temperature=0.1,
    model="gpt-4o-mini",
).bind(
    function_call={
        "name": "create_quiz",
    },
    functions=[
        function,
    ],
)

@st.cache_data(show_spinner="Loading file...")
def split_file(file):
    file_content = file.read()
    file_path = f"./.cache/quiz_files/{file.name}"
    with open(file_path, "wb") as f:
        f.write(file_content)
    splitter = CharacterTextSplitter.from_tiktoken_encoder(
        separator="\n",
        chunk_size=600,
        chunk_overlap=100,
    )
    loader = UnstructuredFileLoader(file_path)
    docs = loader.load_and_split(text_splitter=splitter)
    return docs


@st.cache_data(show_spinner="Making quiz...")
def run_quiz_chain(_docs, topic, level):
    prompt = PromptTemplate.from_template("Make Five {level} quizzes about {docs}.")
    chain = prompt | llm
    response = chain.invoke({"docs": _docs, "level": level})
    response = response.additional_kwargs["function_call"]["arguments"]
    response = json.loads(response)
    return response


@st.cache_data(show_spinner="Searching Wikipedia...")
def wiki_search(term):
    retriever = WikipediaRetriever(top_k_results=5)
    docs = retriever.get_relevant_documents(term)
    return docs


# 퀴즈 초기화 함수
def reset_quiz():
    st.session_state["quiz_started"] = False
    st.session_state["correct_answers"] = 0
    st.session_state["quiz_finished"] = False
    st.session_state["response"] = None


# 세션 상태 초기화
if "quiz_started" not in st.session_state:
    st.session_state["quiz_started"] = False
if "correct_answers" not in st.session_state:
    st.session_state["correct_answers"] = 0
if "quiz_finished" not in st.session_state:
    st.session_state["quiz_finished"] = False
if "response" not in st.session_state:
    st.session_state["response"] = None


# 사이드바에서 난이도와 데이터 소스 선택
with st.sidebar:
    docs = None
    topic = None

    level = st.select_slider(
        "Select a difficulty level of Quiz",
        options=[
            "very easy",
            "very hard",
        ],
    )
    st.write("Difficulty level is", level)

    choice = st.selectbox(
        "Choose what you want to use.",
        (
            "File",
            "Wikipedia Article",
        ),
    )
    if choice == "File":
        file = st.file_uploader(
            "Upload a .docx , .txt or .pdf file",
            type=["pdf", "txt", "docx"],
        )
        if file:
            docs = split_file(file)
    else:
        topic = st.text_input("Search Wikipedia...")
        if topic:
            docs = wiki_search(topic)


if not docs:
    st.markdown(
        """
    Welcome to QuizGPT.
                
    I will make a quiz from Wikipedia articles or files you upload to test your knowledge and help you study.
                
    Get started by uploading a file or searching on Wikipedia in the sidebar.
    """
    )
else:
    if not st.session_state["quiz_started"]:
        if st.button("Start Quiz"):
            st.session_state["quiz_started"] = True

    if st.session_state["quiz_started"] and not st.session_state["quiz_finished"]:
        # 퀴즈를 처음 실행할 때만 response를 생성
        if st.session_state["response"] is None:
            st.session_state["response"] = run_quiz_chain(docs, topic if topic else file.name, level)
        
        response = st.session_state["response"]
        
        with st.form("questions_form"):
            cnt_correct_answers = 0
            for question in response["questions"]:
                st.write(question["question"])
                value = st.radio(
                    "Select an option.",
                    [answer["answer"] for answer in question["answers"]],
                    index=None,
                )
                if {"answer": value, "correct": True} in question["answers"]:
                    st.success("Correct!")
                    cnt_correct_answers += 1
                elif value is not None:
                    st.error("Wrong!")
            button = st.form_submit_button()

            if button:
                st.session_state["correct_answers"] = cnt_correct_answers
                st.session_state["quiz_finished"] = True

    # 퀴즈 완료 후 처리
    if st.session_state["quiz_finished"]:
        response = st.session_state.get("response")
        if response and st.session_state["correct_answers"] == len(response["questions"]):
            st.balloons()
            st.success("Congratulations! You answered all questions correctly!")
            reset_quiz()
        else:
            st.error("You didn't answer all questions correctly.")
            if st.button("Try Again"):
                reset_quiz()
                st.rerun()
