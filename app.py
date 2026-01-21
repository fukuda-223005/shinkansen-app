import os
import csv
import random
from flask import Flask, request, session, render_template_string, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key_for_shinkansen')

# ---------------------------------------------------------
# 1. マスターデータ・設定
# ---------------------------------------------------------

CSV_FILENAME = '67-76_hissu_004.csv'

# 駅データ (ID, 駅名, のぞみ停車フラグ)
STATION_DATA = [
    {"name": "鹿児島中央", "is_nozomi": False}, {"name": "川内", "is_nozomi": False},
    {"name": "出水", "is_nozomi": False}, {"name": "新水俣", "is_nozomi": False},
    {"name": "新八代", "is_nozomi": False}, {"name": "熊本", "is_nozomi": True},
    {"name": "新玉名", "is_nozomi": False}, {"name": "新大牟田", "is_nozomi": False},
    {"name": "筑後船小屋", "is_nozomi": False}, {"name": "久留米", "is_nozomi": False},
    {"name": "新鳥栖", "is_nozomi": False}, {"name": "博多", "is_nozomi": True},
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
    {"name": "品川", "is_nozomi": True}, {"name": "東京", "is_nozomi": True}
]

# ---------------------------------------------------------
# 2. データ読み込みロジック (修正版)
# ---------------------------------------------------------

def load_questions():
    """CSVファイルから問題を読み込む"""
    questions = []
    
    # 【修正1】絶対パスを取得して、確実にファイルを見つけられるようにする
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, CSV_FILENAME)
    
    try:
        # 【修正2】先輩の情報に合わせて 'utf-8' に変更
        # 'utf-8-sig' にしておくと、万が一BOM付き(Excel保存など)でも対応できるので最強です
        with open(csv_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header = next(reader) # ヘッダーをスキップ
            
            for row in reader:
                if len(row) < 11: continue # データ不足行はスキップ
                
                # CSVのカラム位置に合わせてデータを抽出
                q_data = {
                    "id": row[3],
                    "question": row[4],
                    "options": [row[5], row[6], row[7], row[8], row[9]],
                    "answer_idx": int(row[10]) # 1~5の数値
                }
                questions.append(q_data)
                
    except Exception as e:
        # 【デバッグ用】エラー内容を画面に出すように変更
        # これで何が起きているか一目瞭然です！
        error_msg = f"エラー発生: {str(e)} (Path: {csv_path})"
        print(error_msg)
        questions = [{
            "id": "ERROR", 
            "question": error_msg, 
            "options": ["再読み込み", "設定確認", "パス確認", "コード確認", "ログ確認"], 
            "answer_idx": 1
        }]
        
    return questions

# アプリ起動時にデータをメモリにロード
ALL_QUESTIONS = load_questions()

# ---------------------------------------------------------
# 3. HTMLテンプレート (Tailwind CSS使用)
# ---------------------------------------------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>新幹線でGO! 日本縦断・国試必須問題ドリル</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-100 text-slate-800 font-sans min-h-screen">

    <div class="max-w-md mx-auto bg-white min-h-screen shadow-2xl relative">
        
        <!-- ヘッダー -->
        {% if state != 'menu' %}
        <div class="bg-blue-600 text-white p-4 sticky top-0 z-10 shadow-md">
            <div class="flex justify-between items-center">
                <div class="text-sm font-bold flex items-center gap-2">
                    <span class="bg-yellow-400 text-blue-900 px-2 py-0.5 rounded text-xs">{{ mode_label }}</span>
                    {{ current_station }} → {{ next_station }}
                </div>
                <div class="text-sm">正解: {{ score }}問</div>
            </div>
            <div class="w-full bg-blue-800 h-1 mt-2 rounded-full">
                <div class="bg-yellow-400 h-1 rounded-full" style="width: {{ progress }}%"></div>
            </div>
        </div>
        {% endif %}

        <main class="p-4">
            
            <!-- 1. メニュー画面 -->
            {% if state == 'menu' %}
            <div class="text-center py-10">
                <div class="flex justify-center mb-6 text-blue-600">
                    <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="16" height="16" x="4" y="4" rx="2"/><path d="M4 11h16"/><path d="M12 4v16"/><path d="m8 8 2 2-2 2"/><path d="m16 8-2 2 2 2"/></svg>
                </div>
                <h1 class="text-2xl font-bold mb-2 text-blue-900">新幹線でGO!<br>日本縦断<br>国試必須問題ドリル</h1>
                <p class="text-slate-500 mb-8 text-sm">全493問の旅へ出発進行！</p>
                
                <form action="/start" method="post" class="space-y-4">
                    <button name="mode" value="shinkansen" class="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-4 px-6 rounded-xl shadow-lg transition text-left group">
                        <div class="flex justify-between items-center">
                            <div>
                                <div class="text-lg">各駅停車モード</div>
                                <div class="text-xs opacity-80">じっくり学習 (1区間 7問)</div>
                            </div>
                            <span>▶</span>
                        </div>
                    </button>
                    <button name="mode" value="nozomi" class="w-full bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-4 px-6 rounded-xl shadow-lg transition text-left group">
                        <div class="flex justify-between items-center">
                            <div>
                                <div class="text-lg">のぞみ急行モード</div>
                                <div class="text-xs opacity-80">一気に北上 (1区間 28問)</div>
                            </div>
                            <span>▶</span>
                        </div>
                    </button>
                </form>
            </div>
            {% endif %}

            <!-- 2. クイズ画面 -->
            {% if state == 'quiz' %}
            <div class="mb-4">
                <!-- エラー時は赤く表示 -->
                <div class="{{ 'bg-red-50 border-red-200' if question.id == 'ERROR' else 'bg-blue-50 border-blue-100' }} border p-4 rounded-xl mb-6">
                    <div class="text-xs font-bold mb-2 {{ 'text-red-500' if question.id == 'ERROR' else 'text-blue-500' }}">ID: {{ question.id }}</div>
                    <h2 class="text-lg font-bold leading-relaxed">{{ question.question }}</h2>
                </div>

                <form action="/answer" method="post" class="space-y-3">
                    {% for opt in question.options %}
                    <button name="choice" value="{{ loop.index }}" class="w-full bg-white border-2 border-slate-200 hover:border-blue-500 hover:bg-blue-50 text-slate-700 font-bold py-4 px-4 rounded-xl text-left transition shadow-sm">
                        {{ opt }}
                    </button>
                    {% endfor %}
                </form>
            </div>
            {% endif %}

            <!-- 3. 正解/不正解 結果画面 -->
            {% if state == 'judgement' %}
            <div class="text-center py-10">
                {% if is_correct %}
                    <div class="text-green-500 text-6xl mb-4 font-black">◎ 正解</div>
                    <p class="text-slate-600 mb-8">ナイス回答です！</p>
                {% else %}
                    <div class="text-red-500 text-6xl mb-4 font-black">✕ 不正解</div>
                    <p class="text-slate-600 mb-2">正解は...</p>
                    <p class="text-lg font-bold mb-8">{{ correct_answer_text }}</p>
                {% endif %}

                <form action="/next" method="post">
                    <button class="bg-blue-600 text-white font-bold py-3 px-10 rounded-full shadow-lg hover:bg-blue-700 transition">
                        次へ進む
                    </button>
                </form>
            </div>
            {% endif %}

            <!-- 4. 駅到着 -->
            {% if state == 'station_arrival' %}
            <div class="text-center py-10">
                <div class="text-blue-600 mb-4 flex justify-center">
                    <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>
                </div>
                <h2 class="text-3xl font-bold text-slate-800 mb-2">{{ current_station }} に到着！</h2>
                <p class="text-slate-500 mb-8">お疲れ様でした！</p>
                
                <div class="bg-slate-100 p-6 rounded-xl mb-8">
                    <p class="text-sm text-slate-500">現在の累計スコア</p>
                    <p class="text-4xl font-black text-blue-600">{{ score }}問正解</p>
                </div>

                <form action="/depart" method="post">
                    <button class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-8 rounded-xl shadow-lg transition">
                        次の駅へ出発
                    </button>
                </form>
            </div>
            {% endif %}

             <!-- 5. ゴール -->
             {% if state == 'goal' %}
             <div class="text-center py-10">
                 <h2 class="text-4xl font-black text-yellow-500 mb-4">日本縦断達成！</h2>
                 <p class="mb-6 font-bold text-slate-700">東京駅に到着しました！</p>
                 <div class="bg-yellow-50 p-6 rounded-xl mb-8 border-2 border-yellow-200">
                     <p class="text-sm text-slate-500">最終スコア</p>
                     <p class="text-5xl font-black text-slate-800">{{ score }}問</p>
                 </div>
                 <a href="/" class="block w-full bg-slate-800 text-white font-bold py-3 px-6 rounded-xl hover:bg-slate-700">
                     最初から挑戦する
                 </a>
             </div>
             {% endif %}

        </main>
    </div>
</body>
</html>
"""

# ---------------------------------------------------------
# 4. ルーティング & ゲームロジック
# ---------------------------------------------------------

@app.route('/')
def index():
    session.clear()
    return render_template_string(HTML_TEMPLATE, state='menu')

@app.route('/start', methods=['POST'])
def start_game():
    mode = request.form.get('mode')
    session['mode'] = mode
    session['current_station_idx'] = 0
    session['score'] = 0
    set_next_destination(0, mode)
    
    # 問題セットを準備（仕様書に基づき更新）
    questions_per_leg = 7 if mode == 'shinkansen' else 28
    
    # エラー時は1問だけにする（無限ループ防止）
    if len(ALL_QUESTIONS) == 1 and ALL_QUESTIONS[0]['id'] == 'ERROR':
        selected_questions = ALL_QUESTIONS
    else:
        selected_questions = random.sample(ALL_QUESTIONS, min(len(ALL_QUESTIONS), questions_per_leg))
    
    session['quiz_queue'] = selected_questions
    session['current_quiz_idx'] = 0
    return redirect(url_for('play'))

def set_next_destination(current_idx, mode):
    next_idx = current_idx + 1
    if mode == 'nozomi':
        for i in range(current_idx + 1, len(STATION_DATA)):
            if STATION_DATA[i]['is_nozomi']:
                next_idx = i
                break
            next_idx = len(STATION_DATA) - 1
    session['next_station_idx'] = next_idx

@app.route('/play')
def play():
    if 'quiz_queue' not in session: return redirect(url_for('index'))
    queue = session['quiz_queue']
    idx = session['current_quiz_idx']
    
    if idx >= len(queue):
        return render_template_string(HTML_TEMPLATE, 
            state='station_arrival',
            current_station=STATION_DATA[session['next_station_idx']]['name'],
            score=session['score']
        )
        
    return render_template_string(HTML_TEMPLATE,
        state='quiz',
        question=queue[idx],
        mode_label="各駅" if session['mode'] == 'shinkansen' else "のぞみ",
        current_station=STATION_DATA[session['current_station_idx']]['name'],
        next_station=STATION_DATA[session['next_station_idx']]['name'],
        score=session['score'],
        progress=(idx / len(queue)) * 100
    )

@app.route('/answer', methods=['POST'])
def answer():
    choice = int(request.form.get('choice'))
    queue = session['quiz_queue']
    idx = session['current_quiz_idx']
    current_q = queue[idx]
    is_correct = (choice == current_q['answer_idx'])
    
    if is_correct: session['score'] += 1
    return render_template_string(HTML_TEMPLATE,
        state='judgement',
        is_correct=is_correct,
        correct_answer_text=current_q['options'][current_q['answer_idx']-1]
    )

@app.route('/next', methods=['POST'])
def next_question():
    session['current_quiz_idx'] += 1
    return redirect(url_for('play'))

@app.route('/depart', methods=['POST'])
def depart():
    current_idx = session['next_station_idx']
    session['current_station_idx'] = current_idx
    if current_idx >= len(STATION_DATA) - 1:
        return render_template_string(HTML_TEMPLATE, state='goal', score=session['score'])
    
    set_next_destination(current_idx, session['mode'])
    
    # 問題セットを更新（仕様書に基づき更新）
    questions_per_leg = 7 if session['mode'] == 'shinkansen' else 28
    
    if len(ALL_QUESTIONS) == 1 and ALL_QUESTIONS[0]['id'] == 'ERROR':
        selected_questions = ALL_QUESTIONS
    else:
        selected_questions = random.sample(ALL_QUESTIONS, min(len(ALL_QUESTIONS), questions_per_leg))
        
    session['quiz_queue'] = selected_questions
    session['current_quiz_idx'] = 0
    return redirect(url_for('play'))

if __name__ == '__main__':
    app.run(debug=True)