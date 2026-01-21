@app.route('/')
def index():
    # ★修正: タイトルに戻ったら、コレクション以外のゲーム進行データをきれいサッパリ忘れるようにします！
    # これで「やり直し」がきかないトラブルを解決できます✨
    keys_to_remove = ['mode', 'current_station_idx', 'next_station_idx', 'score', 
                      'current_speed', 'question_deck', 'quiz_queue', 'current_quiz_idx', 
                      'question_start_time', 'total_answered_count']
    for key in keys_to_remove:
        session.pop(key, None)

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
        # ★修正: のぞみロジックをより確実に。
        # 現在地より後で、最初に「is_nozomi=True」になる駅を探す
        found = False
        for i in range(current_idx + 1, len(STATION_DATA)):
            if STATION_DATA[i]['is_nozomi']:
                next_idx = i
                found = True
                break
        # もし最後まで見つからなかったら終点（新函館北斗）へ
        if not found:
            next_idx = len(STATION_DATA) - 1
            
    session['next_station_idx'] = next_idx