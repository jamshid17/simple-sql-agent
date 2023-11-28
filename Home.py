import time
import streamlit as st
from agent.agent import create_agent, connect_with_langchain_db, clean_chat_memory
from snowflake.sqlalchemy import URL
from sqlalchemy import create_engine
from decouple import config
from datetime import datetime
from helpers import get_engine, get_df_file
import ast 
import pandas as pd 

st.title("☃️ SQL Agent")
st.button("Clear history", on_click=clean_chat_memory)

engine = get_engine()
connection = engine.connect()

with st.spinner("Getting tables..."):
    connection_db = connect_with_langchain_db(engine)

if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = []

agent_executor = create_agent(connection_db)
for message in st.session_state.chat_memory:
    with st.chat_message(message["type"]):
        st.write(message["content"])
        if "DF" in message:
            last_observation_data = ast.literal_eval(message["DF"].split("DF: ")[1])
            dataframe = pd.DataFrame(last_observation_data)
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
        with st.chat_message('ai'):
            st.write(output) 
            # storing the data
            ai_response = {
                "type" : "AI",
                "content": output
            }
            if response["output_table_name"]:
                ai_response["output_table_name"] = response["output_table_name"]
                df_file = get_df_file(output_table_name=response["output_table_name"])
                st.download_button(
                    label="Download output data as CSV",
                    data=df_file,
                    file_name='output_table.csv',
                    mime='text/csv',
                )
            if response["intermediate_steps"] != []:
                last_observation = response["intermediate_steps"][-1][1]
                if last_observation.startswith("DF: "):
                    ai_response["DF"] = last_observation
                    last_observation_data = ast.literal_eval(last_observation.split("DF: ")[1])
                    dataframe = pd.DataFrame(last_observation_data)
                    st.dataframe(dataframe)
            st.session_state.chat_memory.append(ai_response)
                