import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

# --- 設定 ---
# 你的 Google Sheet 網址
SHEET_URL = "https://docs.google.com/spreadsheets/d/你的ID/edit" 
SCOPE = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

def get_client():
    try:
        # 讀取 secrets 中的 service_account 區塊
        creds_dict = dict(st.secrets["service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"金鑰認證失敗: {e}")
        return None

def load_data():
    client = get_client()
    if not client: return []
    try:
        sheet = client.open_by_url(SHEET_URL).sheet1
        records = sheet.get_all_records() # 取得所有資料
        return records
    except Exception as e:
        # 如果是空的或者是新表格，回傳空列表
        return []

def save_data(data):
    client = get_client()
    if not client: return
    try:
        sheet = client.open_by_url(SHEET_URL).sheet1
        sheet.clear() # 清空舊資料
        
        # 準備寫入資料 (將 List of Dicts 轉為 List of Lists)
        if data:
            df = pd.DataFrame(data)
            # 寫入標題
            update_data = [df.columns.values.tolist()] + df.values.tolist()
            sheet.update(update_data)
        else:
            pass # 空資料不動作
            
        # st.success("已儲存至 Google Sheets")
    except Exception as e:
        st.error(f"儲存失敗: {e}")
