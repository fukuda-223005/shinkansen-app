import os
import csv
import random
import time
from flask import Flask, request, session, render_template_string, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key_for_shinkansen')

# ---------------------------------------------------------
# 1. マスターデータ・設定
# ---------------------------------------------------------

CSV_FILENAME = '67-76_hissu_004.csv'

# 駅データ (九州〜北海道まで完全収録！)
STATION_DATA = [
    # --- 九州新幹線 ---
    {"name": "鹿児島中央", "is_nozomi": False}, {"name": "川内", "is_nozomi": False},
    {"name": "出水", "is_nozomi": False}, {"name": "新水俣", "is_nozomi": False},
    {"name": "新八代", "is_nozomi": False}, {"name": "熊本", "is_nozomi": True},
    {"name": "新玉名", "is_nozomi": False}, {"name": "新大牟田", "is_nozomi": False},
    {"name": "筑後船小屋", "is_nozomi": False}, {"name": "久留米", "is_nozomi": False},
    {"name": "新鳥栖", "is_nozomi": False}, {"name": "博多", "is_nozomi": True},
    # --- 山陽・東海道新幹線 ---
    {"name": "小倉", "is_nozomi": True}, {"name": "新下関", "is_nozomi": False},
    {"name": "厚狭", "is_nozomi": False}, {"name": "新山口", "is_nozomi": False},
    {"name": "徳山", "is_nozomi": False}, {"name": "新岩国", "is_nozomi": False},
    {"name": "広島", "is_nozomi": True}, {"name": "東広島", "is_nozomi": False},
    {"name": "三原", "is_nozomi": False}, {"name": "新尾道", "is_nozomi": False},
    {"name": "福山", "is_nozomi": False}, {"name": "新倉敷", "is_nozomi": False},
    {"name": "岡山", "is_nozomi": True}, {"name": "相生", "is_nozomi": False},
    {"name": "姫路", "is_nozomi": False}, {"name": "西明石", "is_nozomi": False},
    {"name": "新神戸", "is_nozomi": True}, {"name": "新大阪", "is_nozomi": True},
    {"name": "京都", "is_nozomi": True}, {"name": "米原", "is_nozomi": False},
    {"name": "岐阜羽島", "is_nozomi": False}, {"name": "名古屋", "is_nozomi": True},
    {"name": "三河安城", "is_nozomi": False}, {"name": "豊橋", "is_nozomi": False},
    {"name": "浜松", "is_nozomi": False}, {"name": "掛川", "is_nozomi": False},
    {"name": "静岡", "is_nozomi": False}, {"name": "新富士", "is_nozomi": False},
    {"name": "三島", "is_nozomi": False}, {"name": "熱海", "is_nozomi": False},
    {"name": "小田原", "is_nozomi": False}, {"name": "新横浜", "is_nozomi": True},
    {"name": "品川", "is_nozomi": True}, {"name": "東京", "is_nozomi": True},
    # --- 東北・北海道新幹線 ---
    {"name": "上野", "is_nozomi": False}, {"name": "大宮", "is_nozomi": True},
    {"name": "宇都宮", "is_nozomi": False}, {"name": "那須塩原", "is_nozomi": False},
    {"name": "新白河", "is_nozomi": False}, {"name": "郡山", "is_nozomi": False},
    {"name": "福島", "is_nozomi": False}, {"name": "白石蔵王", "is_nozomi": False},
    {"name": "仙台", "is_nozomi": True}, {"name": "古川", "is_nozomi": False},
    {"name": "くりこま高原", "is_nozomi": False}, {"name": "一ノ関", "is_nozomi": False},
    {"name": "水沢江刺", "is_nozomi": False}, {"name": "北上", "is_nozomi": False},
    {"name": "新花巻", "is_nozomi": False}, {"name": "盛岡", "is_nozomi": True},
    {"name": "いわて沼宮内", "is_nozomi": False}, {"name": "二戸", "is_nozomi": False},
    {"name": "八戸", "is_nozomi": False}, {"name": "七戸十和田", "is_nozomi": False},
    {"name": "新青森", "is_nozomi": True}, {"name": "奥津軽いまべつ", "is_nozomi": False},
    {"name": "木古内", "is_nozomi": False}, {"name": "新函館北斗", "is_nozomi": True}
]

# 名所データ (出現する区間の「開始駅インデックス」をキーにする)
LANDMARK_DATA = {
    0: { # 鹿児島中央 -> 川内
        "name": "桜島",
        "svg": '<path fill="#FF8C00" d="M100,200 Q200,50 300,200 L400,250 L0,250 Z" opacity="0.8"/><circle cx="200" cy="50" r="10" fill="#FFF" opacity="0.5"><animate attributeName="cy" from="50" to="20" dur="2s" repeatCount="indefinite"/><animate attributeName="opacity" values="0.5;0;0.5" dur="2s" repeatCount="indefinite"/></circle>',
        "desc": "雄大な桜島の噴煙"
    },
    25: { # 相生 -> 姫路 (姫路の手前)
        "name": "姫路城",
        "svg": '<path fill="#EEE" d="M150,200 L150,150 L250,150 L250,200 Z M120,150 L280,150 L200,80 Z M190,80 L210,80 L200,60 Z" stroke="#333" stroke-width="2"/>',
        "desc": "白鷺城の美しさ"
    },
    30: { # 京都 -> 米原 (京都出発直後)
        "name": "五重塔",
        "svg": '<g fill="#8B4513"><rect x="180" y="50" width="40" height="150"/><path d="M150,90 L250,90 L200,60 Z"/><path d="M140,120 L260,120 L200,90 Z"/><path d="M130,150 L270,150 L200,120 Z"/><path d="M120,180 L280,180 L200,150 Z"/><path d="M110,210 L290,210 L200,180 Z"/></g>',
        "desc": "古都のシンボル"
    },
    38: { # 静岡 -> 新富士
        "name": "富士山",
        "svg": '<path fill="#FFF" d="M150,100 L250,100 L200,60 Z"/><path fill="#4682B4" d="M50,250 L200,60 L350,250 Z" stroke="none"/><path fill="#FFF" d="M165,105 L200,60 L235,105 Q200,120 165,105 Z"/>',
        "desc": "日本一の霊峰"
    },
    44: { # 品川 -> 東京
        "name": "東京タワー",
        "svg": '<path fill="#FF4500" d="M180,250 L220,250 L200,50 Z"/><rect x="190" y="100" width="20" height="10" fill="#FFF"/><rect x="185" y="180" width="30" height="10" fill="#FFF"/>',
        "desc": "首都のランドマーク"
    },
    53: { # 白石蔵王 -> 仙台 (松島付近)
        "name": "松島",
        "svg": '<rect x="0" y="200" width="400" height="50" fill="#4682B4"/><path fill="#228B22" d="M50,210 Q70,180 90,210 Z M150,220 Q180,170 210,220 Z M300,210 Q320,190 340,210 Z"/>',
        "desc": "日本三景の島々"
    },
    66: { # 奥津軽いまべつ -> 木古内 (青函トンネル)
        "name": "青函トンネル",
        "svg": '<rect x="0" y="0" width="1000" height="1000" fill="#111"/><circle cx="200" cy="150" r="10" fill="#FFFF00" opacity="0.5"><animate attributeName="opacity" values="0.5;1;0.5" dur="0.5s" repeatCount="indefinite"/></circle>',
        "desc": "海底の大動脈",
        "is_tunnel": True
    },
    67: { # 木古内 -> 新函館北斗 (函館山)
        "name": "函館山",
        "svg": '<path fill="#000" d="M50,250 Q200,100 350,250 Z" opacity="0.8"/><circle cx="100" cy="50" r="2" fill="white" /><circle cx="200" cy="80" r="2" fill="white" /><circle cx="300" cy="40" r="2" fill="white" />',
        "desc": "100万ドルの夜景"
    }
}

# ---------------------------------------------------------
# 2. データ読み込みロジック
# ---------------------------------------------------------

def load_questions():
    questions = []
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, CSV_FILENAME)
    
    try:
        with open(csv_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header = next(reader)
            for row in reader:
                if len(row) < 11: continue
                q_data = {
                    "id": row[3],
                    "question": row[4],
                    "options": [row[5], row[6], row[7], row[8], row[9]],
                    "answer_idx": int(row[10])
                }
                questions.append(q_data)
    except Exception as e:
        error_msg = f"エラー発生: {str(e)} (Path: {csv_path})"
        print(error_msg)
        questions = [{"id": "ERROR", "question": error_msg, "options": ["-"]*5, "answer_idx": 1}]
    return questions

ALL_QUESTIONS = load_questions()

# ---------------------------------------------------------
# 3. HTMLテンプレート
# ---------------------------------------------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>新幹線でGO! 日本縦断完走ドリル</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Zen+Kaku+Gothic+New:wght@500;700&display=swap');
        
        body { font-family: 'Zen Kaku Gothic New', sans-serif; overflow: hidden; background: #1a1a1a; }
        .digital-font { font-family: 'Share Tech Mono', monospace; }
        
        /* 車窓アニメーション */
        .window-view {
            background: linear-gradient(to bottom, #87CEEB 0%, #E0F6FF 80%, #90EE90 100%);
            position: relative;
            overflow: hidden;
            transition: background 1s ease;
        }
        .weather-rainy { background: linear-gradient(to bottom, #4a5568 0%, #718096 80%, #2d3748 100%) !important; }
        .weather-tunnel { background: #000 !important; }

        .scenery-layer {
            position: absolute;
            bottom: 0; left: 0; width: 200%; height: 100%;
            background-repeat: repeat-x; background-position: bottom left;
            animation: moveScenery linear infinite;
        }
        .landmark-layer {
            position: absolute; bottom: 20px; right: -300px;
            width: 300px; height: 300px; pointer-events: none;
        }
        @keyframes flowLandmark { 0% { transform: translateX(0); } 100% { transform: translateX(-150vw); } }
        
        .layer-mountains {
            background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 300"><path fill="%23A0C0A0" d="M0,300 L200,100 L400,300 Z M300,300 L500,50 L700,300 Z M600,300 L800,150 L1000,300 Z"/></svg>');
            background-size: 50% 60%; animation-duration: 60s;
        }
        .layer-buildings {
            background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 100"><rect x="50" y="50" width="30" height="50" fill="%23666" /><rect x="150" y="20" width="40" height="80" fill="%23777" /><rect x="300" y="40" width="20" height="60" fill="%23555" /><path d="M400,0 L410,100" stroke="%23333" stroke-width="2"/></svg>');
            background-size: 50% 40%; animation-duration: 5s; 
        }
        .rain-effect {
            position: absolute; inset: 0;
            background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20"><path d="M10,0 L10,10" stroke="rgba(255,255,255,0.5)" stroke-width="1"/></svg>');
            animation: rain 0.5s linear infinite; opacity: 0; pointer-events: none;
        }
        @keyframes rain { 0% { background-position: 0 0; } 100% { background-position: -5px 20px; } }
        @keyframes moveScenery { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }

        .cockpit-frame {
            background: linear-gradient(180deg, #2d3748 0%, #1a202c 100%);
            box-shadow: inset 0 2px 10px rgba(0,0,0,0.5);
            border-top: 4px solid #4a5568;
        }
        .glass-panel {
            background: rgba(10, 20, 30, 0.85);
            border: 1px solid #4a5568;
            box-shadow: 0 0 15px rgba(66, 153, 225, 0.1);
            backdrop-filter: blur(2px);
        }
    </style>
</head>
<body class="text-white h-screen flex flex-col">

    <!-- 1. フロントガラス -->
    <div class="window-view flex-grow relative" id="windowView">
        <div class="scenery-layer layer-mountains" id="layerMountains"></div>
        <div class="scenery-layer layer-buildings" id="layerBuildings"></div>
        {% if landmark %}
        <div class="landmark-layer flex flex-col items-center" id="landmarkLayer" style="animation: flowLandmark 15s linear infinite;">
            <div class="transform scale-150">{{ landmark.svg | safe }}</div>
        </div>
        {% endif %}
        <div class="rain-effect" id="rainEffect"></div>
        <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent opacity-0" id="speedEffect"></div>
        
        <div id="landmarkGet" class="absolute top-10 right-10 transform translate-x-full transition-transform duration-500 bg-yellow-400 text-slate-900 p-3 rounded-l-xl shadow-xl border-2 border-white z-30">
            <div class="flex items-center gap-2"><span class="text-2xl">📸</span><div><div class="text-xs font-bold text-slate-700">名所ゲット!</div><div class="font-black text-lg">{{ landmark.name if landmark else '' }}</div></div></div>
        </div>

        {% if state == 'menu' %}
        <div class="absolute inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm z-20">
            <div class="bg-white/90 text-slate-900 p-8 rounded-2xl shadow-2xl max-w-lg text-center border-4 border-blue-600 overflow-y-auto max-h-[90vh]">
                <h1 class="text-3xl font-black mb-2 text-blue-800 tracking-tighter italic transform -skew-x-6">SHINKANSEN GO!</h1>
                <p class="font-bold text-slate-600 mb-6">日本縦断・国試必須問題ドリル</p>
                <form action="/start" method="post" class="space-y-4 mb-8">
                    <button name="mode" value="shinkansen" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-6 rounded shadow-lg transform transition hover:scale-105">
                        <div>各駅停車モード (7問/区間)</div>
                        <div class="text-xs opacity-75 font-normal">じっくり確実に進むならこちら</div>
                    </button>
                    <button name="mode" value="nozomi" class="w-full bg-yellow-500 hover:bg-yellow-400 text-slate-900 font-bold py-3 px-6 rounded shadow-lg transform transition hover:scale-105">
                        <div>超特急のぞみモード (28問/区間)</div>
                        <div class="text-xs opacity-75 font-normal">大量の問題を高速処理！</div>
                    </button>
                </form>
                <div class="border-t border-slate-300 pt-4">
                    <h3 class="text-sm font-bold text-slate-500 mb-3">旅の思い出コレクション</h3>
                    <div class="grid grid-cols-4 gap-2">
                        {% for l_id, l_data in all_landmarks.items() %}
                            <div class="aspect-square rounded border {{ 'bg-yellow-100 border-yellow-400' if l_id|string in collected else 'bg-slate-200 border-slate-300' }} flex flex-col items-center justify-center p-1">
                                {% if l_id|string in collected %}
                                    <div class="w-8 h-8 overflow-hidden">{{ l_data.svg | safe }}</div>
                                    <div class="text-[10px] font-bold mt-1 text-slate-800">{{ l_data.name }}</div>
                                {% else %}<div class="text-2xl text-slate-400">🔒</div>{% endif %}
                            </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
        {% endif %}
    </div>

    <!-- 2. コックピット -->
    <div class="cockpit-frame h-1/2 min-h-[400px] flex flex-col p-2 relative z-10">
        <div class="flex justify-between items-center px-4 py-2 bg-black/40 rounded mb-2 border border-slate-600">
            <div class="flex items-center gap-4">
                <div class="text-xs text-slate-400">MODE</div>
                <div class="text-yellow-400 font-bold tracking-widest">{{ mode_label|default('WAITING') }}</div>
            </div>
            <div class="flex items-center gap-4">
                <div class="text-xs text-slate-400">PROGRESS</div>
                <div class="digital-font text-xl text-green-400">{{ total_answered|default(0) }} / {{ total_questions }} 問</div>
            </div>
        </div>

        <div class="flex flex-grow gap-2">
            <!-- 左パネル -->
            <div class="w-1/3 glass-panel rounded-lg p-2 flex flex-col relative">
                <div class="text-xs text-blue-300 mb-1 border-b border-blue-900/50 pb-1">STATUS MONITOR</div>
                <div class="mb-4">
                    <div class="text-[10px] text-slate-400">NEXT STATION</div>
                    <div class="text-xl font-bold text-white truncate">{{ next_station|default('---') }}</div>
                    <div class="w-full bg-slate-700 h-1 mt-1 rounded"><div class="bg-green-500 h-1 rounded" style="width: {{ progress|default(0) }}%"></div></div>
                </div>
                <div class="flex-grow flex items-center justify-center relative">
                    <canvas id="speedometer" width="200" height="200" class="max-w-full max-h-full"></canvas>
                    <div class="absolute bottom-0 text-center">
                        <div class="digital-font text-4xl text-cyan-400" id="speedDisplay">0</div>
                        <div class="text-[10px] text-slate-500">km/h</div>
                    </div>
                </div>
                <div class="absolute top-2 right-2 text-xs" id="weatherIcon">☀️</div>
            </div>

            <!-- 右パネル -->
            <div class="w-2/3 glass-panel rounded-lg p-4 flex flex-col relative monitor-scanline">
                {% if state == 'quiz' %}
                    <div class="flex-grow flex flex-col justify-center">
                        <div class="text-blue-300 text-xs mb-2 font-mono">ID: {{ question.id }}</div>
                        <h2 class="text-lg md:text-xl font-bold leading-relaxed text-white mb-6 drop-shadow-md">{{ question.question }}</h2>
                        <form action="/answer" method="post" class="grid grid-cols-1 gap-2 overflow-y-auto max-h-[200px] pr-2 custom-scrollbar">
                            <input type="hidden" name="client_speed" id="clientSpeedInput" value="0">
                            <input type="hidden" name="got_landmark" id="gotLandmarkInput" value="0">
                            {% for opt in question.options %}
                            <button name="choice" value="{{ loop.index }}" onclick="submitAnswer(this)" class="w-full bg-slate-800/80 hover:bg-blue-600/50 border border-slate-600 hover:border-blue-400 text-left px-4 py-3 rounded text-sm transition-all duration-200 group">
                                <span class="text-blue-400 mr-2 group-hover:text-white">[{{ loop.index }}]</span>{{ opt }}
                            </button>
                            {% endfor %}
                        </form>
                    </div>
                {% elif state == 'judgement' %}
                     <div class="flex-grow flex flex-col items-center justify-center text-center">
                        {% if is_correct %}
                            <div class="text-green-400 text-6xl font-black mb-4 tracking-tighter drop-shadow-[0_0_10px_rgba(74,222,128,0.5)]">CLEAR</div>
                            <div class="text-blue-200">加速します！</div>
                        {% else %}
                            <div class="text-red-500 text-6xl font-black mb-4 tracking-tighter">WARNING</div>
                            <div class="text-xl font-bold text-white">{{ correct_answer_text }}</div>
                             <!-- 追試メッセージ追加 -->
                            <div class="text-yellow-300 text-sm mt-2 font-bold animate-pulse">※この問題は再出題されます</div>
                        {% endif %}
                        <div class="mt-8"><form action="/next" method="post"><button class="bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 px-8 rounded animate-pulse">RESUME</button></form></div>
                    </div>
                {% elif state == 'station_arrival' %}
                    <div class="flex-grow flex flex-col items-center justify-center">
                        <div class="text-4xl font-bold text-yellow-400 mb-2">{{ current_station }} ARRIVED</div>
                        <div class="text-slate-400 mb-6">区間運行完了</div>
                        <form action="/depart" method="post" class="mt-8"><button class="bg-green-600 hover:bg-green-500 text-white py-3 px-8 rounded font-bold">次駅へ出発</button></form>
                    </div>
                {% elif state == 'goal' %}
                     <div class="flex-grow flex flex-col items-center justify-center">
                        <div class="text-5xl font-black text-yellow-400 mb-4">MISSION COMPLETE</div>
                        <div class="text-xl text-white mb-2">全問走破＆新函館北斗駅 到着</div>
                        <div class="text-lg text-slate-300 mb-8">最終スコア: {{ score }} / {{ total_answered }} 問正解</div>
                        <a href="/" class="bg-slate-700 hover:bg-slate-600 text-white py-2 px-6 rounded">タイトルへ戻る</a>
                     </div>
                {% endif %}
            </div>
        </div>
    </div>
    <script>
        const canvas = document.getElementById('speedometer');
        const ctx = canvas ? canvas.getContext('2d') : null;
        let currentSpeed = {{ current_speed|default(0) }}, targetSpeed = {{ current_speed|default(0) }};
        const hasLandmark = {{ 'true' if landmark else 'false' }};
        const isTunnel = {{ 'true' if landmark and landmark.is_tunnel else 'false' }};
        let landmarkCollected = false;

        function drawSpeedometer() {
            if (!ctx) return;
            ctx.clearRect(0, 0, 200, 200);
            const cx = 100, cy = 100, radius = 80;
            ctx.beginPath(); ctx.arc(cx, cy, radius, 0.75 * Math.PI, 2.25 * Math.PI); ctx.lineWidth = 10; ctx.strokeStyle = '#1e293b'; ctx.stroke();
            const maxSpeed = 350;
            const speedAngle = (0.75 + (1.5 * (currentSpeed / maxSpeed))) * Math.PI;
            ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + Math.cos(speedAngle)*(radius-10), cy + Math.sin(speedAngle)*(radius-10)); ctx.lineWidth = 4; ctx.strokeStyle = '#facc15'; ctx.stroke();
            const display = document.getElementById('speedDisplay'); if(display) display.innerText = Math.round(currentSpeed);
            updateEnvironment(currentSpeed);
        }

        function updateEnvironment(speed) {
            const windowView = document.getElementById('windowView');
            const rainEffect = document.getElementById('rainEffect');
            const weatherIcon = document.getElementById('weatherIcon');
            const landmarkLayer = document.getElementById('landmarkLayer');
            const landmarkNotify = document.getElementById('landmarkGet');
            const inputGotLandmark = document.getElementById('gotLandmarkInput');

            if (isTunnel) {
                windowView.classList.add('weather-tunnel'); if(weatherIcon) weatherIcon.innerText = "🚇";
            } else {
                if (speed < 100) {
                    windowView.classList.add('weather-rainy'); rainEffect.style.opacity = 1; if(weatherIcon) weatherIcon.innerText = "☔️";
                    if(landmarkLayer) landmarkLayer.style.opacity = 0.2;
                } else {
                    windowView.classList.remove('weather-rainy'); rainEffect.style.opacity = 0; if(weatherIcon) weatherIcon.innerText = "☀️";
                    if(landmarkLayer) landmarkLayer.style.opacity = 1;
                    if (hasLandmark && !landmarkCollected && speed > 200) {
                        landmarkCollected = true;
                        if(landmarkNotify) landmarkNotify.classList.remove('translate-x-full');
                        if(inputGotLandmark) inputGotLandmark.value = "1";
                        setTimeout(() => { if(landmarkNotify) landmarkNotify.classList.add('translate-x-full'); }, 3000);
                    }
                }
            }
        }

        function animate() {
            if (Math.abs(targetSpeed - currentSpeed) > 1) currentSpeed += (targetSpeed - currentSpeed) * 0.1; else currentSpeed = targetSpeed;
            drawSpeedometer(); requestAnimationFrame(animate);
        }
        setInterval(() => {
             const mt = document.getElementById('layerMountains'), bd = document.getElementById('layerBuildings'), se = document.getElementById('speedEffect');
             if(!mt) return;
             if(currentSpeed < 5) { mt.style.animationPlayState = 'paused'; bd.style.animationPlayState = 'paused'; se.style.opacity = 0; }
             else { mt.style.animationPlayState = 'running'; bd.style.animationPlayState = 'running'; se.style.opacity = Math.min((currentSpeed - 100) / 200, 0.5);
                 const factor = 300 / Math.max(currentSpeed, 10); bd.style.animationDuration = (0.5 * factor) + 's'; }
        }, 100);
        if (ctx) animate();
        function submitAnswer(btn) { document.getElementById('clientSpeedInput').value = Math.round(currentSpeed); btn.innerHTML = "TRANSMITTING..."; }
    </script>
</body>
</html>
"""

# ---------------------------------------------------------
# 4. ルーティング & ゲームロジック
# ---------------------------------------------------------

@app.route('/')
def index():
    collected = session.get('collected_landmarks', [])
    return render_template_string(HTML_TEMPLATE, state='menu', current_speed=0, all_landmarks=LANDMARK_DATA, collected=collected, total_questions=len(ALL_QUESTIONS))

@app.route('/start', methods=['POST'])
def start_game():
    mode = request.form.get('mode')
    session['mode'] = mode
    session['current_station_idx'] = 0
    session['score'] = 0
    session['current_speed'] = 50
    if 'collected_landmarks' not in session: session['collected_landmarks'] = []

    # ★完走型ロジックの核：問題IDの山札（Deck）を作成してシャッフル
    deck = list(range(len(ALL_QUESTIONS)))
    random.shuffle(deck)
    session['question_deck'] = deck
    session['total_answered_count'] = 0 # 累計回答数
    
    set_next_destination(0, mode)
    
    # 最初の区間の問題を取得
    prepare_next_leg_questions()
    
    session['current_quiz_idx'] = 0
    session['question_start_time'] = time.time()
    return redirect(url_for('play'))

def set_next_destination(current_idx, mode):
    next_idx = current_idx + 1
    if mode == 'nozomi':
        for i in range(current_idx + 1, len(STATION_DATA)):
            if STATION_DATA[i]['is_nozomi']: next_idx = i; break
            next_idx = len(STATION_DATA) - 1
    session['next_station_idx'] = next_idx

def prepare_next_leg_questions():
    """山札から次の区間分の問題を取り出す"""
    mode = session.get('mode')
    count = 7 if mode == 'shinkansen' else 28
    
    deck = session.get('question_deck', [])
    
    # デッキから取り出す（足りない場合はあるだけ取り出す）
    num_to_take = min(count, len(deck))
    
    if num_to_take == 0:
        # もう問題がない場合 -> 空リスト
        selected_indices = []
    else:
        selected_indices = deck[:num_to_take]
        session['question_deck'] = deck[num_to_take:] # デッキ更新
        
    # インデックスから実際の問題データを取得
    questions = [ALL_QUESTIONS[i] for i in selected_indices]
    session['quiz_queue'] = questions

@app.route('/play')
def play():
    if 'quiz_queue' not in session: return redirect(url_for('index'))
    queue = session['quiz_queue']
    idx = session['current_quiz_idx']
    
    # 区間クリア判定
    if idx >= len(queue):
        # もしデッキも空なら、ゲームクリア（ゴール）へ
        if len(session.get('question_deck', [])) == 0:
             return render_template_string(HTML_TEMPLATE, state='goal', score=session['score'], total_answered=session['total_answered_count'])
        
        return render_template_string(HTML_TEMPLATE, 
            state='station_arrival',
            current_station=STATION_DATA[session['next_station_idx']]['name'],
            score=session['score'], current_speed=0, total_questions=len(ALL_QUESTIONS), total_answered=session['total_answered_count']
        )
    
    current_st_idx = session['current_station_idx']
    landmark = LANDMARK_DATA.get(current_st_idx)
    session['question_start_time'] = time.time()
    
    return render_template_string(HTML_TEMPLATE,
        state='quiz',
        question=queue[idx],
        mode_label="各駅停車" if session['mode'] == 'shinkansen' else "超特急のぞみ",
        current_station=STATION_DATA[current_st_idx]['name'],
        next_station=STATION_DATA[session['next_station_idx']]['name'],
        score=session['score'],
        progress=(idx / len(queue)) * 100,
        current_speed=session.get('current_speed', 100),
        landmark=landmark,
        total_questions=len(ALL_QUESTIONS),
        total_answered=session['total_answered_count'] + 1
    )

@app.route('/answer', methods=['POST'])
def answer():
    choice = int(request.form.get('choice'))
    client_speed = int(request.form.get('client_speed', 0))
    got_landmark_flag = request.form.get('got_landmark', '0')
    queue = session['quiz_queue']
    idx = session['current_quiz_idx']
    current_q = queue[idx]
    
    elapsed = time.time() - session.get('question_start_time', time.time())
    is_correct = (choice == current_q['answer_idx'])
    current_speed = client_speed
    
    if is_correct:
        session['score'] += 1
        speed_bonus = max(10, 50 - (elapsed * 2))
        current_speed = min(320, current_speed + speed_bonus)
    else:
        current_speed = max(30, current_speed - 50)
        # ★ 不正解なら問題をキューの末尾に追加（再出題）
        queue.append(current_q)
        session['quiz_queue'] = queue
    
    session['current_speed'] = current_speed
    session['total_answered_count'] += 1 # 回答済みカウントアップ

    landmark_info = LANDMARK_DATA.get(session['current_station_idx'])
    if landmark_info and got_landmark_flag == "1":
        collected = session.get('collected_landmarks', [])
        l_id = str(session['current_station_idx'])
        if l_id not in collected:
            collected.append(l_id)
            session['collected_landmarks'] = collected

    return render_template_string(HTML_TEMPLATE,
        state='judgement',
        is_correct=is_correct,
        correct_answer_text=current_q['options'][current_q['answer_idx']-1],
        current_speed=current_speed,
        total_questions=len(ALL_QUESTIONS),
        total_answered=session['total_answered_count']
    )

@app.route('/next', methods=['POST'])
def next_question():
    session['current_quiz_idx'] += 1
    return redirect(url_for('play'))

@app.route('/depart', methods=['POST'])
def depart():
    current_idx = session['next_station_idx']
    session['current_station_idx'] = current_idx
    
    # 終点チェック or 問題切れチェック
    deck_is_empty = (len(session.get('question_deck', [])) == 0)
    
    if current_idx >= len(STATION_DATA) - 1 or deck_is_empty:
        return render_template_string(HTML_TEMPLATE, state='goal', score=session['score'], total_answered=session['total_answered_count'])
    
    set_next_destination(current_idx, session['mode'])
    
    # 次の問題セット補充（デッキから引く）
    prepare_next_leg_questions()
    
    session['current_quiz_idx'] = 0
    session['current_speed'] = 100
    return redirect(url_for('play'))

if __name__ == '__main__':
    app.run(debug=True)