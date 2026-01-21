import os
import random
from flask import Flask, jsonify, request, session, render_template_string

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'shinkansen_secret_key')

# ---------------------------------------------------------
# 1. マスターデータ定義 (全71駅・493問ロジック用)
# ---------------------------------------------------------

# 駅データリスト (順序, 駅名, のぞみ停車フラグ)
STATION_DATA = [
    (1, "鹿児島中央", False), (2, "川内", False), (3, "出水", False), (4, "新水俣", False), (5, "新八代", False),
    (6, "熊本", True), (7, "新玉名", False), (8, "新大牟田", False), (9, "筑後船小屋", False), (10, "久留米", False),
    (11, "新鳥栖", False), (12, "博多", True), (13, "小倉", True), (14, "新下関", False), (15, "厚狭", False),
    (16, "新山口", False), (17, "徳山", False), (18, "新岩国", False), (19, "広島", True), (20, "東広島", False),
    (21, "三原", False), (22, "新尾道", False), (23, "福山", False), (24, "新倉敷", False), (25, "岡山", True),
    (26, "相生", False), (27, "姫路", False), (28, "西明石", False), (29, "新神戸", True), (30, "新大阪", True),
    (31, "京都", True), (32, "米原", False), (33, "岐阜羽島", False), (34, "名古屋", True), (35, "三河安城", False),
    (36, "豊橋", False), (37, "浜松", False), (38, "掛川", False), (39, "静岡", False), (40, "新富士", False),
    (41, "三島", False), (42, "熱海", False), (43, "小田原", False), (44, "新横浜", True), (45, "品川", True),
    (46, "東京", True), (47, "上野", False), (48, "大宮", True), (49, "小山", False), (50, "宇都宮", False),
    (51, "那須塩原", False), (52, "新白河", False), (53, "郡山", False), (54, "福島", False), (55, "白石蔵王", False),
    (56, "仙台", True), (57, "古川", False), (58, "くりこま高原", False), (59, "一ノ関", False), (60, "水沢江刺", False),
    (61, "北上", False), (62, "新花巻", False), (63, "盛岡", True), (64, "いわて沼宮内", False), (65, "二戸", False),
    (66, "八戸", False), (67, "七戸十和田", False), (68, "新青森", True), (69, "奥津軽いまべつ", False), (70, "木古内", False),
    (71, "新函館北斗", True)
]

# モード設定
MODES = {
    "shinkansen": {
        "name": "新幹線モード（各駅停車）",
        "questions_per_section": 7,
        "final_questions": 3,
        "target_stations": [s for s in STATION_DATA] # 全駅
    },
    "nozomi": {
        "name": "のぞみモード（急行）",
        "questions_normal": 28,
        "questions_hub": 50, # 博多、東京
        "final_questions": 1,
        "hubs": ["博多", "東京"],
        "target_stations": [s for s in STATION_DATA if s[2] or s[1] == "鹿児島中央"] # 停車駅のみ
    }
}

TOTAL_QUESTIONS = 493

# 簡易フロントエンド用テンプレート
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>新幹線試験対策ドリル - Prototype</title>
    <style>
        body { font-family: 'Hiragino Kaku Gothic Pro', sans-serif; background: #222; color: #fff; text-align: center; }
        .dashboard { max-width: 600px; margin: 0 auto; background: #333; padding: 20px; border-radius: 10px; border: 2px solid #555; }
        .hud { background: rgba(0, 255, 255, 0.1); border: 1px solid #00ffff; padding: 15px; margin-bottom: 20px; color: #00ffff; }
        .speedometer { font-size: 2em; font-weight: bold; color: #ffeb3b; margin: 10px 0; }
        .btn { display: block; width: 100%; padding: 15px; margin: 5px 0; background: #444; border: 1px solid #777; color: #fff; cursor: pointer; border-radius: 5px; font-size: 16px; }
        .btn:hover { background: #555; border-color: #aaa; }
        .status { margin-top: 20px; font-size: 0.9em; color: #aaa; }
        .bar-container { width: 100%; background-color: #111; border-radius: 5px; margin: 10px 0; }
        .bar { height: 10px; background-color: #4caf50; border-radius: 5px; transition: width 0.3s; }
    </style>
</head>
<body>
    <div class="dashboard">
        <h1>🚄 {{ game_state.mode_name }}</h1>
        
        <div class="hud">
            <div>NEXT STATION: {{ game_state.next_station }}</div>
            <div>区間残り: {{ game_state.section_remaining }} 問</div>
            <div style="font-size: 0.8em;">(トータル消化: {{ game_state.total_solved }} / 493)</div>
        </div>

        <div class="speedometer">
            {{ game_state.current_speed }} km/h
        </div>

        {% if game_state.is_finished %}
            <h2 style="color: #4caf50;">🎉 全線走破！業務完了！ 🎉</h2>
            <p>最終スコア: {{ game_state.score }}</p>
            <a href="/" class="btn" style="background:#2196f3;">トップへ戻る</a>
        {% else %}
            <div id="question-area">
                <p>Q. {{ current_question.text }} (ダミー問題)</p>
                <form action="/answer" method="post">
                    {% for option in current_question.options %}
                        <button type="submit" name="answer" value="{{ option }}" class="btn">{{ option }}</button>
                    {% endfor %}
                </form>
            </div>
        {% endif %}

        <div class="status">
            現在地: {{ game_state.current_station }} ➡ {{ game_state.next_station }}<br>
            定時運行状況: {{ "🟢 順調" if game_state.is_on_time else "🔴 遅延" }}
        </div>
        
        <div class="bar-container">
            <div class="bar" style="width: {{ (game_state.total_solved / 493) * 100 }}%;"></div>
        </div>
    </div>
</body>
</html>
"""

# ---------------------------------------------------------
# 2. ゲームロジック
# ---------------------------------------------------------

class GameEngine:
    def __init__(self):
        self.reset()

    def reset(self, mode="shinkansen"):
        self.mode = mode
        self.current_station_index = 0
        self.total_solved = 0
        self.section_solved = 0
        self.score = 0
        self.speed = 0
        self.is_on_time = True
        
        # モードごとの駅リスト構築
        self.stations = MODES[mode]["target_stations"]
        # 次の駅までの必要問題数計算
        self.update_section_target()

    def update_section_target(self):
        # ゴール判定
        if self.current_station_index >= len(self.stations) - 1:
            self.section_target = 0
            return

        next_st_name = self.stations[self.current_station_index + 1][1]
        
        if self.mode == "shinkansen":
            # 最後の区間（木古内→新函館北斗）の後の「最終試験」判定
            if next_st_name == "新函館北斗":
                # 木古内→新函館北斗の移動中(7問) + 到着後の試験(3問)
                # ここでは簡易的に到着前の区間として処理し、到着ロジックで分岐させる
                self.section_target = 7 
            else:
                self.section_target = 7
        
        elif self.mode == "nozomi":
            if next_st_name == "新函館北斗":
                self.section_target = 28 # 新青森→新函館北斗区間
            elif next_st_name in MODES["nozomi"]["hubs"]:
                self.section_target = 50 # 乗換駅（博多・東京）へ向かう区間
            else:
                self.section_target = 28 # 通常

    def get_state(self):
        is_finished = self.total_solved >= TOTAL_QUESTIONS
        
        # 次の駅名
        if self.current_station_index < len(self.stations) - 1:
            next_station = self.stations[self.current_station_index + 1][1]
        else:
            next_station = "FINISH"

        # 最終問題（新函館北斗到着後）の処理
        # ロジック: 駅間クイズが終わったら「到着」。到着後に「残り」を出題。
        # このプロトタイプでは簡易化のため、残数が少なくなったら「最終試験中」と表示
        remaining_in_section = self.section_target - self.section_solved
        
        # 特殊処理：ゴール手前の残数調整
        final_questions = MODES[self.mode]["final_questions"]
        if next_station == "新函館北斗" and remaining_in_section <= 0:
            # 区間完走したが、まだ最終試験が残っている場合
            if self.total_solved < TOTAL_QUESTIONS:
                next_station = "新函館北斗（最終試験）"
                remaining_in_section = TOTAL_QUESTIONS - self.total_solved

        return {
            "mode_name": MODES[self.mode]["name"],
            "current_station": self.stations[self.current_station_index][1],
            "next_station": next_station,
            "total_solved": self.total_solved,
            "section_remaining": max(0, remaining_in_section),
            "current_speed": self.speed,
            "is_on_time": self.is_on_time,
            "is_finished": is_finished,
            "score": self.score
        }

    def answer_question(self, is_correct):
        if is_correct:
            self.total_solved += 1
            self.section_solved += 1
            self.score += 100
            self.speed = min(320, self.speed + 30) # 加速
            self.is_on_time = True
        else:
            self.speed = max(0, self.speed - 50) # 減速
            self.is_on_time = False # 遅延扱い

        # 区間クリア判定
        if self.section_solved >= self.section_target:
            # 最終問題でなければ駅を進める
            if self.total_solved < TOTAL_QUESTIONS - MODES[self.mode]["final_questions"]:
                self.current_station_index += 1
                self.section_solved = 0
                self.update_section_target()
                self.speed = 0 # 停車
            elif self.total_solved >= TOTAL_QUESTIONS:
                # 完全クリア
                pass

# インスタンス化 (簡易的にグローバル変数)
game = GameEngine()

# ---------------------------------------------------------
# 3. Webアプリルート
# ---------------------------------------------------------

@app.route('/')
def index():
    # トップページ兼リセット
    game.reset("shinkansen") # デフォルト
    return render_template_string(HTML_TEMPLATE, 
                                  game_state=game.get_state(),
                                  current_question={"text": "スタートしますか？", "options": ["出発進行！"]})

@app.route('/mode/<mode_name>')
def switch_mode(mode_name):
    game.reset(mode_name)
    return render_template_string(HTML_TEMPLATE, 
                                  game_state=game.get_state(),
                                  current_question={"text": f"{mode_name}で出発！", "options": ["出発進行！"]})

@app.route('/answer', methods=['POST'])
def answer():
    # ダミー回答処理（常に正解扱い、またはランダムにする）
    # プロトタイプなので「正解」ボタンと「不正解」ボタンをシミュレート
    user_input = request.form.get('answer')
    
    is_correct = True
    if user_input == "不正解シミュレート":
        is_correct = False
    
    # スタートボタン等の処理
    if user_input == "出発進行！":
        pass
    else:
        game.answer_question(is_correct)

    # 次の問題生成（ダミー）
    question = {
        "text": f"第{game.total_solved + 1}問: 過去問データベースからの出題です。",
        "options": ["正解の選択肢", "不正解シミュレート", "選択肢C", "選択肢D", "選択肢E"]
    }
    
    if game.mode == "nozomi":
        question["options"] = ["正解の選択肢", "不正解シミュレート"]

    return render_template_string(HTML_TEMPLATE, 
                                  game_state=game.get_state(),
                                  current_question=question)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)