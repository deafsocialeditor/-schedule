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

# 平台隱藏標記 (用於 CSS 選擇器識別平台)
PLATFORM_MARKS = {
    'Facebook': '🟦', 
    'Instagram': '🟥', 
    'LINE@': '🟩', 
    'YouTube': '🟪', 
    'Threads': '⬛', 
    '社團': '🟧'
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
        'LINE@': {'type': 'simple', 'reach': 0, 'engagement': 0, 'rate': 0},
        '社團': {'type': 'simple', 'reach': 500, 'engagement': 20, 'rate': 4.0}
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
    """判斷是否不需要填寫成效 (Threads 需填寫，故排除)"""
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

    if not std: return "-", "gray"

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
    elif platform == '社團':
        if reach >= std.get('reach', 0) and rate >= std.get('rate', 0): return "✅ 達標", "green"
        return "🔴 未達標", "red"
    
    return "-", "gray"

# --- Callback 函數 ---
def edit_post_callback(post):
    """點擊編輯按鈕時觸發"""
    st.session_state.editing_post = post
    st.session_state.scroll_to_top = True # 觸發滾動到表單
    
    try:
        st.session_state['entry_date'] = datetime.strptime(post['date'], "%Y-%m-%d").date()
    except:
        st.session_state['entry_date'] = datetime.now().date()
        
    st.session_state['entry_platform_single'] = post['platform']
    st.session_state['entry_topic'] = post['topic']
    st.session_state['entry_type'] = post['postType']
    
    sub_val = post.get('postSubType', '')
    if sub_val in (["-- 無 --"] + SOUVENIR_SUB_TYPES):
        st.session_state['entry_subtype'] = sub_val
    else:
        st.session_state['entry_subtype'] = "-- 無 --"

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
    """日曆點擊跳轉：切換回列表並定位"""
    st.session_state.view_mode_radio = "📋 列表模式"
    st.session_state.target_scroll_id = post_id
    st.session_state.scroll_to_list_item = True 

# --- 3. 初始化 Session State ---
if 'posts' not in st.session_state:
    st.session_state.posts = load_data()
if 'standards' not in st.session_state:
    st.session_state.standards = load_standards()
if 'editing_post' not in st.session_state:
    st.session_state.editing_post = None
if 'scroll_to_top' not in st.session_state:
    st.session_state.scroll_to_top = False
if 'target_scroll_id' not in st.session_state:
    st.session_state.target_scroll_id = None
if 'scroll_to_list_item' not in st.session_state:
    st.session_state.scroll_to_list_item = False

# --- 4. 自訂 CSS (視覺優化：緊湊 + 平台顏色) ---
# 自動生成按鈕顏色的 CSS
calendar_button_css = ""
for pf, mark in PLATFORM_MARKS.items():
    color = PLATFORM_COLORS.get(pf, '#888')
    # 日曆按鈕樣式 - 極致緊湊與滿版
    calendar_button_css += f"""
    div[data-testid="stButton"] button[aria-label^="{mark}"] {{
        background-color: {color} !important;
        color: white !important;
        border: none !important;
        font-size: 0.75em !important; /* 縮小字體 */
        padding: 1px 4px !important; /* 極小內距 */
        border-radius: 3px !important;
        width: 100% !important;
        text-align: left !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        display: block !important;
        margin-top: 0px !important; /* 縮小間距 */
        margin-bottom: 2px !important; /* 縮小間距 */
        line-height: 1.1 !important;
        height: auto !important;
        min-height: 0px !important;
    }}
    div[data-testid="stButton"] button[aria-label^="{mark}"]:hover {{
        filter: brightness(0.9);
        color: white !important;
    }}
    """

st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; }}
    
    /* 縮減上方留白 */
    .block-container {{
        padding-top: 3rem;
        padding-bottom: 2rem;
    }}
    
    /* KPI 標籤 */
    .kpi-badge {{ padding: 2px 6px; border-radius: 8px; font-weight: bold; font-size: 0.8em; display: inline-block; min-width: 50px; text-align: center;}}
    .purple {{ background-color: #f3e8ff; color: #7e22ce; border: 1px solid #d8b4fe; }}
    .green {{ background-color: #dcfce7; color: #15803d; border: 1px solid #86efac; }}
    .orange {{ background-color: #ffedd5; color: #c2410c; border: 1px solid #fdba74; }}
    .red {{ background-color: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }}
    .gray {{ background-color: #f3f4f6; color: #9ca3af; border: 1px solid #e5e7eb; }}
    
    .overdue-alert {{ color: #dc2626; font-weight: bold; font-size: 0.9em; display: flex; align-items: center; }}
    
    /* 平台標籤樣式 (列表用 - 移除 ICON 版) */
    .platform-badge-box {{
        font-weight: 800;
        padding: 4px 8px;
        border-radius: 4px;
        color: white;
        font-size: 0.9em;
        display: inline-block;
        width: 100%;
        text-align: center;
        margin-bottom: 2px;
    }}
    
    /* 列表行樣式 (瘦身版：僅底線，間距縮小) */
    .post-row {{
        background-color: transparent;
        border-bottom: 1px solid #f3f4f6; 
        padding: 8px 0; 
        margin-bottom: 0;
        transition: background-color 0.2s;
    }}
    .post-row:hover {{
        background-color: #f9fafb;
    }}
    
    /* 今日高亮樣式 */
    .today-highlight {{
        background-color: #fffbeb;
        border-bottom: 2px solid #fcd34d;
        padding: 8px 0;
        position: relative;
    }}
    
    /* 滾動定位高亮 */
    @keyframes highlight-fade {{
        0% {{ background-color: #fef08a; }}
        100% {{ background-color: transparent; }}
    }}
    .scroll-highlight {{
        animation: highlight-fade 2s ease-out;
        border-bottom: 2px solid #3b82f6 !important;
        padding: 8px 0;
    }}
    
    .row-text-lg {{ font-size: 1.05em; font-weight: bold; color: #1f2937; }}
    .row-text-md {{ font-size: 0.9em; color: #4b5563; }}
    
    /* 日曆樣式 (緊湊化) */
    .cal-day-header {{ text-align: center; font-weight: bold; color: #6b7280; border-bottom: 1px solid #e5e7eb; padding-bottom: 2px; margin-bottom: 2px; font-size: 0.9em; }}
    .cal-day-cell {{ min-height: 60px; padding: 2px; border-radius: 4px; font-size: 0.8em; border: 1px solid #f3f4f6; }}
    .cal-day-num {{ font-weight: bold; font-size: 0.9em; color: #374151; margin-bottom: 2px; margin-left: 2px; }}
    
    /* 注入按鈕顏色樣式 */
    {calendar_button_css}
    </style>
""", unsafe_allow_html=True)

# --- 5. 側邊欄篩選 ---
with st.sidebar:
    st.title("🔎 篩選條件")
    filter_platform = st.selectbox("平台", ["All"] + PLATFORMS, index=0)
    filter_owner = st.selectbox("負責人", ["All"] + POST_OWNERS, index=0)
    filter_post_type = st.selectbox("貼文類型", ["All"] + MAIN_POST_TYPES, index=0)
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
st.header("📅 2025社群排程與成效")

tab1, tab2 = st.tabs(["🗓️ 排程管理", "📊 數據分析"])

# === TAB 1: 排程管理 ===
with tab1:
    # 錨點：用於編輯時滾動到頂部
    st.markdown("<div id='edit_top'></div>", unsafe_allow_html=True)

    # 1. 編輯模式 -> 滾動到表單頂部
    if st.session_state.scroll_to_top:
        components.html(
            """
            <script>
                setTimeout(function() {
                    try {
                        var top = window.parent.document.getElementById('edit_top');
                        if (top) { top.scrollIntoView({behavior: 'smooth', block: 'start'}); }
                    } catch (e) { console.log(e); }
                }, 100);
            </script>
            """,
            height=0
        )
        st.session_state.scroll_to_top = False

    # 2. 日曆點擊 -> 滾動到列表項目
    if st.session_state.scroll_to_list_item and st.session_state.target_scroll_id:
        target = st.session_state.target_scroll_id
        components.html(
            f"""
            <script>
                setTimeout(function() {{
                    try {{
                        var el = window.parent.document.getElementById('post_{target}');
                        if (el) {{ el.scrollIntoView({{behavior: 'smooth', block: 'center'}}); }}
                    }} catch (e) {{ console.log(e); }}
                }}, 300);
            </script>
            """,
            height=0
        )
        st.session_state.scroll_to_list_item = False

    with st.expander("✨ 新增/編輯 貼文", expanded=st.session_state.editing_post is not None):
        is_edit = st.session_state.editing_post is not None
        target_edit_id = st.session_state.editing_post['id'] if is_edit else None
        
        # 狀態初始化
        if 'entry_date' not in st.session_state: st.session_state['entry_date'] = datetime.now()
        if 'entry_platform_single' not in st.session_state: st.session_state['entry_platform_single'] = PLATFORMS[0]
        if 'entry_platform_multi' not in st.session_state: st.session_state['entry_platform_multi'] = ['Facebook']
        if 'entry_topic' not in st.session_state: st.session_state['entry_topic'] = ""
        if 'entry_type' not in st.session_state: st.session_state['entry_type'] = MAIN_POST_TYPES[0]
        if 'entry_subtype' not in st.session_state: st.session_state['entry_subtype'] = "-- 無 --"
        if 'entry_purpose' not in st.session_state: st.session_state['entry_purpose'] = POST_PURPOSES[0]
        if 'entry_format' not in st.session_state: st.session_state['entry_format'] = ""
        if 'entry_po' not in st.session_state: st.session_state['entry_po'] = ""
        if 'entry_owner' not in st.session_state: st.session_state['entry_owner'] = ""
        if 'entry_designer' not in st.session_state: st.session_state['entry_designer'] = ""
        
        for k in ['entry_m7_reach', 'entry_m7_likes', 'entry_m7_comments', 'entry_m7_shares',
                  'entry_m1_reach', 'entry_m1_likes', 'entry_m1_comments', 'entry_m1_shares']:
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
        f_subtype = c5.selectbox("子類型 (伴手禮用)", ["-- 無 --"] + SOUVENIR_SUB_TYPES, disabled=(f_type != '伴手禮'), key="entry_subtype")
        
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
                for p in selected_platforms:
                    platform_purposes[p] = single_purpose

        f_format = c8.selectbox("形式", [""] + POST_FORMATS, key="entry_format")

        c9, c10, c11 = st.columns(3)
        f_po = c9.selectbox("專案負責人", [""] + PROJECT_OWNERS, key="entry_po")
        f_owner = c10.selectbox("貼文負責人", [""] + POST_OWNERS, key="entry_owner")
        f_designer = c11.selectbox("美編", [""] + DESIGNERS, key="entry_designer")

        st.divider()
        
        if isinstance(f_date, datetime):
            f_date_obj = f_date.date()
        else:
            f_date_obj = f_date

        due_date_7d = f_date_obj + timedelta(days=7)
        due_date_1m = f_date_obj + timedelta(days=30)
        
        current_platform = selected_platforms[0] if selected_platforms else 'Facebook'
        hide_metrics = is_metrics_disabled(current_platform, f_format)
        
        metrics_input = {'metrics7d': {}, 'metrics1m': {}}

        if not hide_metrics:
            st.caption("數據填寫")
            reach_label = "瀏覽數" if current_platform == 'Threads' else "觸及數"
            
            m_cols = st.columns(2)
            with m_cols[0]:
                st.markdown(f"##### 🔥 7天成效 <span style='font-size:0.7em; color:#ef4444; background:#fee2e2; padding:2px 6px; border-radius:4px;'>預計: {due_date_7d.strftime('%m/%d')}</span>", unsafe_allow_html=True)
                metrics_input['metrics7d']['reach'] = st.number_input(f"7天-{reach_label}", step=1, key="entry_m7_reach")
                metrics_input['metrics7d']['likes'] = st.number_input("7天-按讚", step=1, key="entry_m7_likes")
                sub_c1, sub_c2 = st.columns(2)
                metrics_input['metrics7d']['comments'] = sub_c1.number_input("7天-留言", step=1, key="entry_m7_comments")
                metrics_input['metrics7d']['shares'] = sub_c2.number_input("7天-分享", step=1, key="entry_m7_shares")

            with m_cols[1]:
                st.markdown(f"##### 🌳 一個月成效 <span style='font-size:0.7em; color:#a855f7; background:#f3e8ff; padding:2px 6px; border-radius:4px;'>預計: {due_date_1m.strftime('%m/%d')}</span>", unsafe_allow_html=True)
                metrics_input['metrics1m']['reach'] = st.number_input(f"1月-{reach_label}", step=1, key="entry_m1_reach")
                metrics_input['metrics1m']['likes'] = st.number_input("1月-按讚", step=1, key="entry_m1_likes")
                sub_c3, sub_c4 = st.columns(2)
                metrics_input['metrics1m']['comments'] = sub_c3.number_input("1月-留言", step=1, key="entry_m1_comments")
                metrics_input['metrics1m']['shares'] = sub_c4.number_input("1月-分享", step=1, key="entry_m1_shares")
        else:
            st.info(f"ℹ️ {current_platform} / {f_format} 不需要填寫成效數據")

        submitted = st.button("💾 儲存貼文 (預設已發布)", type="primary", use_container_width=True)

        if submitted:
            if not f_topic:
                st.error("請填寫主題")
            else:
                if is_edit:
                    p = selected_platforms[0]
                    final_purpose = platform_purposes[p]
                    new_base = {
                        'date': f_date.strftime("%Y-%m-%d"),
                        'topic': f_topic,
                        'postType': f_type,
                        'postSubType': f_subtype if f_subtype != "-- 無 --" else "",
                        'postPurpose': final_purpose, 
                        'postFormat': f_format,
                        'projectOwner': f_po,
                        'postOwner': f_owner,
                        'designer': f_designer,
                        'status': 'published',
                        'metrics7d': metrics_input['metrics7d'],
                        'metrics1m': metrics_input['metrics1m']
                    }
                    
                    for i, p_data in enumerate(st.session_state.posts):
                        if p_data['id'] == target_edit_id:
                            st.session_state.posts[i] = {**p_data, **new_base, 'platform': p}
                            break
                    st.session_state.editing_post = None
                    st.success("已更新！")
                else:
                    for p in selected_platforms:
                        final_purpose = platform_purposes[p]
                        new_post = {
                            'id': str(uuid.uuid4()),
                            'date': f_date.strftime("%Y-%m-%d"),
                            'platform': p,
                            'topic': f_topic,
                            'postType': f_type,
                            'postSubType': f_subtype if f_subtype != "-- 無 --" else "",
                            'postPurpose': final_purpose,
                            'postFormat': f_format,
                            'projectOwner': f_po,
                            'postOwner': f_owner,
                            'designer': f_designer,
                            'status': 'published',
                            'metrics7d': metrics_input['metrics7d'],
                            'metrics1m': metrics_input['metrics1m']
                        }
                        if is_metrics_disabled(p, f_format):
                            new_post['metrics7d'] = {}
                            new_post['metrics1m'] = {}
                        st.session_state.posts.append(new_post)
                    st.success(f"已新增 {len(selected_platforms)} 則貼文！")
                
                save_data(st.session_state.posts)
                
                keys_to_clear = [key for key in st.session_state.keys() if key.startswith("entry_") or key.startswith("purpose_for_")]
                for key in keys_to_clear:
                    del st.session_state[key]
                st.rerun()

        if st.session_state.editing_post:
            if st.button("取消編輯"):
                st.session_state.editing_post = None
                keys_to_clear = [key for key in st.session_state.keys() if key.startswith("entry_")]
                for key in keys_to_clear:
                    del st.session_state[key]
                st.rerun()

    # --- 檢視模式切換 ---
    if 'view_mode_radio' not in st.session_state:
        st.session_state.view_mode_radio = "🗓️ 日曆模式" # 預設日曆
        
    view_mode = st.radio("檢視模式", ["📋 列表模式", "🗓️ 日曆模式"], horizontal=True, label_visibility="collapsed", key="view_mode_radio")
    st.write("") 

    # --- 列表顯示邏輯 ---
    filtered_posts = st.session_state.posts
    
    if date_filter_type == "月":
        filtered_posts = [p for p in filtered_posts if p['date'].startswith(selected_month)]
    else:
        filtered_posts = [p for p in filtered_posts if start_date <= datetime.strptime(p['date'], "%Y-%m-%d").date() <= end_date]
    
    if filter_platform != "All":
        filtered_posts = [p for p in filtered_posts if p['platform'] == filter_platform]
    if filter_owner != "All":
        filtered_posts = [p for p in filtered_posts if p['postOwner'] == filter_owner]
    if filter_topic_keyword:
        filtered_posts = [p for p in filtered_posts if filter_topic_keyword.lower() in p['topic'].lower()]
    if filter_post_type != "All":
        filtered_posts = [p for p in filtered_posts if p['postType'] == filter_post_type]
    if filter_purpose != "All":
        filtered_posts = [p for p in filtered_posts if p['postPurpose'] == filter_purpose]
    if filter_format != "All":
        filtered_posts = [p for p in filtered_posts if p['postFormat'] == filter_format]

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
        for i, day_name in enumerate(weekdays):
            cols[i].markdown(f"<div class='cal-day-header'>{day_name}</div>", unsafe_allow_html=True)

        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                with cols[i]:
                    if day == 0:
                        st.markdown("<div class='cal-day-cell' style='background-color:#f9fafb;'></div>", unsafe_allow_html=True)
                    else:
                        current_date_str = f"{cal_year}-{cal_month:02d}-{day:02d}"
                        is_today_cal = (current_date_str == datetime.now().strftime("%Y-%m-%d"))
                        bg_style = "background-color:#fef9c3; border:2px solid #fcd34d;" if is_today_cal else "background-color:white; border:1px solid #e5e7eb;"
                        
                        with st.container():
                            st.markdown(f"""
                                <div class='cal-day-cell' style='{bg_style}'>
                                    <div class='cal-day-num'>{day}</div>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            day_posts = [p for p in filtered_posts if p['date'] == current_date_str]
                            
                            for p in day_posts:
                                # 檢查鈴鐺
                                show_bell = False
                                if not is_metrics_disabled(p['platform'], p['postFormat']):
                                    p_date = datetime.strptime(p['date'], "%Y-%m-%d").date()
                                    if datetime.now().date() >= (p_date + timedelta(days=7)):
                                        if safe_num(p.get('metrics7d', {}).get('reach', 0)) == 0:
                                            show_bell = True
                                
                                # 使用色塊 + 標題
                                mark = PLATFORM_MARKS.get(p['platform'], '🟦')
                                bell_icon = "🔔" if show_bell else ""
                                topic_limit = 4 if show_bell else 5
                                label = f"{mark} {bell_icon}{p['topic'][:topic_limit]}.."
                                
                                # 日曆點擊
                                if st.button(label, key=f"cal_btn_{p['id']}", help=f"{p['platform']} - {p['topic']}", on_click=go_to_post_from_calendar, args=(p['id'],)):
                                    pass

    else:
        # --- 列表模式 ---
        # 修正：先初始化 display_data
        display_data = []

        col_sort1, col_sort2, col_count = st.columns([1, 1, 4])
        with col_sort1:
            sort_by = st.selectbox("排序依據", ["日期", "平台", "主題", "貼文類型"], index=0)
        with col_sort2:
            sort_order = st.selectbox("順序", ["升序 (舊->新)", "降序 (新->舊)"], index=0)

        key_map = { "日期": "date", "平台": "platform", "主題": "topic", "貼文類型": "postType" }
        reverse_sort = True if "降序" in sort_order else False
        filtered_posts.sort(key=lambda x: x[key_map[sort_by]], reverse=reverse_sort)

        with col_count:
            st.write("")
            st.markdown(f"**共篩選出 {len(filtered_posts)} 筆資料**")

        st.divider()

        if filtered_posts:
            # 欄位定義：12 欄 (0~11)
            col_list = st.columns([0.8, 0.7, 1.8, 0.7, 0.6, 0.6, 0.6, 0.6, 0.6, 0.4, 0.4, 0.4])
            headers = ["日期", "平台", "主題", "類型", "目的", "形式", "KPI", "7日互動率", "30日互動率", "負責人", "編輯", "刪除"]
            
            for col, h in zip(col_list, headers):
                col.markdown(f"**{h}**")
            st.markdown("<hr style='margin: 0.5em 0; border-top: 1px dashed #ddd;'>", unsafe_allow_html=True)

            today_str = datetime.now().strftime("%Y-%m-%d")
            today_date_obj = datetime.now().date()
            
            for p in filtered_posts:
                raw_p = p
                label, color = get_performance_label(raw_p['platform'], raw_p.get('metrics7d'), raw_p['postFormat'], st.session_state.standards)
                is_today = (p['date'] == today_str)

                def calc_rate_and_check_due(metrics, days_offset):
                    eng = safe_num(metrics.get('likes', 0)) + safe_num(metrics.get('comments', 0)) + safe_num(metrics.get('shares', 0))
                    reach = safe_num(metrics.get('reach', 0))
                    
                    rate_str = "-"
                    # Threads 不計算互動率，顯示「不計」
                    if p['platform'] == 'Threads':
                        rate_str = "<span style='color:#bbb; font-size:0.9em'>🚫 不計</span>"
                    elif reach > 0 and not is_metrics_disabled(p['platform'], p['postFormat']):
                        rate_str = f"{(eng/reach*100):.1f}%"
                    
                    post_date = datetime.strptime(p['date'], "%Y-%m-%d").date()
                    due_date = post_date + timedelta(days=days_offset)
                    
                    # 判斷是否顯示鈴鐺
                    show_bell = False
                    if not is_metrics_disabled(p['platform'], p['postFormat']):
                        if today_date_obj >= due_date and reach == 0:
                            show_bell = True

                    return rate_str, show_bell, int(reach), int(eng)

                rate7, show_bell_7, r7, e7 = calc_rate_and_check_due(p.get('metrics7d', {}), 7)
                rate30, show_bell_30, r30, e30 = calc_rate_and_check_due(p.get('metrics1m', {}), 30)

                # 滾動高亮判定
                is_target = (st.session_state.target_scroll_id == p['id'])
                row_class = "scroll-highlight" if is_target else ("today-highlight" if is_today else "post-row")
                
                # HTML 錨點
                st.markdown(f"<div id='post_{p['id']}'></div>", unsafe_allow_html=True)
                
                with st.container():
                    st.markdown(f'<div class="{row_class}">', unsafe_allow_html=True)
                    # 12 columns
                    cols = st.columns([0.8, 0.7, 1.8, 0.7, 0.6, 0.6, 0.6, 0.6, 0.6, 0.4, 0.4, 0.4])
                    
                    cols[0].markdown(f"<span class='row-text-lg'>{p['date']}</span>", unsafe_allow_html=True)
                    
                    p_color = PLATFORM_COLORS.get(p['platform'], '#6b7280')
                    # 平台標籤 (移除 ICON)
                    cols[1].markdown(f"<span class='platform-badge-box' style='background-color:{p_color}'>{p['platform']}</span>", unsafe_allow_html=True)
                    
                    cols[2].markdown(f"<span class='row-text-lg'>{p['topic']}</span>", unsafe_allow_html=True)
                    
                    cols[3].write(f"{p['postType']}")
                    cols[4].write(p['postPurpose']) 
                    cols[5].write(p['postFormat']) 
                    cols[6].markdown(f"<span class='kpi-badge {color}'>{label.split(' ')[-1] if ' ' in label else label}</span>", unsafe_allow_html=True)
                    
                    # 7日互動率
                    if show_bell_7 and p['platform'] != 'Threads':
                        cols[7].markdown(f"<span class='overdue-alert'>🔔 缺</span>", unsafe_allow_html=True)
                    else:
                        cols[7].markdown(str(rate7), unsafe_allow_html=True)

                    # 30日互動率
                    if show_bell_30 and p['platform'] != 'Threads':
                        cols[8].markdown(f"<span class='overdue-alert'>🔔 缺</span>", unsafe_allow_html=True)
                    else:
                        cols[8].markdown(str(rate30), unsafe_allow_html=True)
                        
                    cols[9].write(f"{p['postOwner']}")

                    # Edit (Index 10)
                    if cols[10].button("✏️", key=f"edit_{p['id']}", on_click=edit_post_callback, args=(p,)):
                        pass 
                    
                    # Delete (Index 11) - Confirmed 12 cols
                    if cols[11].button("🗑️", key=f"del_{p['id']}", on_click=delete_post_callback, args=(p['id'],)):
                        pass

                    # 詳細數據展開區
                    expander_label = "📉 詳細數據"
                    # Threads 若缺資料，外層顯示紅字鈴鐺
                    if p['platform'] == 'Threads' and (show_bell_7 or show_bell_30):
                         expander_label = "📉 詳細數據 :red[🔔 缺資料]" 

                    with st.expander(expander_label):
                        r_label = "瀏覽" if p['platform'] == 'Threads' else "觸及"
                        d_c1, d_c2, d_c3, d_c4 = st.columns(4)
                        
                        warn7 = "🔔 " if (show_bell_7 and p['platform'] == 'Threads') else ""
                        warn30 = "🔔 " if (show_bell_30 and p['platform'] == 'Threads') else ""

                        d_c1.metric(f"{warn7}7天-{r_label}", f"{r7:,}")
                        d_c2.metric(f"{warn7}7天-互動", f"{e7:,}")
                        d_c3.metric(f"{warn30}30天-{r_label}", f"{r30:,}")
                        d_c4.metric(f"{warn30}30天-互動", f"{e30:,}")
                    
                    st.markdown('</div>', unsafe_allow_html=True)

            if display_data:
                csv = pd.DataFrame(display_data).drop(columns=['_raw', 'ID'], errors='ignore').to_csv(index=False).encode('utf-8-sig')
                st.download_button(label="📥 匯出 CSV", data=csv, file_name=f"social_posts_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
        else:
            st.info("目前沒有符合條件的排程資料。")

# === TAB 2: 數據分析 ===
with tab2:
    with st.expander("⚙️ KPI 標準設定"):
        std = st.session_state.standards
        c_fb, c_ig, c_others = st.columns(3)
        with c_fb:
            st.subheader("Facebook")
            for level in ['high', 'std', 'low']:
                l_name = {'high': '🏆 高標', 'std': '✅ 標準', 'low': '🤏 低標'}[level]
                st.caption(l_name)
                c_1, c_2 = st.columns(2)
                std['Facebook'][level]['reach'] = c_1.number_input(f"FB {level} 觸及", value=std['Facebook'][level]['reach'])
                std['Facebook'][level]['rate'] = c_2.number_input(f"FB {level} 率(%)", value=std['Facebook'][level]['rate'])
        with c_ig:
            st.subheader("Instagram")
            std['Instagram']['reach'] = st.number_input("IG 觸及目標", value=std['Instagram']['reach'])
            std['Instagram']['engagement'] = st.number_input("IG 互動數目標", value=std['Instagram']['engagement'])
            std['Instagram']['rate'] = st.number_input("IG 互動率目標(%)", value=std['Instagram']['rate'])
        with c_others:
            st.subheader("其他")
            std['YouTube']['reach'] = st.number_input("YT 觸及", value=std['YouTube']['reach'])
            std['Threads']['reach'] = st.number_input("Threads 瀏覽標竿", value=std['Threads']['reach'])
            c_grp1, c_grp2 = st.columns(2)
            c_grp1.markdown("**社團**")
            std_grp_reach = c_grp1.number_input("社團觸及目標", value=std.get('社團', {}).get('reach', 500))
            std_grp_rate = c_grp2.number_input("社團互動率目標(%)", value=std.get('社團', {}).get('rate', 4.0))
            if '社團' not in std: std['社團'] = {}
            std['社團']['reach'] = std_grp_reach
            std['社團']['rate'] = std_grp_rate

        if st.button("儲存設定"):
            st.session_state.standards = std
            save_standards(std)
            st.success("KPI 設定已更新！")

    st.markdown("### 📊 成效分析設定")
    ctrl1, ctrl2, ctrl3 = st.columns(3)
    period = ctrl1.selectbox("1. 分析基準 (時間)", ["metrics7d", "metrics1m"], format_func=lambda x: "🔥 7天成效" if x == "metrics7d" else "🌳 一個月成效")
    ad_filter_val = ctrl2.selectbox("2. 內容類型", ["全部", "💰 廣告成效 (僅廣告/門市廣告)", "💬 非廣告成效 (排除廣告)"])
    video_filter_val = ctrl3.selectbox("3. 形式過濾", ["全部", "🎬 短影音", "🖼️ 非短影音 (一般貼文)"])

    st.markdown("---")

    published_posts = [p for p in filtered_posts]
    target_posts = published_posts
    
    if ad_filter_val == "💰 廣告成效 (僅廣告/門市廣告)":
        target_posts = [p for p in target_posts if p['postPurpose'] in AD_PURPOSE_LIST]
    elif ad_filter_val == "💬 非廣告成效 (排除廣告)":
        target_posts = [p for p in target_posts if p['postPurpose'] not in AD_PURPOSE_LIST]
        
    if video_filter_val == "🎬 短影音":
        target_posts = [p for p in target_posts if p['postFormat'] == '短影音']
    elif video_filter_val == "🖼️ 非短影音 (一般貼文)":
        target_posts = [p for p in target_posts if p['postFormat'] != '短影音']

    def calc_stats_subset(posts_subset, p_period):
        count = len(posts_subset)
        reach = 0
        engage = 0
        for p in posts_subset:
            if is_metrics_disabled(p['platform'], p['postFormat']): continue
            m = p.get(p_period, {})
            if p['platform'] not in ['Threads', 'LINE@']:
                reach += safe_num(m.get('reach', 0))
            if p['platform'] != 'LINE@':
                engage += (safe_num(m.get('likes', 0)) + safe_num(m.get('comments', 0)) + safe_num(m.get('shares', 0)))
        rate = (engage / reach * 100) if reach > 0 else 0
        return count, reach, engage, rate

    t_c, t_r, t_e, t_rt = calc_stats_subset(target_posts, period)

    st.markdown("### 📈 總體成效概覽 (根據上方設定)")
    ov1, ov2, ov3, ov4 = st.columns(4)
    ov1.metric("篇數", t_c)
    ov1.caption("符合條件的貼文數")
    ov2.metric("總觸及", f"{int(t_r):,}")
    ov2.caption("不含 Threads/LINE@")
    ov3.metric("總互動", f"{int(t_e):,}")
    ov3.caption("不含 LINE@")
    ov4.metric("平均互動率", f"{t_rt:.2f}%")
    ov4.caption("總互動 / 總觸及")

    st.markdown("---")

    st.markdown("### 🏆 各平台成效詳細分析")

    platform_table_data = []
    
    for pf in PLATFORMS:
        if filter_platform != "All" and filter_platform != pf:
            continue
            
        posts_pf = [p for p in target_posts if p['platform'] == pf]
        if not posts_pf: continue
        
        c, r, e, rt = calc_stats_subset(posts_pf, period)
        
        rt_display = f"{rt:.2f}%"
        if pf == 'Threads':
            rt_display = "-"

        platform_table_data.append({
            "平台": f"{ICONS.get(pf, '')} {pf}",
            "篇數": c,
            "總觸及": int(r),
            "總互動": int(e),
            "互動率": rt_display
        })
    
    if platform_table_data:
        st.dataframe(
            pd.DataFrame(platform_table_data),
            column_config={
                "總觸及": st.column_config.NumberColumn(format="%d"),
                "總互動": st.column_config.NumberColumn(format="%d"),
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("在此篩選條件下無資料。")

    st.divider()

    st.markdown("### 🍰 貼文類型分佈 (各平台)")

    view_type = st.radio("顯示模式", ["📄 表格模式", "📊 圖表模式"], horizontal=True)

    if target_posts:
        data_for_dist = []
        for p in target_posts:
            data_for_dist.append({'Platform': p['platform'], 'Type': p['postType']})
        
        df_dist = pd.DataFrame(data_for_dist)
        pivot_df = pd.crosstab(df_dist['Platform'], df_dist['Type'], margins=True, margins_name="總計")
        existing_platforms = [p for p in PLATFORMS if p in pivot_df.index]
        final_index = [x for x in existing_platforms] + ["總計"]
        final_index = [x for x in final_index if x in pivot_df.index]
        pivot_df = pivot_df.reindex(final_index)

        if view_type == "📄 表格模式":
            st.dataframe(pivot_df, use_container_width=True)
        else:
            chart_df = pivot_df.drop(index="總計", columns="總計", errors='ignore')
            st.bar_chart(chart_df)
    else:
        st.caption("無符合條件的貼文數據")
