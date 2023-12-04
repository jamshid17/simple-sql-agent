from snowflake.sqlalchemy import URL
from sqlalchemy import create_engine
from decouple import config
import streamlit as st
import pandas as pd


@st.cache_resource
def get_engine():
    url = URL(
        user=config("sn_username"),
        password=config("sn_password"),
        account=config("sn_account"),
        warehouse=config("sn_warehouse"),
        database=config("sn_database"),
        schema=config("sn_schema"),
        role=config("sn_role"),

    )
    engine = create_engine(url)
    return engine

@st.cache_data
def get_df_file(output_table_name):
    url = URL(
        user=config("sn_username"),
        password=config("sn_password"),
        account=config("sn_account"),
        warehouse=config("sn_warehouse"),
        database=config("sn_database"),
        schema=config("sn_schema"),
        role=config("sn_role"),

    )
    engine = create_engine(url)
    connection = engine.connect()
    sql_query = f"SELECT * FROM PROD_USE_CASES.ALAMO.{output_table_name.upper()}"
    df = pd.read_sql(sql_query, connection)
    return df.to_csv().encode('utf-8')


def write_to_last_query_text(response):
    last_five_actions = last_five_actions_text()
    intermediate_steps = response["intermediate_steps"]
    if len(intermediate_steps) != 0:
        last_action = intermediate_steps[-1][0]
        last_action_log = f"Action tool: {last_action.tool}\nInput: {last_action.tool_input}"
        if len(last_five_actions.split("\n\n")) == 5: 
            last_five_actions = "".join(action_log + "\n\n" for action_log in last_five_actions.split("\n\n")[1:])[:-2]
            last_five_actions = f"{last_five_actions}\n\n{last_action_log}"
        elif last_five_actions == "":
            last_five_actions = last_action_log
        else:
            last_five_actions = f"{last_five_actions}\n\n{last_action_log}"

        with open("last_query.txt", "w") as f: 
            f.write(last_five_actions)


def last_five_actions_text():
    try:
        with open("last_query.txt", "r") as last_query_file:
            last_action_input = last_query_file.read()
    except Exception as e:
        print(e, ' exception')
        last_action_input = ''
    return last_action_input

def get_intermediate_steps_str(response):
    final_str = ''
    for step in response["intermediate_steps"]:
        agent_action, observation = step
        if observation.startswith("DataFrame: "):
            observation = "DataFrame below"
        final_str += f"{agent_action.log}\n\nObservation: {observation}\n\n"
    
    return final_str