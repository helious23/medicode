import streamlit as st
from api import search_drugs, get_drug_details
from utils import copy_to_clipboard

st.set_page_config(page_title="의약품 검색기", layout="centered")

st.title("💊 의약품 검색 서비스")

query = st.text_input("의약품 이름을 입력하세요")

if query:
    if (
        "search_results" not in st.session_state
        or st.session_state.get("last_query") != query
    ):
        with st.spinner("🔍 의약품을 검색 중입니다..."):
            st.session_state.search_results = search_drugs(query)
            st.session_state.last_query = query

    results = st.session_state.search_results
    options = {f"{r['itemName']} ({r['ediCode']})": r["ediCode"] for r in results}
    selected = st.selectbox("검색 결과", list(options.keys()))

    if selected:
        edi_code = options[selected]
        with st.spinner("📦 바코드 정보를 불러오는 중입니다..."):
            barcode = get_drug_details(edi_code) or "정보 없음"
        st.subheader("📦 바코드")
        for code in barcode.split(","):
            code = code.strip()
            st.code(code, language="text")
