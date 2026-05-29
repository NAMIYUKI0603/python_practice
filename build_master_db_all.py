import os
import glob
import pandas as pd
import time
import warnings

# --- 1. 安全装置と空間設計 ---
# Excel読み込み時の古い規格に関する警告をミュート
warnings.filterwarnings('ignore', category=UserWarning)

INPUT_DIR = "input"
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 【改修】旧形式(.xls)と新形式(.xlsx)の両方を一括で探索する指定
TARGET_FILES = glob.glob(os.path.join(INPUT_DIR, "sisyou_db_*.xls*"))
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "master_sisyou_all_integrated.csv")

print(f"--- 労災データベース（Excel・120ヶ月全業種丸ごと自動統合版）の統合を開始 ---")
print(f"発見されたファイル数: {len(TARGET_FILES)}件\n")

all_data = []
total_rows = 0
integrated_rows = 0

start_time = time.time()

# 抽出・リネームする絶対座標のマッピング
rename_map = {
    2: '年', 
    3: '月', 
    4: '発生時間', 
    5: '災害状況', 
    7: '業種_大分類', 
    9: '業種_中分類',
    11: '業種_小分類',
    12: '事業場規模', 
    14: '起因物_大分類', 
    16: '起因物_中分類',
    18: '起因物_小分類',
    20: '事故の型', 
    21: '年齢'
}

# --- 2. 動的データ行検知コンベア ---
for file in TARGET_FILES:
    filename = os.path.basename(file)
    print(f"[{filename}] を解析中...", end="")

    try:
        # sheet_name=0 でシート名の違いを無視し、header=None で生データとして強制読込
        df = pd.read_excel(file, sheet_name=0, header=None)
        total_rows += len(df)

        # 【中核の改修】年度による「ヘッダーの行数違い」や「空行」を自動で裏かくロジック
        # 1番目の列（年号列）が「平成」または「令和」である行だけを「本物のデータ行」として動的に判定
        if 1 in df.columns:
            is_data_row = df[1].astype(str).str.strip().isin(['平成', '令和'])
            clean_df = df[is_data_row].copy()
            
            if not clean_df.empty:
                # 存在する列だけをマッピングして全行抽出
                existing_cols = [c for c in rename_map.keys() if c in clean_df.columns]
                sub_df = clean_df[existing_cols]
                sub_df.rename(columns=rename_map, inplace=True)
                
                all_data.append(sub_df)
                integrated_rows += len(sub_df)
                print(f" -> 統合完了（データ行: {len(sub_df)}行 / 総行数: {len(df)}行）")
            else:
                print(" -> [警告] 有効なデータ行が検出されませんでした。")
        else:
            print(" -> [警告] 想定される列構造（年号列）が存在しません。")

    except Exception as e:
        print(f" -> [エラー] 読み込み失敗（エンジンまたはファイル破損の可能性）: {e}")

# --- 3. 出力 ---
print("\n--- データの丸ごと結合とマスターCSVの出力 ---")
if all_data:
    master_df = pd.concat(all_data, ignore_index=True)
    
    # 最後に「年」「月」の欠損値を排除してクリーンに仕上げる
    master_df = master_df.dropna(subset=['年', '月'])
    
    master_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    
    end_time = time.time()
    print(f"[完了] 所要時間: {end_time - start_time:.1f}秒")
    print(f"総統合ファイル数                       : {len(all_data)} 件")
    print(f"出力された全業種マスターデータの総行数    : {len(master_df)} 行")
    print(f"\n[指示] 以下の場所に出荷されました: {os.path.abspath(OUTPUT_CSV)}")
else:
    print("[失敗] 結合できるデータがありませんでした。")