import streamlit as st
import pandas as pd
import json
import os
import uuid
import calendar
import streamlit.components.v1 as components
from datetime import datetime, timedelta
import io
import math # 新增 math 模組處理 NaN

# --- 1. 配置與常數 ---
st.set_page_config(
    page_title="2025社群排程與成效",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 檔案路徑
DATA_FILE = "social_posts.json"
STANDARDS_FILE = "social_standards.json"

# 選項定義
PLATFORMS = ['Facebook', 'Instagram', 'LINE@', 'YouTube', 'Threads', '社團']
MAIN_POST_TYPES = ['喜餅', '彌月', '伴手禮', '社群互動', '圓夢計畫', '公告']
SOUVENIR_SUB_TYPES = ['端午節', '中秋', '聖誕', '新春', '蒙友週']
POST_PURPOSES = ['互動', '廣告', '門市廣告', '導購', '公告']
POST_FORMATS = ['單圖', '多圖', '假多圖', '短影音', '限動', '純文字', '留言處']

# 專案負責人
PROJECT_OWNERS = ['夢涵', 'MOMO', '櫻樺', '季嫻', '凌萱', '宜婷', '門市']
POST_OWNERS = ['一千', '楷曜', '可榆']
DESIGNERS = ['千惟', '靖嬙']

# 定義廣告類型的目的
AD_PURPOSE_LIST = ['廣告', '門市廣告']

# CSV 欄位對照 (匯入用：中文 -> 英文 key)
CSV_IMPORT_MAP = {
    '日期': 'date', '平台': 'platform', '主題': 'topic', '類型': 'postType',
    '子類型': 'postSubType', '目的': 'postPurpose', '形式': 'postFormat',
    '專案負責人': 'projectOwner', '貼文負責人': 'postOwner', '美編': 'designer',
    '7天瀏覽/觸及': 'metrics7d_reach', '7天互動': 'metrics7d_eng',
    '30天瀏覽/觸及': 'metrics1m_reach', '30天互動': 'metrics1m_eng'
}

# Icon Mapping (列表標籤用)
ICONS = {
    'Facebook': '📘', 'Instagram': '📸', 'LINE@': '🟢', 'YouTube': '▶️', 'Threads': '🧵',
    '社團': '👥',
    'reach': '👀', 'likes': '❤️', 'comments': '💬', 'rate': '📈'
}

# 平台顏色對照 (全域定義)
PLATFORM_COLORS = {
    'Facebook': '#1877F2',   # FB Blue
    'Instagram': '#E1306C',  # IG Pink
    'LINE@': '#06C755',      # LINE Green
    'YouTube': '#FF0000',    # YT Red
    'Threads': '#101010',    # Threads Black
    '社團': '#F97316'        # Community Orange
}

# 平台隱藏標記 (用於 CSS 選擇器)
PLATFORM_MARKS = {
    'Facebook': '🟦', 'Instagram': '🟪', 'LINE@': '🟩', 
    'YouTube': '🟥', 'Threads': '⬛', '社團': '🟧'
}

# --- 2. 資料處理函式 ---

def load_data():
    if not os.path.exists(DATA_FILE): return []
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return []

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=4)

def load_standards():
    defaults = {
        'Facebook': {'type': 'tiered', 'high': {'reach': 2000, 'engagement': 100}, 'std': {'reach': 1500, 'engagement': 45}, 'low': {'reach': 1000, 'engagement': 15}},
        'Instagram': {'type': 'simple', 'reach': 900, 'engagement': 30},
        'Threads': {'type': 'reference', 'reach': 500, 'reach_label': '瀏覽', 'engagement': 50, 'engagement_label': '互動', 'rate': 0},
        'YouTube': {'type': 'simple', 'reach': 500, 'engagement': 20},
        'LINE@': {'type': 'simple', 'reach': 0, 'engagement': 0},
        '社團': {'type': 'simple', 'reach': 500, 'engagement': 20}
    }
    if not os.path.exists(STANDARDS_FILE): return defaults
    try:
        with open(STANDARDS_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return defaults

def save_standards(standards):
    with open(STANDARDS_FILE, 'w', encoding='utf-8') as f: json.dump(standards, f, ensure_ascii=False, indent=4)

def is_metrics_disabled(platform, fmt):
    return platform == 'LINE@' or fmt in ['限動', '留言處']

def safe_num(val):
    """安全轉換數值，防止 NaN 導致 int() 崩潰"""
    try:
        f = float(val)
        # 檢查是否為 NaN (NaN != NaN 在 Python 中為 True) 或 無限大
        if f != f or f == float('inf') or f == float('-inf'):
            return 0.0
        return f
    except:
        return 0.0

def get_performance_label(platform, metrics, fmt, standards):
    """
    回傳: (標籤文字, 顏色class, Tooltip提示文字)
    邏輯：只要一項達標 (觸及 OR 互動 OR 互動率) 即算達標
    """
    if is_metrics_disabled(platform, fmt): 
        return "🚫 不計", "gray", "此形式/平台不需計算成效"
    
    reach = safe_num(metrics.get('reach', 0))
    if reach == 0: 
        return "-", "gray", "尚未填寫數據"
    
    eng = safe_num(metrics.get('likes', 0)) + safe_num(metrics.get('comments', 0)) + safe_num(metrics.get('shares', 0))
    rate = (eng / reach) * 100
    
    std = standards.get(platform, {})
    if not std: return "-", "gray", "未設定標準"
    
    label = "-"
    color = "gray"
    tooltip = ""

    # Helper function for OR logic
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
        
        if check_pass(h.get('reach', 2000), h.get('engagement', 100)):
            return "🏆 高標雙指標" if (reach >= h.get('reach') and eng >= h.get('engagement')) else ("🏆 高標觸及" if reach >= h.get('reach') else "🏆 高標互動"), "purple", tooltip
        elif check_pass(s.get('reach', 1500), s.get('engagement', 45)):
            return "✅ 標準雙指標" if (reach >= s.get('reach') and eng >= s.get('engagement')) else ("✅ 標準觸及" if reach >= s.get('reach') else "✅ 標準互動"), "green", tooltip
        elif check_pass(l.get('reach', 1000), l.get('engagement', 15)):
            return "🤏 低標雙指標" if (reach >= l.get('reach') and eng >= l.get('engagement')) else ("🤏 低標觸及" if reach >= l.get('reach') else "🤏 低標互動"), "orange", tooltip
        else: return "🔴 未達標", "red", tooltip
        
    elif platform in ['Instagram', 'YouTube', '社團']:
        t_reach = std.get('reach', 0)
        t_eng = std.get('engagement', 0)
        t_rate = (t_eng / t_reach * 100) if t_reach > 0 else 0
        
        tooltip = f"目標: 觸及 {int(t_reach)} / 互動 {int(t_eng)} (率{t_rate:.1f}%)"
        
        if check_pass(t_reach, t_eng): return "✅ 達標", "green", tooltip
        else: return "🔴 未達標", "red", tooltip

    elif platform == 'Threads':
        t_reach = std.get('reach', 500)
        t_eng = std.get('engagement', 50)
        l_reach = std.get('reach_label', '瀏覽')
        l_eng = std.get('engagement_label', '互動')
        
        tooltip = f"{l_reach}: {int(t_reach)} / {l_eng}: {int(t_eng)}"
        
        pass_reach = reach >= t_reach
        pass_eng = eng >= t_eng
        
        if pass_reach and pass_eng: return "✅ 雙指標", "green", tooltip
        elif pass_reach: return f"✅ {l_reach}", "green", tooltip
        elif pass_eng: return f"✅ {l_eng}", "green", tooltip
        else: return "🔴 未達標", "red", tooltip

    return label, color, tooltip

def process_post_metrics(p):
    """預處理單篇貼文數據"""
    m7 = p.get('metrics7d', {})
    m30 = p.get('metrics1m', {})
    
    r7 = safe_num(m7.get('reach', 0))
    e7 = safe_num(m7.get('likes', 0)) + safe_num(m7.get('comments', 0)) + safe_num(m7.get('shares', 0))
    r30 = safe_num(m30.get('reach', 0))
    e30 = safe_num(m30.get('likes', 0)) + safe_num(m30.get('comments', 0)) + safe_num(m30.get('shares', 0))
    
    rate7_val = (e7 / r7 * 100) if r7 > 0 else 0
    rate30_val = (e30 / r30 * 100) if r30 > 0 else 0
    
    disabled = is_metrics_disabled(p.get('platform'), p.get('postFormat'))
    is_threads = p.get('platform') == 'Threads'
    
    rate7_str = "-"
    rate30_str = "-"
    
    if disabled or is_threads:
        rate7_str = "🚫 不計"
        rate30_str = "🚫 不計"
    elif r7 > 0:
        rate7_str = f"{rate7_val:.1f}%"
        if r30 > 0: rate30_str = f"{rate30_val:.1f}%"

    today = datetime.now().date()
    try: p_date = datetime.strptime(p.get('date', ''), "%Y-%m-%d").date()
    except: p_date = today
    
    due_date_7 = p_date + timedelta(days=7)
    due_date_30 = p_date + timedelta(days=30)
    
    bell7 = False
    bell30 = False
    if not disabled: 
        if today >= due_date_7 and r7 == 0: bell7 = True
        if today >= due_date_30 and r30 == 0: bell30 = True

    return {
        **p,
        'r7': int(r7), 'e7': int(e7), 'rate7_val': rate7_val, 'rate7_str': rate7_str, 'bell7': bell7,
        'r30': int(r30), 'e30': int(e30), 'rate30_val': rate30_val, 'rate30_str': rate30_str, 'bell30': bell30,
        '_sort_date': p.get('date', str(today))
    }

# --- Callback ---
def edit_post_callback(post):
    st.session_state.editing_post = post
    st.session_state.scroll_to_top = True
    if st.session_state.view_mode_radio == "🗓️ 日曆模式":
         st.session_state.view_mode_radio = "📋 列表模式"
    
    try: st.session_state['entry_date'] = datetime.strptime(post['date'], "%Y-%m-%d").date()
    except: st.session_state['entry_date'] = datetime.now().date()
        
    st.session_state['entry_platform_single'] = post['platform']
    st.session_state['entry_topic'] = post['topic']
    st.session_state['entry_type'] = post['postType']
    sub = post.get('postSubType', '')
    st.session_state['entry_subtype'] = sub if sub in (["-- 無 --"] + SOUVENIR_SUB_TYPES) else "-- 無 --"
    st.session_state['entry_purpose'] = post['postPurpose']
    st.session_state['entry_format'] = post['postFormat']
    st.session_state['entry_po'] = post['projectOwner']
    st.session_state['entry_owner'] = post['postOwner']
    st.session_state['entry_designer'] = post['designer']
    
    m7 = post.get('metrics7d', {})
    st.session_state['entry_m7_reach'] = safe_num(m7.get('reach', 0))
    st.session_state['entry_m7_likes'] = safe_num(m7.get('likes', 0))
    st.session_state['entry_m7_comments'] = safe_num(m7.get('comments', 0))
    st.session_state['entry_m7_shares'] = safe_num(m7.get('shares', 0))
    
    m1 = post.get('metrics1m', {})
    st.session_state['entry_m1_reach'] = safe_num(m1.get('reach', 0))
    st.session_state['entry_m1_likes'] = safe_num(m1.get('likes', 0))
    st.session_state['entry_m1_comments'] = safe_num(m1.get('comments', 0))
    st.session_state['entry_m1_shares'] = safe_num(m1.get('shares', 0))

def delete_post_callback(post_id):
    st.session_state.posts = [item for item in st.session_state.posts if item['id'] != post_id]
    save_data(st.session_state.posts)

def go_to_post_from_calendar(post_id):
    st.session_state.view_mode_radio = "📋 列表模式"
    st.session_state.target_scroll_id = post_id
    st.session_state.scroll_to_list_item = True 

# --- Init State ---
if 'posts' not in st.session_state: st.session_state.posts = load_data()
if 'standards' not in st.session_state: st.session_state.standards = load_standards()
if 'editing_post' not in st.session_state: st.session_state.editing_post = None
if 'scroll_to_top' not in st.session_state: st.session_state.scroll_to_top = False
if 'target_scroll_id' not in st.session_state: st.session_state.target_scroll_id = None
if 'scroll_to_list_item' not in st.session_state: st.session_state.scroll_to_list_item = False
if 'view_mode_radio' not in st.session_state: st.session_state.view_mode_radio = "🗓️ 日曆模式"

# --- CSS ---
cal_btn_css = ""
for pf, mark in PLATFORM_MARKS.items():
    color = PLATFORM_COLORS.get(pf, '#888')
    cal_btn_css += f"""
    div[data-testid="stButton"] button[aria-label^="{mark}"] {{
        background-color: {color} !important; color: white !important; border: none !important;
        font-size: 0.75em !important; padding: 1px 4px !important; border-radius: 3px !important;
        width: 100% !important; text-align: left !important; white-space: nowrap !important;
        overflow: hidden !important; text-overflow: ellipsis !important; display: block !important;
        margin-top: 0px !important; margin-bottom: 2px !important; line-height: 1.1 !important;
        height: auto !important; min-height: 0px !important;
    }}
    div[data-testid="stButton"] button[aria-label^="{mark}"]:hover {{ filter: brightness(0.9); color: white !important; }}
    """

st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; }}
    .block-container {{ padding-top: 3rem; padding-bottom: 2rem; }}
    .kpi-badge {{ padding: 2px 6px; border-radius: 8px; font-weight: bold; font-size: 0.8em; display: inline-block; min-width: 50px; text-align: center; cursor: help; }}
    .purple {{ background-color: #f3e8ff; color: #7e22ce; border: 1px solid #d8b4fe; }}
    .green {{ background-color: #dcfce7; color: #15803d; border: 1px solid #86efac; }}
    .orange {{ background-color: #ffedd5; color: #c2410c; border: 1px solid #fdba74; }}
    .red {{ background-color: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }}
    .gray {{ background-color: #f3f4f6; color: #9ca3af; border: 1px solid #e5e7eb; }}
    .overdue-alert {{ color: #dc2626; font-weight: bold; font-size: 0.9em; display: flex; align-items: center; }}
    .platform-badge-box {{ font-weight: 800; padding: 4px 8px; border-radius: 4px; color: white; font-size: 0.9em; display: inline-block; width: 100%; text-align: center; margin-bottom: 2px; }}
    .post-row {{ background-color: transparent; border-bottom: 1px solid #f3f4f6; padding: 8px 0; margin-bottom: 0; transition: background-color 0.2s; }}
    .post-row:hover {{ background-color: #f9fafb; }}
    .today-highlight {{ background-color: #fffbeb; border-bottom: 2px solid #fcd34d; padding: 8px 0; position: relative; }}
    @keyframes highlight-fade {{ 0% {{ background-color: #fef08a; }} 100% {{ background-color: transparent; }} }}
    .scroll-highlight {{ animation: highlight-fade 2s ease-out; border-bottom: 2px solid #3b82f6 !important; padding: 8px 0; }}
    .row-text-lg {{ font-size: 1.05em; font-weight: bold; color: #1f2937; }}
    .cal-day-header {{ text-align: center; font-weight: bold; color: #6b7280; border-bottom: 1px solid #e5e7eb; padding-bottom: 2px; margin-bottom: 2px; font-size: 0.9em; }}
    .cal-day-cell {{ min-height: 60px; padding: 2px; border-radius: 4px; font-size: 0.8em; border: 1px solid #f3f4f6; }}
    .cal-day-num {{ font-weight: bold; font-size: 0.9em; color: #374151; margin-bottom: 2px; margin-left: 2px; }}
    {cal_btn_css}
    </style>
""", unsafe_allow_html=True)

# --- 5. Sidebar ---
with st.sidebar:
    st.title("🔎 篩選條件")
    filter_platform = st.multiselect("平台", ["All"] + PLATFORMS, key='
