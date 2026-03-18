import os
import glob
import pandas as pd
import time
import warnings

# --- 1. 安全装置と空間設計 ---
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')
# xlrd（.xls読み込み用）の警告もミュート
warnings.filterwarnings('ignore', category=UserWarning, module='xlrd')

INPUT_DIR = "input"
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# .xlsx と .xls の両方を一網打尽にする
TARGET_FILES = glob.glob(os.path.join(INPUT_DIR, "sisyou_db_*.xls*"))
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "master_sisyou_manufacturing.csv")

print(f"--- 第1工程：労災データベース（完全防弾版）の統合を開始 ---")
print(f"発見されたパレット（ファイル）数: {len(TARGET_FILES)}件\n")

all_data = []
total_rows = 0
mfg_rows = 0

start_time = time.time()

# --- 2. 絶対座標抽出コンベア（ヘッダー無視機構） ---
for file in TARGET_FILES:
    filename = os.path.basename(file)
    print(f"[{filename}] を投入中...", end="")

    try:
        # 【中核の改修】見出し（header）を一切信用せず、ただの配列として読み込む
        df = pd.read_excel(file, header=None)
        total_rows += len(df)

        # 列インデックス7（左から8番目）が「業種の大分類」であるという絶対座標を利用
        if 7 in df.columns:
            # 余計な空白や改行を削ぎ落とし、「製造業」という文字列と完全一致する「行」だけを抽出
            # これにより、見出し行や空行は自動的に除外され、純粋なデータ行だけが残る
            mfg_df = df[df[7].astype(str).str.strip() == '製造業'].copy()
            
            if not mfg_df.empty:
                # 現場とP/Lに直結する絶対座標（列番号）だけを抽出し、我々独自の美しい名前をつける
                rename_map = {
                    2: '年', 
                    3: '月', 
                    4: '発生時間', 
                    5: '災害状況', 
                    7: '業種_大分類', 
                    12: '事業場規模', 
                    14: '起因物_大分類', 
                    20: '事故の型', 
                    21: '年齢'
                }
                
                # 存在する列だけを抽出してリネーム
                existing_cols = [c for c in rename_map.keys() if c in mfg_df.columns]
                mfg_df = mfg_df[existing_cols]
                mfg_df.rename(columns=rename_map, inplace=True)
                
                all_data.append(mfg_df)
                mfg_rows += len(mfg_df)
                print(f" -> 抽出完了（赤のコア: {len(mfg_df)}件）")
            else:
                print(" -> [スキップ] 製造業のデータが存在しません。")
        else:
            print(" -> [警告] 想定される座標（列）が存在しません。")

    except Exception as e:
        print(f" -> [エラー] 読み込み失敗: {e}")

# --- 3. 圧縮と出力 ---
print("\n--- データの結合とマスターCSVの出力 ---")
if all_data:
    master_df = pd.concat(all_data, ignore_index=True)
    master_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    
    end_time = time.time()
    print(f"[完了] 所要時間: {end_time - start_time:.1f}秒")
    print(f"総読み込み行数 (ノイズ・ヘッダー含む) : {total_rows} 行")
    print(f"製造業のみの純化データ (赤のコア)       : {mfg_rows} 件")
    print(f"\n[指示] 以下の場所に出荷されました: {os.path.abspath(OUTPUT_CSV)}")
else:
    print("[失敗] 結合できるデータがありませんでした。")