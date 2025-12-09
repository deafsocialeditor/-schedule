<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>社群排程與成效管家</title>
    
    <!-- 1. 載入 React 核心 (使用 UMD Production 版本，穩定且快速) -->
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    
    <!-- 2. 載入 Babel (用於解析 JSX) -->
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    
    <!-- 3. 載入 Tailwind CSS (用於樣式設計) -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <style>
        body { background-color: #fff0f5; font-family: "Microsoft JhengHei", "Heiti TC", sans-serif; }
        .animate-fade-in-down { animation: fadeInDown 0.3s ease-out; }
        .animate-pop-in { animation: popIn 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
        .animate-pulse-slow { animation: pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
        
        @keyframes fadeInDown {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes popIn {
            from { opacity: 0; transform: scale(0.9); }
            to { opacity: 1; transform: scale(1); }
        }

        /* 自定義 select 箭頭 */
        select {
            -webkit-appearance: none;
            -moz-appearance: none;
            appearance: none;
            background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23ec4899' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
            background-repeat: no-repeat;
            background-position: right 0.5rem center;
            background-size: 1em;
        }
    </style>
</head>
<body>
    <div id="root"></div>

    <script type="text/babel">
        const { useState, useMemo, useEffect, useRef } = React;

        // --- 穩定版圖示系統 (Emoji) ---
        const ICONS = {
            platforms: {
                'Facebook': '📘',
                'Instagram': '📸',
                'LINE@': '🟢',
                'YouTube': '▶️',
                'Threads': '🧵',
                'All': '🌈'
            },
            metrics: {
                reach: '👀',
                likes: '❤️',
                comments: '💬',
                shares: '📲',
                rate: '📈'
            },
            status: {
                draft: '🌱',
                planned: '⏰',
                published: '🚀'
            },
            periods: {
                d7: '🔥', // 短期熱度
                m1: '🌳'  // 長期長青
            },
            ui: {
                edit: '✏️',
                delete: '🗑️',
                save: '💾',
                export: '📤',
                reset: '🔄',
                calendar: '🗓️',
                chart: '📊',
                target: '🎯',
                filter: '🔎'
            }
        };

        // 自製確認視窗元件
        const ConfirmModal = ({ isOpen, title, message, onConfirm, onCancel, confirmText = "確定", cancelText = "再想想", confirmColor = "bg-red-400" }) => {
            if (!isOpen) return null;
            return (
                <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50 backdrop-blur-sm p-4">
                    <div className="bg-white rounded-3xl shadow-2xl p-6 max-w-sm w-full animate-pop-in border-4 border-pink-100">
                        <h3 className="text-xl font-bold text-gray-800 mb-2 text-center">{title}</h3>
                        <p className="text-gray-600 mb-6 text-center">{message}</p>
                        <div className="flex justify-center space-x-3">
                            <button onClick={onCancel} className="px-5 py-2 rounded-xl bg-gray-100 text-gray-600 font-bold hover:bg-gray-200 transition-colors">
                                {cancelText}
                            </button>
                            <button onClick={onConfirm} className={`px-5 py-2 rounded-xl text-white font-bold hover:opacity-90 transition-colors shadow-md ${confirmColor}`}>
                                {confirmText}
                            </button>
                        </div>
                    </div>
                </div>
            );
        };

        const SocialScheduler = () => {
            const [activeTab, setActiveTab] = useState('schedule');
            
            // --- Helper: Safe Number ---
            const safeNum = (val) => {
                const n = Number(val);
                return isNaN(n) ? 0 : n;
            };

            // --- 資料淨化與讀取 (Data Sanitizer) ---
            const sanitizePosts = (posts) => {
                if (!Array.isArray(posts)) return [];
                return posts.map(p => {
                    const ensureMetrics = (m) => ({
                        reach: safeNum(m?.reach),
                        likes: safeNum(m?.likes),
                        comments: safeNum(m?.comments),
                        shares: safeNum(m?.shares)
                    });

                    // 兼容舊版資料結構
                    const baseMetrics = p.metrics7d ? p.metrics7d : {
                        reach: safeNum(p.reach),
                        likes: safeNum(p.likes),
                        comments: safeNum(p.comments),
                        shares: safeNum(p.shares)
                    };

                    return {
                        ...p,
                        metrics7d: ensureMetrics(baseMetrics),
                        metrics1m: p.metrics1m ? ensureMetrics(p.metrics1m) : { reach: 0, likes: 0, comments: 0, shares: 0 }
                    };
                });
            };

            const loadState = (key, defaultValue) => {
                try {
                    const saved = localStorage.getItem(key);
                    if (saved) {
                        const parsed = JSON.parse(saved);
                        if (key === 'social_posts') return sanitizePosts(parsed);
                        return parsed;
                    }
                    return defaultValue;
                } catch (e) {
                    console.error("讀取失敗，使用預設值", e);
                    return defaultValue;
                }
            };

            // 狀態管理
            const [filterType, setFilterType] = useState('month');
            const [selectedMonth, setSelectedMonth] = useState(new Date().toISOString().slice(0, 7));
            const [customRange, setCustomRange] = useState({ 
                start: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().slice(0, 10), 
                end: new Date().toISOString().slice(0, 10) 
            });
            const [filterPlatform, setFilterPlatform] = useState('All');
            
            // 排程列表專用篩選
            const [filterPostType, setFilterPostType] = useState('All');
            const [filterPurpose, setFilterPurpose] = useState('All');
            const [filterFormat, setFilterFormat] = useState('All');
            const [filterKPI, setFilterKPI] = useState('All'); 

            // 成效分析專用篩選
            const [analyticsPeriod, setAnalyticsPeriod] = useState('7d'); 
            const [filterPurposeCategory, setFilterPurposeCategory] = useState('All');

            const [sortConfig, setSortConfig] = useState({ key: 'date', direction: 'desc' });
            const [showStandardsConfig, setShowStandardsConfig] = useState(false);
            const [modalConfig, setModalConfig] = useState({ isOpen: false, type: '', data: null });
            
            // 複選平台狀態
            const [selectedPlatforms, setSelectedPlatforms] = useState(['Facebook']);

            // 選項定義
            const platforms = ['Facebook', 'Instagram', 'LINE@', 'YouTube', 'Threads'];
            const mainPostTypes = ['喜餅', '彌月', '伴手禮', '社群互動', '圓夢計畫', '公告'];
            const souvenirSubTypes = ['端午節', '中秋', '聖誕', '新春', '蒙友週'];
            const postPurposes = ['互動', '廣告', '門市廣告', '導購', '公告'];
            const postFormats = ['單圖', '多圖', '假多圖', '短影音', '限動', '純文字', '留言處'];
            const projectOwners = ['夢涵', 'MOMO', '櫻樺', '季嫻', '凌萱', '宜婷']; 
            const postOwners = ['一千', '凱曜', '可榆'];
            const designers = ['千惟', '靖嬙'];

            const defaultStandards = {
                'Facebook': { type: 'tiered', high: { reach: 2000, rate: 5.0 }, std: { reach: 1500, rate: 3.0 }, low: { reach: 1000, rate: 1.5 } },
                'Instagram': { type: 'simple', reach: 900, engagement: 30, rate: 3.5 },
                'Threads': { type: 'reference', reach: 84000, engagement: 1585, rate: 0, note: "標竿: 09/17更新(瀏覽8.4萬), 10/07孕婦節(互動1585)" },
                'YouTube': { type: 'simple', reach: 500, engagement: 0, rate: 2.0 },
                'LINE@': { type: 'simple', reach: 0, engagement: 0, rate: 0 } 
            };

            const defaultPosts = [
                { 
                    id: 1729000000001, date: '2023-10-01', platform: 'Facebook', topic: '範例：十月新品預告', 
                    postType: '喜餅', postSubType: '', postPurpose: '廣告', postFormat: '單圖', 
                    projectOwner: '夢涵', postOwner: '一千', designer: '千惟',
                    status: 'published', 
                    metrics7d: { reach: 2100, likes: 150, comments: 20, shares: 5 },
                    metrics1m: { reach: 2500, likes: 160, comments: 22, shares: 6 }
                }
            ];

            const [posts, setPosts] = useState(() => loadState('social_posts', defaultPosts));
            const [standards, setStandards] = useState(() => loadState('social_standards', defaultStandards));

            // 自動儲存 Effects
            useEffect(() => { localStorage.setItem('social_posts', JSON.stringify(posts)); }, [posts]);
            useEffect(() => { localStorage.setItem('social_standards', JSON.stringify(standards)); }, [standards]);

            const [isEditing, setIsEditing] = useState(null);
            const [formData, setFormData] = useState({
                date: new Date().toISOString().slice(0, 10),
                platform: 'Facebook', 
                topic: '', postType: '喜餅', postSubType: '',
                postPurpose: '互動', postFormat: '單圖',
                projectOwner: '夢涵', postOwner: '一千', designer: '千惟', status: 'draft',
                metrics7d: { reach: 0, likes: 0, comments: 0, shares: 0 },
                metrics1m: { reach: 0, likes: 0, comments: 0, shares: 0 }
            });

            // --- Helper to check if metrics should be disabled ---
            const isMetricsDisabled = (platform, format) => {
                return platform === 'LINE@' || format === '限動' || format === '留言處';
            };

            const resetForm = () => {
                setFormData({
                    date: new Date().toISOString().slice(0, 10),
                    platform: 'Facebook', topic: '', postType: '喜餅', postSubType: '',
                    postPurpose: '互動', postFormat: '單圖',
                    projectOwner: '夢涵', postOwner: '一千', designer: '千惟', status: 'draft',
                    metrics7d: { reach: 0, likes: 0, comments: 0, shares: 0 },
                    metrics1m: { reach: 0, likes: 0, comments: 0, shares: 0 }
                });
                setSelectedPlatforms(['Facebook']);
                setIsEditing(null);
            };

            const handleInputChange = (e) => {
                const { name, value } = e.target;
                if (name === 'postType' && value !== '伴手禮') {
                    setFormData(prev => ({ ...prev, [name]: value, postSubType: '' }));
                } else {
                    setFormData(prev => ({ ...prev, [name]: value }));
                }
            };

            const togglePlatform = (p) => {
                if (isEditing) {
                    setSelectedPlatforms([p]);
                    setFormData(prev => ({ ...prev, platform: p }));
                } else {
                    setSelectedPlatforms(prev => {
                        if (prev.includes(p)) {
                            const filtered = prev.filter(item => item !== p);
                            return filtered.length > 0 ? filtered : [p]; 
                        } else {
                            return [...prev, p];
                        }
                    });
                }
            };

            const handleMetricChange = (period, field, value) => {
                setFormData(prev => ({
                    ...prev,
                    [period]: { ...prev[period], [field]: value === '' ? '' : safeNum(value) }
                }));
            };

            const handleStandardChange = (platform, path, value) => {
                setStandards(prev => {
                    const newStandards = { ...prev };
                    const pData = { ...newStandards[platform] };
                    if (path.length === 1) pData[path[0]] = safeNum(value); 
                    else if (path.length === 2) pData[path[0]] = { ...pData[path[0]], [path[1]]: safeNum(value) };
                    newStandards[platform] = pData;
                    return newStandards;
                });
            };

            const handleSavePost = (e) => {
                e.preventDefault();
                let dataTemplate = { ...formData };
                
                if (isEditing) {
                    if (isMetricsDisabled(dataTemplate.platform, dataTemplate.postFormat)) {
                        dataTemplate.metrics7d = { reach: 0, likes: 0, comments: 0, shares: 0 };
                        dataTemplate.metrics1m = { reach: 0, likes: 0, comments: 0, shares: 0 };
                    }
                    dataTemplate.platform = selectedPlatforms[0];

                    setPosts(posts.map(post => post.id === isEditing ? { ...dataTemplate, id: isEditing } : post));
                } else {
                    const newPosts = selectedPlatforms.map(p => {
                        let postData = { ...dataTemplate, platform: p, id: Date.now() + Math.random() };
                        if (isMetricsDisabled(p, dataTemplate.postFormat)) {
                            postData.metrics7d = { reach: 0, likes: 0, comments: 0, shares: 0 };
                            postData.metrics1m = { reach: 0, likes: 0, comments: 0, shares: 0 };
                        }
                        return postData;
                    });
                    
                    setPosts([...posts, ...newPosts]);
                    
                    const postMonth = dataTemplate.date.slice(0, 7);
                    if (postMonth !== selectedMonth && filterType === 'month') {
                        setSelectedMonth(postMonth);
                    }
                }
                resetForm();
            };

            const triggerDeletePost = (id) => {
                setModalConfig({ isOpen: true, type: 'delete_single', data: id, title: '確定要刪除嗎？🗑️', message: '刪除這則貼文排程後，資料將無法復原喔！' });
            };

            const triggerResetData = () => {
                setModalConfig({ isOpen: true, type: 'reset_data', data: null, title: '🔄 重置所有資料', message: '這將會清除當前瀏覽器的所有儲存資料並恢復預設值。' });
            };

            const handleConfirmAction = () => {
                if (modalConfig.type === 'delete_single') {
                    setPosts(posts.filter(post => post.id !== modalConfig.data));
                } else if (modalConfig.type === 'reset_data') {
                    localStorage.removeItem('social_posts');
                    localStorage.removeItem('social_standards');
                    setPosts(defaultPosts);
                    setStandards(defaultStandards);
                }
                setModalConfig({ isOpen: false, type: '', data: null });
            };

            const handleEditClick = (post) => {
                setIsEditing(post.id);
                setFormData(post);
                setSelectedPlatforms([post.platform]); 
                window.scrollTo({ top: 0, behavior: 'smooth' });
            };

            const requestSort = (key) => {
                let direction = 'asc';
                if (sortConfig.key === key && sortConfig.direction === 'asc') direction = 'desc';
                setSortConfig({ key, direction });
            };

            // KPI Label
            function getPerformanceLabel(platform, metrics, format) {
                if (isMetricsDisabled(platform, format)) return { label: '-', color: 'text-gray-400', pass: false };
                if (!metrics || !metrics.reach) return { label: '-', color: 'text-gray-400', pass: false };
                
                const std = standards[platform];
                const engagement = (safeNum(metrics.likes)) + (safeNum(metrics.comments)) + (safeNum(metrics.shares));
                const rate = (engagement / safeNum(metrics.reach)) * 100;

                if (platform === 'Facebook') {
                    if (metrics.reach >= std.high.reach && rate >= std.high.rate) return { label: '高標 (S)', color: 'text-purple-600 bg-purple-50 border-purple-200', pass: true };
                    if (metrics.reach >= std.std.reach && rate >= std.std.rate) return { label: '標準 (A)', color: 'text-green-600 bg-green-50 border-green-200', pass: true };
                    if (metrics.reach >= std.low.reach && rate >= std.low.rate) return { label: '低標 (B)', color: 'text-orange-600 bg-orange-50 border-orange-200', pass: true };
                    return { label: '未達標', color: 'text-red-600 bg-red-50 border-red-200', pass: false };
                } 
                else if (platform === 'Instagram') {
                    const passReach = metrics.reach >= std.reach;
                    const passEngage = engagement >= std.engagement;
                    const passRate = rate >= std.rate;
                    if (passReach && passEngage && passRate) return { label: '達標', color: 'text-green-600 bg-green-50 border-green-200', pass: true };
                    return { label: '未達標', color: 'text-red-600 bg-red-50 border-red-200', pass: false };
                }
                else if (platform === 'Threads') {
                    if (metrics.reach >= std.reach) return { label: '超標竿', color: 'text-purple-600 bg-purple-50 border-purple-200', pass: true };
                    return { label: '-', color: 'text-gray-400', pass: true };
                }
                else if (platform === 'YouTube') {
                    if (metrics.reach >= std.reach && rate >= std.rate) return { label: '達標', color: 'text-green-600 bg-green-50 border-green-200', pass: true };
                    return { label: '未達標', color: 'text-red-600 bg-red-50 border-red-200', pass: false };
                }
                return { label: '-', color: 'text-gray-400', pass: false };
            }

            // --- Date Calculation Helper ---
            const calculateDueDates = (dateString) => {
                if (!dateString) return { date7d: '', date1m: '' };
                const date = new Date(dateString);
                // Simple date adding with basic validity check
                if (isNaN(date.getTime())) return { date7d: '', date1m: '' };

                const addDays = (d, days) => {
                    const result = new Date(d);
                    result.setDate(result.getDate() + days);
                    return result.toISOString().slice(0, 10);
                };
                const addMonths = (d, months) => {
                    const result = new Date(d);
                    result.setMonth(result.getMonth() + months);
                    return result.toISOString().slice(0, 10);
                };
                return { date7d: addDays(date, 7), date1m: addMonths(date, 1) };
            };
            
            const getLocalToday = () => {
                const d = new Date();
                const year = d.getFullYear();
                const month = String(d.getMonth() + 1).padStart(2, '0');
                const day = String(d.getDate()).padStart(2, '0');
                return `${year}-${month}-${day}`;
            };

            const getDueStatus = (post, period) => {
                if (post.status !== 'published' || isMetricsDisabled(post.platform, post.postFormat)) return null;
                const { date7d, date1m } = calculateDueDates(post.date);
                if (!date7d || !date1m) return null;

                const today = getLocalToday();
                const metrics = period === '7d' ? post.metrics7d : post.metrics1m;
                const targetDate = period === '7d' ? date7d : date1m;
                
                if (today >= targetDate && (!metrics || metrics.reach === 0)) return { isDue: true, date: targetDate };
                return { isDue: false, date: targetDate };
            };

            // --- Base Filtered Posts (Shared by List and Analytics) ---
            const baseFilteredPosts = useMemo(() => {
                 return posts.filter(p => {
                    const dateMatch = filterType === 'month' ? p.date.startsWith(selectedMonth) : (p.date >= customRange.start && p.date <= customRange.end);
                    const platformMatch = filterPlatform === 'All' || p.platform === filterPlatform;
                    return dateMatch && platformMatch;
                });
            }, [posts, filterType, selectedMonth, customRange, filterPlatform]);

            // --- List View Filtered Posts ---
            const listFilteredPosts = useMemo(() => {
                return baseFilteredPosts.filter(p => {
                    const typeMatch = filterPostType === 'All' || p.postType === filterPostType;
                    const purposeMatch = filterPurpose === 'All' || p.postPurpose === filterPurpose;
                    const formatMatch = filterFormat === 'All' || p.postFormat === filterFormat;

                    let kpiMatch = true;
                    if (filterKPI !== 'All') {
                        const perf = getPerformanceLabel(p.platform, p.metrics7d, p.postFormat);
                        if (filterKPI === 'Good') kpiMatch = ['高標 (S)', '標準 (A)', '達標', '超標竿'].some(k => perf.label.includes(k));
                        else if (filterKPI === 'Fair') kpiMatch = perf.label.includes('低標');
                        else if (filterKPI === 'Poor') kpiMatch = perf.label.includes('未達標');
                        else if (filterKPI === 'None') kpiMatch = perf.label === '-';
                    }

                    return typeMatch && purposeMatch && formatMatch && kpiMatch;
                });
            }, [baseFilteredPosts, filterPostType, filterPurpose, filterFormat, filterKPI, standards]);

            // --- Sorted Posts for List ---
            const sortedPosts = useMemo(() => {
                let items = [...listFilteredPosts];
                if (sortConfig.key) {
                    items.sort((a, b) => {
                        let aVal, bVal;
                        switch(sortConfig.key) {
                            case 'date': aVal = new Date(a.date); bVal = new Date(b.date); break;
                            case 'platform': aVal = a.platform; bVal = b.platform; break;
                            case 'topic': aVal = a.topic; bVal = b.topic; break;
                            case 'status': aVal = a.status; bVal = b.status; break;
                            case 'metrics7d': aVal = a.metrics7d?.reach || 0; bVal = b.metrics7d?.reach || 0; break;
                            case 'rate7d': 
                                const getRate7d = (p) => (isMetricsDisabled(p.platform, p.postFormat) || !p.metrics7d?.reach) ? 0 : ((p.metrics7d.likes + p.metrics7d.comments + p.metrics7d.shares) / p.metrics7d.reach);
                                aVal = getRate7d(a); bVal = getRate7d(b); break;
                            case 'metrics1m': aVal = a.metrics1m?.reach || 0; bVal = b.metrics1m?.reach || 0; break;
                            case 'rate1m':
                                const getRate1m = (p) => (isMetricsDisabled(p.platform, p.postFormat) || !p.metrics1m?.reach) ? 0 : ((p.metrics1m.likes + p.metrics1m.comments + p.metrics1m.shares) / p.metrics1m.reach);
                                aVal = getRate1m(a); bVal = getRate1m(b); break;
                            default: aVal = a[sortConfig.key]; bVal = b[sortConfig.key];
                        }
                        if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
                        if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
                        return 0;
                    });
                }
                return items;
            }, [listFilteredPosts, sortConfig]);

            // --- Analytics Data Calculation ---
            const stats = useMemo(() => {
                let targetPosts = baseFilteredPosts.filter(p => p.status === 'published');
                if (filterPurposeCategory !== 'All') {
                    targetPosts = targetPosts.filter(p => {
                         const isAd = ['廣告', '門市廣告'].includes(p.postPurpose);
                         return filterPurposeCategory === 'Ad' ? isAd : !isAd;
                    });
                }
                
                const getMetrics = (p) => analyticsPeriod === '7d' ? (p.metrics7d || { reach:0, likes:0, comments:0, shares:0 }) : (p.metrics1m || { reach:0, likes:0, comments:0, shares:0 });
                const calculablePosts = targetPosts.filter(p => !isMetricsDisabled(p.platform, p.postFormat));

                const totalReach = calculablePosts.reduce((sum, p) => sum + safeNum(getMetrics(p).reach), 0);
                const totalEngagement = calculablePosts.reduce((sum, p) => {
                    const m = getMetrics(p);
                    return sum + safeNum(m.likes) + safeNum(m.comments) + safeNum(m.shares);
                }, 0);
                
                const platformStats = {};
                const typeDistribution = {};
                platforms.forEach(p => {
                    platformStats[p] = { total: { count: 0, reach: 0, engagement: 0, rate: 0 }, shortVideo: { count: 0, reach: 0, engagement: 0, rate: 0 }, regular: { count: 0, reach: 0, engagement: 0, rate: 0 } };
                    typeDistribution[p] = {};
                    mainPostTypes.forEach(t => { typeDistribution[p][t] = 0; });
                });

                targetPosts.forEach(post => {
                    if (!platformStats[post.platform]) return; 
                    const pStats = platformStats[post.platform];
                    const isShortVideo = post.postFormat === '短影音';
                    // Update: story includes '留言處' for exclusion logic
                    const isStory = isMetricsDisabled(post.platform, post.postFormat);

                    if (!typeDistribution[post.platform]) typeDistribution[post.platform] = {};
                    if (!typeDistribution[post.platform][post.postType]) typeDistribution[post.platform][post.postType] = 0;
                    typeDistribution[post.platform][post.postType] += 1;

                    if (isStory) { pStats.total.count += 1; return; }
                    
                    const m = getMetrics(post);
                    const eng = safeNum(m.likes) + safeNum(m.comments) + safeNum(m.shares);
                    const updateCat = (cat) => { cat.count += 1; cat.reach += safeNum(m.reach); cat.engagement += eng; };

                    updateCat(pStats.total);
                    updateCat(isShortVideo ? pStats.shortVideo : pStats.regular);
                });

                Object.keys(platformStats).forEach(pKey => {
                    const p = platformStats[pKey];
                    ['total', 'shortVideo', 'regular'].forEach(cat => {
                        if (p[cat].reach > 0 && pKey !== 'Threads' && pKey !== 'LINE@') {
                            p[cat].rate = ((p[cat].engagement / p[cat].reach) * 100).toFixed(2);
                        } else {
                            p[cat].rate = 0;
                        }
                    });
                });

                return { 
                    totalReach, 
                    totalEngagement, 
                    platformStats, 
                    typeDistribution,
                    publishedCount: targetPosts.length 
                };
            }, [baseFilteredPosts, platforms, mainPostTypes, analyticsPeriod, filterPurposeCategory]);

            const monthOptions = useMemo(() => {
                const options = new Set();
                posts.forEach(p => { if(p.date) options.add(p.date.slice(0, 7)); });
                if (options.size === 0) options.add(new Date().toISOString().slice(0, 7));
                return Array.from(options).sort().reverse();
            }, [posts]);

            useEffect(() => {
                if (monthOptions.length > 0 && !monthOptions.includes(selectedMonth)) setSelectedMonth(monthOptions[0]);
            }, [monthOptions, selectedMonth]);

            const currentDueDates = useMemo(() => calculateDueDates(formData.date), [formData.date]);

            // UI Components
            const SortIcon = ({ colKey }) => {
                if (sortConfig.key !== colKey) return <span className="ml-1 text-gray-300 opacity-0 group-hover:opacity-50 text-xs">⬆️</span>;
                return sortConfig.direction === 'asc' ? <span className="ml-1 text-pink-500 text-xs">⬆️</span> : <span className="ml-1 text-pink-500 text-xs">⬇️</span>;
            };

            const ThSortable = ({ label, colKey, align = "left", className="" }) => (
                <th className={`p-4 font-medium cursor-pointer group hover:bg-pink-50 transition-colors text-gray-600 ${className}`} onClick={() => requestSort(colKey)}>
                    <div className={`flex items-center ${align === 'right' ? 'justify-end' : align === 'center' ? 'justify-center' : 'justify-start'}`}>
                        {label}
                        <SortIcon colKey={colKey} />
                    </div>
                </th>
            );

            const handleExport = () => {
                const filename = filterType === 'month' ? `社群排程_${selectedMonth}.csv` : `社群排程_${customRange.start}_${customRange.end}.csv`;
                const headers = "ID,日期,平台,主題,類型,子類型,目的,形式,專案負責人,貼文負責人,美編負責人,狀態,7天_觸及,7天_按讚,7天_留言,7天_分享,7天_互動率,KPI等級,一個月_觸及,一個月_按讚,一個月_留言,一個月_分享,一個月_互動率\n";
                const exportList = listFilteredPosts; 
                const csvContent = "data:text/csv;charset=utf-8,\uFEFF" + headers + exportList.map(e => {
                    const m7 = e.metrics7d || { reach:0, likes:0, comments:0, shares:0 };
                    const m1 = e.metrics1m || { reach:0, likes:0, comments:0, shares:0 };

                    const eng7d = safeNum(m7.likes) + safeNum(m7.comments) + safeNum(m7.shares);
                    const rate7d = (isMetricsDisabled(e.platform, e.postFormat) || m7.reach === 0) ? '-' : ((eng7d / m7.reach) * 100).toFixed(2) + '%';
                    
                    const eng1m = safeNum(m1.likes) + safeNum(m1.comments) + safeNum(m1.shares);
                    const rate1m = (isMetricsDisabled(e.platform, e.postFormat) || m1.reach === 0) ? '-' : ((eng1m / m1.reach) * 100).toFixed(2) + '%';
                    
                    return `${e.id},${e.date},${e.platform},${e.topic},${e.postType},${e.postSubType},${e.postPurpose},${e.postFormat},${e.projectOwner},${e.postOwner},${e.designer},${e.status},` +
                    `${m7.reach},${m7.likes},${m7.comments},${m7.shares},${rate7d},` +
                    `${getPerformanceLabel(e.platform, m7, e.postFormat).label},` +
                    `${m1.reach},${m1.likes},${m1.comments},${m1.shares},${rate1m}`;
                }).join("\n");
                const encodedUri = encodeURI(csvContent);
                const link = document.createElement("a");
                link.setAttribute("href", encodedUri);
                link.setAttribute("download", filename);
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            };
            
            // Check if post date matches today
            const isToday = (dateString) => dateString === getLocalToday();

            return (
                <div className="min-h-screen bg-gray-50 text-gray-800 font-sans pb-10">
                    <ConfirmModal 
                        isOpen={modalConfig.isOpen} 
                        title={modalConfig.title} 
                        message={modalConfig.message} 
                        onConfirm={handleConfirmAction} 
                        onCancel={() => setModalConfig({ isOpen: false })} 
                    />

                    <header className="bg-white shadow-sm sticky top-0 z-10 border-b border-pink-100">
                        <div className="max-w-7xl mx-auto px-4 py-4 flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
                            <div className="flex items-center space-x-2 w-full md:w-auto">
                                <div className="bg-gradient-to-tr from-pink-400 to-purple-400 text-white p-2 rounded-xl text-2xl shadow-md">📅</div>
                                <h1 className="text-xl font-bold text-gray-700 tracking-wide">社群排程小幫手</h1>
                            </div>
                            <div className="flex flex-col md:flex-row items-end md:items-center space-y-2 md:space-y-0 md:space-x-4 w-full md:w-auto justify-between md:justify-end">
                                <div className="flex flex-col md:flex-row space-y-2 md:space-y-0 md:space-x-2">
                                    <div className="relative">
                                        <select value={filterPlatform} onChange={(e) => setFilterPlatform(e.target.value)} className="appearance-none bg-white border border-pink-200 text-gray-600 py-2 pl-3 pr-8 rounded-xl focus:outline-none focus:ring-2 focus:ring-pink-300 font-medium cursor-pointer text-sm w-full md:w-auto hover:border-pink-300 transition-colors">
                                            <option value="All">🌈 全部平台</option>
                                            {platforms.map(p => <option key={p} value={p}>{ICONS.platforms[p]} {p}</option>)}
                                        </select>
                                    </div>
                                    <div className="flex items-center space-x-1 bg-white border border-pink-200 p-1 rounded-xl">
                                        <button onClick={() => setFilterType('month')} className={`px-3 py-1 text-sm rounded-lg transition-all ${filterType === 'month' ? 'bg-pink-100 text-pink-600 font-bold' : 'text-gray-400 hover:text-gray-600'}`}>月</button>
                                        <button onClick={() => setFilterType('custom')} className={`px-3 py-1 text-sm rounded-lg transition-all ${filterType === 'custom' ? 'bg-pink-100 text-pink-600 font-bold' : 'text-gray-400 hover:text-gray-600'}`}>日</button>
                                    </div>
                                    {filterType === 'month' ? (
                                        <div className="relative">
                                            <select value={selectedMonth} onChange={(e) => setSelectedMonth(e.target.value)} className="appearance-none bg-white border border-pink-200 text-gray-600 py-2 pl-4 pr-10 rounded-xl focus:outline-none focus:ring-2 focus:ring-pink-300 font-medium cursor-pointer w-full md:w-auto hover:border-pink-300 transition-colors">
                                                {monthOptions.map(m => <option key={m} value={m}>{m}</option>)}
                                            </select>
                                        </div>
                                    ) : (
                                        <div className="flex items-center space-x-1">
                                            <input type="date" value={customRange.start} onChange={(e) => setCustomRange(prev => ({ ...prev, start: e.target.value }))} className="border border-pink-200 rounded-xl p-2 text-sm focus:outline-none focus:ring-2 focus:ring-pink-300 w-32 text-gray-600" />
                                            <span className="text-gray-400">-</span>
                                            <input type="date" value={customRange.end} onChange={(e) => setCustomRange(prev => ({ ...prev, end: e.target.value }))} className="border border-pink-200 rounded-xl p-2 text-sm focus:outline-none focus:ring-2 focus:ring-pink-300 w-32 text-gray-600" />
                                        </div>
                                    )}
                                </div>
                                <div className="flex space-x-2">
                                    <button onClick={() => setActiveTab('schedule')} className={`px-4 py-2 rounded-xl flex items-center space-x-2 transition-all shadow-sm ${activeTab === 'schedule' ? 'bg-white text-pink-500 font-bold border-2 border-pink-200' : 'text-gray-500 hover:bg-white hover:text-pink-400'}`}>
                                        <span className="text-lg">🗓️</span> <span className="hidden sm:inline ml-1">排程</span>
                                    </button>
                                    <button onClick={() => setActiveTab('analytics')} className={`px-4 py-2 rounded-xl flex items-center space-x-2 transition-all shadow-sm ${activeTab === 'analytics' ? 'bg-white text-purple-500 font-bold border-2 border-purple-200' : 'text-gray-500 hover:bg-white hover:text-purple-400'}`}>
                                        <span className="text-lg">📊</span> <span className="hidden sm:inline ml-1">分析</span>
                                    </button>
                                    <button onClick={triggerResetData} className="px-3 py-2 text-gray-400 hover:text-red-400 hover:bg-red-50 rounded-xl font-bold transition-colors" title="重置所有資料">🔄</button>
                                </div>
                            </div>
                        </div>
                    </header>

                    <main className="max-w-7xl mx-auto px-4 py-8">
                        {activeTab === 'schedule' && (
                            <div className="space-y-6">
                                {/* Input Form */}
                                <div className="bg-white rounded-3xl shadow-sm border border-pink-100 p-6 animate-fade-in-down">
                                    <div className="flex justify-between items-center mb-6">
                                        <h2 className="text-lg font-bold flex items-center text-gray-700">
                                            <span className="mr-2 text-2xl bg-yellow-100 p-1.5 rounded-lg">{isEditing ? '✏️' : '✨'}</span>
                                            {isEditing ? '編輯貼文' : '新增排程'}
                                        </h2>
                                        {isEditing && <button onClick={resetForm} className="text-sm text-gray-400 hover:text-pink-500 underline decoration-dashed">取消編輯</button>}
                                    </div>
                                    <form onSubmit={handleSavePost} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
                                        <div className="space-y-1"><label className="text-xs font-bold text-gray-400 ml-1">日期</label><input type="date" name="date" required value={formData.date} onChange={handleInputChange} className="w-full p-2.5 border border-gray-200 rounded-xl outline-none focus:border-pink-300 focus:ring-2 focus:ring-pink-100 transition-all bg-gray-50" /></div>
                                        
                                        <div className="space-y-1 md:col-span-2 lg:col-span-1">
                                            <label className="text-xs font-bold text-gray-400 ml-1">平台 {isEditing ? '(單選)' : '(可複選)'}</label>
                                            <div className="flex flex-wrap gap-2 mt-1">
                                                {platforms.map(p => (
                                                    <button
                                                        key={p}
                                                        type="button"
                                                        onClick={() => togglePlatform(p)}
                                                        className={`px-3 py-1.5 rounded-lg text-sm border transition-all flex items-center ${selectedPlatforms.includes(p) ? 'bg-pink-100 border-pink-300 text-pink-600 font-bold shadow-sm' : 'bg-white border-gray-200 text-gray-500 hover:bg-gray-50'}`}
                                                    >
                                                        <span className="mr-1">{ICONS.platforms[p]}</span>
                                                        {p}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>

                                        <div className="space-y-1 md:col-span-2"><label className="text-xs font-bold text-gray-400 ml-1">主題</label><input type="text" name="topic" required placeholder="例如：母親節促銷 🎉" value={formData.topic} onChange={handleInputChange} className="w-full p-2.5 border border-gray-200 rounded-xl outline-none focus:border-pink-300 focus:ring-2 focus:ring-pink-100 transition-all bg-gray-50 placeholder-gray-300" /></div>
                                        <div className="space-y-1"><label className="text-xs font-bold text-gray-400 ml-1">貼文類型</label><select name="postType" value={formData.postType} onChange={handleInputChange} className="w-full p-2.5 border border-gray-200 rounded-xl outline-none focus:border-pink-300 focus:ring-2 focus:ring-pink-100 transition-all bg-white">{mainPostTypes.map(o => <option key={o} value={o}>{o}</option>)}</select></div>
                                        <div className="space-y-1"><label className={`text-xs font-bold ml-1 ${formData.postType !== '伴手禮' ? 'text-gray-200' : 'text-pink-400'}`}>節慶/子類型 (伴手禮)</label><select name="postSubType" value={formData.postSubType} onChange={handleInputChange} disabled={formData.postType !== '伴手禮'} className={`w-full p-2.5 border rounded-xl outline-none transition-all ${formData.postType !== '伴手禮' ? 'bg-gray-50 text-gray-300 border-gray-100' : 'bg-yellow-50 border-yellow-200 text-gray-700'}`}><option value="">-- 無 --</option>{souvenirSubTypes.map(o => <option key={o} value={o}>{o}</option>)}</select></div>
                                        <div className="space-y-1"><label className="text-xs font-bold text-gray-400 ml-1">目的 / 形式</label><div className="flex space-x-2"><select name="postPurpose" value={formData.postPurpose} onChange={handleInputChange} className="w-1/2 p-2.5 border border-gray-200 rounded-xl outline-none focus:ring-2 focus:ring-pink-100 bg-white">{postPurposes.map(o => <option key={o} value={o}>{o}</option>)}</select><select name="postFormat" value={formData.postFormat} onChange={handleInputChange} className="w-1/2 p-2.5 border border-gray-200 rounded-xl outline-none focus:ring-2 focus:ring-pink-100 bg-white">{postFormats.map(o => <option key={o} value={o}>{o}</option>)}</select></div></div>
                                        <div className="space-y-1"><label className="text-xs font-bold text-gray-400 ml-1">負責人員 (P/E/D)</label><div className="flex space-x-1"><select name="projectOwner" value={formData.projectOwner} onChange={handleInputChange} className="w-1/3 p-2.5 border border-gray-200 rounded-xl text-xs bg-white"><option value="">P:無</option>{projectOwners.map(o=><option key={o} value={o}>{o}</option>)}</select><select name="postOwner" value={formData.postOwner} onChange={handleInputChange} className="w-1/3 p-2.5 border border-gray-200 rounded-xl text-xs bg-white">{postOwners.map(o=><option key={o} value={o}>{o}</option>)}</select><select name="designer" value={formData.designer} onChange={handleInputChange} className="w-1/3 p-2.5 border border-gray-200 rounded-xl text-xs bg-white"><option value="">D:無</option>{designers.map(o=><option key={o} value={o}>{o}</option>)}</select></div></div>
                                        <div className="space-y-1"><label className="text-xs font-bold text-gray-400 ml-1">狀態</label><select name="status" value={formData.status} onChange={handleInputChange} className="w-full p-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-pink-100 outline-none bg-white"><option value="draft">{ICONS.status.draft} 草稿</option><option value="planned">{ICONS.status.planned} 已排程</option><option value="published">{ICONS.status.published} 已發布</option></select></div>
                                        
                                        {/* Metrics Inputs */}
                                        <div className={`col-span-1 md:col-span-2 lg:col-span-4 grid grid-cols-1 md:grid-cols-2 gap-6 border-t border-gray-100 pt-6 mt-2 transition-opacity duration-300 ${formData.status !== 'published' ? 'opacity-40 grayscale' : 'opacity-100'}`}>
                                            <div className={`p-5 rounded-2xl border relative transition-colors ${isMetricsDisabled(formData.platform, formData.postFormat) ? 'bg-gray-100 border-gray-200' : 'bg-blue-50 border-blue-100'}`}>
                                                {isMetricsDisabled(formData.platform, formData.postFormat) && (
                                                    <div className="absolute inset-0 flex items-center justify-center bg-gray-100 bg-opacity-70 z-10 rounded-2xl backdrop-blur-[1px]">
                                                        <span className="bg-white text-gray-400 px-4 py-1.5 rounded-full text-sm font-bold shadow-sm border">
                                                            {formData.postFormat === '限動' ? '限動不需填寫成效' : formData.postFormat === '留言處' ? '留言處不需填寫成效' : '此平台不需填寫成效'}
                                                        </span>
                                                    </div>
                                                )}
                                                <div className="absolute top-3 right-3">{!isMetricsDisabled(formData.platform, formData.postFormat) && <span className="text-[10px] bg-white px-2 py-1 rounded-lg border text-blue-400 font-bold shadow-sm">KPI 基準</span>}</div>
                                                <h4 className="text-sm font-bold text-blue-600 mb-4 flex items-center flex-wrap">
                                                    <span className="mr-2 text-lg">{ICONS.periods.d7}</span> 發文 7 天成效
                                                    {formData.date && <span className="ml-2 text-xs text-blue-400 bg-blue-50 px-2 py-0.5 rounded border border-blue-100">預計: {currentDueDates.date7d.slice(5).replace('-','/')}</span>}
                                                    {formData.status === 'published' && !isMetricsDisabled(formData.platform, formData.postFormat) && (
                                                        <span className="ml-2 text-xs text-red-500 bg-red-50 px-2 py-0.5 rounded border border-red-200 animate-pulse">👈 請填寫數據</span>
                                                    )}
                                                </h4>
                                                <div className="grid grid-cols-3 gap-3">
                                                    <div className="space-y-1"><label className="text-xs text-blue-400 font-bold ml-1">{ICONS.metrics.reach} 觸及/瀏覽</label><input type="number" disabled={isMetricsDisabled(formData.platform, formData.postFormat)} value={formData.metrics7d.reach} onChange={(e) => handleMetricChange('metrics7d', 'reach', e.target.value)} className="w-full p-2 border border-blue-100 rounded-lg bg-white text-sm disabled:bg-gray-50 focus:border-blue-300 outline-none text-right" placeholder="0" /></div>
                                                    <div className="space-y-1"><label className="text-xs text-blue-400 font-bold ml-1">{ICONS.metrics.likes} 按讚</label><input type="number" disabled={isMetricsDisabled(formData.platform, formData.postFormat)} value={formData.metrics7d.likes} onChange={(e) => handleMetricChange('metrics7d', 'likes', e.target.value)} className="w-full p-2 border border-blue-100 rounded-lg bg-white text-sm disabled:bg-gray-50 focus:border-blue-300 outline-none text-right" placeholder="0" /></div>
                                                    <div className="space-y-1"><label className="text-xs text-blue-400 font-bold ml-1">{ICONS.metrics.comments} 留言+分享</label><div className="flex space-x-1"><input type="number" disabled={isMetricsDisabled(formData.platform, formData.postFormat)} value={formData.metrics7d.comments} onChange={(e) => handleMetricChange('metrics7d', 'comments', e.target.value)} className="w-1/2 p-2 border border-blue-100 rounded-lg bg-white text-sm disabled:bg-gray-50 text-center focus:border-blue-300 outline-none" placeholder="言" /><input type="number" disabled={isMetricsDisabled(formData.platform, formData.postFormat)} value={formData.metrics7d.shares} onChange={(e) => handleMetricChange('metrics7d', 'shares', e.target.value)} className="w-1/2 p-2 border border-blue-100 rounded-lg bg-white text-sm disabled:bg-gray-50 text-center focus:border-blue-300 outline-none" placeholder="享" /></div></div>
                                                </div>
                                            </div>
                                            <div className={`p-5 rounded-2xl border relative transition-colors ${isMetricsDisabled(formData.platform, formData.postFormat) ? 'bg-gray-100 border-gray-200' : 'bg-purple-50 border-purple-100'}`}>
                                                {isMetricsDisabled(formData.platform, formData.postFormat) && <div className="absolute inset-0 flex items-center justify-center bg-gray-100 bg-opacity-70 z-10 rounded-2xl backdrop-blur-[1px]"></div>}
                                                <h4 className="text-sm font-bold text-purple-600 mb-4 flex items-center flex-wrap">
                                                    <span className="mr-2 text-lg">{ICONS.periods.m1}</span> 發文一個月成效
                                                    {formData.date && <span className="ml-2 text-xs text-purple-400 bg-purple-50 px-2 py-0.5 rounded border border-purple-100">預計: {currentDueDates.date1m.slice(5).replace('-','/')}</span>}
                                                </h4>
                                                <div className="grid grid-cols-3 gap-3">
                                                    <div className="space-y-1"><label className="text-xs text-purple-400 font-bold ml-1">{ICONS.metrics.reach} 觸及/瀏覽</label><input type="number" disabled={isMetricsDisabled(formData.platform, formData.postFormat)} value={formData.metrics1m.reach} onChange={(e) => handleMetricChange('metrics1m', 'reach', e.target.value)} className="w-full p-2 border border-purple-100 rounded-lg bg-white text-sm disabled:bg-gray-50 focus:border-purple-300 outline-none text-right" placeholder="0" /></div>
                                                    <div className="space-y-1"><label className="text-xs text-purple-400 font-bold ml-1">{ICONS.metrics.likes} 按讚</label><input type="number" disabled={isMetricsDisabled(formData.platform, formData.postFormat)} value={formData.metrics1m.likes} onChange={(e) => handleMetricChange('metrics1m', 'likes', e.target.value)} className="w-full p-2 border border-purple-100 rounded-lg bg-white text-sm disabled:bg-gray-50 focus:border-purple-300 outline-none text-right" placeholder="0" /></div>
                                                    <div className="space-y-1"><label className="text-xs text-purple-400 font-bold ml-1">{ICONS.metrics.comments} 留言+分享</label><div className="flex space-x-1"><input type="number" disabled={isMetricsDisabled(formData.platform, formData.postFormat)} value={formData.metrics1m.comments} onChange={(e) => handleMetricChange('metrics1m', 'comments', e.target.value)} className="w-1/2 p-2 border border-purple-100 rounded-lg bg-white text-sm disabled:bg-gray-50 text-center focus:border-purple-300 outline-none" placeholder="言" /><input type="number" disabled={isMetricsDisabled(formData.platform, formData.postFormat)} value={formData.metrics1m.shares} onChange={(e) => handleMetricChange('metrics1m', 'shares', e.target.value)} className="w-1/2 p-2 border border-purple-100 rounded-lg bg-white text-sm disabled:bg-gray-50 text-center focus:border-purple-300 outline-none" placeholder="享" /></div></div>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="md:col-span-2 lg:col-span-4 flex justify-end"><button type="submit" className="bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white px-8 py-2.5 rounded-xl font-bold flex items-center transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"><span className="mr-2">{ICONS.ui.save}</span> {isEditing ? '更新貼文' : '加入排程'}</button></div>
                                    </form>
                                </div>

                                {/* List View */}
                                <div className="bg-white rounded-3xl shadow-sm border border-gray-200 overflow-hidden">
                                    <div className="p-5 border-b border-gray-100 flex flex-col xl:flex-row justify-between items-start xl:items-center gap-4">
                                        <div className="flex items-center space-x-2">
                                            <h3 className="font-bold text-gray-700 whitespace-nowrap">排程列表 ({listFilteredPosts.length})</h3>
                                            <div className="flex flex-wrap gap-2 ml-2">
                                                <select value={filterPostType} onChange={(e) => setFilterPostType(e.target.value)} className="text-xs bg-white text-gray-500 px-2 py-1.5 rounded-lg border border-gray-200 shadow-sm outline-none cursor-pointer hover:border-pink-200">
                                                    <option value="All">類型: 全部</option>
                                                    {mainPostTypes.map(t => <option key={t} value={t}>{t}</option>)}
                                                </select>
                                                <select value={filterPurpose} onChange={(e) => setFilterPurpose(e.target.value)} className="text-xs bg-white text-gray-500 px-2 py-1.5 rounded-lg border border-gray-200 shadow-sm outline-none cursor-pointer hover:border-pink-200">
                                                    <option value="All">目的: 全部</option>
                                                    {postPurposes.map(t => <option key={t} value={t}>{t}</option>)}
                                                </select>
                                                <select value={filterFormat} onChange={(e) => setFilterFormat(e.target.value)} className="text-xs bg-white text-gray-500 px-2 py-1.5 rounded-lg border border-gray-200 shadow-sm outline-none cursor-pointer hover:border-pink-200">
                                                    <option value="All">形式: 全部</option>
                                                    {postFormats.map(t => <option key={t} value={t}>{t}</option>)}
                                                </select>
                                                <select value={filterKPI} onChange={(e) => setFilterKPI(e.target.value)} className="text-xs bg-white text-gray-500 px-2 py-1.5 rounded-lg border border-gray-200 shadow-sm outline-none cursor-pointer hover:border-pink-200">
                                                    <option value="All">KPI: 全部</option>
                                                    <option value="Good">🟢 達標/高標</option>
                                                    <option value="Fair">🟠 低標</option>
                                                    <option value="Poor">🔴 未達標</option>
                                                    <option value="None">⚪ 無數據/不需填</option>
                                                </select>
                                            </div>
                                        </div>
                                        <div className="flex space-x-3 w-full xl:w-auto justify-end">
                                            <button onClick={handleExport} className="text-xs text-blue-600 hover:text-blue-800 flex items-center font-bold bg-blue-50 hover:bg-blue-100 px-4 py-2 rounded-lg transition-colors"><span className="mr-1">{ICONS.ui.export}</span> 匯出 CSV</button>
                                        </div>
                                    </div>
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-left border-collapse whitespace-nowrap">
                                            <thead>
                                                <tr className="bg-gray-50 text-gray-500 text-sm border-b">
                                                    <ThSortable label="日期/平台" colKey="date" />
                                                    <ThSortable label="主題/類型" colKey="topic" />
                                                    <th className="p-4 font-medium text-gray-500">負責人員</th>
                                                    <ThSortable label="狀態" colKey="status" />
                                                    <ThSortable label="KPI" colKey="metrics7d" />
                                                    <ThSortable label={`7天 ${ICONS.metrics.reach} / ${ICONS.metrics.likes}`} colKey="metrics7d" align="right" />
                                                    <ThSortable label={`7天 ${ICONS.metrics.rate}`} colKey="rate7d" align="right" />
                                                    <ThSortable label={`一個月 ${ICONS.metrics.reach} / ${ICONS.metrics.likes}`} colKey="metrics1m" align="right" />
                                                    <ThSortable label={`一個月 ${ICONS.metrics.rate}`} colKey="rate1m" align="right" />
                                                    <th className="p-4 font-medium text-center text-gray-400">操作</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-gray-100">
                                                {sortedPosts.map(post => {
                                                    const m7 = post.metrics7d || { reach:0, likes:0, comments:0, shares:0 };
                                                    const m1 = post.metrics1m || { reach:0, likes:0, comments:0, shares:0 };

                                                    const engage7d = m7.likes + m7.comments + m7.shares;
                                                    const engage1m = m1.likes + m1.comments + m1.shares;
                                                    const perf = getPerformanceLabel(post.platform, m7, post.postFormat);
                                                    
                                                    const rate7d = (post.platform === 'Threads' || post.platform === 'LINE@' || post.postFormat === '限動' || post.postFormat === '留言處' || m7.reach === 0) ? '-' : ((engage7d / m7.reach) * 100).toFixed(2) + '%';
                                                    const rate1m = (post.platform === 'Threads' || post.platform === 'LINE@' || post.postFormat === '限動' || post.postFormat === '留言處' || m1.reach === 0) ? '-' : ((engage1m / m1.reach) * 100).toFixed(2) + '%';

                                                    const dueStatus7d = getDueStatus(post, '7d');
                                                    const dueStatus1m = getDueStatus(post, '1m');
                                                    const isTodayPost = isToday(post.date);

                                                    return (
                                                        <tr key={post.id} className={`hover:bg-pink-50 transition-colors group ${isTodayPost ? 'bg-yellow-50 border-l-4 border-l-yellow-400' : ''}`}>
                                                            <td className="p-4 text-sm">
                                                                <div className={`font-mono font-bold mb-1 ${isTodayPost ? 'text-yellow-700' : 'text-gray-500'}`}>{post.date} {isTodayPost && '✨'}</div>
                                                                <span className={`px-2 py-0.5 rounded-md text-xs font-bold inline-block shadow-sm ${post.platform === 'Facebook' ? 'bg-blue-100 text-blue-700' : post.platform === 'Instagram' ? 'bg-pink-100 text-pink-700' : post.platform === 'LINE@' ? 'bg-green-100 text-green-700' : post.platform === 'Threads' ? 'bg-gray-800 text-white' : 'bg-red-100 text-red-700'}`}>{ICONS.platforms[post.platform]} {post.platform}</span>
                                                            </td>
                                                            <td className="p-4 text-sm">
                                                                <div className="font-bold text-gray-800 mb-1">{post.topic}</div>
                                                                <div className="flex items-center space-x-1 mb-1"><span className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">{post.postType}</span>{post.postSubType && <span className="text-xs bg-yellow-100 text-yellow-800 px-1.5 py-0.5 rounded">{post.postSubType}</span>}</div>
                                                                <div className="text-[10px] text-gray-400 flex space-x-1">
                                                                    <span className="bg-blue-50 text-blue-600 px-1.5 rounded">{post.postPurpose}</span>
                                                                    <span className="bg-purple-50 text-purple-600 px-1.5 rounded">{post.postFormat}</span>
                                                                </div>
                                                            </td>
                                                            <td className="p-4 text-xs text-gray-600">
                                                                {post.projectOwner && <div className="mb-0.5"><span className="text-gray-400 bg-gray-100 px-1 rounded mr-1">專案</span>{post.projectOwner}</div>}
                                                                <div className="mb-0.5"><span className="text-gray-400 bg-gray-100 px-1 rounded mr-1">貼文</span>{post.postOwner}</div>
                                                                {post.designer && <div><span className="text-gray-400 bg-gray-100 px-1 rounded mr-1">美編</span>{post.designer}</div>}
                                                            </td>
                                                            <td className="p-4 text-sm">
                                                                <span className={`px-2 py-1 rounded text-xs font-bold border block w-fit mb-1 ${post.status === 'published' ? 'bg-green-100 text-green-700 border-green-200' : post.status === 'planned' ? 'bg-blue-100 text-blue-700 border-blue-200' : 'bg-gray-100 text-gray-500 border-gray-200'}`}>
                                                                    {ICONS.status[post.status]} {post.status === 'published' ? '已發布' : post.status === 'planned' ? '已排程' : '草稿'}
                                                                </span>
                                                            </td>
                                                            <td className="p-4 text-sm">{post.status === 'published' ? <span className={`text-xs px-2 py-1 rounded-lg border font-bold ${perf.color} ${perf.bg || 'bg-white'}`}>{perf.label}</span> : <span className="text-xs text-gray-300 italic">...</span>}</td>
                                                            
                                                            {/* 7 Days Column */}
                                                            <td className="p-4 text-sm text-right">
                                                                {post.status === 'published' ? (
                                                                    <div className="text-gray-600 text-xs">
                                                                        {post.platform === 'LINE@' || post.postFormat === '限動' || post.postFormat === '留言處' ? '-' : (
                                                                            dueStatus7d?.isDue ? 
                                                                            <span className="text-red-500 font-bold bg-red-50 px-2 py-1 rounded border border-red-200 flex flex-col items-center animate-pulse-slow">
                                                                                <span className="mb-0.5">🔔 請填</span>
                                                                                <span className="text-[10px]">{dueStatus7d.date.slice(5).replace('-','/')}</span>
                                                                            </span> :
                                                                            <><div className="mb-0.5">{(m7.reach || 0).toLocaleString()}</div><div className="text-blue-500 mt-1 font-bold">{engage7d.toLocaleString()}</div></>
                                                                        )}
                                                                    </div>
                                                                ) : '-'}
                                                            </td>
                                                            <td className="p-4 text-sm text-right text-blue-600 font-bold">{post.status === 'published' ? rate7d : '-'}</td>
                                                            
                                                            {/* 1 Month Column */}
                                                            <td className="p-4 text-sm text-right">
                                                                {post.status === 'published' ? (
                                                                    <div className="text-gray-600 text-xs">
                                                                        {post.platform === 'LINE@' || post.postFormat === '限動' || post.postFormat === '留言處' ? '-' : (
                                                                            dueStatus1m?.isDue ? 
                                                                            <span className="text-red-500 font-bold bg-red-50 px-2 py-1 rounded border border-red-200 flex flex-col items-center animate-pulse-slow">
                                                                                <span className="mb-0.5">🔔 請填</span>
                                                                                <span className="text-[10px]">{dueStatus1m.date.slice(5).replace('-','/')}</span>
                                                                            </span> :
                                                                             <><div className="mb-0.5">{(m1.reach || 0).toLocaleString()}</div><div className="text-purple-500 mt-1 font-bold">{engage1m.toLocaleString()}</div></>
                                                                        )}
                                                                    </div>
                                                                ) : '-'}
                                                            </td>
                                                            <td className="p-4 text-sm text-right text-purple-600 font-bold">{post.status === 'published' ? rate1m : '-'}</td>
                                                            <td className="p-4 text-center">
                                                                <div className="flex justify-center space-x-1">
                                                                    <button onClick={() => handleEditClick(post)} className="text-gray-400 hover:text-blue-500 hover:bg-blue-50 p-2 rounded-lg transition-colors text-lg" title="編輯">{ICONS.ui.edit}</button>
                                                                    <button onClick={() => triggerDeletePost(post.id)} className="text-gray-400 hover:text-red-500 hover:bg-red-50 p-2 rounded-lg transition-colors text-lg" title="刪除">{ICONS.ui.delete}</button>
                                                                </div>
                                                            </td>
                                                        </tr>
                                                    );
                                                })}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === 'analytics' && (
                            <div className="space-y-6">
                                {/* Analytics Header */}
                                <div className="flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0">
                                    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100 rounded-2xl p-4 flex flex-col md:flex-row items-start md:items-center text-sm shadow-sm">
                                        <span className="font-bold text-blue-700 flex items-center mr-4"><span className="mr-2 text-xl">{ICONS.ui.calendar}</span> {filterType === 'month' ? selectedMonth : `${customRange.start} ~ ${customRange.end}`}</span>
                                        <span className="font-bold text-indigo-700 flex items-center mr-4 mt-1 md:mt-0"><span className="mr-2 text-xl">{ICONS.ui.filter}</span> {filterPlatform === 'All' ? '全部平台' : filterPlatform}</span>
                                        <span className="text-blue-400 text-xs hidden md:inline ml-2 bg-white px-2 py-1 rounded-full shadow-sm">數據統計以 {analyticsPeriod === '7d' ? '7天' : '一個月'} 成效為主</span>
                                        
                                        {/* Purpose Filter Selector */}
                                        <div className="flex items-center bg-white rounded-lg border border-indigo-100 p-1 ml-0 md:ml-4 mt-2 md:mt-0">
                                            <button 
                                                onClick={() => setFilterPurposeCategory('All')}
                                                className={`px-3 py-1 text-xs font-bold rounded-md transition-colors flex items-center ${filterPurposeCategory === 'All' ? 'bg-indigo-100 text-indigo-600' : 'text-gray-400 hover:text-gray-600'}`}
                                            >
                                                全部
                                            </button>
                                            <button 
                                                onClick={() => setFilterPurposeCategory('Ad')}
                                                className={`px-3 py-1 text-xs font-bold rounded-md transition-colors flex items-center ${filterPurposeCategory === 'Ad' ? 'bg-yellow-100 text-yellow-600' : 'text-gray-400 hover:text-gray-600'}`}
                                            >
                                                💰 廣告類
                                            </button>
                                            <button 
                                                onClick={() => setFilterPurposeCategory('NonAd')}
                                                className={`px-3 py-1 text-xs font-bold rounded-md transition-colors flex items-center ${filterPurposeCategory === 'NonAd' ? 'bg-green-100 text-green-600' : 'text-gray-400 hover:text-gray-600'}`}
                                            >
                                                💬 非廣告
                                            </button>
                                        </div>
                                    </div>

                                    <div className="flex items-center space-x-3">
                                        <div className="flex items-center bg-white rounded-lg border border-gray-200 p-1">
                                            <button 
                                                onClick={() => setAnalyticsPeriod('7d')}
                                                className={`px-3 py-1 text-xs font-bold rounded-md transition-colors flex items-center ${analyticsPeriod === '7d' ? 'bg-blue-100 text-blue-600' : 'text-gray-400 hover:text-gray-600'}`}
                                            >
                                                <span className="mr-1">🔥</span> 7天
                                            </button>
                                            <button 
                                                onClick={() => setAnalyticsPeriod('1m')}
                                                className={`px-3 py-1 text-xs font-bold rounded-md transition-colors flex items-center ${analyticsPeriod === '1m' ? 'bg-purple-100 text-purple-600' : 'text-gray-400 hover:text-gray-600'}`}
                                            >
                                                <span className="mr-1">🌳</span> 一個月
                                            </button>
                                        </div>
                                        <button onClick={() => setShowStandardsConfig(!showStandardsConfig)} className="flex items-center text-sm bg-white border border-gray-200 px-4 py-2.5 rounded-xl hover:bg-gray-50 text-gray-600 shadow-sm transition-all font-bold hover:shadow-md"><span className="mr-2 text-lg">{ICONS.ui.target}</span> {showStandardsConfig ? '隱藏標準' : 'KPI標準'} <span className="ml-2 text-lg">⚙️</span></button>
                                    </div>
                                </div>

                                {/* Standards Panel */}
                                {showStandardsConfig && (
                                    <div className="bg-white p-6 rounded-3xl border border-pink-100 shadow-lg animate-fade-in-down mb-6">
                                        <h4 className="font-bold text-gray-700 mb-4 flex items-center"><span className="mr-2 text-2xl">{ICONS.ui.target}</span> 各平台 KPI 標準設定</h4>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                            <div className="bg-blue-50 p-5 rounded-2xl border border-blue-100"><div className="font-bold text-blue-700 mb-3 text-lg">Facebook (三級制)</div><div className="grid grid-cols-3 gap-3 text-xs text-blue-400 mb-2 font-bold uppercase tracking-wider"><div>等級</div><div>觸及目標</div><div>互動率(%)</div></div>{['high', 'std', 'low'].map(level => (<div key={level} className="grid grid-cols-3 gap-3 mb-2 items-center"><div className="text-xs font-bold text-gray-600 capitalize bg-white py-1 px-2 rounded border border-blue-100 text-center shadow-sm">{level === 'high' ? '🏆 高標' : level === 'std' ? '✅ 標準' : '🤏 低標'}</div><input type="number" value={standards.Facebook[level].reach} onChange={(e) => handleStandardChange('Facebook', [level, 'reach'], e.target.value)} className="p-1.5 border border-blue-200 rounded-lg text-right outline-none focus:ring-2 focus:ring-blue-300" /><input type="number" step="0.1" value={standards.Facebook[level].rate} onChange={(e) => handleStandardChange('Facebook', [level, 'rate'], e.target.value)} className="p-1.5 border border-blue-200 rounded-lg text-right outline-none focus:ring-2 focus:ring-blue-300" /></div>))}</div>
                                            <div className="bg-pink-50 p-5 rounded-2xl border border-pink-100"><div className="font-bold text-pink-700 mb-3 text-lg">Instagram</div><div className="space-y-3"><div className="flex justify-between items-center text-sm bg-white p-2 rounded-xl border border-pink-100 shadow-sm"><span className="text-gray-600 font-bold ml-2">觸及目標</span><input type="number" value={standards.Instagram.reach} onChange={(e) => handleStandardChange('Instagram', ['reach'], e.target.value)} className="w-24 p-1 border border-pink-200 rounded text-right outline-none font-mono text-pink-600" /></div><div className="flex justify-between items-center text-sm bg-white p-2 rounded-xl border border-pink-100 shadow-sm"><span className="text-gray-600 font-bold ml-2">互動數目標</span><input type="number" value={standards.Instagram.engagement} onChange={(e) => handleStandardChange('Instagram', ['engagement'], e.target.value)} className="w-24 p-1 border border-pink-200 rounded text-right outline-none font-mono text-pink-600" /></div><div className="flex justify-between items-center text-sm bg-white p-2 rounded-xl border border-pink-100 shadow-sm"><span className="text-gray-600 font-bold ml-2">互動率(%)</span><input type="number" step="0.1" value={standards.Instagram.rate} onChange={(e) => handleStandardChange('Instagram', ['rate'], e.target.value)} className="w-24 p-1 border border-pink-200 rounded text-right outline-none font-mono text-pink-600" /></div></div></div>
                                            <div className="bg-gray-50 p-5 rounded-2xl border border-gray-200 md:col-span-2"><div className="font-bold text-gray-700 mb-3 text-lg">Threads (歷史標竿)</div><input type="text" value={standards.Threads.note} onChange={(e) => handleStandardChange('Threads', ['note'], e.target.value)} className="w-full p-3 border border-gray-200 rounded-xl text-sm mb-4 text-gray-600 bg-white focus:ring-2 focus:ring-gray-300 outline-none" /><div className="flex space-x-6 text-sm"><div className="flex items-center space-x-2 bg-white px-3 py-2 rounded-lg border shadow-sm"><span>🔥 瀏覽標竿:</span><input type="number" value={standards.Threads.reach} onChange={(e) => handleStandardChange('Threads', ['reach'], e.target.value)} className="w-24 p-1 border-b border-gray-300 text-right outline-none font-bold" /></div><div className="flex items-center space-x-2 bg-white px-3 py-2 rounded-lg border shadow-sm"><span>💬 互動標竿:</span><input type="number" value={standards.Threads.engagement} onChange={(e) => handleStandardChange('Threads', ['engagement'], e.target.value)} className="w-24 p-1 border-b border-gray-300 text-right outline-none font-bold" /></div></div></div>
                                        </div>
                                    </div>
                                )}

                                {/* KPI Cards */}
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    <div className="bg-white p-6 rounded-3xl border border-blue-50 shadow-sm flex items-center justify-between hover:shadow-md transition-shadow"><div><p className="text-sm text-gray-400 font-bold mb-1">已發布貼文 ({filterPurposeCategory === 'Ad' ? '廣告類' : filterPurposeCategory === 'NonAd' ? '非廣告' : '全部'})</p><p className="text-4xl font-bold text-gray-700">{stats.publishedCount}</p></div><div className="bg-blue-50 p-4 rounded-2xl text-blue-500 text-3xl">📝</div></div>
                                    <div className="bg-white p-6 rounded-3xl border border-green-50 shadow-sm flex items-center justify-between hover:shadow-md transition-shadow">
                                        <div>
                                            <p className="text-sm text-gray-400 font-bold mb-1">總觸及 ({analyticsPeriod === '7d' ? '7天' : '一個月'})</p>
                                            <p className="text-4xl font-bold text-gray-700">{(stats.totalReach || 0).toLocaleString()}</p>
                                            <p className="text-xs text-gray-300 mt-2 font-bold bg-gray-50 px-2 py-1 rounded inline-block">不含 Threads/LINE@/限動/留言處</p>
                                        </div>
                                        <div className="bg-green-50 p-4 rounded-2xl text-green-500 text-3xl">{ICONS.metrics.reach}</div>
                                    </div>
                                    <div className="bg-white p-6 rounded-3xl border border-pink-50 shadow-sm flex items-center justify-between hover:shadow-md transition-shadow">
                                        <div>
                                            <p className="text-sm text-gray-400 font-bold mb-1">總互動 ({analyticsPeriod === '7d' ? '7天' : '一個月'})</p>
                                            <p className="text-4xl font-bold text-gray-700">{(stats.totalEngagement || 0).toLocaleString()}</p>
                                            <p className="text-xs text-gray-300 mt-2 font-bold bg-gray-50 px-2 py-1 rounded inline-block">不含 LINE@/限動/留言處</p>
                                        </div>
                                        <div className="bg-pink-50 p-4 rounded-2xl text-pink-500 text-3xl">{ICONS.metrics.likes}</div>
                                    </div>
                                </div>

                                {/* Platform Cards */}
                                <div>
                                    <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center"><span className="mr-2 text-2xl">{ICONS.ui.filter}</span> 各平台成效明細 ({analyticsPeriod === '7d' ? '7天' : '一個月'})</h3>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                                        {platforms.filter(p => p !== 'LINE@').map(platform => {
                                            if (filterPlatform !== 'All' && filterPlatform !== platform) return null;
                                            const data = stats.platformStats[platform];
                                            const hasData = data.total.count > 0;
                                            const isThreads = platform === 'Threads';
                                            const isFB = platform === 'Facebook';
                                            const std = standards[platform];
                                            
                                            const RenderRow = ({ label, icon, stats, isTotal }) => {
                                                const avgReach = stats.count > 0 ? Math.round(stats.reach / stats.count) : 0;
                                                let summaryColor = 'text-gray-700';
                                                
                                                if (isFB && isTotal && hasData && analyticsPeriod === '7d') { 
                                                    if (avgReach >= std.std.reach && stats.rate >= std.std.rate) summaryColor = 'text-green-500 font-bold';
                                                    else if (avgReach < std.low.reach) summaryColor = 'text-red-400 font-bold';
                                                }
                                                return (
                                                    <div className={`grid grid-cols-12 gap-2 text-sm py-3 px-2 ${isTotal ? 'font-bold bg-gray-50 rounded-xl' : 'border-t border-gray-100 text-gray-600'}`}>
                                                        <div className="col-span-3 flex items-center">{icon && <span className="mr-2 text-lg">{icon}</span>}<span>{label}</span></div>
                                                        <div className="col-span-2 text-right text-xs text-gray-400 flex items-center justify-end">{stats.count} 篇</div>
                                                        <div className={`col-span-3 text-right ${summaryColor}`}>{(stats.reach || 0).toLocaleString()}</div>
                                                        <div className="col-span-2 text-right text-pink-400 font-bold">{(stats.engagement || 0).toLocaleString()}</div>
                                                        <div className="col-span-2 text-right text-indigo-500 font-bold bg-indigo-50 rounded px-1">{isThreads ? '-' : `${stats.rate}%`}</div>
                                                    </div>
                                                );
                                            };

                                            return (
                                                <div key={platform} className={`border rounded-3xl overflow-hidden ${hasData ? 'bg-white border-gray-100 shadow-sm' : 'bg-white border-gray-100 opacity-60'}`}>
                                                    <div className="p-5 border-b border-gray-50 bg-white">
                                                        <div className="flex justify-between items-center mb-2"><h4 className="font-bold text-gray-700 flex items-center text-lg">{ICONS.platforms[platform]} {platform}{isThreads && <span className="ml-2 text-xs bg-gray-800 text-white px-2 py-0.5 rounded-full">👀 瀏覽制</span>}</h4></div>
                                                        <div className="text-xs text-gray-500 bg-gray-50 rounded-lg p-2 border border-gray-100">{isFB ? <span>🎯 標準(A): 觸及 {std.std.reach} / 互動率 {std.std.rate}%</span> : isThreads ? <span className="italic">🔥 {std.note}</span> : <span>🎯 目標: 觸及 {std.reach} / 互動 {std.engagement} / 率 {std.rate}%</span>}</div>
                                                    </div>
                                                    <div className="p-4">
                                                        <div className="grid grid-cols-12 gap-2 text-xs font-bold text-gray-300 mb-3 px-2 uppercase tracking-wide"><div className="col-span-3">類別</div><div className="col-span-2 text-right">篇數</div><div className="col-span-3 text-right">{ICONS.metrics.reach}</div><div className="col-span-2 text-right">{ICONS.metrics.likes}</div><div className="col-span-2 text-right">{ICONS.metrics.rate}</div></div>
                                                        <RenderRow label="總成效" stats={data.total} isTotal={true} />
                                                        <RenderRow label="短影音" icon="🎬" stats={data.shortVideo} isTotal={false} />
                                                        <RenderRow label="非短影音" icon="🖼️" stats={data.regular} isTotal={false} />
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>

                                {/* Distribution */}
                                <div>
                                    <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center"><span className="mr-2 text-2xl">🍰</span> 各平台貼文類型分佈</h3>
                                    <div className="bg-white border border-gray-100 rounded-3xl overflow-hidden shadow-sm">
                                        <div className="overflow-x-auto">
                                            <table className="w-full text-left">
                                                <thead>
                                                    <tr className="bg-gray-50 border-b border-gray-100"><th className="p-4 text-sm font-bold text-gray-500 pl-6">平台 / 類型</th>{mainPostTypes.map(type => <th key={type} className="p-4 text-sm font-bold text-gray-500 text-center">{type}</th>)}<th className="p-4 text-sm font-bold text-gray-500 text-center pr-6">總計</th></tr>
                                                </thead>
                                                <tbody className="divide-y divide-gray-50">
                                                    {platforms.map(platform => {
                                                        if (filterPlatform !== 'All' && filterPlatform !== platform) return null;
                                                        const typeCounts = stats.typeDistribution[platform] || {};
                                                        const rowTotal = Object.values(typeCounts).reduce((a, b) => a + b, 0);
                                                        if (rowTotal === 0) return null; 
                                                        return (
                                                            <tr key={platform} className="hover:bg-pink-50 transition-colors">
                                                                <td className="p-4 font-bold text-gray-700 pl-6">{ICONS.platforms[platform]} {platform}</td>
                                                                {mainPostTypes.map(type => {
                                                                    const count = typeCounts[type] || 0;
                                                                    return <td key={type} className="p-4 text-center">{count > 0 ? <span className="inline-block bg-pink-100 text-pink-600 rounded-full px-2.5 py-1 text-xs font-bold min-w-[28px]">{count}</span> : <span className="text-gray-200">-</span>}</td>;
                                                                })}
                                                                <td className="p-4 text-center font-bold text-gray-800 pr-6">{rowTotal}</td>
                                                            </tr>
                                                        );
                                                    })}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </main>
                </div>
            );
        };

        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<SocialScheduler />);
    </script>
</body>
</html>
