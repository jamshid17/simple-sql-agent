from snowflake.sqlalchemy import URL
from sqlalchemy import create_engine
from decouple import config
import streamlit as st
import pandas as pd
import re 


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


def get_intermediate_steps_str(response):
    final_str = ''
    for step in response["intermediate_steps"]:
        agent_action, observation = step
        if observation.startswith("DataFrame: "):
            observation = "DataFrame below"
        action_log = agent_action.log

        final_str += f"{action_log}\n\nObservation: {observation}\n\n"
    return final_str


def get_output_parts(response, connection):
    pattern = r"```sql\n(.*?)\n```"
    
    match = re.search(pattern, response, re.DOTALL)
    dataframe = None
    
    if match:
        sql_query = match.group(1)
        if not sql_query.startswith("CREATE"):
            dataframe = pd.read_sql(sql_query, connection)
        before_sql, _, after_sql = response.partition(match.group(0))
        
        return before_sql.strip(), dataframe, after_sql.strip()
    else:
        return response, None, None
    
    
