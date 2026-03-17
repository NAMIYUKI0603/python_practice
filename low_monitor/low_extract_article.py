import os
import requests
import xml.etree.ElementTree as ET

# ==========================================
# 標的の空間設定（ここを書き換えて実行する）
# ==========================================
TARGET_LAW = "大気汚染防止法"
TARGET_ARTICLE = "3"  # 取得したい条文番号（※必ず「算用数字」で指定すること。例: 3, 18の2 など）
OUTPUT_DIR = "output"
# ==========================================

API_LAWMAP_URL = "https://laws.e-gov.go.jp/api/1/lawlists/1"
API_LAWDATA_URL = "https://laws.e-gov.go.jp/api/1/lawdata/"

print(f"--- 【標的捕捉】 {TARGET_LAW} 第{TARGET_ARTICLE}条 ---")

try:
    # --- フェーズ1: 法令名からIDへの翻訳 ---
    print("辞書データと照合中...")
    response_list = requests.get(API_LAWMAP_URL)
    response_list.encoding = 'utf-8'
    root_list = ET.fromstring(response_list.text)
    
    law_id = None
    for law in root_list.findall(".//LawNameListInfo"):
        if law.find("LawName").text == TARGET_LAW:
            law_id = law.find("LawId").text
            break
            
    if not law_id:
        print(f"[致命的エラー] {TARGET_LAW} が辞書に見つかりません。正式名称を確認してください。")
        exit()

    # --- フェーズ2: 法令データの取得と狙撃 ---
    print("法令XMLデータをダウンロード中...")
    response_data = requests.get(API_LAWDATA_URL + law_id)
    response_data.encoding = 'utf-8'
    root_data = ET.fromstring(response_data.text)
    
    # e-Gov XMLの構造から、属性 Num="3" を持つ Article（条）を検索
    # （※「第十八条の二」などの枝番は Num="18_2" となっていることが多いが、基本の数字で検索可能）
    xpath_query = f".//Article[@Num='{TARGET_ARTICLE}']"
    target_article_node = root_data.find(xpath_query)
    
    if target_article_node is None:
        print(f"[エラー] {TARGET_LAW} の中に「第{TARGET_ARTICLE}条」が見つかりません。")
        print("※枝番（例：第3条の2）の場合は、XMLの仕様上 '3_2' のように指定する必要があります。")
        exit()

    # --- フェーズ3: テキストの抽出と精製 ---
    print("条文のテキストを抽出・精製中...")
    extracted_lines = []
    
    # XMLの階層の奥底にある「葉（末端のテキストデータ）」だけを拾い集める
    for elem in target_article_node.iter():
        if elem.text and elem.text.strip():
            # 子要素を持たない（＝最下層のテキスト）場合のみ追加
            if len(elem) == 0:
                extracted_lines.append(elem.text.strip())

    # 抽出したテキストブロックを改行で結合
    final_text = "\n".join(extracted_lines)

    # --- フェーズ4: 出力層（TXT保存） ---
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_filename = os.path.join(OUTPUT_DIR, f"{TARGET_LAW}_第{TARGET_ARTICLE}条.txt")
    
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(final_text)

    print(f"\n[狙撃完了] 以下のファイルに抽出しました。")
    print(f" -> {output_filename}")
    
    # 確認のためターミナルにもプレビューを表示
    print("\n--- 条文プレビュー ---")
    print(final_text[:200] + "...\n(以下略)")

except Exception as e:
    print(f"[エラー発生] {e}")