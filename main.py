from pickle import NONE
import dotenv
from streamlit.runtime.state import query_params

dotenv.load_dotenv()
import asyncio
import streamlit as st
import time
from agents import Agent, Runner, SQLiteSession, WebSearchTool

if "agent" not in st.session_state:
    st.session_state["agent"] = Agent(
        name="Life Coach",
        instructions="""
        You are a helpful life coach assistant.
        너는 유저를 격려하는 라이프 코치처럼 행동해야 한다.
        유저가 질문한 것에 조언하려면 웹 검색 도구를 사용한 내용을 올린다.
        !! IMPORTANT !!
        간단한 대화 조차 너는 무조건 도구를 사용해서 답변을 할수있도록.
        도구는 WebSearchTool()이 있으니 무조건 이것만 쓰도록한다.
        
        """,
        tools = [
            WebSearchTool()
            ],
        
    )
agent = st.session_state["agent"]

if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "chat-history",
        "life-coach-memory-dummy.db",
    )
session = st.session_state["session"]

async def paint_history():
    messages = await session.get_items()
    for message in messages:
        if "role" in message:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.write(message["content"])
                else:
                    if message["type"] == "message":
                        st.write(message["content"][0]["text"])

        if "type" in message and message["type"] == "web_search_call":
            query = message.get("query", "") or message.get("action", {}).get("query", "")
            with st.chat_message("ai"):
                st.write(f"[웹 검색: {query}]")


def update_status(status_container, event):
    
    status_messages = {
        'response.web_search_call.completed': ("웹 검색 완료", "complete"),
        'response.web_search_call.in_progress': ("웹 검색 시작:", "running"),
        'response.web_search_call.searching': ("웹 검색중...", "running"),
        'response.completed':(" ","complete")
    }

    if event in status_messages:
        label, state = status_messages[event]
        status_container.update(label=label, state=state)



asyncio.run(paint_history())

async def run_agent(message):
    with st.chat_message("ai"):
        status_container = st.status("⏳", expanded=False)
        text_placeholder = st.empty()
        response = ""
        stream = Runner.run_streamed(
            agent,
            message,
            session=session,
        )

        async for event in stream.stream_events():
            if event.type == "raw_response_event":

                update_status(status_container, event.data.type)
                if event.data.type == "response.output_text.delta":
                    response += event.data.delta
                    text_placeholder.write(response)



prompt = st.chat_input("Write a message for your assistant")

if prompt:
    with st.chat_message("human"):
        st.write(prompt)
    asyncio.run(run_agent(prompt))


with st.sidebar:
    reset = st.button("Reset memory")
    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))