import time
import streamlit as st
from agent.agent import create_agent, connect_with_langchain_db, clean_chat_memory
from snowflake.sqlalchemy import URL
from sqlalchemy import create_engine
from decouple import config
from datetime import datetime
from helpers import get_engine, get_df_file, write_to_last_query_text, get_intermediate_steps_str
import ast 
import pandas as pd 
import random


st.title("☃️ SQL Agent")
st.button("Clear history", on_click=clean_chat_memory)

engine = get_engine()
connection = engine.connect()

with st.spinner("Getting tables..."):
    connection_db = connect_with_langchain_db(engine)

if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = []
    clean_chat_memory()
    

agent_executor = create_agent(connection_db)
for message in st.session_state.chat_memory:
    with st.chat_message(message["type"]):
        st.write(message["content"])
        if "intermediate_steps_string" in message:

            st.write("My Intermediate_steps: ", message["intermediate_steps_string"])
            print(message["intermediate_steps_string"])
        # st.write(message.keys())
        if "last_sql_input" in message:
                dataframe = pd.read_sql(message["last_sql_input"], connection)
                st.dataframe(dataframe)
        if "output_table_name" in message.keys():
            df_file = get_df_file(output_table_name=message["output_table_name"])
            st.download_button(
                label="Download output data as CSV",
                data=df_file,
                file_name='output_table.csv',
                mime='text/csv',
            )


chat_input = st.chat_input("Chat here")
if chat_input:
    with st.chat_message('human'):
        st.write(chat_input) 
        # storing the data
        st.session_state.chat_memory.append(
            {
                "type" : "human",
                "content": chat_input
            }
        )
    
    with st.spinner("Thinking..."):
        response = agent_executor.invoke({"input": chat_input})
        output = response["output"]
        intermediate_steps_string = get_intermediate_steps_str(response)
        # adding last action log 
        write_to_last_query_text(response)
        with st.chat_message('ai'):
            st.write(output) 
            st.write(intermediate_steps_string)

            # storing the data
            ai_response = {
                "type" : "AI",
                "content": output,
                "intermediate_steps_string":intermediate_steps_string
            }
            if response["output_table_name"]:
                ai_response["output_table_name"] = response["output_table_name"]
                df_file = get_df_file(output_table_name=response["output_table_name"])
                st.download_button(
                    label="Download output data as CSV",
                    data=df_file,
                    file_name='output_table.csv',
                    mime='text/csv',
                    key=str(random.random()),
                )
            if response["intermediate_steps"] != []:
                last_observation = response["intermediate_steps"][-1][1]
                if last_observation.startswith("DataFrame: "):
                    if not last_observation.startswith("DataFrame: {'status': "):
                        last_sql_input = response["intermediate_steps"][-1][0].tool_input
                        ai_response["last_sql_input"] = last_sql_input
                        dataframe = pd.read_sql(last_sql_input, connection)
                        st.dataframe(dataframe)
            st.session_state.chat_memory.append(ai_response)
                
