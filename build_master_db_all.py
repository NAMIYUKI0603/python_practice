import os
import glob
import pandas as pd
import time
import warnings
import unicodedata
import re
from datetime import datetime

# --- 1. 安全装置と空間設計 ---
warnings.filterwarnings('ignore', category=UserWarning)

INPUT_DIR = "input"
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 旧形式(.xls)と新形式(.xlsx)の両方を一括探索
TARGET_FILES = glob.glob(os.path.join(INPUT_DIR, "sisyou_db_*.xls*"))
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "master_sisyou_all_cleaned.csv")

print(f"--- 労災データベース［Excel統合 ＆ 範囲・日付バグ完全制圧版］起動 ---")
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

# --- 2. 範囲・日付誤変換リカバリー用関数定義 ---
def sanitize_range_format(val, is_size=False):
    """
    Excelによって「8月9日」などに誤変換された発生時間や事業場規模を
    「8～9」の正しい数値範囲（全角～）に完全復元・統一する関数
    """
    if pd.isna(val) or str(val).strip() == "" or str(val).lower() == "nan":
        return None
        
    # パターンA: Excelが完全に日付型（datetimeオブジェクト）に変換してしまっている場合
    if isinstance(val, (datetime, pd.Timestamp)):
        res = f"{val.month}～{val.day}"
        return f"{res}人" if is_size else res
        
    s = str(val).strip()
    
    # パターンB: 文字列として「8月9日」や「08月09日」化している場合
    match_date = re.search(r'(\d+)月(\d+)日', s)
    if match_date:
        res = f"{int(match_date.group(1))}～{int(match_date.group(2))}"
        return f"{res}人" if is_size else res

    # パターンC: あらゆる不規則な波線・ハイフン・スラッシュを全角「～」に集約
    wave_pattern = r'[\u301c\uff5e\u007e\u223c\u223d\u203e〜～~‐-－─—_／/]'
    s_unified = re.sub(wave_pattern, '～', s)
    
    # コア抽出: 「数字～数字」の形を探し、余計なゼロや文字（時、人など）を削ぎ落として純化
    match_range = re.search(r'(\d+)～(\d+)', s_unified)
    if match_range:
        res = f"{int(match_range.group(1))}～{int(match_range.group(2))}"
        return f"{res}人" if is_size else res
        
    # パターンD: 「1000人以上」などの単一数値パターンのノイズ処理
    if is_size:
        digits = re.sub(r'\D', '', s_unified)
        if digits and '以上' in s_unified:
            return f"{digits}人以上"
        elif digits:
            return f"{digits}人"
            
    return s_unified

# --- 3. 第一工程：動的データ行検知・一括結合 ---
print(">>> 第一工程: Excelファイルの自動読込・結合を開始...")
for file in TARGET_FILES:
    filename = os.path.basename(file)
    print(f"  [{filename}] を解析中...", end="")

    try:
        df = pd.read_excel(file, sheet_name=0, header=None)
        total_rows += len(df)

        # 「年号列」が「平成」または「令和」である行だけを動的に判定して抽出
        if 1 in df.columns:
            is_data_row = df[1].astype(str).str.strip().isin(['平成', '令和'])
            clean_df = df[is_data_row].copy()
            
            if not clean_df.empty:
                existing_cols = [c for c in rename_map.keys() if c in clean_df.columns]
                sub_df = clean_df[existing_cols]
                sub_df.rename(columns=rename_map, inplace=True)
                
                all_data.append(sub_df)
                integrated_rows += len(sub_df)
                print(f" -> 結合（データ行: {len(sub_df)}行）")
            else:
                print(" -> [警告] 有効なデータ行なし。")
        else:
            print(" -> [警告] 年号列（インデックス1）が存在しません。")

    except Exception as e:
        print(f" -> [エラー] 読込失敗: {e}")

if not all_data:
    print("\n[失敗] 結合できるデータがありませんでした。処理を中断します。")
    exit()

master_df = pd.concat(all_data, ignore_index=True)

# --- 4. 第二工程: 特殊範囲修復 ＆ 文字列名寄せクレンジング ---
print("\n>>> 第二工程: 31万件規模のマスターデータ純化処理を開始...")

# 2-1. 【最重要】発生時間と事業場規模の「日付バグ」および「全角～」への強制統一
print("  [発生時間] の日付誤変換を復元 ＆ 全角「～」に完全統一中...")
master_df['発生時間'] = master_df['発生時間'].apply(lambda x: sanitize_range_format(x, is_size=False))

print("  [事業場規模] の表記分裂を復元 ＆ 「〇～〇人」に完全統一中...")
master_df['事業場規模'] = master_df['事業場規模'].apply(lambda x: sanitize_range_format(x, is_size=True))


# 2-2. 業種・起因物列のステルスノイズ名寄せ
category_columns = [
    '業種_大分類', '業種_中分類', '業種_小分類', 
    '起因物_大分類', '起因物_中分類', '起因物_小分類'
]

for col in category_columns:
    if col not in master_df.columns:
        continue
        
    print(f"  [{col}] のステルスノイズ・表記ゆれを名寄せ中...", end="")
    
    master_df[col] = master_df[col].fillna("nan").astype(str)
    
    # 特殊スペース（ノーブレークスペース等）の破壊
    master_df[col] = master_df[col].apply(lambda x: x.replace('\xa0', ' ').replace('\u200b', '').replace(' ', ' '))
    
    # Unicode正規化（NFKC）で半角カナ中点「･」を全角「・」に統一
    master_df[col] = master_df[col].apply(lambda x: unicodedata.normalize('NFKC', x))
    
    # ハイフン・ダッシュ類の表記ゆれを全角「－」に統一
    master_df[col] = master_df[col].apply(lambda x: re.sub(r'[-－──━─•‑–—―〜~～]+', '－', x))
    
    # 正規表現で、中点（・）およびハイフン（－）の前後に残るすべてのスペースを狙撃
    master_df[col] = master_df[col].apply(lambda x: re.sub(r'\s*・\s*', '・', x))
    master_df[col] = master_df[col].apply(lambda x: re.sub(r'\s*－\s*', '－', x))
    
    # 文字列前後の無駄な空白をトリミング
    master_df[col] = master_df[col].str.strip()
    
    # 頻度ベースの最終名寄せ（スペース完全抜きの原型比較による最大頻度への上書き）
    counts = master_df[col].value_counts()
    best_match_map = {}
    
    for raw_string in counts.index:
        if raw_string == "nan":
            continue
        pure_key = raw_string.replace(" ", "")
        if pure_key not in best_match_map:
            best_match_map[pure_key] = raw_string
            
    def align_string(val):
        if val == "nan":
            return None
        pure_k = str(val).replace(" ", "")
        return best_match_map.get(pure_k, val)
        
    master_df[col] = master_df[col].apply(align_string)
    print(" -> 完了")

# 最後に、データ行として成立していない「年」「月」の欠損値を排除
master_df = master_df.dropna(subset=['年', '月'])

# --- 5. 第三工程: クリーンデータの出荷 ---
print("\n>>> 第三工程: 最終結果の書き出し...")
master_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')

end_time = time.time()
print(f"\n[大成功] すべての工程が完了しました。所要時間: {end_time - start_time:.1f}秒")
print(f"総読み込み行数 (ヘッダー等含む)       : {total_rows} 行")
print(f"純化された全業種マスターデータの総行数 : {len(master_df)} 行")
print(f"出荷先絶対パス: {os.path.abspath(OUTPUT_CSV)}")