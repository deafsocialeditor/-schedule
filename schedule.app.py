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

# --- 4. 自訂 CSS (更新：白色背景) ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
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

# --- 5. 側邊欄篩選 ---
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
        sort_by = st.selectbox("排序依據", ["日期", "平台", "主題", "貼文類型", "狀態"], index=0)
    with col_sort2:
        sort_order = st.selectbox("順序", ["降序 (新->舊)", "升序 (舊->新)"], index=0)

    key_map = { "日期": "date", "平台": "platform", "主題": "topic", "貼文類型": "postType", "狀態": "status" }
    reverse_sort = True if "降序" in sort_order else False
    filtered_posts.sort(key=lambda x: x[key_map[sort_by]], reverse=reverse_sort)

    with col_count:
        st.write("")
        st.markdown(f"**共篩選出 {len(filtered_posts)} 筆資料**")

    st.divider()

    if filtered_posts:
        # 表頭 (更新：名詞調整)
        col_list = st.columns([0.8, 0.7, 1.8, 0.7, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.4, 0.4])
        headers = ["日期", "平台", "主題", "類型", "目的", "形式", "狀態", "KPI", "7日互動率", "30日互動率", "負責人", "編", "刪"]
        
        for col, h in zip(col_list, headers):
            col.markdown(f"**{h}**")
        st.markdown("<hr style='margin: 0.5em 0; border-top: 1px dashed #ddd;'>", unsafe_allow_html=True)

        status_map = {'draft': '🌱 草稿', 'planned': '⏰ 已排程', 'published': '🚀 已發布'}
        today = datetime.now().date()

        for p in filtered_posts:
            # 準備數據
            raw_p = p
            label, color = get_performance_label(raw_p['platform'], raw_p.get('metrics7d'), raw_p['postFormat'], st.session_state.standards)
            
            # 計算 7 天與 30 天的互動率
            def calc_rate_and_check_due(metrics, days_offset):
                eng = safe_num(metrics.get('likes', 0)) + safe_num(metrics.get('comments', 0)) + safe_num(metrics.get('shares', 0))
                reach = safe_num(metrics.get('reach', 0))
                
                # 計算互動率
                rate_str = "-"
                if reach > 0 and not is_metrics_disabled(p['platform'], p['postFormat']):
                    rate_str = f"{(eng/reach*100):.1f}%"
                
                # 檢查是否逾期未填
                post_date = datetime.strptime(p['date'], "%Y-%m-%d").date()
                due_date = post_date + timedelta(days=days_offset)
                is_due = False
                
                if p['status'] == 'published' and not is_metrics_disabled(p['platform'], p['postFormat']):
                    if today > due_date and reach == 0:
                        is_due = True
                
                return rate_str, is_due, int(reach), int(eng)

            rate7, overdue7, r7, e7 = calc_rate_and_check_due(p.get('metrics7d', {}), 7)
            rate30, overdue30, r30, e30 = calc_rate_and_check_due(p.get('metrics1m', {}), 30)

            # 顯示 Row
            cols = st.columns([0.8, 0.7, 1.8, 0.7, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.4, 0.4])
            
            cols[0].write(p['date'])
            cols[1].write(f"{ICONS.get(p['platform'], '')} {p['platform']}")
            cols[2].write(p['topic'])
            cols[3].write(f"{p['postType']}")
            cols[4].write(p['postPurpose']) 
            cols[5].write(p['postFormat']) 
            cols[6].write(status_map.get(p['status'], p['status']))
            cols[7].markdown(f"<span class='kpi-badge {color}'>{label.split(' ')[-1] if ' ' in label else label}</span>", unsafe_allow_html=True)
            
            # 7日互動率 (含逾期提示)
            if overdue7:
                cols[8].markdown(f"<span class='overdue-alert'>🔔 缺</span>", unsafe_allow_html=True)
            else:
                cols[8].write(rate7)

            # 30日互動率 (含逾期提示)
            if overdue30:
                cols[9].markdown(f"<span class='overdue-alert'>🔔 缺</span>", unsafe_allow_html=True)
            else:
                cols[9].write(rate30)
                
            cols[10].write(f"{p['postOwner']}")

            if cols[11].button("✏️", key=f"edit_{p['id']}"):
                st.session_state.editing_post = p
                st.rerun()
            if cols[12].button("🗑️", key=f"del_{p['id']}"):
                st.session_state.posts = [item for item in st.session_state.posts if item['id'] != p['id']]
                save_data(st.session_state.posts)
                st.rerun()

            # 摺疊詳細數據
            with st.expander(f"📉 {p['topic']} - 詳細數據 (點擊展開)"):
                d_c1, d_c2, d_c3, d_c4 = st.columns(4)
                d_c1.metric("7天-觸及", f"{r7:,}")
                d_c2.metric("7天-互動", f"{e7:,}")
                d_c3.metric("30天-觸及", f"{r30:,}")
                d_c4.metric("30天-互動", f"{e30:,}")

            st.markdown("<hr style='margin: 0; border-top: 1px solid #f0f0f0;'>", unsafe_allow_html=True)

        # 匯出邏輯 (修復: 確保 DataFrame 欄位正確)
        if display_data:
            df = pd.DataFrame(display_data)
            if not df.empty:
                # 修改匯出欄位名稱以符合新的 UI
                export_df = df.drop(columns=['_raw', 'ID'], errors='ignore')
                export_df.rename(columns={'7天率': '7日互動率', '30天率': '30日互動率'}, inplace=True)
                csv = export_df.to_csv(index=False).encode('utf-8-sig')
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
        if st.button("儲存設定"):
            st.session_state.standards = std
            save_standards(std)
            st.success("KPI 設定已更新！")

    # --- 數據概覽 ---
    published_posts = [p for p in filtered_posts if p['status'] == 'published']
    period = st.radio("分析基準", ["metrics7d", "metrics1m"], format_func=lambda x: "🔥 7天成效" if x == "metrics7d" else "🌳 一個月成效", horizontal=True)
    
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
        return count, reach, engage

    ad_posts_all = [p for p in published_posts if p['postPurpose'] in AD_PURPOSE_LIST]
    non_ad_posts_all = [p for p in published_posts if p['postPurpose'] not in AD_PURPOSE_LIST]

    t_c, t_r, t_e = calc_stats_subset(published_posts, period)
    a_c, a_r, a_e = calc_stats_subset(ad_posts_all, period)
    n_c, n_r, n_e = calc_stats_subset(non_ad_posts_all, period)

    st.markdown("### 📊 總體成效概覽")
    
    ov1, ov2, ov3 = st.columns(3)
    
    with ov1:
        st.markdown("""<div style="background:#f8fafc; padding:15px; border-radius:10px; border:1px solid #e2e8f0;">
        <h3 style="margin:0; color:#334155;">🔵 總體成效</h3>
        </div>""", unsafe_allow_html=True)
        st.metric("總篇數", t_c)
        st.metric("總觸及", f"{int(t_r):,}")
        st.metric("總互動", f"{int(t_e):,}")

    with ov2:
        st.markdown("""<div style="background:#fffbeb; padding:15px; border-radius:10px; border:1px solid #fef3c7;">
        <h3 style="margin:0; color:#b45309;">💰 廣告成效</h3>
        <span style="font-size:0.8em; color:#92400e;">(廣告/門市廣告)</span>
        </div>""", unsafe_allow_html=True)
        st.metric("廣告篇數", a_c)
        st.metric("廣告觸及", f"{int(a_r):,}")
        st.metric("廣告互動", f"{int(a_e):,}")

    with ov3:
        st.markdown("""<div style="background:#f0fdf4; padding:15px; border-radius:10px; border:1px solid #dcfce7;">
        <h3 style="margin:0; color:#15803d;">💬 非廣告成效</h3>
        <span style="font-size:0.8em; color:#166534;">(互動/導購/公告等)</span>
        </div>""", unsafe_allow_html=True)
        st.metric("非廣篇數", n_c)
        st.metric("非廣觸及", f"{int(n_r):,}")
        st.metric("非廣互動", f"{int(n_e):,}")

    st.markdown("---")

    # --- 平台詳細分析 ---
    st.markdown("### 📈 各平台成效詳細分析")

    def calc_platform_stats(posts_subset, p_period):
        count = len(posts_subset)
        reach = 0
        engage = 0
        for p in posts_subset:
            if is_metrics_disabled(p['platform'], p['postFormat']): continue
            m = p.get(p_period, {})
            reach += safe_num(m.get('reach', 0))
            engage += (safe_num(m.get('likes', 0)) + safe_num(m.get('comments', 0)) + safe_num(m.get('shares', 0)))
        rate = (engage / reach * 100) if reach > 0 else 0
        return count, reach, engage, rate

    for pf in PLATFORMS:
        if filter_platform != "All" and filter_platform != pf:
            continue
            
        posts_pf = [p for p in published_posts if p['platform'] == pf]
        if not posts_pf: continue 
            
        st.subheader(f"{ICONS.get(pf, '')} {pf}")
        
        ad_posts = [p for p in posts_pf if p['postPurpose'] in AD_PURPOSE_LIST]
        non_ad_posts = [p for p in posts_pf if p['postPurpose'] not in AD_PURPOSE_LIST]
        short_posts = [p for p in posts_pf if p['postFormat'] == '短影音']
        regular_posts = [p for p in posts_pf if p['postFormat'] != '短影音']
        
        stats_map = [
            ("🔵 總成效", posts_pf),
            ("💰 廣告成效", ad_posts),
            ("💬 非廣告成效", non_ad_posts),
            ("🎬 短影音", short_posts),
            ("🖼️ 一般貼文", regular_posts)
        ]
        
        table_data = []
        for label, subset in stats_map:
            c, r, e, rt = calc_platform_stats(subset, period)
            table_data.append({
                "類別": label,
                "篇數": c,
                "總觸及": int(r),
                "總互動": int(e),
                "互動率": f"{rt:.2f}%"
            })
        
        st.dataframe(
            pd.DataFrame(table_data),
            column_config={
                "總觸及": st.column_config.NumberColumn(format="%d"),
                "總互動": st.column_config.NumberColumn(format="%d"),
            },
            use_container_width=True,
            hide_index=True
        )
        st.divider()

    # --- 類型分佈圖 ---
    st.markdown("### 🍰 貼文類型分佈")
    type_dist = {}
    for p in published_posts:
        t = p['postType']
        type_dist[t] = type_dist.get(t, 0) + 1
    
    if type_dist:
        dist_df = pd.DataFrame(list(type_dist.items()), columns=['類型', '數量']).set_index('類型')
        st.bar_chart(dist_df)
    else:
        st.caption("無數據")
