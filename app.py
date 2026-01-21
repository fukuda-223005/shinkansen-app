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
                        <div class="pointer-events-none">各駅停車モード (7問/区間)</div>
                        <div class="text-xs opacity-75 font-normal pointer-events-none">じっくり確実に進むならこちら</div>
                    </button>
                    <button name="mode" value="nozomi" class="w-full bg-yellow-500 hover:bg-yellow-400 text-slate-900 font-bold py-3 px-6 rounded shadow-lg transform transition hover:scale-105">
                        <div class="pointer-events-none">超特急のぞみモード (28問/区間)</div>
                        <div class="text-xs opacity-75 font-normal pointer-events-none">大量の問題を高速処理！</div>
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
    <div class="cockpit-frame h-1/2 min-h-[400px] flex flex-col p-2 relative z-