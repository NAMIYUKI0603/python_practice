import pandas as pd
import unicodedata
import re

# --- 1. マスターデータの読み込み ---
MASTER_CSV = "output/master_sisyou_all_integrated.csv"
CLEANED_CSV = "output/master_sisyou_all_cleaned.csv"

print("31万件のマスターデータを読み込み中...")
df = pd.read_csv(MASTER_CSV, low_memory=False)

# 【改修】『業種_大分類』を完全装填し、すべての分類列を網羅
target_columns = [
    '業種_大分類', '業種_中分類', '業種_小分類', 
    '起因物_大分類', '起因物_中分類', '起因物_小分類'
]

print("\n--- 第2世代：特殊スペース・ハイフン対応型クレンジングエンジン起動 ---")

for col in target_columns:
    if col not in df.columns:
        continue
        
    print(f"[{col}] の特殊ノイズを根絶中...")
    
    # 欠損値を文字列の空欄に変換
    df[col] = df[col].fillna("nan").astype(str)
    
    # 【第1工程】バイナリレベルのノイズ除去
    # 見た目が半角スペースの「ノーブレークスペース(\xa0)」や特殊空白を、通常の半角スペースに強制置換
    df[col] = df[col].apply(lambda x: x.replace('\xa0', ' ').replace('\u200b', '').replace('　', ' '))
    
    # 【第2工程】Unicode正規化（NFKC）
    # 半角カナ中点「･」を全角「・」に、全角英数を半角に強制統一
    df[col] = df[col].apply(lambda x: unicodedata.normalize('NFKC', x))
    
    # 【第3工程】ハイフン・ダッシュ類の表記ゆれを全角「－」に完全統一
    # 「-（半角）」「ー（長音）」「─（罫線）」などの混在をすべて名寄せ
    df[col] = df[col].apply(lambda x: re.sub(r'[-－──━─•‑–—―〜~～]+', '－', x))
    
    # 【第4工程】正規表現で、中点（・）の前後に残るすべてのスペース（連続スペース対応）を完全に狙撃
    # 例：「映画・ 演劇業」「映画 ・演劇業」をすべて「映画・演劇業」に強制結合
    df[col] = df[col].apply(lambda x: re.sub(r'\s*・\s*', '・', x))
    
    # ハイフン（－）の前後のスペースも同時に狙撃して結合
    df[col] = df[col].apply(lambda x: re.sub(r'\s*－\s*', '－', x))
    
    # 【第5工程】文字列前後の無駄な空白を最終トリミング
    df[col] = df[col].str.strip()
    
    # 【第6工程】頻度ベースの最終名寄せ（スペース完全抜きの原型比較）
    counts = df[col].value_counts()
    best_match_map = {}
    
    for raw_string in counts.index:
        if raw_string == "nan":
            continue
        # 文字列内のすべてのスペースを完全に消去したものを比較用キーにする
        pure_key = raw_string.replace(" ", "")
        
        # 最も出現件数が多い文字列を、そのグループの「絶対正解」として辞書に登録
        if pure_key not in best_match_map:
            best_match_map[pure_key] = raw_string
            
    # 作成した絶対正解マップを元に、全データを上書き変換
    def align_string(val):
        if val == "nan" or pd.isna(val):
            return None
        pure_k = str(val).replace(" ", "")
        return best_match_map.get(pure_k, val)
        
    df[col] = df[col].apply(align_string)
    print(f"  └ [{col}] の名寄せ・純化が完了しました。")

# --- 3. クリーンデータの出荷 ---
print("\nクリーンなマスターデータを出力中...")
df.to_csv(CLEANED_CSV, index=False, encoding='utf-8-sig')
print(f"[完了] すべてのステルスノイズが死滅しました。出荷先: {CLEANED_CSV}")