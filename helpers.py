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
    sql_query = f"SELECT * FROM TESTFORADF.PUBLIC.{output_table_name.upper()}"
    df = pd.read_sql(sql_query, connection)
    return df.to_csv().encode('utf-8')