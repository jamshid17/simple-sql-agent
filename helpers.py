from snowflake.sqlalchemy import URL
from sqlalchemy import create_engine
from decouple import config
import streamlit as st


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