import streamlit as st
import pandas as pd
import gspread, uuid, calendar, math, os, json
from datetime import datetime, timedelta
from oauth2client.service_account import ServiceAccountCredentials
import streamlit.components.v1 as components

# --- 1. 配置與核心設定 ---
st.set_page_config(page_title="2025社群排程", page_icon="📅", layout="wide")

SHEET_URL = "https://docs.google.com/spreadsheets/d/1Nvqid5fHkcrkOJE322Xqv_R_7kU4krc9q8us3iswRGc/edit#gid=0"
SCOPE = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
STANDARDS_FILE = "social_standards.json"

COL_MAP = {
    'id': 'ID', 'date': '日期', 'platform': '平台', 'topic': '主題', 'postType': '類型',
    'postSubType': '子類型', 'postPurpose': '目的', 'postFormat': '形式',
    'projectOwner': '專案負責人', 'postOwner': '貼文負責人', 'designer': '美編', 'status': '狀態',
    'metrics7d_reach': '7天觸及', 'metrics7d_likes': '7天互動', 'metrics7d_comments': '7天留言', 'metrics7d_shares': '7天分享',
    'metrics1m_reach': '30天觸及', 'metrics1m_likes': '30天互動', 'metrics1m_comments': '30天留言', 'metrics1m_shares': '30天分享'
}

# 選項定義
PLATFORMS = ['Facebook', 'Instagram', 'LINE@', 'YouTube', 'Threads', '社團']
MAIN_POST_TYPES = ['喜餅', '彌月', '伴手禮', '社群互動', '圓夢計畫', '公告']
SOUVENIR_SUB_TYPES = ['端午節', '中秋', '聖誕', '新春', '蒙友週']
POST_PURPOSES = ['互動', '廣告', '門市廣告', '導購', '公告']
POST_FORMATS = ['單圖', '多圖', '假多圖', '短影音', '限動', '純文字', '留言處']
PROJECT_OWNERS = ['夢涵', 'MOMO', '櫻樺', '季嫻', '凌萱', '宜婷', '門市']
POST_OWNERS = ['一千', '楷曜', '可榆']
DESIGNERS = ['千惟', '靖嬙']
PLATFORM_COLORS = {'Facebook': '#1877F2', 'Instagram': '#E1306C', 'LINE@': '#06C755', 'YouTube': '#FF0000', 'Threads': '#101010', '社團': '#F97316'}
PLATFORM_MARKS = {'Facebook': '🟦', 'Instagram': '🟪', 'LINE@': '🟩', 'YouTube': '🟥', 'Threads': '⬛', '社團': '🟧'}

# --- 2. 資料存取邏輯 ---
def get_client():
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["service_account"]), SCOPE)
        return gspread.authorize(creds)
    except: return None

def load_data():
    client = get_client()
    if not client: return []
    try:
        sheet = client.open_by_url(SHEET_URL).sheet1
        rows = sheet.get_all_records()
        data = []
        for r in rows:
            p = {k: r.get(v, "") for k, v in COL_MAP.items() if "_" not in k}
            p['metrics7d'] = {k.split('_')[1]: r.get(v, 0) for k, v in COL_MAP.items() if "metrics7d_" in k}
            p['metrics1m'] = {k.split('_')[1]: r.get(v, 0) for k, v in COL_MAP.items() if "metrics1m_" in k}
            if not p.get('id'): p['id'] = str(uuid.uuid4())
            data.append(p)
        return data
    except: return []

def save_data(data):
    client = get_client()
    if not client: return
    try:
        sheet = client.open_by_url(SHEET_URL).sheet1
        flat = []
        for p in data:
            row = {COL_MAP[k]: p.get(k) for k in COL_MAP if "_" not in k}
            for m in ['metrics7d', 'metrics1m']:
                for k, v in p.get(m, {}).items():
                    row[COL_MAP[f"{m}_{k}"]] = v
            flat.append(row)
        df = pd.DataFrame(flat).reindex(columns=list(COL_MAP.values())).fillna("")
        sheet.clear()
        sheet.update([df.columns.values.tolist()] + df.values.tolist())
    except Exception as e: st.error(f"儲存失敗: {e}")

# --- 3. 核心邏輯 (KPI 與 狀態) ---
def get_performance(p, standards):
    platform, fmt = p['platform'], p['postFormat']
    if platform == 'LINE@' or fmt in ['限動', '留言處']: return "🚫 不計", "gray", ""
    
    m = p['metrics7d']
    reach = float(str(m.get('reach', 0)).replace(',',''))
    if reach == 0: return "-", "gray", "未填數據"
    
    eng = sum([float(str(m.get(k, 0)).replace(',','')) for k in ['likes', 'comments', 'shares']])
    rate = (eng / reach * 100) if reach > 0 else 0
    
    # 簡化判定邏輯示例
    std = standards.get(platform, {})
    if platform == 'Facebook':
        if reach >= 2000 and eng >= 100: return "🏆 高標", "purple", "達標"
        if reach >= 1500 or eng >= 45: return "✅ 標準", "green", "達標"
        return "🔴 未達標", "red", ""
    return "✅ 檢視中", "green", ""

# --- 4. 介面樣式 ---
st.markdown(f"""
<style>
    .stApp {{ background: #f8fafc; }}
    .kpi-badge {{ padding: 2px 8px; border-radius: 6px; font-weight: 600; font-size: 12px; }}
    .purple {{ background: #f3e8ff; color: #7e22ce; }} .green {{ background: #dcfce7; color: #15803d; }}
    .red {{ background: #fee2e2; color: #b91c1c; }} .gray {{ background: #f3f4f6; color: #6b7280; }}
    .cal-cell {{ border: 1px solid #e2e8f0; border-radius: 4px; padding: 4px; min-height: 80px; background: white; }}
    { "".join([f'button[aria-label^="{m}"] {{ background: {c} !important; color: white !important; font-size: 11px !important; margin-bottom: 2px !important; }}' for m, c in PLATFORM_MARKS.items()]) }
</style>
""", unsafe_allow_html=True)

# --- 5. 初始化與側邊欄 ---
if 'posts' not in st.session_state: st.session_state.posts = load_data()
if 'editing_id' not in st.session_state: st.session_state.editing_id = None

with st.sidebar:
    st.title("⚙️ 控制面板")
    if st.button("🔄 同步雲端", use_container_width=True):
        st.session_state.posts = load_data(); st.rerun()
    
    st.divider()
    f_plt = st.multiselect("平台篩選", PLATFORMS)
    f_own = st.multiselect("負責人", POST_OWNERS)
    f_month = st.selectbox("月份", sorted(list(set([p['date'][:7] for p in st.session_state.posts])), reverse=True) if st.session_state.posts else [datetime.now().strftime("%Y-%m")])

# --- 6. 主頁面內容 ---
st.header("📅 社群排程與成效系統")
t1, t2 = st.tabs(["🗓️ 管理排程", "📊 數據看板"])

with t1:
    # 編輯器 (新增/編輯共用)
    with st.expander("📝 編輯貼文資訊", expanded=st.session_state.editing_id is not None):
        edit_p = next((p for p in st.session_state.posts if p['id'] == st.session_state.editing_id), None) if st.session_state.editing_id else {}
        
        c1, c2, c3 = st.columns(3)
        d_date = c1.date_input("日期", datetime.strptime(edit_p['date'], "%Y-%m-%d") if edit_p else datetime.now())
        d_plt = c2.multiselect("平台", PLATFORMS, default=edit_p.get('platform', 'Facebook').split(',') if edit_p else ['Facebook'])
        d_topic = c3.text_input("主題", edit_p.get('topic', ""))
        
        if st.button("💾 儲存資料", type="primary", use_container_width=True):
            new_posts = [p for p in st.session_state.posts if p['id'] != st.session_state.editing_id]
            for p_name in d_plt:
                new_posts.append({
                    'id': str(uuid.uuid4()) if not st.session_state.editing_id else st.session_state.editing_id,
                    'date': d_date.strftime("%Y-%m-%d"), 'platform': p_name, 'topic': d_topic,
                    'postType': edit_p.get('postType', MAIN_POST_TYPES[0]), 'postFormat': edit_p.get('postFormat', POST_FORMATS[0]),
                    'postOwner': edit_p.get('postOwner', POST_OWNERS[0]), 'status': 'published',
                    'metrics7d': edit_p.get('metrics7d', {'reach':0, 'likes':0, 'comments':0, 'shares':0}),
                    'metrics1m': edit_p.get('metrics1m', {'reach':0, 'likes':0, 'comments':0, 'shares':0})
                })
            st.session_state.posts = new_posts; save_data(new_posts)
            st.session_state.editing_id = None; st.rerun()

    # 顯示模式切換
    v_mode = st.radio("檢視", ["日曆", "列表"], horizontal=True)
    
    # 篩選資料
    display_posts = [p for p in st.session_state.posts if p['date'].startswith(f_month)]
    if f_plt: display_posts = [p for p in display_posts if p['platform'] in f_plt]
    if f_own: display_posts = [p for p in display_posts if p['postOwner'] in f_own]

    if v_mode == "日曆":
        y, m = map(int, f_month.split('-'))
        cal = calendar.monthcalendar(y, m)
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0: continue
                with cols[i]:
                    st.markdown(f"**{day}**")
                    curr_date = f"{f_month}-{day:02d}"
                    for p in [p for p in display_posts if p['date'] == curr_date]:
                        if st.button(f"{PLATFORM_MARKS.get(p['platform'],'')} {p['topic'][:6]}...", key=p['id']):
                            st.session_state.editing_id = p['id']; st.rerun()
    else:
        for p in sorted(display_posts, key=lambda x: x['date'], reverse=True):
            c1, c2, c3, c4 = st.columns([1, 4, 2, 1])
            label, color, _ = get_performance(p, {})
            c1.markdown(f"<span class='kpi-badge {color}'>{p['platform']}</span>", unsafe_allow_html=True)
            c2.markdown(f"**{p['topic']}**")
            c3.markdown(f"<span class='kpi-badge {color}'>{label}</span>", unsafe_allow_html=True)
            if c4.button("編輯", key=f"btn_{p['id']}"):
                st.session_state.editing_id = p['id']; st.rerun()

with t2:
    if display_posts:
        df_perf = pd.DataFrame([{
            '平台': p['platform'], 
            '觸及': float(str(p['metrics7d']['reach']).replace(',','')),
            '互動': sum([float(str(p['metrics7d'][k]).replace(',','')) for k in ['likes','comments','shares']])
        } for p in display_posts])
        st.subheader(f"📈 {f_month} 成效概覽")
        st.bar_chart(df_perf.groupby('平台').sum())
    else:
        st.info("尚無數據可供分析")

# 滾動腳本 (如有需要)
if st.session_state.editing_id:
    components.html("<script>window.parent.document.querySelector('.stExpander').scrollIntoView();</script>", height=0)
