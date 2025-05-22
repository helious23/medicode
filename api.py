import os
import requests
from dotenv import load_dotenv
import streamlit as st
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time


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


# def get_drug_details(edi_code):
#     params = {"serviceKey": PRODUCT_API_KEY, "edi_code": edi_code, "type": "json"}
#     res = requests.get(DETAIL_URL, params=params)
#     res.raise_for_status()
#     return res.json().get("body", {}).get("items", [{}])[0].get("BAR_CODE", "")


def get_drug_details(edi_code):
    url = "https://biz.kpis.or.kr/kpis_biz/index.jsp?sso=ok"
    options = Options()
    options.add_argument("--headless")  # Headless 모드
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
        Object.defineProperty(navigator, 'platform', {
            get: () => "Win32"
        });
        Object.defineProperty(navigator, 'userAgent', {
            get: () => "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        });
        Object.defineProperty(navigator, 'appVersion', {
            get: () => "5.0 (Windows)"
        });
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """
        },
    )
    driver.get(url)

    try:
        # Navigate to the code mapping search
        search_menu_btn = WebDriverWait(driver, 100).until(
            EC.element_to_be_clickable((By.XPATH, "//*[text()='의약품정보검색']"))
        )
        search_menu_btn.click()

        mapping_menu_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[text()='코드매핑조회']"))
        )
        mapping_menu_btn.click()

        # Wait for 제품코드(개정후) input and enter edi_code
        input_box = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable(
                (
                    By.ID,
                    "mainframe.VFrameSet00.HFrameSet00.VFrameSet00.FrameSet00.M_MP00000060.form.divWork.form.divSearchTb.form.edtAdtPrdCd:input",
                )
            )
        )

        driver.execute_script("arguments[0].scrollIntoView(true);", input_box)
        time.sleep(1)
        input_box.click()
        input_box.send_keys(edi_code)

        # Click 조회
        # search_button = driver.find_element(By.CSS_SELECTOR, "button.btnSearch")
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[@class='nexacontentsbox'][.//div[text()='조회']]")
            )
        )
        search_button.click()
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//*[contains(@id, 'gridMSUPCDList.body:container')]//div[contains(@class, 'GridRowControl') and not(contains(@class, 'dummy'))]",
                )
            )
        )
        rows = driver.find_elements(
            By.XPATH,
            "//*[contains(@id, 'gridMSUPCDList.body:container')]//div[contains(@class, 'GridRowControl') and not(contains(@class, 'dummy'))]",
        )

        results = []
        for row in rows:
            if "dummy" in row.get_attribute("class"):
                continue
            cols = row.find_elements(By.CSS_SELECTOR, ".GridCellControl.cell")
            if len(cols) >= 12:
                result = {
                    "상품명": cols[1].text.strip(),
                    "보험코드": cols[8].text.strip(),
                    "약품규격": cols[2].text.strip(),
                    "적용규격": cols[9].text.strip(),
                    "표준코드": cols[6].text.strip(),
                }
                results.append(result)
        return results
    finally:
        driver.quit()
