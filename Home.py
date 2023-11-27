import time
import streamlit as st
from agent.agent import create_agent, connect_with_langchain_db, clean_chat_memory
from snowflake.sqlalchemy import URL
from sqlalchemy import create_engine
from decouple import config
from datetime import datetime
from helpers import get_engine

st.title("☃️ SQL Agent")
st.button("Clear history", on_click=clean_chat_memory)

engine = get_engine()
with st.spinner("Getting tables..."):
    connection_db = connect_with_langchain_db(engine)

agent_executor, memory = create_agent(connection_db)
for message in memory.chat_memory.messages:
    with st.chat_message(message.type):
        st.write(message.content)

chat_input = st.chat_input("Chat here")
if chat_input:
    with st.chat_message('human'):
        st.write(chat_input) 
    
    with st.spinner("Thinking..."):
        response = agent_executor.invoke({"input": chat_input})
        output = response["output"]
        with st.chat_message('ai'):
            st.write(output) 
