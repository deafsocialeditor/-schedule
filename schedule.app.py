import streamlit as st
import pandas as pd
import json
import os
import uuid
from datetime import datetime, timedelta

# --- 1. 配置與常數 ---
st.set_page_config(
    page_title="社群排程與成效管家",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 檔案路徑
DATA_FILE = "social_posts.json"
STANDARDS_FILE = "social_standards.json"

# 選項定義
PLATFORMS = ['Facebook', 'Instagram', 'LINE@', 'YouTube', 'Threads']
MAIN_POST_TYPES = ['喜餅', '彌月', '伴手禮', '社群互動', '圓夢計畫', '公告']
SOUVENIR_SUB_TYPES = ['端午節', '中秋', '聖誕', '新春', '蒙友週']
POST_PURPOSES = ['互動', '廣告', '門市廣告', '導購', '公告']
POST_FORMATS = ['單圖', '多圖', '假多圖', '短影音', '限動', '純文字', '留言處']
PROJECT_OWNERS = ['夢涵', 'MOMO', '櫻樺', '季嫻', '凌萱', '宜婷']
POST_OWNERS = ['一千', '凱曜', '可榆']
DESIGNERS = ['千惟', '靖嬙']

# 定義廣告類型的目的
AD_PURPOSE_LIST = ['廣告', '門市廣告']

# Icon Mapping
ICONS = {
    'Facebook': '📘', 'Instagram': '📸', 'LINE@': '🟢', 'YouTube': '▶️', 'Threads': '🧵',
    'reach': '👀', 'likes': '❤️', 'comments': '💬', 'rate': '📈'
}

# --- 2. 資料處理函式 ---

def load_data():
    """讀取貼文數據"""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    """儲存貼文數據"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_standards():
    """讀取 KPI 標準"""
    default_standards = {
        'Facebook': {'type': 'tiered', 'high': {'reach': 2000, 'rate': 5.0}, 'std': {'reach': 1500, 'rate': 3.0}, 'low': {'reach': 1000, 'rate': 1.5}},
        'Instagram': {'type': 'simple', 'reach': 900, 'engagement': 30, 'rate': 3.5},
        'Threads': {'type': 'reference', 'reach': 84000, 'engagement': 1585, 'rate': 0, 'note': "標竿: 09/17更新(瀏覽8.4萬), 10/07孕婦節(互動1585)"},
        'YouTube': {'type': 'simple', 'reach': 500, 'engagement': 0, 'rate': 2.0},
        'LINE@': {'type': 'simple', 'reach': 0, 'engagement': 0, 'rate': 0}
    }
    if not os.path.exists(STANDARDS_FILE):
        return default_standards
    try:
        with open(STANDARDS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return default_standards

def save_standards(standards):
    """儲存 KPI 標準"""
    with open(STANDARDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(standards, f, ensure_ascii=False, indent=4)

def is_metrics_disabled(platform, fmt):
    """判斷是否不需要填寫成效"""
    return platform == 'LINE@' or fmt in ['限動', '留言處']

def safe_num(val):
    try:
        return float(val)
    except:
        return 0.0

def get_performance_label(platform, metrics, fmt, standards):
    """計算 KPI 標籤"""
    if is_metrics_disabled(platform, fmt):
        return "-", "gray"
    
    reach = safe_num(metrics.get('reach', 0))
    likes = safe_num(metrics.get('likes', 0))
    comments = safe_num(metrics.get('comments', 0))
    shares = safe_num(metrics.get('shares', 0))
    
    if reach == 0:
        return "-", "gray"

    engagement = likes + comments + shares
    rate = (engagement / reach) * 100
    std = standards.get(platform, {})

    if platform == 'Facebook':
        if reach >= std['high']['reach'] and rate >= std['high']['rate']: return "🏆 高標", "purple"
        if reach >= std['std']['reach'] and rate >= std['std']['rate']: return "✅ 標準", "green"
        if reach >= std['low']['reach'] and rate >= std['low']['rate']: return "🤏 低標", "orange"
        return "🔴 未達標", "red"
    elif platform == 'Instagram':
        if reach >= std['reach'] and engagement >= std['engagement'] and rate >= std['rate']:
            return "✅ 達標", "green"
        return "🔴 未達標", "red"
    elif platform == 'YouTube':
        if reach >= std['reach'] and rate >= std['rate']: return "✅ 達標", "green"
        return "🔴 未達標", "red"
    elif platform == 'Threads':
        if reach >= std['reach']: return "🔥 超標竿", "purple"
        return "-", "gray"
    
    return "-", "gray"

# --- 3. 初始化 Session State ---
if 'posts' not in st.session_state:
    st.session_state.posts = load_data()
if 'standards' not in st.session_state:
    st.session_state.standards = load_standards()
if 'editing_post' not in st.session_state:
    st.session_state.editing_post = None

# --- 4. 自訂 CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #fff0f
