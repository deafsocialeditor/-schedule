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
    </style>
""", unsafe_allow_html=True)

# --- 5. 側邊欄篩選 ---
with st.sidebar:
    st.title("🔎 篩選條件")
    
    filter_platform = st.selectbox("平台", ["All"] + PLATFORMS, index=0)
    
    date_filter_type = st.radio("日期模式", ["月", "自訂範圍"], horizontal=True)
    
    if date_filter_type == "月":
        # 產生月份選單
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
            # 如果是編輯模式，預填資料
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
            
            # 動態子類型
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

            # Metrics Input (只有在非 Draft 且非限動時才需要)
            st.divider()
            st.caption("數據填寫 (若狀態為已發布)")
            
            # Helper to get metrics safely
            def get_m(key, period):
                return post_data.get(period, {}).get(key, 0) if post_data else 0

            m_cols = st.columns(2)
            metrics_input = {'metrics7d': {}, 'metrics1m': {}}
            
            with m_cols[0]:
                st.markdown("##### 🔥 7天成效")
                metrics_input['metrics7d']['reach'] = st.number_input("7天-觸及", value=get_m('reach', 'metrics7d'), step=1)
                metrics_input['metrics7d']['likes'] = st.number_input("7天-按讚", value=get_m('likes', 'metrics7d'), step=1)
                c_sub1, c_sub2 = st.columns(2)
                metrics_input['metrics7d']['comments'] = c_sub1.number_input("7天-留言", value=get_m('comments', 'metrics7d'), step=1)
                metrics_input['metrics7d']['shares'] = c_sub2.number_input("7天-分享", value=get_m('shares', 'metrics7d'), step=1)

            with m_cols[1]:
                st.markdown("##### 🌳 一個月成效")
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
                        # 更新現有
                        for i, p in enumerate(st.session_state.posts):
                            if p['id'] == post_data['id']:
                                st.session_state.posts[i] = {**p, **new_base, 'platform': selected_platforms[0]}
                                break
                        st.session_state.editing_post = None
                        st.success("已更新！")
                    else:
                        # 新增 (支援複選平台)
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

    # --- 列表顯示 ---
    
    # 篩選邏輯
    filtered_posts = st.session_state.posts
    if date_filter_type == "月":
        filtered_posts = [p for p in filtered_posts if p['date'].startswith(selected_month)]
    else:
        filtered_posts = [p for p in filtered_posts if start_date <= datetime.strptime(p['date'], "%Y-%m-%d").date() <= end_date]
    
    if filter_platform != "All":
        filtered_posts = [p for p in filtered_posts if p['platform'] == filter_platform]

    # 排序
    filtered_posts.sort(key=lambda x: x['date'], reverse=True)

    st.markdown(f"### 📋 排程列表 ({len(filtered_posts)})")

    # 轉換成 DataFrame 方便顯示
    if filtered_posts:
        display_data = []
        for p in filtered_posts:
            # 計算 KPI
            perf_label, perf_color = get_performance_label(p['platform'], p.get('metrics7d', {}), p['postFormat'], st.session_state.standards)
            
            # 計算互動率顯示
            m7 = p.get('metrics7d', {})
            eng7 = safe_num(m7.get('likes', 0)) + safe_num(m7.get('comments', 0)) + safe_num(m7.get('shares', 0))
            reach7 = safe_num(m7.get('reach', 0))
            rate7 = f"{(eng7/reach7*100):.1f}%" if reach7 > 0 and not is_metrics_disabled(p['platform'], p['postFormat']) else "-"

            display_data.append({
                'ID': p['id'],
                '日期': p['date'],
                '平台': f"{ICONS.get(p['platform'], '')} {p['platform']}",
                '主題': p['topic'],
                '類型': f"{p['postType']}-{p['postSubType']}" if p['postSubType'] else p['postType'],
                '形式': p['postFormat'],
                '負責人': f"{p['postOwner']} (D:{p['designer']})",
                '狀態': {'draft': '🌱', 'planned': '⏰', 'published': '🚀'}[p['status']],
                'KPI': perf_label,
                '7天觸及': int(reach7),
                '7天互動': int(eng7),
                '7天率': rate7,
                '_raw': p  # 保留原始數據用於操作
            })
        
        df = pd.DataFrame(display_data)
        
        # 操作按鈕欄位
        col_list = st.columns([0.8, 0.8, 2, 1, 1, 1, 1, 0.8, 0.8, 0.5, 0.5])
        headers = ["日期", "平台", "主題", "類型", "負責人", "狀態", "KPI", "觸及(7d)", "互動(7d)", "編輯", "刪除"]
        
        # 表頭
        for col, h in zip(col_list, headers):
            col.markdown(f"**{h}**")
            
        st.divider()

        for index, row in df.iterrows():
            cols = st.columns([0.8, 0.8, 2, 1, 1, 1, 1, 0.8, 0.8, 0.5, 0.5])
            
            cols[0].write(row['日期'])
            cols[1].write(row['平台'])
            cols[2].write(row['主題'])
            cols[3].write(row['類型'])
            cols[4].write(row['負責人'])
            cols[5].write(row['狀態'])
            
            # KPI Badge (Markdown HTML)
            raw_p = row['_raw']
            label, color = get_performance_label(raw_p['platform'], raw_p.get('metrics7d'), raw_p['postFormat'], st.session_state.standards)
            cols[6].markdown(f"<span class='kpi-badge {color}'>{label.split(' ')[-1] if ' ' in label else label}</span>", unsafe_allow_html=True)
            
            cols[7].write(f"{row['7天觸及']:,}")
            cols[8].write(f"{row['7天互動']:,}")
            
            # 操作
            if cols[9].button("✏️", key=f"edit_{row['ID']}"):
                st.session_state.editing_post = row['_raw']
                st.rerun()
            
            if cols[10].button("🗑️", key=f"del_{row['ID']}"):
                st.session_state.posts = [p for p in st.session_state.posts if p['id'] != row['ID']]
                save_data(st.session_state.posts)
                st.rerun()
            
            st.divider()

        # CSV 匯出
        csv = df.drop(columns=['_raw', 'ID']).to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 匯出 CSV",
            data=csv,
            file_name=f"social_posts_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("目前沒有符合條件的排程資料。")

# === TAB 2: 數據分析 ===
with tab2:
    
    # --- KPI 設定 (Expander) ---
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
    # 使用與 Tab 1 相同的 filtered_posts (根據日期與平台)
    published_posts = [p for p in filtered_posts if p['status'] == 'published']
    
    st.markdown("### 📊 總體成效概覽")
    
    # 選擇分析週期
    period = st.radio("分析基準", ["metrics7d", "metrics1m"], format_func=lambda x: "🔥 7天成效" if x == "metrics7d" else "🌳 一個月成效", horizontal=True)
    
    # 計算總數
    total_reach = 0
    total_engagement = 0
    
    for p in published_posts:
        if is_metrics_disabled(p['platform'], p['postFormat']):
            continue
        m = p.get(period, {})
        # Threads/Line@ 不計入總觸及加總 (邏輯與 React 版一致)
        if p['platform'] not in ['Threads', 'LINE@']:
            total_reach += safe_num(m.get('reach', 0))
        
        if p['platform'] != 'LINE@':
            total_engagement += (safe_num(m.get('likes', 0)) + safe_num(m.get('comments', 0)) + safe_num(m.get('shares', 0)))

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("已發布篇數", len(published_posts))
    kpi2.metric("總觸及 (不含Threads/Line)", f"{int(total_reach):,}")
    kpi3.metric("總互動", f"{int(total_engagement):,}")

    st.markdown("---")

    # --- 平台詳細分析 (Table) ---
    st.markdown("### 📈 各平台成效明細")
    
    platform_stats = []
    
    for pf in PLATFORMS:
        if filter_platform != "All" and filter_platform != pf:
            continue
            
        posts_in_pf = [p for p in published_posts if p['platform'] == pf]
        
        count = len(posts_in_pf)
        sum_reach = 0
        sum_engage = 0
        
        for p in posts_in_pf:
            if is_metrics_disabled(p['platform'], p['postFormat']): continue
            m = p.get(period, {})
            sum_reach += safe_num(m.get('reach', 0))
            sum_engage += (safe_num(m.get('likes', 0)) + safe_num(m.get('comments', 0)) + safe_num(m.get('shares', 0)))
        
        avg_rate = (sum_engage / sum_reach * 100) if sum_reach > 0 else 0
        
        # 短影音分析
        short_posts = [p for p in posts_in_pf if p['postFormat'] == '短影音']
        s_count = len(short_posts)
        s_reach = 0
        s_engage = 0
        for p in short_posts:
            m = p.get(period, {})
            s_reach += safe_num(m.get('reach', 0))
            s_engage += (safe_num(m.get('likes', 0)) + safe_num(m.get('comments', 0)) + safe_num(m.get('shares', 0)))
        s_rate = (s_engage / s_reach * 100) if s_reach > 0 else 0

        platform_stats.append({
            '平台': pf,
            '篇數': count,
            '總觸及': int(sum_reach),
            '總互動': int(sum_engage),
            '互動率': f"{avg_rate:.2f}%",
            '短影音佔比': f"{s_count}篇 ({s_rate:.2f}%)" if s_count > 0 else "-"
        })

    st.dataframe(
        pd.DataFrame(platform_stats),
        column_config={
            "總觸及": st.column_config.NumberColumn(format="%d"),
            "總互動": st.column_config.NumberColumn(format="%d"),
        },
        use_container_width=True,
        hide_index=True
    )

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
