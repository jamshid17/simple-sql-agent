from langchain.memory import ConversationBufferWindowMemory
from .agent_prompt import sql_helper_prompt_template, second_tool_description
from langchain.agents import AgentExecutor, LLMSingleActionAgent, AgentOutputParser
from langchain.chains.llm import LLMChain
from langchain.chat_models import AzureChatOpenAI
from langchain.agents.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from decouple import config
import os
from .custom_classes import CustomOutputParser, CustomPromptTemplate, CustomSQLDatabase
import streamlit as st
from sqlalchemy.engine.base import Connection, Engine
from langchain.memory.chat_message_histories import RedisChatMessageHistory, StreamlitChatMessageHistory


os.environ["OPENAI_API_TYPE"] = config("OPENAI_API_TYPE")
os.environ["OPENAI_API_BASE"] = config("OPENAI_API_BASE")
os.environ["OPENAI_API_VERSION"] = config("OPENAI_API_VERSION")
os.environ["OPENAI_API_KEY"] = config("OPENAI_API_KEY")


# I could not find any good resource to cache db connection in streamlit, but I think it is doable
@st.cache_resource(hash_funcs={Engine:id})
def connect_with_langchain_db(engine):
    print("here")
    db = CustomSQLDatabase(engine)
    return db


def create_agent(snowflake_db):
    llm_chat_model = AzureChatOpenAI(deployment_name="gpt-4-32k", temperature=0)
    # db = SQLDatabase(connection, include_tables=include_tables)
    toolkit = SQLDatabaseToolkit(
        db=snowflake_db, llm=AzureChatOpenAI(deployment_name="gpt-4", temperature=0)
    )
    tools = toolkit.get_tools()
    tools[1].description = second_tool_description

    tool_names = [tool.name for tool in tools]

    prompt = CustomPromptTemplate(
        template=sql_helper_prompt_template,
        tools=tools,
        # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
        # This includes the `intermediate_steps` variable because that is needed
        input_variables=["input", "intermediate_steps", "history"],
    )
    output_parser = CustomOutputParser()
    llm_chain = LLMChain(llm=llm_chat_model, prompt=prompt)
    agent = LLMSingleActionAgent(
        llm_chain=llm_chain,
        output_parser=output_parser,
        stop=["\nObservation:"],
        allowed_tools=tool_names,
    )
    message_history = StreamlitChatMessageHistory()
    # message_history = RedisChatMessageHistory(
    #     url="redis://localhost:6379/0", ttl=600, session_id="my-session"
    # )
    memory = ConversationBufferWindowMemory(
        memory_key="history",
        chat_memory=message_history,
        k=10,
        return_messages=True,
        output_key="output",
        input_key="input",
    )

    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        verbose=True,
        memory=memory,
        return_intermediate_steps=True,
    )
    return agent_executor


def clean_chat_memory():
    # message_history = StreamlitChatMessageHistory()
    # message_history.clear()
    with open("last_query.txt", "w") as f:
        f.write("")
    st.session_state.chat_memory = []
