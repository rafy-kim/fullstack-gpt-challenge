import requests
import wikipedia
import json
from urllib.parse import urlparse, parse_qs
from typing import Type
from langchain.chat_models import ChatOpenAI
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from langchain.agents import initialize_agent, AgentType
from bs4 import BeautifulSoup
import streamlit as st
from langchain.utilities.duckduckgo_search import DuckDuckGoSearchAPIWrapper
import time
# import openai as client
from openai import OpenAI
client = OpenAI()

# assistant = client.beta.assistants.create(
#     name="Research Assistant2",
#     instructions="You help users do research on query using by duckduckgo and wikipedia.",
#     model="gpt-4o-mini",
#     tools=functions,
# )
# print(assistant)
assistant_id = "asst_G2BTRBBFDmC05QOpp06KvLsr"



# 이전 과제에서 만든 에이전트를 OpenAI 어시스턴트로 리팩터링합니다.
# 대화 기록을 표시하는 Streamlit 을 사용하여 유저 인터페이스를 제공하세요.
# 유저가 자체 OpenAI API 키를 사용하도록 허용하고, st.sidebar 내부의 st.input에서 이를 로드합니다.
# st.sidebar를 사용하여 Streamlit app 의 코드과 함께 깃허브 리포지토리에 링크를 넣습니다.


st.set_page_config(
    page_title="ResearchAssistant",
    page_icon="🔍",
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

# API 키 유효성 확인
if "api_key_valid" not in st.session_state or not st.session_state["api_key_valid"]:
    st.error("You do not have access to this page. Please provide a valid API key.")
    st.stop()  # 페이지 실행 중지


st.markdown(
    """
    # ResearchAssistant
            
    Research about something using by DuckDuckGo and Wikipedia.
"""
)

llm = ChatOpenAI(
    temperature=0.1,
    model="gpt-4o-mini",
)


def get_docs_from_dgg(inputs):
    try:
        # DuckDuckGo 검색
        search_url = f"https://html.duckduckgo.com/html/?q={query}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(search_url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('a', class_='result__a')
            
            # 각 웹사이트의 링크를 따라가서 콘텐츠 추출
            extracted_content = []
            print(len(results))
            for result in results[:5]:
                url = result['href']
                actual_url = extract_actual_url(url)
                print(actual_url)
                if actual_url:
                    website_content = fetch_website_content(actual_url)
                    if website_content:
                        extracted_content.append(website_content)
            
            all_content = "\n\n".join(extracted_content)
            # save_to_txt(f"research_DDG.txt", all_content)
            return all_content
        else:
            return f"Error fetching results from DuckDuckGo with status code {response.status_code}."
    except Exception as e:
        return f"Error fetching results from DuckDuckGo: {str(e)}"

def extract_actual_url(self, duckduckgo_url: str):
    """DuckDuckGo 리다이렉션 URL에서 실제 URL을 추출하는 함수"""
    parsed_url = urlparse(duckduckgo_url)
    query_params = parse_qs(parsed_url.query)
    actual_url = query_params.get('uddg', [None])[0]
    
    # DuckDuckGo 리다이렉션 URL에 HTTPS 스킴이 없을 경우 추가
    if actual_url and not actual_url.startswith('http'):
        actual_url = 'https://' + actual_url
    return actual_url

def fetch_website_content(self, url: str):
    """웹사이트의 콘텐츠를 가져오는 함수"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = soup.find_all('p')  # 주요 텍스트 콘텐츠 추출
            return "\n".join([p.get_text() for p in paragraphs])
        else:
            return None
    except Exception as e:
        return f"Error fetching content from {url}: {str(e)}"

def get_docs_from_wiki(inputs):
    try:
        # query = inputs["query"]
        # headers = {'User-Agent': 'Mozilla/5.0'}
        # wiki_wiki = wikipediaapi.Wikipedia('en', headers=headers)  
        # page = wiki_wiki.page(query)
        page = wikipedia.page(query)
        if page.exists():
            # save_to_txt(f"research_WIKI.txt", page.text)
            # return page.text
            return page.content
        else:
            return f"No Wikipedia page found for {query}."
    except Exception as e:
        return f"Error fetching results from Wikipedia: {str(e)}"





def send_message(thread_id, content):
    return client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=content,
    )


def get_run(run_id, thread_id):
    return client.beta.threads.runs.retrieve(run_id=run_id, thread_id=thread_id)


def get_messages(thread_id):
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    messages = list(messages)
    messages.reverse()
    return messages


def get_tool_outputs(run_id, thread_id):
    run = get_run(run_id, thread_id)
    outputs = []
    for action in run.required_action.submit_tool_outputs.tool_calls:
        action_id = action.id
        function = action.function
        print(f"Calling function: {function.name} with args {function.arguments}")
        outputs.append(
            {
                "tool_call_id": action_id,
                "output": functions_map[function.name](json.loads(function.arguments)),
            }
        )
    return outputs


def submit_tool_outputs(run_id, thread_id):
    outputs = get_tool_outputs(run.id, thread.id)
    return client.beta.threads.runs.submit_tool_outputs(
        run_id=run_id, thread_id=thread_id, tool_outputs=outputs
    )


def paint_message(message, role, save=True):
    with st.chat_message(role):
        st.markdown(message)
    if save:
        st.session_state["messages"].append({"message": message, "role": role})





functions_map = {
    "get_docs_from_dgg": get_docs_from_dgg,
    "get_docs_from_wiki": get_docs_from_wiki,
    # "extract_actual_url": extract_actual_url,
    # "fetch_website_content": fetch_website_content,
}


functions = [
    {
        "type": "function",
        "function": {
            "name": "get_docs_from_dgg",
            "description": "Given the query returns its related documents using by duckduckgosearch engine.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Something I want to know",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_docs_from_wiki",
            "description": "Given the query returns its related documents using by wikipedia dictionary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Something I want to know",
                    }
                },
                "required": ["query"],
            },
        },
    },

]



query = st.chat_input("Research about ...")






def paint_history():
    for message in st.session_state["messages"]:
        paint_message(
            message["message"].replace("$", "\$"), message["role"], save=False
        )


if "messages" not in st.session_state:
    st.session_state["messages"] = []


if query:
    paint_history()
    paint_message(query, "human")
    if "thread" not in st.session_state:
        thread = client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": query,
                }
            ]
        )
        st.session_state["thread"] = thread
    else:
        thread = st.session_state["thread"]
        send_message(thread.id, query)
    run = client.beta.threads.runs.create(
        thread_id=st.session_state["thread"].id,
        assistant_id=assistant_id,
    )
    with st.chat_message("ai"):
        with st.spinner("답변 생성 중.."):
            while get_run(run.id, thread.id).status in [
                "queued",
                "in_progress",
                "requires_action",
            ]:
                if get_run(run.id, thread.id).status == "requires_action":
                    submit_tool_outputs(run.id, thread.id)
                    time.sleep(0.5)
                else:
                    time.sleep(0.5)
            message = (
                get_messages(thread.id)[-1].content[0].text.value.replace("$", "\$")
            )
            st.session_state["messages"].append(
                {
                    "message": message,
                    "role": "ai",
                }
            )
            st.markdown(message)





