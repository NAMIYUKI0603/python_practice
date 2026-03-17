import os
import glob
import pandas as pd
import time

# --- 1. 空間設計（倉庫と出荷口） ---
INPUT_DIR = "input"
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ターゲットとなるExcelファイルの経路（sisyou_db_ で始まる全ファイル）
TARGET_FILES = glob.glob(os.path.join(INPUT_DIR, "sisyou_db_*.xlsx"))
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "master_sisyou_manufacturing.csv")

print(f"--- 第1工程：労災データベース（死傷）の統合と純化を開始 ---")
print(f"発見されたパレット（ファイル）数: {len(TARGET_FILES)}件\n")

all_data = []
total_rows = 0
mfg_rows = 0

start_time = time.time()

# --- 2. 高速選別コンベアの稼働 ---
for file in TARGET_FILES:
    filename = os.path.basename(file)
    print(f"[{filename}] をプレスマシンに投入中...", end="")

    try:
        # 1行目の大見出しをスキップし、2行目の列名を使用する
        df = pd.read_excel(file, header=1)
        total_rows += len(df)

        # Pandasは重複する列名（「分類名」など）に .1, .2 と連番を振る
        # 最初の「分類名」列（業種の大分類）が「製造業」の行だけを抽出
        if '分類名' in df.columns:
            mfg_df = df[df['分類名'] == '製造業'].copy()
        else:
            print(" -> [警告] '分類名'列が見つかりません。スキップします。")
            continue

        all_data.append(mfg_df)
        mfg_rows += len(mfg_df)
        print(f" -> 抽出完了（赤のコア: {len(mfg_df)}件）")

    except Exception as e:
        print(f" -> [エラー] 読み込み失敗: {e}")

# --- 3. 圧縮と出力 ---
print("\n--- データの結合とマスターCSVの出力 ---")
if all_data:
    # リストに溜まった全ての製造業データを縦に結合
    master_df = pd.concat(all_data, ignore_index=True)
    
    # 結合したデータを1つのCSVとして出力（Excelで文字化けしない utf-8-sig）
    master_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    
    end_time = time.time()
    print(f"[完了] 所要時間: {end_time - start_time:.1f}秒")
    print(f"総読み込みデータ数 (グレーのノイズ含む) : {total_rows} 件")
    print(f"製造業のみの純化データ (赤のコア)       : {mfg_rows} 件")
    print(f"\n[指示] 以下の場所に出荷されました: {os.path.abspath(OUTPUT_CSV)}")
else:
    print("[失敗] 結合できるデータがありませんでした。")