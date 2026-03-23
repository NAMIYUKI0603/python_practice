import os
import glob
import pandas as pd
import time
import warnings
import re

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')
warnings.filterwarnings('ignore', category=UserWarning, module='xlrd')

INPUT_DIR = "input"
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 死亡災害DBのファイルをすべて狙い撃ち
TARGET_FILES = glob.glob(os.path.join(INPUT_DIR, "sibou_db_*.xls*"))
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "master_sibou_all_industries.csv")

print(f"--- 第3工程：死亡災害データベース（全業種統合版）の構築を開始 ---")
print(f"発見されたパレット（ファイル）数: {len(TARGET_FILES)}件\n")

all_data = []
total_rows = 0
valid_rows = 0

start_time = time.time()

for file in TARGET_FILES:
    filename = os.path.basename(file)
    print(f"[{filename}] を投入中...", end="")

    try:
        # ファイル名から「h25」や「r05」を抽出し、「年」のデータとして付与する準備
        year_match = re.search(r'(h|r)(\d+)', filename, re.IGNORECASE)
        file_year = year_match.group(0).upper() if year_match else "不明"

        df = pd.read_excel(file, header=None)
        total_rows += len(df)

        # 死亡DBの絶対座標：インデックス3（左から4番目）に「災害状況」が入っている
        # 災害状況が空欄ではなく、文字列長が10文字以上の「実データ行」だけを抽出（ヘッダー等のノイズ排除）
        df_valid = df[df[3].astype(str).str.len() > 10].copy()
        
        if not df_valid.empty:
            # 死亡DB特有の絶対座標マッピング
            rename_map = {
                1: '月', 
                2: '発生時間', 
                3: '災害状況', 
                5: '業種_大分類', 
                7: '業種_中分類',
                9: '業種_小分類',
                10: '事業場規模', 
                12: '起因物_大分類', 
                14: '起因物_中分類',
                16: '起因物_小分類',
                18: '事故の型'
            }
            
            existing_cols = [c for c in rename_map.keys() if c in df_valid.columns]
            df_valid = df_valid[existing_cols]
            df_valid.rename(columns=rename_map, inplace=True)
            
            # 抽出した「年」を新しい列として先頭に挿入
            df_valid.insert(0, '年', file_year)
            
            all_data.append(df_valid)
            valid_rows += len(df_valid)
            print(f" -> 抽出完了（赤のコア: {len(df_valid)}件）")
        else:
            print(" -> [スキップ] 有効なデータ行が存在しません。")

    except Exception as e:
        print(f" -> [エラー] 読み込み失敗: {e}")

# --- 圧縮と出力 ---
print("\n--- データの結合とマスターCSVの出力 ---")
if all_data:
    master_df = pd.concat(all_data, ignore_index=True)
    master_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    
    end_time = time.time()
    print(f"[完了] 所要時間: {end_time - start_time:.1f}秒")
    print(f"総読み込み行数 (ノイズ・ヘッダー含む) : {total_rows} 行")
    print(f"全業種の有効な死亡データ (赤のコア)     : {valid_rows} 件")
    print(f"\n[指示] 以下の場所に出荷されました: {os.path.abspath(OUTPUT_CSV)}")
else:
    print("[失敗] 結合できるデータがありませんでした。")