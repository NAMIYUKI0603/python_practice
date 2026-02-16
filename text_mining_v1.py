import MeCab
from collections import Counter
import os

# ==========================================
# 設定：除外したい単語（ストップワード）
# ここに「意味のない高頻度語」を追加していく
# ==========================================
STOP_WORDS = ["よう", "こと", "もの", "ん", "これ", "それ", "あれ", "の", "ため", "日"]

def extract_nouns(text):
    """
    MeCabを使ってテキストから名詞を抽出する
    """
    # MeCabの初期化（辞書を指定しない場合は標準辞書が使われる）
    # Windowsでエラーが出る場合は r'-Ochasen' などを引数に入れてみる
    tagger = MeCab.Tagger()
    
    # 解析実行
    node = tagger.parseToNode(text)
    nouns = []
    
    while node:
        # featureには品詞情報が入っている（例: 名詞,一般,*,*,*,*,猫,ネコ,ネコ）
        features = node.feature.split(",")
        word = node.surface # 単語そのもの
        
        # 品詞判定：今回は「名詞」のみをターゲットにする
        if features[0] == "名詞":
            # ノイズ除去フィルタ（代名詞、数、非自立語、ストップワードを除外）
            if (features[1] not in ["代名詞", "数", "非自立", "接尾"] and 
                word not in STOP_WORDS):
                nouns.append(word)
                
        node = node.next
        
    return nouns

def analyze_file(file_path):
    if not os.path.exists(file_path):
        print(f"エラー: {file_path} が見つかりません。")
        return

    print(f"[{file_path}] を分析中...")
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
        
    nouns = extract_nouns(text)
    
    # 集計（出現頻度順）
    counter = Counter(nouns)
    
    print(f"\n--- 出現頻度ランキング Top 20 ---")
    for word, count in counter.most_common(20):
        print(f"{word}: {count} 回")
        
    return counter

# ==========================================
# 実行部
# ==========================================
if __name__ == "__main__":
    # ここに分析したいファイル名を指定
    target_file = "diary.txt" 
    
    # ダミーデータ（ファイルがない場合のテスト用）
    sample_text = "私は工場の安全管理を担当しています。安全第一で工場を巡回し、環境問題を解決します。"
    
    if os.path.exists(target_file):
        analyze_file(target_file)
    else:
        print("※diary.txtが見つからないため、サンプルで実行します")
        print(extract_nouns(sample_text))      