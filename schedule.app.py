import streamlit as st
import pandas as pd
import json
import os
import uuid
import calendar
import streamlit.components.v1 as components
from datetime import datetime, timedelta

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
    try: return float(val)
    except: return 0.0

def get_performance_label(platform, metrics, fmt, standards):
    """
    回傳: (標籤文字, 顏色class, Tooltip提示文字)
    邏輯：細分顯示 觸及/互動/互動率 哪項達標
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

    # Helper: 計算目標互動率
    def get_target_rate(r, e):
        return (e / r * 100) if r > 0 else 0

    if platform == 'Facebook':
        h = std['high']
        s = std['std']
        l = std['low']
        
        # Tooltip info
        h_rt = get_target_rate(h['reach'], h['engagement'])
        s_rt = get_target_rate(s['reach'], s['engagement'])
        l_rt = get_target_rate(l['reach'], l['engagement'])
        
        tooltip = f"高標: 觸及{int(h['reach'])} / 互動{int(h['engagement'])} (率{h_rt:.1f}%)\n標準: 觸及{int(s['reach'])} / 互動{int(s['engagement'])} (率{s_rt:.1f}%)\n低標: 觸及{int(l['reach'])} / 互動{int(l['engagement'])} (率{l_rt:.1f}%)"
        
        # Check High
        if (reach >= h['reach']) or (eng >= h['engagement']) or (rate >= h_rt):
            if reach >= h['reach'] and eng >= h['engagement']: return "🏆 高標雙達標", "purple", tooltip
            if reach >= h['reach']: return "🏆 高標觸及達標", "purple", tooltip
            if eng >= h['engagement']: return "🏆 高標互動達標", "purple", tooltip
            return "🏆 高標互動率達標", "purple", tooltip
            
        # Check Std
        if (reach >= s['reach']) or (eng >= s['engagement']) or (rate >= s_rt):
            if reach >= s['reach'] and eng >= s['engagement']: return "✅ 標準雙達標", "green", tooltip
            if reach >= s['reach']: return "✅ 標準觸及達標", "green", tooltip
            if eng >= s['engagement']: return "✅ 標準互動達標", "green", tooltip
            return "✅ 標準互動率達標", "green", tooltip

        # Check Low
        if (reach >= l['reach']) or (eng >= l['engagement']) or (rate >= l_rt):
            if reach >= l['reach'] and eng >= l['engagement']: return "🤏 低標雙達標", "orange", tooltip
            if reach >= l['reach']: return "🤏 低標觸及達標", "orange", tooltip
            if eng >= l['engagement']: return "🤏 低標互動達標", "orange", tooltip
            return "🤏 低標互動率達標", "orange", tooltip
            
        return "🔴 未達標", "red", tooltip
        
    elif platform in ['Instagram', 'YouTube', '社團']:
        t_reach = std.get('reach', 0)
        t_eng = std.get('engagement', 0)
        t_rate = get_target_rate(t_reach, t_eng)
        
        tooltip = f"目標: 觸及 {int(t_reach)} / 互動 {int(t_eng)} (率{t_rate:.1f}%)"
        
        pass_reach = reach >= t_reach
        pass_eng = eng >= t_eng
        pass_rate = rate >= t_rate
        
        if pass_reach and pass_eng: return "✅ 雙指標達標", "green", tooltip
        elif pass_reach: return "✅ 觸及達標", "green", tooltip
        elif pass_eng: return "✅ 互動達標", "green", tooltip
        elif pass_rate: return "✅ 互動率達標", "green", tooltip
        else: return "🔴 未達標", "red", tooltip

    elif platform == 'Threads':
        t_reach = std.get('reach', 500)
        t_eng = std.get('engagement', 50)
        l_reach = std.get('reach_label', '瀏覽')
        l_eng = std.get('engagement_label', '互動')
        
        tooltip = f"{l_reach}: {int(t_reach)} / {l_eng}: {int(t_eng)}"
        
        pass_reach = reach >= t_reach
        pass_eng = eng >= t_eng
        
        if pass_reach and pass_eng: return "✅ 雙指標達標", "green", tooltip
        elif pass_reach: return f"✅ {l_reach}達標", "green", tooltip
        elif pass_eng: return f"✅ {l_eng}達標", "green", tooltip
        else: return "🔴 未達標", "red", tooltip

    return label, color, tooltip

def process_post_metrics(p):
    """預處理單篇貼文數據 (List View Helper)"""
    m7 = p.get('metrics7d', {})
    m30 = p.get('metrics1m', {})
    
    r7 = safe_num(m7.get('reach', 0))
    e7 = safe_num(m7.get('likes', 0)) + safe_num(m7.get('comments', 0)) + safe_num(m7.get('shares', 0))
    r30 = safe_num(m30.get('reach', 0))
    e30 = safe_num(m30.get('likes', 0)) + safe_num(m30.get('comments', 0)) + safe_num(m30.get('shares', 0))
    
    rate7_val = (e7 / r7 * 100) if r7 > 0 else 0
    rate30_val = (e30 / r30 * 100) if r30 > 0 else 0
    
    disabled = is_metrics_disabled(p['platform'], p['postFormat'])
    is_threads = p['platform'] == 'Threads'
    
    rate7_str = "-"
    rate30_str = "-"
    
    if disabled or is_threads:
        rate7_str = "🚫 不計"
        rate30_str = "🚫 不計"
    elif r7 > 0:
        rate7_str = f"{rate7_val:.1f}%"
        if r30 > 0: rate30_str = f"{rate30_val:.1f}%"

    today = datetime.now().date()
    try: p_date = datetime.strptime(p['date'], "%Y-%m-%d").date()
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
        '_sort_date': p['date']
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
    filter_platform = st.multiselect("平台", ["All"] + PLATFORMS, key='filter_platform')
    filter_owner = st.multiselect("負責人", ["All"] + POST_OWNERS, key='filter_owner')
    filter_post_type = st.multiselect("貼文類型", ["All"] + MAIN_POST_TYPES, key='filter_post_type')
    filter_purpose = st.multiselect("目的", ["All"] + POST_PURPOSES, key='filter_purpose')
    filter_format = st.multiselect("形式", ["All"] + POST_FORMATS, key='filter_format')
    filter_topic_keyword = st.text_input("搜尋主題 (關鍵字)", key='filter_topic_keyword')
    
    st.divider()
    date_filter_type = st.radio("日期模式", ["月", "自訂範圍"], horizontal=True, key='date_filter_type')
    if date_filter_type == "月":
        dates = [p['date'] for p in st.session_state.posts] if st.session_state.posts else [datetime.now().strftime("%Y-%m-%d")]
        months = sorted(list(set([d[:7] for d in dates])), reverse=True)
        if not months: months = [datetime.now().strftime("%Y-%m")]
        selected_month = st.selectbox("選擇月份", months, key='selected_month')
    else:
        c1, c2 = st.columns(2)
        start_date = c1.date_input("開始", datetime.now().replace(day=1), key='start_date')
        end_date = c2.date_input("結束", datetime.now(), key='end_date')

# --- 6. Main Page ---
st.header("📅 2025社群排程與成效")
tab1, tab2 = st.tabs(["🗓️ 排程管理", "📊 數據分析"])

# === TAB 1 ===
with tab1:
    st.markdown("<div id='edit_top'></div>", unsafe_allow_html=True)

    # JS Injection
    js_code = ""
    if st.session_state.scroll_to_top:
        js_code += """setTimeout(function() { try { var top = window.parent.document.getElementById('edit_top'); if (top) { top.scrollIntoView({behavior: 'smooth', block: 'start'}); } } catch (e) {} }, 150);"""
        st.session_state.scroll_to_top = False
    if st.session_state.scroll_to_list_item and st.session_state.target_scroll_id:
        target = st.session_state.target_scroll_id
        js_code += f"""setTimeout(function() {{ try {{ var el = window.parent.document.getElementById('post_{target}'); if (el) {{ el.scrollIntoView({{behavior: 'smooth', block: 'center'}}); }} }} catch (e) {{}} }}, 300);"""
        st.session_state.scroll_to_list_item = False
    if js_code: components.html(f"<script>{js_code}</script>", height=0)

    # Editor
    with st.expander("✨ 新增/編輯 貼文", expanded=st.session_state.editing_post is not None):
        is_edit = st.session_state.editing_post is not None
        target_edit_id = st.session_state.editing_post['id'] if is_edit else None
        
        # Init form
        for k in ['entry_date', 'entry_platform_single', 'entry_platform_multi', 'entry_topic', 'entry_type', 'entry_subtype', 'entry_purpose', 'entry_format', 'entry_po', 'entry_owner', 'entry_designer']:
            if k not in st.session_state:
                if k == 'entry_date': st.session_state[k] = datetime.now()
                elif 'platform_single' in k: st.session_state[k] = PLATFORMS[0]
                elif 'platform_multi' in k: st.session_state[k] = ['Facebook']
                elif 'type' in k: st.session_state[k] = MAIN_POST_TYPES[0]
                elif 'purpose' in k: st.session_state[k] = POST_PURPOSES[0]
                else: st.session_state[k] = "" if 'owner' in k or 'po' in k or 'designer' in k or 'format' in k or 'topic' in k or 'subtype' in k else "-- 無 --"
        for k in ['entry_m7_reach', 'entry_m7_likes', 'entry_m7_comments', 'entry_m7_shares', 'entry_m1_reach', 'entry_m1_likes', 'entry_m1_comments', 'entry_m1_shares']:
             if k not in st.session_state: st.session_state[k] = 0.0

        c1, c2, c3 = st.columns([1, 2, 1])
        f_date = c1.date_input("發布日期", key="entry_date")
        if is_edit:
            f_platform = c2.selectbox("平台 (編輯模式僅單選)", PLATFORMS, key="entry_platform_single")
            selected_platforms = [f_platform]
        else:
            selected_platforms = c2.multiselect("平台 (可複選)", PLATFORMS, key="entry_platform_multi")
        f_topic = c3.text_input("主題", key="entry_topic")

        c4, c5, c6 = st.columns(3)
        f_type = c4.selectbox("貼文類型", MAIN_POST_TYPES, key="entry_type")
        f_subtype = c5.selectbox("子類型", ["-- 無 --"] + SOUVENIR_SUB_TYPES, disabled=(f_type != '伴手禮'), key="entry_subtype")
        
        c7, c8 = st.columns(2)
        platform_purposes = {} 
        with c7:
            if not is_edit and len(selected_platforms) > 1:
                st.markdown("**🎯 各平台目的設定**")
                for p in selected_platforms:
                    k = f"purpose_for_{p}"
                    if k not in st.session_state: st.session_state[k] = POST_PURPOSES[0]
                    platform_purposes[p] = st.selectbox(f"{ICONS.get(p, '')} {p}", POST_PURPOSES, key=k)
            else:
                single_purpose = st.selectbox("目的", POST_PURPOSES, key="entry_purpose")
                for p in selected_platforms: platform_purposes[p] = single_purpose
        f_format = c8.selectbox("形式", [""] + POST_FORMATS, key="entry_format")

        c9, c10, c11 = st.columns(3)
        f_po = c9.selectbox("專案負責人", [""] + PROJECT_OWNERS, key="entry_po")
        f_owner = c10.selectbox("貼文負責人", [""] + POST_OWNERS, key="entry_owner")
        f_designer = c11.selectbox("美編", [""] + DESIGNERS, key="entry_designer")

        st.divider()
        current_platform = selected_platforms[0] if selected_platforms else 'Facebook'
        hide_metrics = is_metrics_disabled(current_platform, f_format)
        metrics_input = {'metrics7d': {}, 'metrics1m': {}}
        
        if not hide_metrics:
            st.caption("數據填寫")
            m_cols = st.columns(2)
            with m_cols[0]:
                st.markdown("##### 🔥 7天成效")
                metrics_input['metrics7d']['reach'] = st.number_input("7天-觸及", step=1, key="entry_m7_reach")
                metrics_input['metrics7d']['likes'] = st.number_input("7天-按讚", step=1, key="entry_m7_likes")
                sub_c1, sub_c2 = st.columns(2)
                metrics_input['metrics7d']['comments'] = sub_c1.number_input("7天-留言", step=1, key="entry_m7_comments")
                metrics_input['metrics7d']['shares'] = sub_c2.number_input("7天-分享", step=1, key="entry_m7_shares")
            with m_cols[1]:
                st.markdown("##### 🌳 一個月成效")
                metrics_input['metrics1m']['reach'] = st.number_input("1月-觸及", step=1, key="entry_m1_reach")
                metrics_input['metrics1m']['likes'] = st.number_input("1月-按讚", step=1, key="entry_m1_likes")
                sub_c3, sub_c4 = st.columns(2)
                metrics_input['metrics1m']['comments'] = sub_c3.number_input("1月-留言", step=1, key="entry_m1_comments")
                metrics_input['metrics1m']['shares'] = sub_c4.number_input("1月-分享", step=1, key="entry_m1_shares")
        else:
            st.info(f"ℹ️ {current_platform} / {f_format} 不需要填寫成效數據")

        submitted = st.button("💾 儲存貼文", type="primary", use_container_width=True)
        if submitted:
            if not f_topic: st.error("請填寫主題")
            else:
                date_str = f_date.strftime("%Y-%m-%d")
                if is_edit:
                    p = selected_platforms[0]
                    base = {'date': date_str, 'topic': f_topic, 'postType': f_type, 'postSubType': f_subtype if f_subtype != "-- 無 --" else "", 'postPurpose': platform_purposes[p], 'postFormat': f_format, 'projectOwner': f_po, 'postOwner': f_owner, 'designer': f_designer, 'status': 'published', 'metrics7d': metrics_input['metrics7d'], 'metrics1m': metrics_input['metrics1m']}
                    for i, d in enumerate(st.session_state.posts):
                        if d['id'] == target_edit_id: st.session_state.posts[i] = {**d, **base, 'platform': p}; break
                    st.session_state.editing_post = None
                    st.success("已更新！")
                else:
                    for p in selected_platforms:
                        new_p = {'id': str(uuid.uuid4()), 'date': date_str, 'platform': p, 'topic': f_topic, 'postType': f_type, 'postSubType': f_subtype if f_subtype != "-- 無 --" else "", 'postPurpose': platform_purposes[p], 'postFormat': f_format, 'projectOwner': f_po, 'postOwner': f_owner, 'designer': f_designer, 'status': 'published', 'metrics7d': metrics_input['metrics7d'], 'metrics1m': metrics_input['metrics1m']}
                        if is_metrics_disabled(p, f_format): new_p['metrics7d'] = {}; new_p['metrics1m'] = {}
                        st.session_state.posts.append(new_p)
                    st.success("已新增！")
                save_data(st.session_state.posts)
                for key in st.session_state.keys():
                    if key.startswith("entry_") or key.startswith("purpose_for_"): del st.session_state[key]
                st.rerun()

        if st.session_state.editing_post:
            if st.button("取消編輯"):
                st.session_state.editing_post = None
                for key in st.session_state.keys():
                    if key.startswith("entry_"): del st.session_state[key]
                st.rerun()

    # --- View Mode ---
    view_mode = st.radio("檢視模式", ["📋 列表模式", "🗓️ 日曆模式"], horizontal=True, label_visibility="collapsed", key="view_mode_radio")
    st.write("")

    # --- Filter Logic ---
    filtered_posts = st.session_state.posts
    if date_filter_type == "月":
        filtered_posts = [p for p in filtered_posts if p['date'].startswith(selected_month)]
    else:
        filtered_posts = [p for p in filtered_posts if start_date <= datetime.strptime(p['date'], "%Y-%m-%d").date() <= end_date]
    
    if filter_platform: filtered_posts = [p for p in filtered_posts if p['platform'] in filter_platform]
    if filter_owner: filtered_posts = [p for p in filtered_posts if p['postOwner'] in filter_owner]
    if filter_topic_keyword: filtered_posts = [p for p in filtered_posts if filter_topic_keyword.lower() in p['topic'].lower()]
    if filter_post_type: filtered_posts = [p for p in filtered_posts if p['postType'] in filter_post_type]
    if filter_purpose: filtered_posts = [p for p in filtered_posts if p['postPurpose'] in filter_purpose]
    if filter_format: filtered_posts = [p for p in filtered_posts if p['postFormat'] in filter_format]

    # --- Calendar View ---
    if view_mode == "🗓️ 日曆模式":
        if date_filter_type == "月":
            year_str, month_str = selected_month.split("-")
            cal_year, cal_month = int(year_str), int(month_str)
        else:
            cal_year, cal_month = start_date.year, start_date.month

        st.markdown(f"### 🗓️ {cal_year} 年 {cal_month} 月")
        cal = calendar.monthcalendar(cal_year, cal_month)
        cols = st.columns(7)
        weekdays = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
        for i, day in enumerate(weekdays): cols[i].markdown(f"<div class='cal-day-header'>{day}</div>", unsafe_allow_html=True)

        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                with cols[i]:
                    if day == 0: st.markdown("<div class='cal-day-cell' style='background-color:#f9fafb;'></div>", unsafe_allow_html=True)
                    else:
                        date_s = f"{cal_year}-{cal_month:02d}-{day:02d}"
                        is_today = (date_s == datetime.now().strftime("%Y-%m-%d"))
                        bg = "background-color:#fef9c3; border:2px solid #fcd34d;" if is_today else "background-color:white; border:1px solid #e5e7eb;"
                        with st.container():
                            st.markdown(f"<div class='cal-day-cell' style='{bg}'><div class='cal-day-num'>{day}</div></div>", unsafe_allow_html=True)
                            day_p = [p for p in filtered_posts if p['date'] == date_s]
                            for p in day_p:
                                # Bell Logic for Calendar
                                show_bell = False
                                if not is_metrics_disabled(p['platform'], p['postFormat']):
                                    p_d = datetime.strptime(p['date'], "%Y-%m-%d").date()
                                    if datetime.now().date() >= (p_d + timedelta(days=7)) and safe_num(p.get('metrics7d', {}).get('reach', 0)) == 0:
                                        show_bell = True
                                
                                mark = PLATFORM_MARKS.get(p['platform'], '🟦')
                                bell = "🔔" if show_bell else ""
                                label = f"{mark} {bell}{p['topic'][:4]}.."
                                if st.button(label, key=f"cal_{p['id']}", help=f"{p['platform']} - {p['topic']}", on_click=go_to_post_from_calendar, args=(p['id'],)): pass
    
    # --- List View ---
    else:
        processed_data = [process_post_metrics(p) for p in filtered_posts]
        
        col_s1, col_s2, col_cnt = st.columns([1, 1, 4])
        with col_s1: sort_by = st.selectbox("排序依據", ["日期", "平台", "主題", "貼文類型", "7天觸及", "7天互動", "7天互動率", "30天觸及", "30天互動", "30天互動率"], index=0, key='sort_by')
        with col_s2: sort_order = st.selectbox("順序", ["升序 (舊->新)", "降序 (新->舊)"], index=0, key='sort_order')

        key_map = { 
            "日期": "_sort_date", "平台": "platform", "主題": "topic", "貼文類型": "postType",
            "7天觸及": "r7", "7天互動": "e7", "7天互動率": "rate7_val",
            "30天觸及": "r30", "30天互動": "e30", "30天互動率": "rate30_val"
        }
        reverse = True if "降序" in sort_order else False
        processed_data.sort(key=lambda x: x[key_map[sort_by]], reverse=reverse)

        with col_cnt:
            st.write("")
            st.markdown(f"**共篩選出 {len(processed_data)} 筆資料**")
        st.divider()

        if processed_data:
            # 12 Cols - CONFIRMED
            cols = st.columns([0.8, 0.7, 1.8, 0.7, 0.6, 0.6, 0.6, 0.6, 0.6, 0.4, 0.4, 0.4])
            headers = ["日期", "平台", "主題", "類型", "目的", "形式", "KPI", "7日互動率", "30日互動率", "負責人", "編輯", "刪除"]
            for c, h in zip(cols, headers): c.markdown(f"**{h}**")
            st.markdown("<hr style='margin:0.5em 0; border-top:1px dashed #ddd;'>", unsafe_allow_html=True)

            today_s = datetime.now().strftime("%Y-%m-%d")

            for p in processed_data:
                label, color, tooltip = get_performance_label(p['platform'], p.get('metrics7d'), p['postFormat'], st.session_state.standards)
                
                is_today = (p['date'] == today_s)
                is_target = (st.session_state.target_scroll_id == p['id'])
                
                row_cls = "scroll-highlight" if is_target else ("today-highlight" if is_today else "post-row")
                st.markdown(f"<div id='post_{p['id']}'></div>", unsafe_allow_html=True)

                with st.container():
                    st.markdown(f'<div class="{row_cls}">', unsafe_allow_html=True)
                    # 12 Cols Config - FIXED
                    c = st.columns([0.8, 0.7, 1.8, 0.7, 0.6, 0.6, 0.6, 0.6, 0.6, 0.4, 0.4, 0.4])
                    
                    c[0].markdown(f"<span class='row-text-lg'>{p['date']}</span>", unsafe_allow_html=True)
                    pf_clr = PLATFORM_COLORS.get(p['platform'], '#888')
                    c[1].markdown(f"<span class='platform-badge-box' style='background-color:{pf_clr}'>{p['platform']}</span>", unsafe_allow_html=True)
                    c[2].markdown(f"<span class='row-text-lg'>{p['topic']}</span>", unsafe_allow_html=True)
                    c[3].write(p['postType'])
                    c[4].write(p['postPurpose'])
                    c[5].write(p['postFormat'])
                    
                    # Tooltip logic
                    c[6].markdown(f"<span class='kpi-badge {color}' title='{tooltip}'>{label.split(' ')[-1] if ' ' in label else label}</span>", unsafe_allow_html=True)
                    
                    # 7D Rate
                    if p['bell7'] and p['platform'] != 'Threads': c[7].markdown(f"<span class='overdue-alert'>🔔 缺</span>", unsafe_allow_html=True)
                    elif p['platform'] == 'YouTube': c[7].markdown("-", unsafe_allow_html=True)
                    else: c[7].markdown(p['rate7_str'], unsafe_allow_html=True)

                    # 30D Rate
                    if p['bell30'] and p['platform'] != 'Threads': c[8].markdown(f"<span class='overdue-alert'>🔔 缺</span>", unsafe_allow_html=True)
                    elif p['platform'] == 'YouTube': c[8].markdown("-", unsafe_allow_html=True)
                    else: c[8].markdown(p['rate30_str'], unsafe_allow_html=True)
                    
                    c[9].write(p['postOwner'])
                    if c[10].button("✏️", key=f"ed_{p['id']}", on_click=edit_post_callback, args=(p,)): pass
                    if c[11].button("🗑️", key=f"del_{p['id']}", on_click=delete_post_callback, args=(p['id'],)): pass

                    # Expander
                    exp_label = "📉 詳細數據"
                    if p['platform'] == 'Threads' and (p['bell7'] or p['bell30']): exp_label += " :red[🔔 缺資料]"
                    
                    with st.expander(exp_label):
                        rl = "瀏覽" if p['platform'] == 'Threads' else "觸及"
                        dc = st.columns(4)
                        w7 = "🔔 " if (p['bell7'] and p['platform'] == 'Threads') else ""
                        w30 = "🔔 " if (p['bell30'] and p['platform'] == 'Threads') else ""
                        dc[0].metric(f"{w7}7天-{rl}", f"{p['r7']:,}")
                        dc[1].metric(f"{w7}7天-互動", f"{p['e7']:,}")
                        dc[2].metric(f"{w30}30天-{rl}", f"{p['r30']:,}")
                        dc[3].metric(f"{w30}30天-互動", f"{p['e30']:,}")
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Export CSV
            export_df = pd.DataFrame(processed_data)
            export_cols = {
                'date': '日期', 'platform': '平台', 'topic': '主題', 'postType': '類型', 
                'postSubType': '子類型', 'postPurpose': '目的', 'postFormat': '形式',
                'projectOwner': '專案負責人', 'postOwner': '貼文負責人', 'designer': '美編',
                'r7': '7天瀏覽/觸及', 'e7': '7天互動', 'rate7_str': '7天互動率',
                'r30': '30天瀏覽/觸及', 'e30': '30天互動', 'rate30_str': '30天互動率'
            }
            export_df = export_df.rename(columns=export_cols)
            final_cols = [c for c in export_cols.values() if c in export_df.columns]
            csv = export_df[final_cols].to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 匯出 CSV", csv, f"social_posts_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

        else:
            st.info("目前沒有符合條件的排程資料。")

# === TAB 2 ===
with tab2:
    with st.expander("⚙️ KPI 標準設定"):
        std = st.session_state.standards
        # 4 cols layout
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.subheader("Facebook")
            st.markdown("**高標**")
            h_reach = st.number_input("FB高標 觸及", value=std['Facebook']['high']['reach'], key='fb_h_r')
            h_eng = st.number_input("FB高標 互動", value=std['Facebook']['high'].get('engagement', 100), key='fb_h_e')
            st.caption(f"預估互動率: {(h_eng/h_reach*100 if h_reach>0 else 0):.1f}%")
            
            st.markdown("**標準**")
            s_reach = st.number_input("FB標準 觸及", value=std['Facebook']['std']['reach'], key='fb_s_r')
            s_eng = st.number_input("FB標準 互動", value=std['Facebook']['std'].get('engagement', 45), key='fb_s_e')
            st.caption(f"預估互動率: {(s_eng/s_reach*100 if s_reach>0 else 0):.1f}%")

            st.markdown("**低標**")
            l_reach = st.number_input("FB低標 觸及", value=std['Facebook']['low']['reach'], key='fb_l_r')
            l_eng = st.number_input("FB低標 互動", value=std['Facebook']['low'].get('engagement', 15), key='fb_l_e')
            st.caption(f"預估互動率: {(l_eng/l_reach*100 if l_reach>0 else 0):.1f}%")
            
            std['Facebook']['high'] = {'reach': h_reach, 'engagement': h_eng}
            std['Facebook']['std'] = {'reach': s_reach, 'engagement': s_eng}
            std['Facebook']['low'] = {'reach': l_reach, 'engagement': l_eng}

        with c2:
            st.subheader("Instagram")
            ig_reach = st.number_input("IG 觸及目標", value=std['Instagram']['reach'])
            ig_eng = st.number_input("IG 互動目標", value=std['Instagram'].get('engagement', 30))
            ig_rt = (ig_eng/ig_reach*100) if ig_reach>0 else 0
            st.caption(f"預估互動率: {ig_rt:.2f}%")
            
            std['Instagram']['engagement'] = ig_eng
            std['Instagram']['reach'] = ig_reach

        with c3:
            st.subheader("Threads")
            tr_reach_lbl = st.text_input("指標1名稱", value=std.get('Threads',{}).get('reach_label', '瀏覽'))
            tr_reach = st.number_input("指標1數值", value=std.get('Threads',{}).get('reach', 500))
            tr_eng_lbl = st.text_input("指標2名稱", value=std.get('Threads',{}).get('engagement_label', '互動'))
            tr_eng = st.number_input("指標2數值", value=std.get('Threads',{}).get('engagement', 50))
            
            std['Threads']['reach_label'] = tr_reach_lbl
            std['Threads']['reach'] = tr_reach
            std['Threads']['engagement_label'] = tr_eng_lbl
            std['Threads']['engagement'] = tr_eng

        with c4:
            st.subheader("其他")
            st.markdown("**YouTube**")
            yt_reach = st.number_input("YT 觸及", value=std['YouTube']['reach'])
            yt_eng = st.number_input("YT 互動", value=std['YouTube'].get('engagement', 20))
            yt_rt = (yt_eng/yt_reach*100) if yt_reach>0 else 0
            st.caption(f"預估互動率: {yt_rt:.2f}%")
            std['YouTube']['reach'] = yt_reach
            std['YouTube']['engagement'] = yt_eng

            st.markdown("**社團**")
            grp_reach = st.number_input("社團觸及", value=std['社團']['reach'])
            grp_eng = st.number_input("社團互動", value=std['社團'].get('engagement', 20))
            grp_rt = (grp_eng/grp_reach*100) if grp_reach>0 else 0
            st.caption(f"預估互動率: {grp_rt:.2f}%")
            std['社團']['reach'] = grp_reach
            std['社團']['engagement'] = grp_eng
        
        if st.button("儲存設定"):
            st.session_state.standards = std
            save_standards(std)
            st.success("已更新！")

    st.markdown("### 📊 成效分析設定")
    c1, c2, c3 = st.columns(3)
    p_sel = c1.selectbox("1. 分析基準", ["metrics7d", "metrics1m"], format_func=lambda x: "🔥 7天" if x == "metrics7d" else "🌳 30天")
    ad_sel = c2.selectbox("2. 內容", ["全部", "💰 廣告", "💬 非廣告"])
    fmt_sel = c3.selectbox("3. 形式", ["全部", "🎬 短影音", "🖼️ 非短影音"])
    
    # Filter Logic
    target = st.session_state.posts
    if "廣告" in ad_sel: target = [p for p in target if p['postPurpose'] in AD_PURPOSE_LIST]
    elif "非廣告" in ad_sel: target = [p for p in target if p['postPurpose'] not in AD_PURPOSE_LIST]
    if "短影音" in fmt_sel: target = [p for p in target if p['postFormat'] == '短影音']
    elif "非短影音" in fmt_sel: target = [p for p in target if p['postFormat'] != '短影音']

    cnt = len(target)
    reach_sum = 0
    eng_sum = 0
    for p in target:
        if is_metrics_disabled(p['platform'], p['postFormat']): continue
        m = p.get(p_sel, {})
        if p['platform'] not in ['Threads', 'LINE@']: reach_sum += safe_num(m.get('reach', 0))
        if p['platform'] != 'LINE@': eng_sum += (safe_num(m.get('likes', 0)) + safe_num(m.get('comments', 0)) + safe_num(m.get('shares', 0)))
    
    rate_avg = (eng_sum / reach_sum * 100) if reach_sum > 0 else 0
    
    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("篇數", cnt)
    m2.metric("總觸及", f"{int(reach_sum):,}")
    m3.metric("總互動", f"{int(eng_sum):,}")
    m4.metric("平均互動率", f"{rate_avg:.2f}%")
    
    st.markdown("### 🏆 各平台成效")
    if target:
        p_stats = []
        for pf in PLATFORMS:
            sub = [p for p in target if p['platform'] == pf]
            if not sub: continue
            r = e = 0
            for p in sub:
                if is_metrics_disabled(p['platform'], p['postFormat']): continue
                m = p.get(p_sel, {})
                if pf != 'Threads': r += safe_num(m.get('reach', 0))
                e += (safe_num(m.get('likes', 0)) + safe_num(m.get('comments', 0)) + safe_num(m.get('shares', 0)))
            rt = (e/r*100) if r > 0 else 0
            rt_s = f"{rt:.2f}%" if pf != 'Threads' else "-"
            p_stats.append({"平台": pf, "篇數": len(sub), "總觸及": int(r), "總互動": int(e), "互動率": rt_s})
        st.dataframe(pd.DataFrame(p_stats), use_container_width=True)

    st.markdown("### 🍰 類型分佈")
    view_type = st.radio("顯示模式", ["📄 表格模式", "📊 圖表模式"], horizontal=True)
    if target:
        df = pd.DataFrame(target)
        if not df.empty:
            piv = pd.crosstab(df['platform'], df['postType'], margins=True, margins_name="總計")
            ex_pf = [p for p in PLATFORMS if p in piv.index]
            final_idx = ex_pf + ["總計"]
            piv = piv.reindex(final_idx)

            if view_type == "📄 表格模式":
                st.dataframe(piv, use_container_width=True)
            else:
                c_df = piv.drop(index="總計", columns="總計", errors='ignore')
                st.bar_chart(c_df)
