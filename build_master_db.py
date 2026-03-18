import os
import glob
import pandas as pd
import time
import warnings

# --- 1. 安全装置と空間設計 ---
# 素人の不安を煽るだけの無害な警告（Excelの書式非対応など）を完全にミュートする
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

INPUT_DIR = "input"
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

TARGET_FILES = glob.glob(os.path.join(INPUT_DIR, "sisyou_db_*.xlsx"))
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "master_sisyou_manufacturing.csv")

print(f"--- 第1工程：労災データベース（死傷）の統合と純化を再稼働 ---")
print(f"発見されたパレット（ファイル）数: {len(TARGET_FILES)}件\n")

all_data = []
total_rows = 0
mfg_rows = 0

start_time = time.time()

# --- 2. 動的補正エンジン搭載コンベア ---
for file in TARGET_FILES:
    filename = os.path.basename(file)
    print(f"[{filename}] を投入中...", end="")

    try:
        # 【中核の改修】ファイルごとに1〜10行目を走査し、真の「見出し行」を動的に探し出す
        df_temp = pd.read_excel(file, header=None, nrows=10)
        header_row = 0
        for i, row in df_temp.iterrows():
            # 行内の全テキストを結合し、「災害状況」という単語が含まれる行をヘッダーとみなす
            row_str = "".join([str(x) for x in row.values])
            if "災害状況" in row_str:
                header_row = i
                break

        # 発見した正しいヘッダー位置で本番読み込み
        df = pd.read_excel(file, header=header_row)
        total_rows += len(df)

        # 製造業のみの抽出（Pandasは重複列名に .1, .2 を振るため、最初の '分類名' を大分類として指定）
        if '分類名' in df.columns:
            mfg_df = df[df['分類名'] == '製造業'].copy()
            
            # 【データ正規化】結合時のズレを防ぐため、絶対に必要な列だけを抽出し名前を統一する
            # ※役所のフォーマット揺れに対応するための防御機構
            cols_to_keep = {}
            for col in ['年', '月', '発生時間', '災害状況', '事業場規模', '年齢', '分類名', '分類名.3', '分類名.6']:
                if col in mfg_df.columns:
                    cols_to_keep[col] = col
                    
            # リネームマッピング（P/Lと現場に直結する変数のみを厳選）
            rename_map = {
                '分類名': '業種_大分類',
                '分類名.3': '起因物_大分類',
                '分類名.6': '事故の型'
            }
            mfg_df = mfg_df[list(cols_to_keep.keys())].rename(columns=rename_map)
            
            all_data.append(mfg_df)
            mfg_rows += len(mfg_df)
            print(f" -> 抽出完了（赤のコア: {len(mfg_df)}件）")
        else:
            print(" -> [警告] '分類名'列が見つかりません。スキップします。")

    except Exception as e:
        print(f" -> [エラー] 読み込み失敗: {e}")

# --- 3. 圧縮と出力 ---
print("\n--- データの結合とマスターCSVの出力 ---")
if all_data:
    master_df = pd.concat(all_data, ignore_index=True)
    master_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    
    end_time = time.time()
    print(f"[完了] 所要時間: {end_time - start_time:.1f}秒")
    print(f"総読み込みデータ数 (グレーのノイズ含む) : {total_rows} 件")
    print(f"製造業のみの純化データ (赤のコア)       : {mfg_rows} 件")
    print(f"\n[絶対指示] 出力されたCSVをExcelで開き、列のズレがないか自分の目で確認せよ: {os.path.abspath(OUTPUT_CSV)}")
else:
    print("[失敗] 結合できるデータがありませんでした。")