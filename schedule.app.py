import streamlit as st
import pandas as pd
import json
import os
import uuid
import calendar
import math
import gspread
from datetime import datetime, timedelta
import streamlit.components.v1 as components
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. 配置與常數 ---
st.set_page_config(
    page_title="2025社群排程與成效",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ⚠️ 請填入你的 Google Sheet 網址
SHEET_URL = "https://docs.google.com/spreadsheets/d/你的ID/edit" 
STANDARDS_FILE = "social_standards.json"

# Google API Scope
SCOPE = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# --- 核心設定：Google Sheet 中文欄位對照表 ---
COL_MAP = {
    'id': 'ID',
    'date': '日期',
    'platform': '平台',
    'topic': '主題',
    'postType': '類型',
    'postSubType': '子類型',
    'postPurpose': '目的',
    'postFormat': '形式',
    'projectOwner': '專案負責人',
    'postOwner': '貼文負責人',
    'designer': '美編',
    'status': '狀態',
    # 成效數據 (Input)
    'metrics7d_reach': '7天觸及',
    'metrics7d_likes': '7天按讚',
    'metrics7d_comments': '7天留言',
    'metrics7d_shares': '7天分享',
    'metrics1m_reach': '30天觸及',
    'metrics1m_likes': '30天按讚',
    'metrics1m_comments': '30天留言',
    'metrics1m_shares': '30天分享'
}

# 選項定義
PLATFORMS = ['Facebook', 'Instagram', 'LINE@', 'YouTube', 'Threads', '社團']
MAIN_POST_TYPES = ['喜餅', '彌月', '伴手禮', '社群互動', '圓夢計畫', '公告']
SOUVENIR_SUB_TYPES = ['端午節', '中秋', '聖誕', '新春', '蒙友週']
POST_PURPOSES = ['互動', '廣告', '門市廣告', '導購', '公告']
POST_FORMATS = ['單圖', '多圖', '假多圖', '短影音', '限動', '純文字', '留言處']

# 選項 (含空白)
PROJECT_OWNERS = ['', '夢涵', 'MOMO', '櫻樺', '季嫻', '凌萱', '宜婷', '門市']
POST_OWNERS = ['一千', '楷曜', '可榆']
DESIGNERS = ['', '千惟', '靖嬙']

# 樣式設定
ICONS = {'Facebook': '📘', 'Instagram': '📸', 'LINE@': '🟢', 'YouTube': '▶️', 'Threads': '🧵', '社團': '👥'}
PLATFORM_COLORS = {'Facebook': '#1877F2', 'Instagram': '#E1306C', 'LINE@': '#06C755', 'YouTube': '#FF0000', 'Threads': '#101010', '社團': '#F97316'}
PLATFORM_MARKS = {'Facebook': '🟦', 'Instagram': '🟪', 'LINE@': '🟩', 'YouTube': '🟥', 'Threads': '⬛', '社團': '🟧'}

# --- 2. Google Sheets 連線與資料處理 ---

def get_client():
    try:
        if "service_account" in st.secrets:
            creds_dict = dict(st.secrets["service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
            return gspread.authorize(creds)
        else:
            st.error("❌ 未設定 Secrets")
            return None
    except Exception as e:
        st.error(f"認證失敗: {e}")
        return None

def safe_num(val):
    try:
        if isinstance(val, str): val = val.replace(',', '').strip()
        f = float(val)
        if math.isnan(f) or math.isinf(f): return 0.0
        return f
    except: return 0.0

def load_data():
    client = get_client()
    if not client: return []
    try:
        sheet = client.open_by_url(SHEET_URL).sheet1
        raw_records = sheet.get_all_records()
        
        processed_posts = []
        for row in raw_records:
            def get_val(cn_key, default=""):
                return row.get(cn_key, default)

            raw_date = str(get_val('日期', ''))
            try:
                std_date = pd.to_datetime(raw_date).strftime('%Y-%m-%d')
            except:
                std_date = raw_date

            m7 = {
                'reach': safe_num(get_val('7天觸及', 0)),
                'likes': safe_num(get_val('7天按讚', 0)),
                'comments': safe_num(get_val('7天留言', 0)),
                'shares': safe_num(get_val('7天分享', 0))
            }
            m1 = {
                'reach': safe_num(get_val('30天觸及', 0)),
                'likes': safe_num(get_val('30天按讚', 0)),
                'comments': safe_num(get_val('30天留言', 0)),
                'shares': safe_num(get_val('30天分享', 0))
            }
            
            post = {
                'id': str(get_val('ID')) if get_val('ID') else str(uuid.uuid4()),
                'date': std_date,
                'platform': str(get_val('平台', 'Facebook')),
                'topic': str(get_val('主題', '')),
                'postType': str(get_val('類型', '')),
                'postSubType': str(get_val('子類型', '')),
                'postPurpose': str(get_val('目的', '')),
                'postFormat': str(get_val('形式', '')),
                'projectOwner': str(get_val('專案負責人', '')),
                'postOwner': str(get_val('貼文負責人', '')),
                'designer': str(get_val('美編', '')),
                'status': str(get_val('狀態', 'published')),
                'metrics7d': m7,
                'metrics1m': m1
            }
            processed_posts.append(post)
        return processed_posts
    except Exception as e:
        return []

def save_data(data):
    client = get_client()
    if not client: return
    try:
        sheet = client.open_by_url(SHEET_URL).sheet1
        
        flat_data = []
        for p in data:
            m7 = p.get('metrics7d', {})
            m1 = p.get('metrics1m', {})
            flat_data.append({
                'id': p.get('id'),
                'date': p.get('date'),
                'platform': p.get('platform'),
                'topic': p.get('topic'),
                'postType': p.get('postType'),
                'postSubType': p.get('postSubType'),
                'postPurpose': p.get('postPurpose'),
                'postFormat': p.get('postFormat'),
                'projectOwner': p.get('projectOwner'),
                'postOwner': p.get('postOwner'),
                'designer': p.get('designer'),
                'status': p.get('status', 'published'),
                'metrics7d_reach': m7.get('reach', 0), 'metrics7d_likes': m7.get('likes', 0),
                'metrics7d_comments': m7.get('comments', 0), 'metrics7d_shares': m7.get('shares', 0),
                'metrics1m_reach': m1.get('reach', 0), 'metrics1m_likes': m1.get('likes', 0),
                'metrics1m_comments': m1.get('comments', 0), 'metrics1m_shares': m1.get('shares', 0)
            })

        if flat_data:
            df = pd.DataFrame(flat_data)
            df = df.rename(columns=COL_MAP)
            
            chinese_cols_order = [
                'ID', '日期', '平台', '主題', '類型', '子類型', '目的', '形式', 
                '專案負責人', '貼文負責人', '美編', '狀態',
                '7天觸及', '7天按讚', '7天留言', '7天分享',
                '30天觸及', '30天按讚', '30天留言', '30天分享'
            ]
            
            for c in chinese_cols_order:
                if c not in df.columns: df[c] = ""
            
            df = df[chinese_cols_order]
            
            sheet.clear()
            update_data = [df.columns.values.tolist()] + df.values.tolist()
            sheet.update(update_data)
        else:
            sheet.clear()
            sheet.append_row(list(COL_MAP.values()))

    except Exception as e:
        st.error(f"儲存失敗: {e}")

# KPI 標準
def load_standards():
    defaults = {'Facebook': {'type': 'tiered', 'high': {'reach': 2000, 'engagement': 100}, 'std': {'reach': 1500, 'engagement': 45}, 'low': {'reach': 1000, 'engagement': 15}},'Instagram': {'type': 'simple', 'reach': 900, 'engagement': 30},'Threads': {'type': 'reference', 'reach': 500, 'reach_label': '瀏覽', 'engagement': 50, 'engagement_label': '互動', 'rate': 0},'YouTube': {'type': 'simple', 'reach': 500, 'engagement': 20},'LINE@': {'type': 'simple', 'reach': 0, 'engagement': 0},'社團': {'type': 'simple', 'reach': 500, 'engagement': 20}}
    if not os.path.exists(STANDARDS_FILE): return defaults
    try:
        with open(STANDARDS_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return defaults

def save_standards(standards):
    with open(STANDARDS_FILE, 'w', encoding='utf-8') as f: json.dump(standards, f, ensure_ascii=False, indent=4)

def is_metrics_disabled(platform, fmt): return platform == 'LINE@' or fmt in ['限動', '留言處']

def get_performance_label(platform, metrics, fmt, standards):
    if is_metrics_disabled(platform, fmt): return "🚫 不計", "gray", "此形式/平台不需計算成效"
    reach = safe_num(metrics.get('reach', 0))
    if reach == 0: return "-", "gray", "尚未填寫數據"
    eng = safe_num(metrics.get('likes', 0)) + safe_num(metrics.get('comments', 0)) + safe_num(metrics.get('shares', 0))
    rate = (eng / reach) * 100
    std = standards.get(platform, {})
    if not std: return "-", "gray", "未設定標準"
    label = "-"; color = "gray"; tooltip = ""
    def check_pass(target_r, target_e):
        target_rate = (target_e / target_r * 100) if target_r > 0 else 0
        return (reach >= target_r) or (eng >= target_e) or (rate >= target_rate)
    if platform == 'Facebook':
        h = std.get('high', {'reach': 2000, 'engagement': 100})
        s = std.get('std', {'reach': 1500, 'engagement': 45})
        l = std.get('low', {'reach': 1000, 'engagement': 15})
        h_rt = (h.get('engagement', 0)/h.get('reach', 1)*100) if h.get('reach', 0)>0 else 0
        s_rt = (s.get('engagement', 0)/s.get('reach', 1)*100) if s.get('reach', 0)>0 else 0
        l_rt = (l.get('engagement', 0)/l.get('reach', 1)*100) if l.get('reach', 0)>0 else 0
        tooltip = f"高標: 觸及{int(h.get('reach',0))} / 互動{int(h.get('engagement',0))} (率{h_rt:.1f}%)\n標準: 觸及{int(s.get('reach',0))} / 互動{int(s.get('engagement',0))} (率{s_rt:.1f}%)\n低標: 觸及{int(l.get('reach',0))} / 互動{int(l.get('engagement',0))} (率{l_rt:.1f}%)"
        if check_pass(h.get('reach', 2000), h.get('engagement', 100)): return "🏆 高標雙指標" if (reach >= h.get('reach') and eng >= h.get('engagement')) else ("🏆 高標觸及" if reach >= h.get('reach') else "🏆 高標互動"), "purple", tooltip
        elif check_pass(s.get('reach', 1500), s.get('engagement', 45)): return "✅ 標準雙指標" if (reach >= s.get('reach') and eng >= s.get('engagement')) else ("✅ 標準觸及" if reach >= s.get('reach') else "✅ 標準互動"), "green", tooltip
        elif check_pass(l.get('reach', 1000), l.get('engagement', 15)): return "🤏 低標雙指標" if (reach >= l.get('reach') and eng >= l.get('engagement')) else ("🤏 低標觸及" if reach >= l.get('reach') else "🤏 低標互動"), "orange", tooltip
        else: return "🔴 未達標", "red", tooltip
    elif platform in ['Instagram', 'YouTube', '社團']:
        t_reach = std.get('reach', 0); t_eng = std.get('engagement', 0); t_rate = (t_eng / t_reach * 100) if t_reach > 0 else 0
        tooltip = f"目標: 觸及 {int(t_reach)} / 互動 {int(t_eng)} (率{t_rate:.1f}%)"
        if check_pass(t_reach, t_eng): return "✅ 達標", "green", tooltip
        else: return "🔴 未達標", "red", tooltip
    elif platform == 'Threads':
        t_reach = std.get('reach', 500); t_eng = std.get('engagement', 50); l_reach = std.get('reach_label', '瀏覽'); l_eng = std.get('engagement_label', '互動')
        tooltip = f"{l_reach}: {int(t_reach)} / {l_eng}: {int(t_eng)}"
        pass_reach = reach >= t_reach; pass_eng = eng >= t_eng
        if pass_reach and pass_eng: return "✅ 雙指標", "green", tooltip
        elif pass_reach: return f"✅ {l_reach}", "green", tooltip
        elif pass_eng: return f"✅ {l_eng}", "green", tooltip
        else: return "🔴 未達標", "red", tooltip
    return label, color, tooltip

def process_post_metrics(p):
    m7 = p.get('metrics7d', {}); m30 = p.get('metrics1m', {})
    r7 = safe_num(m7.get('reach', 0)); e7 = safe_num(m7.get('likes', 0)) + safe_num(m7.get('comments', 0)) + safe_num(m7.get('shares', 0))
    r30 = safe_num(m30.get('reach', 0)); e30 = safe_num(m30.get('likes', 0)) + safe_num(m30.get('comments', 0)) + safe_num(m30.get('shares', 0))
    rate7_val = (e7 / r7 * 100) if r7 > 0 else 0; rate30_val = (e30 / r30 * 100) if r30 > 0 else 0
    disabled = is_metrics_disabled(p.get('platform'), p.get('postFormat')); is_threads = p.get('platform') == 'Threads'
    rate7_str = "-"; rate30_str = "-"
    if disabled or is_threads: rate7_str = "🚫 不計"; rate30_str = "🚫 不計"
    elif r7 > 0: rate7_str = f"{rate7_val:.1f}%"; rate30_str = f"{rate30_val:.1f}%" if r30 > 0 else "-"
    today = datetime.now().date()
    try: p_date = datetime.strptime(p.get('date', ''), "%Y-%m-%d").date()
    except: p_date = today
    bell7 = False; bell30 = False
    if not disabled: 
        if today >= (p_date + timedelta(days=7)) and r7 == 0: bell7 = True
        if today >= (p_date + timedelta(days=30)) and r30 == 0: bell
