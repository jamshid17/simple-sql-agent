import streamlit as st
from agent.agent import create_agent, connect_with_langchain_db, clean_chat_memory
from helpers import get_engine, get_df_file, get_intermediate_steps_str, get_output_parts
from pandas.core.frame import DataFrame 
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
        output = message["content"]
        output_intro, dataframe, output_outro = get_output_parts(output, connection)
        st.write(output_intro)
        if type(dataframe) == DataFrame:
            st.dataframe(dataframe)
        if output_outro:
            st.write(output_outro)
            
        if "intermediate_steps_string" in message:
            st.write("MY INTERMEDIATE STEPS: \n\n", message["intermediate_steps_string"])
            print(message["intermediate_steps_string"])
        # st.write(message.keys())
        # if "output_table_name" in message.keys():
        #     df_file = get_df_file(output_table_name=message["output_table_name"])
        #     st.download_button(
        #         label="Download output data as CSV",
        #         data=df_file,
        #         file_name='output_table.csv',
        #         mime='text/csv',
        #     )

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
        output_intro, dataframe, output_outro = get_output_parts(output, connection)
        intermediate_steps_string = get_intermediate_steps_str(response)
        # adding last action log 
        with st.chat_message('ai'):
            st.write(output_intro)
            if type(dataframe) == DataFrame:
                st.dataframe(dataframe)
            if output_outro:
                st.write(output_outro)
            st.write("MY INTERMEDIATE STEPS: \n\n", intermediate_steps_string)

            # storing the data
            ai_response = {
                "type" : "AI",
                "content": output,
                "intermediate_steps_string":intermediate_steps_string
            }
            # if response["output_table_name"]:
            #     ai_response["output_table_name"] = response["output_table_name"]
            #     df_file = get_df_file(output_table_name=response["output_table_name"])
            #     st.download_button(
            #         label="Download output data as CSV",
            #         data=df_file,
            #         file_name='output_table.csv',
            #         mime='text/csv',
            #         key=str(random.random()),
            #     )
            st.session_state.chat_memory.append(ai_response)
                
