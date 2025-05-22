import streamlit as st


def copy_to_clipboard(text):
    st.code(text, language="text")
    st.button(
        "📋 클립보드에 복사하기", on_click=st.write, args=("Ctrl+C로 복사해 주세요.",)
    )
