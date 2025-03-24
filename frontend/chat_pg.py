import streamlit as st
import requests
import sqlparse
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import SqlLexer
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL")
if not API_URL:
    st.error("API_URL environment variable is not set")
    st.stop()

API_URL = API_URL.rstrip('/')

st.set_page_config(page_title="AI SQL Assistant", layout="wide")

st.title("🤖 AI SQL Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

try:
    health_response = requests.get(f"{API_URL}/health")
    if health_response.status_code == 200:
        health_data = health_response.json()
        if not health_data.get("model_loaded", False):
            load_response = requests.post(f"{API_URL}/load-model")
            if load_response.status_code != 200:
                st.error("Failed to load the model")
except requests.exceptions.RequestException as e:
    st.error(f"cant connect to the api: {str(e)}")
    st.stop()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant" and "sql" in message:
            formatted_sql = sqlparse.format(
                message["sql"], reindent=True, keyword_case="upper"
            )
            highlighted_sql = highlight(
                formatted_sql, SqlLexer(), HtmlFormatter(style="monokai")
            )
            st.markdown(message["content"])
            st.markdown(
                f'<div class="sql-code">{highlighted_sql}</div>', unsafe_allow_html=True
            )
        else:
            st.markdown(message["content"])

if prompt := st.chat_input("Feel free to ask anything about SQL!"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        with st.chat_message("assistant"):
            with st.spinner("Generating SQL query..."):
                response = requests.post(
                    f"{API_URL}/generate-sql",
                    json={"query": prompt},
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    result = response.json()
                    if result is None:
                        st.error("Invalid response from API")
                        st.session_state.messages.append(
                            {"role": "assistant", "content": "Try again"}
                        )
                    else:
                        sql = result.get("sql", "")
                        formatted_sql = result.get("sql_formatted", sql)

                        formatted_sql = sqlparse.format(
                            formatted_sql, reindent=True, keyword_case="upper"
                        )
                        highlighted_sql = highlight(
                            formatted_sql, SqlLexer(), HtmlFormatter(style="monokai")
                        )

                        st.markdown(
                            f'<div class="sql-code">{highlighted_sql}</div>',
                            unsafe_allow_html=True,
                        )

                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": "Here's the SQL query for your request:",
                                "sql": sql,
                            }
                        )
                else:
                    st.error(f"Failed to generate SQL: {response.text}")
                    st.session_state.messages.append(
                        {"role": "assistant", "content": "Failed to generate SQL"}
                    )
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the API: {str(e)}")
        st.session_state.messages.append(
            {"role": "assistant", "content": "❌ Connection error"}
        )