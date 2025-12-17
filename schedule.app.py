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
SHEET_URL = "https://docs.google.com/spreadsheets/d/1Nvqid5fHkcrkOJE322Xqv_R_7kU4krc9q8us3iswRGc/edit?gid=0#gid=0" 
STANDARDS_FILE = "social_standards.json"

# Google API Scope
SCOPE = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# --- 核心設定：中文欄位對照表 ---
# 左邊是程式用的(英文)，右邊是試算表顯示的(中文)
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
    # 成效數據
    'metrics7d_reach': '7天觸及',
    'metrics7d_likes': '7天互動',
    'metrics7d_comments': '7天留言',
    'metrics7d_shares': '7天分享',
    'metrics1m_reach': '30天觸及',
    'metrics1m_likes': '30天互動',
    'metrics1m_comments': '30天留言',
    'metrics1m_shares': '30天分享'
}

# 反向對照 (讀取用：中文 -> 英文)
REV_COL_MAP = {v: k for k, v in COL_MAP.items()}

# 選項定義
PLATFORMS = ['Facebook', 'Instagram', 'LINE@', 'YouTube', 'Threads', '社團']
MAIN_POST_TYPES = ['喜餅', '彌月', '伴手禮', '社群互動', '圓夢計畫', '公告']
SOUVENIR_SUB_TYPES = ['端午節', '中秋', '聖誕', '新春', '蒙友週']
POST_PURPOSES = ['互動', '廣告', '門市廣告', '導購', '公告']
POST_FORMATS = ['單圖', '多圖', '假多圖', '短影音', '限動', '純文字', '留言處']
PROJECT_OWNERS = ['夢涵', 'MOMO', '櫻樺', '季嫻', '凌萱', '宜婷', '門市']
POST_OWNERS = ['一千', '楷曜', '可榆']
DESIGNERS = ['千惟', '靖嬙']

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
        raw_records = sheet.get_all_records() # 讀取下來的是中文 Key
        
        processed_posts = []
        for row in raw_records:
            # 使用中文 Key 讀取資料
            def get_val(cn_key, default=""):
                return row.get(cn_key, default)

            m7 = {
                'reach': safe_num(get_val('7天觸及', 0)),
                'likes': safe_num(get_val('7天互動', 0)),
                'comments': safe_num(get_val('7天留言', 0)),
                'shares': safe_num(get_val('7天分享', 0))
            }
            m1 = {
                'reach': safe_num(get_val('30天觸及', 0)),
                'likes': safe_num(get_val('30天互動', 0)),
                'comments': safe_num(get_val('30天留言', 0)),
                'shares': safe_num(get_val('30天分享', 0))
            }
            
            post = {
                'id': str(get_val('ID')) if get_val('ID') else str(uuid.uuid4()),
                'date': str(get_val('日期', '')),
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
        # st.error(f"讀取失敗: {e}") # 剛初始化時可能會錯，先隱藏
        return []

def save_data(data):
    client = get_client()
    if not client: return
    try:
        sheet = client.open_by_url(SHEET_URL).sheet1
        
        # 1. 將資料攤平 (使用程式英文 Key)
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
            
            # 2. 將英文欄位名稱 -> 轉換為中文
            df = df.rename(columns=COL_MAP)
            
            # 3. 確保欄位順序 (中文)
            chinese_cols_order = [
                'ID', '日期', '平台', '主題', '類型', '子類型', '目的', '形式', 
                '專案負責人', '貼文負責人', '美編', '狀態',
                '7天觸及', '7天互動', '7天留言', '7天分享',
                '30天觸及', '30天互動', '30天留言', '30天分享'
            ]
            
            # 防呆：補齊沒出現的欄位
            for c in chinese_cols_order:
                if c not in df.columns: df[c] = ""
            
            df = df[chinese_cols_order] # 排序
            
            sheet.clear()
            update_data = [df.columns.values.tolist()] + df.values.tolist()
            sheet.update(update_data)
        else:
            # 如果是空的，至少寫入標題
            sheet.clear()
            sheet.append_row(list(COL_MAP.values()))

    except Exception as e:
        st.error(f"儲存失敗: {e}")

# KPI 標準 (維持不變)
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
        if today >= (p_date + timedelta(days=30)) and r30 == 0: bell30 = True
    return {**p, 'r7': int(r7), 'e7': int(e7), 'rate7_val': rate7_val, 'rate7_str': rate7_str, 'bell7': bell7, 'r30': int(r30), 'e30': int(e30), 'rate30_val': rate30_val, 'rate30_str': rate30_str, 'bell30': bell30, '_sort_date': p.get('date', str(today))}

def edit_post_callback(post):
    st.session_state.editing_post = post; st.session_state.scroll_to_top = True
    if st.session_state.view_mode_radio == "🗓️ 日曆模式": st.session_state.view_mode_radio = "📋 列表模式"
    try: st.session_state['entry_date'] = datetime.strptime(post['date'], "%Y-%m-%d").date()
    except: st.session_state['entry_date'] = datetime.now().date()
    st.session_state['entry_platform_single'] = post['platform'] if post['platform'] in PLATFORMS else PLATFORMS[0]
    st.session_state['entry_topic'] = post['topic']
    st.session_state['entry_type'] = post['postType'] if post['postType'] in MAIN_POST_TYPES else MAIN_POST_TYPES[0]
    sub = post.get('postSubType', ''); st.session_state['entry_subtype'] = sub if sub in SOUVENIR_SUB_TYPES else "-- 無 --"
    st.session_state['entry_purpose'] = post['postPurpose'] if post['postPurpose'] in POST_PURPOSES else POST_PURPOSES[0]
    st.session_state['entry_format'] = post['postFormat'] if post['postFormat'] in POST_FORMATS else POST_FORMATS[0]
    st.session_state['entry_po'] = post['projectOwner'] if post['projectOwner'] in PROJECT_OWNERS else PROJECT_OWNERS[0]
    st.session_state['entry_owner'] = post['postOwner'] if post['postOwner'] in POST_OWNERS else POST_OWNERS[0]
    st.session_state['entry_designer'] = post['designer'] if post['designer'] in DESIGNERS else DESIGNERS[0]
    m7 = post.get('metrics7d', {}); st.session_state['entry_m7_reach'] = safe_num(m7.get('reach', 0)); st.session_state['entry_m7_likes'] = safe_num(m7.get('likes', 0)); st.session_state['entry_m7_comments'] = safe_num(m7.get('comments', 0)); st.session_state['entry_m7_shares'] = safe_num(m7.get('shares', 0))
    m1 = post.get('metrics1m', {}); st.session_state['entry_m1_reach'] = safe_num(m1.get('reach', 0)); st.session_state['entry_m1_likes'] = safe_num(m1.get('likes', 0)); st.session_state['entry_m1_comments'] = safe_num(m1.get('comments', 0)); st.session_state['entry_m1_shares'] = safe_num(m1.get('shares', 0))

def delete_post_callback(post_id):
    st.session_state.posts = [item for item in st.session_state.posts if item['id'] != post_id]
    save_data(st.session_state.posts)

def go_to_post_from_calendar(post_id):
    st.session_state.view_mode_radio = "📋 列表模式"; st.session_state.target_scroll_id = post_id; st.session_state.scroll_to_list_item = True 

def reset_filters():
    st.session_state.filter_platform = []; st.session_state.filter_owner = []; st.session_state.filter_post_type = []; st.session_state.filter_purpose = []; st.session_state.filter_format = []; st.session_state.filter_topic_keyword = ""

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
    cal_btn_css += f"""div[data-testid="stButton"] button[aria-label^="{mark}"] {{background-color: {color} !important; color: white !important; border: none !important; font-size: 0.75em !important; padding: 1px 4px !important; border-radius: 3px !important; width: 100% !important; text-align: left !important; white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important; display: block !important; margin-top: 0px !important; margin-bottom: 2px !important; line-height: 1.1 !important; height: auto !important; min-height: 0px !important;}} div[data-testid="stButton"] button[aria-label^="{mark}"]:hover {{ filter: brightness(0.9); color: white !important; }}"""

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
    # 同步按鈕
    if st.button("🔄 強制同步雲端資料"):
        st.session_state.posts = load_data()
        st.success("已更新！")
        st.rerun()

    st.title("🔎 篩選條件")
    if st.button("🧹 重置所有篩選", use_container_width=True):
        reset_filters(); st.rerun()
        
    filter_platform = st.multiselect("平台", ["All"] + PLATFORMS, key='filter_platform')
    filter_owner = st.multiselect("負責人", ["All"] + POST_OWNERS, key='filter_owner')
    filter_post_type = st.multiselect("貼文類型", ["All"] + MAIN_POST_TYPES, key='filter_post_type')
    filter_purpose = st.multiselect("目的", ["All"] + POST_PURPOSES, key='filter_purpose')
    filter_format = st.multiselect("形式", ["All"] + POST_FORMATS, key='filter_format')
    filter_topic_keyword = st.text_input("搜尋主題 (關鍵字)", key='filter_topic_keyword')
    
    st.divider()
    
    # 初始化/修復按鈕 (寫入中文標題)
    if st.button("🔨 修復試算表標題 (中文)"):
        try:
            client = get_client()
            if client:
                sheet = client.open_by_url(SHEET_URL).sheet1
                # 使用定義好的中文欄位順序
                chinese_cols_order = [
                    'ID', '日期', '平台', '主題', '類型', '子類型', '目的', '形式', 
                    '專案負責人', '貼文負責人', '美編', '狀態',
                    '7天觸及', '7天互動', '7天留言', '7天分享',
                    '30天觸及', '30天互動', '30天留言', '30天分享'
                ]
                sheet.clear()
                sheet.append_row(chinese_cols_order)
                st.success("已將 Google Sheets 標題重置為中文！")
        except Exception as e:
            st.error(f"失敗: {e}")

    st.divider()
    date_filter_type = st.radio("日期模式", ["月", "自訂範圍"], horizontal=True, key='date_filter_type')
    if date_filter_type == "月":
        dates = [p['date'] for p in st.session_state.posts] if st.session_state.posts else [datetime.now().strftime("%Y-%m-%d")]
        months = sorted(list(set([d[:7] for d in dates if len(d) >= 7])), reverse=True)
        if not months: months = [datetime.now().strftime("%Y-%m")]
        selected_month = st.selectbox("選擇月份", months, key='selected_month')
    else:
        c1, c2 = st.columns(2)
        start_date = c1.date_input("開始", datetime.now().replace(day=1), key='start_date')
        end_date = c2.date_input("結束", datetime.now(), key='end_date')
    
    st.divider()
    with st.expander("🗑️ 危險區域：清空資料"):
        st.warning("警告：此操作將刪除所有貼文資料，且無法復原！")
        if st.button("🧨 確認清空所有資料", type="primary", use_container_width=True):
            st.session_state.posts = []; save_data([]); st.success("資料已清空！"); st.rerun()

# --- 6. Main Page ---
st.header("📅 2025社群排程與成效")
tab1, tab2 = st.tabs(["🗓️ 排程管理", "📊 數據分析"])

# === TAB 1 ===
with tab1:
    st.markdown("<div id='edit_top'></div>", unsafe_allow_html=True)
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
        
        # Init form defaults
        for k in ['entry_date', 'entry_platform_single', 'entry_platform_multi', 'entry_topic', 'entry_type', 'entry_subtype', 'entry_purpose', 'entry_format', 'entry_po', 'entry_owner', 'entry_designer']:
            if k not in st.session_state:
                if k == 'entry_date': st.session_state[k] = datetime.now()
                elif 'platform_single' in k: st.session_state[k] = PLATFORMS[0]
                elif 'platform_multi' in k: st.session_state[k] = ['Facebook']
                elif 'type' in k: st.session_state[k] = MAIN_POST_TYPES[0]
                elif 'purpose' in k: st.session_state[k] = POST_PURPOSES[0]
                elif 'format' in k: st.session_state[k] = POST_FORMATS[0]
                elif 'po' in k: st.session_state[k] = PROJECT_OWNERS[0]
                elif 'owner' in k: st.session_state[k] = POST_OWNERS[0]
                elif 'designer' in k: st.session_state[k] = DESIGNERS[0]
                elif 'subtype' in k: st.session_state[k] = "-- 無 --"
                else: st.session_state[k] = ""
        
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
        f_format = c8.selectbox("形式", POST_FORMATS, key="entry_format")

        c9, c10, c11 = st.columns(3)
        f_po = c9.selectbox("專案負責人", PROJECT_OWNERS, key="entry_po")
        f_owner = c10.selectbox("貼文負責人", POST_OWNERS, key="entry_owner")
        f_designer = c11.selectbox("美編", DESIGNERS, key="entry_designer")

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
                target_new_id = None
                if is_edit:
                    p = selected_platforms[0]
                    base = {'date': date_str, 'topic': f_topic, 'postType': f_type, 'postSubType': f_subtype if f_subtype != "-- 無 --" else "", 'postPurpose': platform_purposes[p], 'postFormat': f_format, 'projectOwner': f_po, 'postOwner': f_owner, 'designer': f_designer, 'status': 'published', 'metrics7d': metrics_input['metrics7d'], 'metrics1m': metrics_input['metrics1m']}
                    for i, d in enumerate(st.session_state.posts):
                        if d['id'] == target_edit_id: st.session_state.posts[i] = {**d, **base, 'platform': p}; break
                    st.session_state.editing_post = None
                    st.session_state.target_scroll_id = target_edit_id
                    st.success("已更新！")
                else:
                    for p in selected_platforms:
                        new_id = str(uuid.uuid4())
                        target_new_id = new_id
                        new_p = {'id': new_id, 'date': date_str, 'platform': p, 'topic': f_topic, 'postType': f_type, 'postSubType': f_subtype if f_subtype != "-- 無 --" else "", 'postPurpose': platform_purposes[p], 'postFormat': f_format, 'projectOwner': f_po, 'postOwner': f_owner, 'designer': f_designer, 'status': 'published', 'metrics7d': metrics_input['metrics7d'], 'metrics1m': metrics_input['metrics1m']}
                        if is_metrics_disabled(p, f_format): new_p['metrics7d'] = {}; new_p['metrics1m'] = {}
                        st.session_state.posts.append(new_p)
                    st.session_state.target_scroll_id = target_new_id
                    st.success("已新增！")
                
                save_data(st.session_state.posts)
                st.session_state.view_mode_radio = "📋 列表模式"
                st.session_state.scroll_to_list_item = True
                
                for key in st.session_state.keys():
                    if key.startswith("entry_") or key.startswith("purpose_for_"): del st.session_state[key]
                st.rerun()

        if st.session_state.editing_post:
            if st.button("取消編輯"):
                st.session_state.editing_post = None
                for key in st.session_state.keys():
                    if key.startswith("entry_"): del st.session_state[key]
                st.rerun()

    # --- Filter Logic ---
    filtered_posts = st.session_state.posts
    if date_filter_type == "月":
        filtered_posts = [p for p in filtered_posts if p.get('date', '').startswith(selected_month)]
    else:
        filtered_posts = [p for p in filtered_posts if start_date <= datetime.strptime(p.get('date', str(datetime.now().date())), "%Y-%m-%d").date() <= end_date]
    
    if filter_platform: filtered_posts = [p for p in filtered_posts if p['platform'] in filter_platform]
    if filter_owner: filtered_posts = [p for p in filtered_posts if p['postOwner'] in filter_owner]
    if filter_topic_keyword: filtered_posts = [p for p in filtered_posts if filter_topic_keyword.lower() in p['topic'].lower()]
    if filter_post_type: filtered_posts = [p for p in filtered_posts if p['postType'] in filter_post_type]
    if filter_purpose: filtered_posts = [p for p in filtered_posts if p['postPurpose'] in filter_purpose]
    if filter_format: filtered_posts = [p for p in filtered_posts if p['postFormat'] in filter_format]

    # --- View Mode ---
    view_mode = st.radio("檢視模式", ["📋 列表模式", "🗓️ 日曆模式"], horizontal=True, label_visibility="collapsed", key="view_mode_radio")
    st.write("")

    # --- Calendar View ---
    if view_mode == "🗓️ 日曆模式":
        if date_filter_type == "月":
            try:
                year_str, month_str = selected_month.split("-")
                cal_year, cal_month = int(year_str), int(month_str)
            except:
                now = datetime.now()
                cal_year, cal_month = now.year, now.month
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
                    if day == 0: st.markdown("<div class='cal-day-cell' style='background-color:#f9fafb;'></div>", unsafe_allow_htm

保留所有功能，刪除多餘的程式
