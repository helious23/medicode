import os
import requests
from dotenv import load_dotenv
import streamlit as st
from bs4 import BeautifulSoup as bs

load_dotenv()

EDI_API_KEY = (
    st.secrets["edi_api_key"]
    if "edi_api_key" in st.secrets
    else os.getenv("EDI_API_KEY")
)
PRODUCT_API_KEY = (
    st.secrets["product_api_key"]
    if "product_api_key" in st.secrets
    else os.getenv("PRODUCT_API_KEY")
)

LIST_URL = "http://apis.data.go.kr/B551182/dgamtCrtrInfoService1.2/getDgamtList"
DETAIL_URL = (
    "http://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService06/getDrugPrdtPrmsnDtlInq05"
)


def search_drugs(keyword):
    params = {
        "serviceKey": EDI_API_KEY,
        "numOfRows": 10,
        "pageNo": 1,
        "itmNm": keyword,
        "type": "json",
    }
    try:
        res = requests.get(LIST_URL, params=params)
        res.raise_for_status()
        if res.status_code == 200:
            html = res.text
            soup = bs(html, "xml")
            items = soup.find_all("item")
            items = [
                item
                for item in items
                if item.find("payTpNm") and item.find("payTpNm").text != "삭제"
            ]
            results = [
                {
                    "itemName": item.find("itmNm").text or "",
                    "ediCode": item.find("mdsCd").text or "",
                    "manufacturer": item.find("mnfEntpNm").text or "",
                    "payType": item.find("payTpNm").text or "",
                    "unit": item.find("unit").text or "",
                }
                for item in items
            ]
            return results
        else:
            return []
    except requests.exceptions.HTTPError as e:
        print(f"API 요청 실패: {e}")
        return []


def get_drug_details(edi_code):
    params = {"serviceKey": PRODUCT_API_KEY, "edi_code": edi_code, "type": "json"}
    res = requests.get(DETAIL_URL, params=params)
    res.raise_for_status()
    return res.json().get("body", {}).get("items", [{}])[0].get("BAR_CODE", "")
