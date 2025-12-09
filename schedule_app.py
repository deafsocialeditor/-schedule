import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# --- 設定頁面資訊 ---
st.set_page_config(
    page_title="社群排程小幫手",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 常數設定 ---
FILE_PATH = "social_posts_data.csv"

PLATFORMS = ['Facebook', 'Instagram', 'LINE@', 'YouTube', 'Threads']
POST_TYPES = ['喜餅', '彌月', '伴手禮', '社群互動', '圓夢計畫', '公告']
SUB_TYPES = ['無', '端午節', '中秋', '聖誕', '新春', '蒙友週']
PURPOSES = ['互動', '廣告', '門市廣告', '導購', '公告']
FORMATS = ['單圖', '多圖', '假多圖', '短影音', '限動', '純文字', '留言處']
OWNERS_PROJECT = ['無', '夢涵', 'MOMO', '櫻樺', '季嫻', '凌萱', '宜婷']
OWNERS_POST = ['一千', '凱曜', '可榆']
OWNERS_DESIGN = ['無', '千惟', '靖嬙']
STATUS_OPTIONS = ['草稿', '已排程', '已發布']

# KPI 標準設定
KPI_STANDARDS = {
    'Facebook': {'high': {'reach': 2000, 'rate': 5.0}, 'std': {'reach': 1500, 'rate': 3.0}, 'low': {'reach': 1000, 'rate': 1.5}},
    'Instagram': {'reach': 900, 'engagement': 30, 'rate': 3.5},
    'Threads': {'reach': 84000, 'engagement': 1585, 'rate': 0}, # 標竿
    'YouTube': {'reach': 500, 'rate': 2.0},
    'LINE@': {'reach': 0, 'rate': 0}
}

# --- 資料處理函數 ---

def load_data():
    """讀取 CSV 資料，若無則建立預設資料"""
    if os.path.exists(FILE_PATH):
        try:
            df = pd.read_csv(FILE_PATH)
            # 確保欄位型別正確，避免錯誤
            num_cols = ['reach_7d', 'likes_7d', 'comments_7d', 'shares_7d', 
                        'reach_1m', 'likes_1m', 'comments_1m', 'shares_1m']
            for col in num_cols:
                if col not in df.columns:
                    df[col] = 0
                df[col] = df[col].fillna(0).astype(int)
            
            # [重要修復] 將日期字串轉換為 date 物件，避免 data_editor 報錯
            df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
            # 填補無效日期為今天
            df['date'] = df['date'].fillna(datetime.now().date())
            
            return df
        except Exception as e:
            st.error(f"讀取資料失敗，將建立新檔案: {e}")
            return create_default_data()
    else:
        return create_default_data()

def create_default_data():
    # 預設範例資料
    return pd.DataFrame([{
        'id': int(datetime.now().timestamp()),
        'date': datetime.now().date(),
        'platform': 'Facebook',
        'topic': '範例：新春活動預告',
        'type': '喜餅', 'sub_type': '新春',
        'purpose': '廣告', 'format': '單圖',
        'owner_project': '夢涵', 'owner_post': '一千', 'owner_design': '千惟',
        'status': '草稿',
        'reach_7d': 0, 'likes_7d': 0, 'comments_7d': 0, 'shares_7d': 0,
        'reach_1m': 0, 'likes_1m': 0, 'comments_1m': 0, 'shares_1m': 0
    }])

def save_data(df):
    """儲存資料到 CSV"""
    df.to_csv(FILE_PATH, index=False)

def calculate_kpi(row, period='7d'):
    """計算 KPI 標籤"""
    platform = row['platform']
    fmt = row['format']
    
    # 排除不需要計算的情況
    if platform == 'LINE@' or fmt in ['限動', '留言處']:
        return "-"
    
    # 取得數據
    reach = row[f'reach_{period}']
    likes = row[f'likes_{period}']
    comments = row[f'comments_{period}']
    shares = row[f'shares_{period}']
    
    if reach == 0:
        return "-"
        
    engagement = likes + comments + shares
    rate = (engagement / reach) * 100
    
    std = KPI_STANDARDS.get(platform, {})
    
    if platform == 'Facebook':
        if reach >= std['high']['reach'] and rate >= std['high']['rate']: return "🏆 高標"
        if reach >= std['std']['reach'] and rate >= std['std']['rate']: return "✅ 標準"
        if reach >= std['low']['reach'] and rate >= std['low']['rate']: return "🤏 低標"
        return "🔴 未達標"
        
    elif platform == 'Instagram':
        if reach >= std['reach'] and engagement >= std['engagement'] and rate >= std['rate']:
            return "✅ 達標"
        return "🔴 未達標"
        
    elif platform == 'Threads':
        if reach >= std['reach']: return "🔥 超標竿"
        return "-"
        
    elif platform == 'YouTube':
        if reach >= std['reach'] and rate >= std['rate']: return "✅ 達標"
        return "🔴 未達標"
        
    return "-"

def get_due_status(row):
    """計算是否逾期未填"""
    if row['status'] != '已發布' or row['platform'] == 'LINE@' or row['format'] in ['限動', '留言處']:
        return None
    
    # row['date'] 已經是 date 物件
    pub_date = row['date']
    if not isinstance(pub_date, (datetime, type(datetime.now().date()))):
         # 防呆：如果日期格式錯誤
         return None

    today = datetime.now().date()
    
    due_7d = pub_date + timedelta(days=7)
    due_1m = pub_date + timedelta(days=30)
    
    # 檢查 7 天成效
    if today >= due_7d and row['reach_7d'] == 0:
        return f"🔔 7天({due_7d.strftime('%m/%d')})"
    
    # 檢查 1 個月成效 (如果7天已填，檢查1個月)
    if today >= due_1m and row['reach_1m'] == 0:
        return f"🔔 月({due_1m.strftime('%m/%d')})"
        
    return None

# --- 主程式 ---

def main():
    # 讀取資料
    if 'df' not in st.session_state:
        st.session_state.df = load_data()
    
    df = st.session_state.df

    # --- 側邊欄：篩選與設定 ---
    with st.sidebar:
        st.header("🔍 篩選條件")
        
        # 轉換日期為字串以便篩選月份
        df['date_str'] = df['date'].apply(lambda x: x.strftime('%Y-%m'))
        all_months = sorted(list(set(df['date_str'])), reverse=True)
        if not all_months: all_months = [datetime.now().strftime('%Y-%m')]
        
        filter_mode = st.radio("時間篩選", ["依月份", "自訂區間"], horizontal=True)
        
        if filter_mode == "依月份":
            selected_month = st.selectbox("選擇月份", all_months)
            mask_date = df['date_str'] == selected_month
        else:
            d_start = st.date_input("開始日期", value=datetime.now().replace(day=1))
            d_end = st.date_input("結束日期", value=datetime.now())
            mask_date = (pd.to_datetime(df['date']).dt.date >= d_start) & \
                        (pd.to_datetime(df['date']).dt.date <= d_end)

        selected_platform = st.selectbox("平台", ["全部"] + PLATFORMS)
        mask_platform = (df['platform'] == selected_platform) if selected_platform != "全部" else [True] * len(df)
        
        # 篩選後的資料
        filtered_df = df[mask_date & mask_platform].copy()

    # --- 主頁面 ---
    st.title("📅 社群排程小幫手")
    
    tab1, tab2 = st.tabs(["📝 排程管理", "📊 成效分析"])

    # === Tab 1: 排程管理 ===
    with tab1:
        # --- 新增區域 ---
        with st.expander("✨ 新增排程 (點擊展開)", expanded=False):
            with st.form("add_form", clear_on_submit=True):
                c1, c2, c3 = st.columns([1, 1, 2])
                new_date = c1.date_input("日期", value=datetime.now())
                new_platforms = c2.multiselect("平台 (可複選)", PLATFORMS, default=['Facebook'])
                new_topic = c3.text_input("主題", placeholder="例如：母親節促銷 🎉")
                
                c4, c5, c6 = st.columns(3)
                new_type = c4.selectbox("類型", POST_TYPES)
                new_sub = c5.selectbox("子類型 (伴手禮用)", SUB_TYPES, disabled=(new_type != '伴手禮'))
                new_purpose = c6.selectbox("目的", PURPOSES)
                
                c7, c8, c9 = st.columns(3)
                new_format = c7.selectbox("形式", FORMATS)
                new_owner_p = c8.selectbox("專案負責", OWNERS_PROJECT)
                new_owner_e = c9.selectbox("貼文負責", OWNERS_POST)
                new_owner_d = st.selectbox("美編負責", OWNERS_DESIGN)
                
                new_status = st.selectbox("狀態", STATUS_OPTIONS)

                submitted = st.form_submit_button("💾 加入排程")
                
                if submitted and new_topic:
                    new_rows = []
                    for p in new_platforms:
                        new_row = {
                            'id': int(datetime.now().timestamp() * 1000) + len(new_rows), # Unique ID
                            'date': new_date, # 直接存 date object
                            'platform': p,
                            'topic': new_topic,
                            'type': new_type,
                            'sub_type': new_sub if new_type == '伴手禮' else '',
                            'purpose': new_purpose,
                            'format': new_format,
                            'owner_project': new_owner_p if new_owner_p != '無' else '',
                            'owner_post': new_owner_e,
                            'owner_design': new_owner_d if new_owner_d != '無' else '',
                            'status': new_status,
                            'reach_7d': 0, 'likes_7d': 0, 'comments_7d': 0, 'shares_7d': 0,
                            'reach_1m': 0, 'likes_1m': 0, 'comments_1m': 0, 'shares_1m': 0
                        }
                        new_rows.append(new_row)
                    
                    if new_rows:
                        new_df = pd.DataFrame(new_rows)
                        # 確保新資料的日期欄位型別一致
                        new_df['date'] = pd.to_datetime(new_df['date']).dt.date
                        st.session_state.df = pd.concat([st.session_state.df, new_df], ignore_index=True)
                        save_data(st.session_state.df)
                        st.success(f"已新增 {len(new_rows)} 筆排程！")
                        st.rerun()

        # --- 列表編輯區域 ---
        st.subheader("📋 排程列表")
        st.caption("💡 提示：直接點擊表格內容即可修改，修改後會自動儲存。勾選左側框框可刪除。")

        # 準備顯示用的 DataFrame
        display_df = filtered_df.sort_values(by='date', ascending=False).copy()
        
        # 計算提醒狀態
        display_df['提醒'] = display_df.apply(get_due_status, axis=1)
        
        # 計算互動率 (僅供顯示)
        def calc_rate_display(r, l, c, s, p, f):
            if p == 'LINE@' or f in ['限動', '留言處'] or r == 0: return "-"
            return f"{((l+c+s)/r)*100:.2f}%"
            
        display_df['7天互動率'] = display_df.apply(lambda x: calc_rate_display(x['reach_7d'], x['likes_7d'], x['comments_7d'], x['shares_7d'], x['platform'], x['format']), axis=1)
        display_df['月互動率'] = display_df.apply(lambda x: calc_rate_display(x['reach_1m'], x['likes_1m'], x['comments_1m'], x['shares_1m'], x['platform'], x['format']), axis=1)
        
        # 計算 KPI
        display_df['KPI等級'] = display_df.apply(lambda x: calculate_kpi(x, '7d'), axis=1)

        # 設定表格編輯器
        column_config = {
            "id": None, 
            "date_str": None, # 隱藏輔助欄位
            "date": st.column_config.DateColumn("日期", format="YYYY-MM-DD", width="small"),
            "platform": st.column_config.SelectboxColumn("平台", options=PLATFORMS, width="small"),
            "topic": st.column_config.TextColumn("主題", width="medium"),
            "type": st.column_config.SelectboxColumn("類型", options=POST_TYPES, width="small"),
            "sub_type": st.column_config.SelectboxColumn("子類", options=SUB_TYPES, width="small"),
            "purpose": st.column_config.SelectboxColumn("目的", options=PURPOSES, width="small"),
            "format": st.column_config.SelectboxColumn("形式", options=FORMATS, width="small"),
            "owner_project": st.column_config.SelectboxColumn("專案", options=OWNERS_PROJECT, width="small"),
            "owner_post": st.column_config.SelectboxColumn("貼文", options=OWNERS_POST, width="small"),
            "owner_design": st.column_config.SelectboxColumn("美編", options=OWNERS_DESIGN, width="small"),
            "status": st.column_config.SelectboxColumn("狀態", options=STATUS_OPTIONS, width="small"),
            "reach_7d": st.column_config.NumberColumn("7天觸及"),
            "likes_7d": st.column_config.NumberColumn("7天按讚"),
            "comments_7d": st.column_config.NumberColumn("7天留言"),
            "shares_7d": st.column_config.NumberColumn("7天分享"),
            "reach_1m": st.column_config.NumberColumn("月觸及"),
            "likes_1m": st.column_config.NumberColumn("月按讚"),
            "comments_1m": st.column_config.NumberColumn("月留言"),
            "shares_1m": st.column_config.NumberColumn("月分享"),
            "提醒": st.column_config.TextColumn("提醒", disabled=True),
            "7天互動率": st.column_config.TextColumn("7天互動率", disabled=True),
            "月互動率": st.column_config.TextColumn("月互動率", disabled=True),
            "KPI等級": st.column_config.TextColumn("KPI (7天)", disabled=True),
        }

        # 顯示可編輯表格 (使用 fixed row 避免新增錯誤)
        edited_data = st.data_editor(
            display_df,
            column_config=column_config,
            use_container_width=True,
            num_rows="fixed", 
            key="editor",
            hide_index=True,
            disabled=["提醒", "7天互動率", "月互動率", "KPI等級"]
        )

        # 處理資料更新與刪除
        if st.session_state.get("editor"):
            changes = st.session_state["editor"]
            
            # 1. 處理刪除
            if changes["deleted_rows"]:
                indices_to_delete = changes["deleted_rows"]
                ids_to_delete = display_df.iloc[indices_to_delete]['id'].tolist()
                st.session_state.df = st.session_state.df[~st.session_state.df['id'].isin(ids_to_delete)]
                save_data(st.session_state.df)
                st.rerun()

            # 2. 處理修改
            if changes["edited_rows"]:
                for idx, change in changes["edited_rows"].items():
                    real_id = display_df.iloc[idx]['id']
                    
                    for key, value in change.items():
                        # 特別處理：如果選了 LINE@ 或 限動/留言處，將數據歸零
                        if key in ['platform', 'format']:
                            row = st.session_state.df.loc[st.session_state.df['id'] == real_id].iloc[0]
                            new_p = value if key == 'platform' else row['platform']
                            new_f = value if key == 'format' else row['format']
                            
                            if new_p == 'LINE@' or new_f in ['限動', '留言處']:
                                for metric in ['reach_7d', 'likes_7d', 'comments_7d', 'shares_7d', 'reach_1m', 'likes_1m', 'comments_1m', 'shares_1m']:
                                    st.session_state.df.loc[st.session_state.df['id'] == real_id, metric] = 0
                        
                        st.session_state.df.loc[st.session_state.df['id'] == real_id, key] = value
                
                save_data(st.session_state.df)

    # === Tab 2: 成效分析 ===
    with tab2:
        st.header("📊 成效分析儀表板")
        
        # 分析篩選器
        col_f1, col_f2 = st.columns(2)
        period = col_f1.radio("分析週期", ["7天", "一個月"], horizontal=True)
        period_suffix = "_7d" if period == "7天" else "_1m"
        
        purpose_filter = col_f2.radio("目的類型", ["全部", "💰 廣告類", "💬 非廣告類"], horizontal=True)

        # 準備分析資料
        analytics_df = filtered_df[filtered_df['status'] == '已發布'].copy()
        
        if purpose_filter == "💰 廣告類":
            analytics_df = analytics_df[analytics_df['purpose'].isin(['廣告', '門市廣告'])]
        elif purpose_filter == "💬 非廣告類":
            analytics_df = analytics_df[~analytics_df['purpose'].isin(['廣告', '門市廣告'])]

        # 排除不計算的貼文 (限動、留言處)
        calculable_df = analytics_df[~analytics_df['format'].isin(['限動', '留言處'])].copy()
        
        # [重要修復] 總數據計算 (轉為 float/int 避免 numpy 類型問題)
        # 總觸及：排除 LINE@ & Threads
        total_reach = int(calculable_df[~calculable_df['platform'].isin(['LINE@', 'Threads'])][f'reach{period_suffix}'].sum())
        
        # 總互動：排除 LINE@
        total_engagement_df = calculable_df[calculable_df['platform'] != 'LINE@']
        total_engagement = int((total_engagement_df[f'likes{period_suffix}'] + 
                            total_engagement_df[f'comments{period_suffix}'] + 
                            total_engagement_df[f'shares{period_suffix}']).sum())
        
        # 顯示 KPI
        k1, k2, k3 = st.columns(3)
        k1.metric("已發布貼文數", len(analytics_df))
        k2.metric(f"總觸及 ({period})", f"{total_reach:,}", help="排除 Threads/LINE@/限動/留言處")
        k3.metric(f"總互動 ({period})", f"{total_engagement:,}", help="排除 LINE@/限動/留言處")
        
        st.divider()

        # 各平台詳細數據
        st.subheader(f"🔍 各平台表現 ({period})")
        
        platform_stats = []
        for p in platforms:
            if selected_platform != '全部' and p != selected_platform: continue
            
            p_df = analytics_df[analytics_df['platform'] == p]
            count = len(p_df)
            
            # 計算成效時排除限動/留言處
            p_calc_df = p_df[~p_df['format'].isin(['限動', '留言處'])]
            
            p_reach = int(p_calc_df[f'reach{period_suffix}'].sum())
            p_eng = int((p_calc_df[f'likes{period_suffix}'] + p_calc_df[f'comments{period_suffix}'] + p_calc_df[f'shares{period_suffix}']).sum())
            
            p_rate = 0
            if p_reach > 0 and p not in ['Threads', 'LINE@']:
                p_rate = (p_eng / p_reach) * 100
                
            platform_stats.append({
                "平台": p,
                "篇數": count,
                "總觸及/瀏覽": p_reach,
                "總互動": p_eng,
                "平均互動率": f"{p_rate:.2f}%" if p not in ['Threads', 'LINE@'] else "-"
            })
            
        st.dataframe(
            pd.DataFrame(platform_stats).set_index("平台"),
            use_container_width=True,
            column_config={
                # [重要修復] 確保 max_value 是 int，且不為 0
                "總觸及/瀏覽": st.column_config.ProgressColumn(format="%d", min_value=0, max_value=int(total_reach) if total_reach > 0 else 100),
                "總互動": st.column_config.ProgressColumn(format="%d", min_value=0, max_value=int(total_engagement) if total_engagement > 0 else 100),
            }
        )
        
        # 類型分佈圖
        if not analytics_df.empty:
            st.subheader("🍰 貼文類型分佈")
            chart_data = analytics_df['type'].value_counts()
            st.bar_chart(chart_data)

if __name__ == "__main__":
    main()
