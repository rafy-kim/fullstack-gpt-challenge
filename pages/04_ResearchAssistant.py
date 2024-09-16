import json
from langchain.chat_models import ChatOpenAI
import streamlit as st
import time
import openai as client
from langchain.tools import WikipediaQueryRun, DuckDuckGoSearchRun
from langchain.utilities import WikipediaAPIWrapper


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

def redirect(target_url):
    st.markdown(f"""
        <meta http-equiv="refresh" content="0; url={target_url}">
        """, unsafe_allow_html=True)

# API 키 유효성 확인
if "api_key_valid" not in st.session_state or not st.session_state["api_key_valid"]:
    st.error("You do not have access to this page. Please provide a valid API key.")
    time.sleep(0.5)
    redirect("/")
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


def dgg_get_docs(inputs):
    query = inputs["query"]
    ddg = DuckDuckGoSearchRun()
    return ddg.run(query)


def wiki_get_docs(inputs):
    query = inputs["query"]
    wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
    return wikipedia.invoke(query)


functions_map = {
    "dgg_get_docs": dgg_get_docs,
    "wiki_get_docs": wiki_get_docs,
}


functions = [
    {
        "type": "function",
        "function": {
            "name": "dgg_get_docs",
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
            "name": "wiki_get_docs",
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

# assistant = client.beta.assistants.create(
#     name="Research Assistant",
#     instructions="You help users do research on query using by duckduckgo and wikipedia.",
#     model="gpt-4o-mini",
#     tools=functions,
# )
assistant_id = "asst_rtrqB8zsqBQfntMyW58WJI8z"

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
