import dotenv
dotenv.load_dotenv()
from openai import OpenAI
import asyncio
import streamlit as st
import time
from agents import Agent, Runner, SQLiteSession, WebSearchTool, FileSearchTool

client = OpenAI()

VECTOR_STORE_ID="vs_69deec2f2e2c819191c75ae0c3180b58"
if "agent" not in st.session_state:
    st.session_state["agent"] = Agent(
        name="Life Coach",
        instructions="""
        너는 유저를 격려하는 라이프 코치처럼 행동해야 한다.
        
        너는 이 도구들을 사용할수 있다.
            - Web Search Tool : Use this when the user asks a questions that isn't in your training data. Use this tool when the users asks about current or future events, 
            when you think you don't know the answer, try searching for it in the web first. 
            - File Search Tool : Use this tool when the users asks a question about facts related to themselves. Or when they ask questions about specific files.
        

        """,

        tools = [
            WebSearchTool(),
            FileSearchTool(
                vector_store_ids=[VECTOR_STORE_ID],
                max_num_results=3,
            )
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

        if "type" in message:
            if message["type"] == "web_serach_call":
                with st.chat_message("ai"):
                    st.write(f"웹에서 찾음...", " ")
            elif message["type"] == "file_search_call":
                with st.chat_message("ai"):
                    st.write(f"파일 검색함...", " ")
        

asyncio.run(paint_history())

def update_status(status_container, event):
    
    status_messages = {
        'response.web_search_call.completed': ("웹 검색 완료", "complete"),
        'response.web_search_call.in_progress': ("웹 검색 시작:", "running"),
        'response.web_search_call.searching': ("웹 검색중...", "running"),
        'response.file_search_call.completed': ("파일 검색 완료", "complete"),
        'response.file_search_call.in_progress': ("파일 검색 시작:", "running"),
        'response.file_search_call.searching': ("파일 검색중...", "running"),
    }

    if event in status_messages:
        label, state = status_messages[event]
        status_container.update(label=label, state=state)





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



prompt = st.chat_input(
    "Write a message for your assistant",
    accept_file=True,
    file_type=["txt"],

    )


if prompt:

    for file in prompt.files:
        if file.type.startswith("text/"):
            with st.chat_message("ai"):
                with st.status("파일 업로드중...") as status:
                    uploaded_file = client.files.create(
                        file=(file.name, file.getvalue()),
                        purpose="user_data",
                    )
                    status.update(label="파일 첨부중...")
                    client.vector_stores.files.create(
                        vector_store_id=VECTOR_STORE_ID,
                        file_id=uploaded_file.id
                    )
                    status.update(label="파일 업로드 완료", state="complete")
                

    if prompt.text:
        with st.chat_message("human"):
            st.write(prompt.text)
        asyncio.run(run_agent(prompt.text))
    


with st.sidebar:
    reset = st.button("Reset memory")
    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))