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
    .stApp { background-color: #fff0f5; }
    div[data-testid="stMetricValue"] { font-size: 24px; color: #4b5563; }
    .kpi-badge { padding: 4px 8px; border-radius: 12px; font-weight: bold; font-size: 0.8em; }
    .purple { background-color: #f3e8ff; color: #7e22ce; border: 1px solid #d8b4fe; }
    .green { background-color: #dcfce7; color: #15803d; border: 1px solid #86efac; }
    .orange { background-color: #ffedd5; color: #c2410c; border: 1px solid #fdba74; }
    .red { background-color: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }
    .gray { background-color: #f3f4f6; color: #9ca3af; }
    .overdue-alert { color: #dc2626; font-weight: bold; font-size: 0.9em; display: flex; align-items: center; }
    </style>
""", unsafe_allow_html=True)

# --- 5. 側邊欄篩選 (更新：新增目的與形式) ---
with st.sidebar:
    st.title("🔎 篩選條件")
    
    filter_platform = st.selectbox("平台", ["All"] + PLATFORMS, index=0)
    filter_post_type = st.selectbox("貼文類型", ["All"] + MAIN_POST_TYPES, index=0)
    
    # 新增目的與形式篩選
    filter_purpose = st.selectbox("目的", ["All"] + POST_PURPOSES, index=0)
    filter_format = st.selectbox("形式", ["All"] + POST_FORMATS, index=0)
    
    filter_topic_keyword = st.text_input("搜尋主題 (關鍵字)")
    
    st.divider()
    date_filter_type = st.radio("日期模式", ["月", "自訂範圍"], horizontal=True)
    
    if date_filter_type == "月":
        dates = [p['date'] for p in st.session_state.posts] if st.session_state.posts else [datetime.now().strftime("%Y-%m-%d")]
        months = sorted(list(set([d[:7] for d in dates])), reverse=True)
        if not months: months = [datetime.now().strftime("%Y-%m")]
        selected_month = st.selectbox("選擇月份", months)
    else:
        c1, c2 = st.columns(2)
        start_date = c1.date_input("開始", datetime.now().replace(day=1))
        end_date = c2.date_input("結束", datetime.now())

# --- 6. 主頁面 ---
st.header("📅 社群排程與成效管家")

tab1, tab2 = st.tabs(["🗓️ 排程管理", "📊 數據分析"])

# === TAB 1: 排程管理 ===
with tab1:
    # --- 新增/編輯區塊 ---
    with st.expander("✨ 新增/編輯 貼文", expanded=st.session_state.editing_post is not None):
        with st.form("post_form"):
            is_edit = st.session_state.editing_post is not None
            post_data = st.session_state.editing_post if is_edit else {}
            
            c1, c2, c3 = st.columns([1, 2, 1])
            f_date = c1.date_input("發布日期", 
                                   datetime.strptime(post_data.get('date', datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d") 
                                   if post_data else datetime.now())
            
            if is_edit:
                f_platform = c2.selectbox("平台 (編輯模式僅單選)", PLATFORMS, index=PLATFORMS.index(post_data['platform']))
                selected_platforms = [f_platform]
            else:
                selected_platforms = c2.multiselect("平台 (可複選)", PLATFORMS, default=['Facebook'])
                
            f_topic = c3.text_input("主題", value=post_data.get('topic', ''))

            c4, c5, c6 = st.columns(3)
            f_type = c4.selectbox("貼文類型", MAIN_POST_TYPES, index=MAIN_POST_TYPES.index(post_data.get('postType', '喜餅')) if post_data else 0)
            
            sub_index = 0
            if is_edit and post_data.get('postSubType') in SOUVENIR_SUB_TYPES:
                sub_index = SOUVENIR_SUB_TYPES.index(post_data['postSubType']) + 1
            f_subtype = c5.selectbox("子類型 (伴手禮用)", ["-- 無 --"] + SOUVENIR_SUB_TYPES, disabled=(f_type != '伴手禮'), index=sub_index)
            
            f_status = c6.selectbox("狀態", ["draft", "planned", "published"], 
                                   index=["draft", "planned", "published"].index(post_data.get('status', 'draft')) if post_data else 0,
                                   format_func=lambda x: {'draft': '🌱 草稿', 'planned': '⏰ 已排程', 'published': '🚀 已發布'}[x])

            c7, c8 = st.columns(2)
            f_purpose = c7.selectbox("目的", POST_PURPOSES, index=POST_PURPOSES.index(post_data.get('postPurpose', '互動')) if post_data else 0)
            f_format = c8.selectbox("形式", POST_FORMATS, index=POST_FORMATS.index(post_data.get('postFormat', '單圖')) if post_data else 0)

            c9, c10, c11 = st.columns(3)
            f_po = c9.selectbox("專案負責人", [""] + PROJECT_OWNERS, index=(PROJECT_OWNERS.index(post_data['projectOwner']) + 1) if post_data and post_data['projectOwner'] else 0)
            f_owner = c10.selectbox("貼文負責人", POST_OWNERS, index=POST_OWNERS.index(post_data.get('postOwner', '一千')) if post_data else 0)
            f_designer = c11.selectbox("美編", [""] + DESIGNERS, index=(DESIGNERS.index(post_data['designer']) + 1) if post_data and post_data['designer'] else 0)

            st.divider()
            
            due_date_7d = f_date + timedelta(days=7)
            due_date_1m = f_date + timedelta(days=30)
            
            st.caption("數據填寫 (若狀態為已發布)")
            
            def get_m(key, period):
                return post_data.get(period, {}).get(key, 0) if post_data else 0

            m_cols = st.columns(2)
            metrics_input = {'metrics7d': {}, 'metrics1m': {}}
            
            with m_cols[0]:
                st.markdown(f"##### 🔥 7天成效 <span style='font-size:0.7em; color:#ef4444; background:#fee2e2; padding:2px 6px; border-radius:4px;'>預計: {due_date_7d.strftime('%m/%d')}</span>", unsafe_allow_html=True)
                metrics_input['metrics7d']['reach'] = st.number_input("7天-觸及", value=get_m('reach', 'metrics7d'), step=1)
                metrics_input['metrics7d']['likes'] = st.number_input("7天-按讚", value=get_m('likes', 'metrics7d'), step=1)
                c_sub1, c_sub2 = st.columns(2)
                metrics_input['metrics7d']['comments'] = c_sub1.number_input("7天-留言", value=get_m('comments', 'metrics7d'), step=1)
                metrics_input['metrics7d']['shares'] = c_sub2.number_input("7天-分享", value=get_m('shares', 'metrics7d'), step=1)

            with m_cols[1]:
                st.markdown(f"##### 🌳 一個月成效 <span style='font-size:0.7em; color:#a855f7; background:#f3e8ff; padding:2px 6px; border-radius:4px;'>預計: {due_date_1m.strftime('%m/%d')}</span>", unsafe_allow_html=True)
                metrics_input['metrics1m']['reach'] = st.number_input("1月-觸及", value=get_m('reach', 'metrics1m'), step=1)
                metrics_input['metrics1m']['likes'] = st.number_input("1月-按讚", value=get_m('likes', 'metrics1m'), step=1)
                c_sub3, c_sub4 = st.columns(2)
                metrics_input['metrics1m']['comments'] = c_sub3.number_input("1月-留言", value=get_m('comments', 'metrics1m'), step=1)
                metrics_input['metrics1m']['shares'] = c_sub4.number_input("1月-分享", value=get_m('shares', 'metrics1m'), step=1)

            submitted = st.form_submit_button("💾 儲存貼文", type="primary")

            if submitted:
                if not f_topic:
                    st.error("請填寫主題")
                else:
                    new_base = {
                        'date': f_date.strftime("%Y-%m-%d"),
                        'topic': f_topic,
                        'postType': f_type,
                        'postSubType': f_subtype if f_subtype != "-- 無 --" else "",
                        'postPurpose': f_purpose,
                        'postFormat': f_format,
                        'projectOwner': f_po,
                        'postOwner': f_owner,
                        'designer': f_designer,
                        'status': f_status,
                        'metrics7d': metrics_input['metrics7d'],
                        'metrics1m': metrics_input['metrics1m']
                    }

                    if is_edit:
                        for i, p in enumerate(st.session_state.posts):
                            if p['id'] == post_data['id']:
                                st.session_state.posts[i] = {**p, **new_base, 'platform': selected_platforms[0]}
                                break
                        st.session_state.editing_post = None
                        st.success("已更新！")
                    else:
                        for p in selected_platforms:
                            new_post = {**new_base, 'id': str(uuid.uuid4()), 'platform': p}
                            st.session_state.posts.append(new_post)
                        st.success(f"已新增 {len(selected_platforms)} 則貼文！")
                    
                    save_data(st.session_state.posts)
                    st.rerun()

        if st.session_state.editing_post:
            if st.button("取消編輯"):
                st.session_state.editing_post = None
                st.rerun()

    # --- 列表顯示邏輯 ---
    filtered_posts = st.session_state.posts
    
    if date_filter_type == "月":
        filtered_posts = [p for p in filtered_posts if p['date'].startswith(selected_month)]
    else:
        filtered_posts = [p for p in filtered_posts if start_date <= datetime.strptime(p['date'], "%Y-%m-%d").date() <= end_date]
    
    if filter_platform != "All":
        filtered_posts = [p for p in filtered_posts if p['platform'] == filter_platform]
        
    if filter_topic_keyword:
        filtered_posts = [p for p in filtered_posts if filter_topic_keyword.lower() in p['topic'].lower()]

    if filter_post_type != "All":
        filtered_posts = [p for p in filtered_posts if p['postType'] == filter_post_type]

    # 新增篩選邏輯
    if filter_purpose != "All":
        filtered_posts = [p for p in filtered_posts if p['postPurpose'] == filter_purpose]
    
    if filter_format != "All":
        filtered_posts = [p for p in filtered_posts if p['postFormat'] == filter_format]

    # 排序
    col_sort1, col_sort2, col_count = st.columns([1, 1, 4])
    with col_sort1:
        sort_by = st.selectbox("排序依據
