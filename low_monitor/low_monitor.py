import os
import requests
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime
import time

# --- 1. 監視対象の空間定義（リスト） ---
# ご指摘の通り、土壌汚染防止法 -> 土壌汚染対策法へ修正
# 現場を守る「網目」として代表的な施行令・施行規則も配置済
TARGET_LAWS = [
    "大気汚染防止法", "大気汚染防止法施行令", "大気汚染防止法施行規則",
    "水質汚濁防止法", "水質汚濁防止法施行令", "水質汚濁防止法施行規則",
    "土壌汚染対策法", "土壌汚染対策法施行令", "土壌汚染対策法施行規則",
    "騒音規制法", "振動規制法", "悪臭防止法", 
    "廃棄物の処理及び清掃に関する法律", "海洋汚染等及び海上災害の防止に関する法律", "下水道法",
    "化学物質の審査及び製造等の規制に関する法律", "毒物及び劇物取締法", 
    "特定化学物質の環境への排出量の把握等及び管理の改善の促進に関する法律",
    "労働安全衛生法", "消防法", "高圧ガス保安法", "石油コンビナート等災害防止法", 
    "電気事業法", "工場立地法", "建築基準法",
    "外国為替及び外国貿易法", "船舶安全法", "航空法", "道路法", 
    "エネルギーの使用の合理化及び非化石エネルギーへの転換等に関する法律", 
    "地球温暖化対策の推進に関する法律"
]

API_LAWMAP_URL = "https://laws.e-gov.go.jp/api/1/lawlists/1"
API_LAWDATA_URL = "https://laws.e-gov.go.jp/api/1/lawdata/"

print("--- [フェーズ1] e-Gov APIから「全法令の目次データ（辞書）」を取得中... ---")
law_dict = {}

try:
    response_list = requests.get(API_LAWMAP_URL)
    response_list.encoding = 'utf-8'
    root_list = ET.fromstring(response_list.text)
    
    for law in root_list.findall(".//LawNameListInfo"):
        name = law.find("LawName").text
        law_id = law.find("LawId").text
        if name and law_id:
            law_dict[name] = law_id
            
    print(f"[OK] {len(law_dict)} 件の法令インデックスを構築しました。\n")
except Exception as e:
    print(f"[致命的エラー] 目次データの取得に失敗しました: {e}")
    exit()

print(f"--- [フェーズ2] 全 {len(TARGET_LAWS)} 件のターゲット法令の更新レーダー走査を開始 ---")
results = []

for law_name in TARGET_LAWS:
    print(f"[{law_name}] を照会中...")
    
    if law_name not in law_dict:
        print(f"  -> [警告] e-Govのデータベースに存在しません。名称不一致です。")
        results.append({
            "法令名": law_name,
            "最終改正（公布）法令": "取得失敗（名称不一致）",
            "確認ステータス": "要確認",
            "最終確認日": datetime.now().strftime("%Y-%m-%d")
        })
        continue

    law_id = law_dict[law_name]
    
    try:
        response = requests.get(API_LAWDATA_URL + law_id)
        response.encoding = 'utf-8'
        time.sleep(1) # サーバー負荷への配慮（絶対ルール）
        
        root = ET.fromstring(response.text)
        
        # 【修正箇所】エラー確認層の空間指定を修正（DataRootの中ではなく、直下のResultを探す）
        result_code = root.find(".//Result/Code")
        if result_code is not None and result_code.text != "0":
            print(f"  -> [警告] APIがデータを返しませんでした。")
            results.append({
                "法令名": law_name,
                "最終改正（公布）法令": "データ取得エラー（API応答なし）",
                "確認ステータス": "要確認",
                "最終確認日": datetime.now().strftime("%Y-%m-%d")
            })
            continue

        # e-Gov XMLの構造に基づく、最も堅牢な改正履歴（附則）の抽出
        suppl_provisions = root.findall(".//SupplProvision")
        amend_law_num_text = "改正履歴なし"
        
        if suppl_provisions:
            # 最後の附則（SupplProvision）が最新の改正データを持っている
            latest_suppl = suppl_provisions[-1]
            if "AmendLawNum" in latest_suppl.attrib:
                amend_law_num_text = latest_suppl.attrib["AmendLawNum"]
            else:
                label = latest_suppl.find("SupplProvisionLabel")
                if label is not None and label.text:
                    amend_law_num_text = f"（改正法令）{label.text}"
        
        results.append({
            "法令名": law_name,
            "最終改正（公布）法令": amend_law_num_text,
            "確認ステータス": "未確認", 
            "最終確認日": datetime.now().strftime("%Y-%m-%d")
        })

    except Exception as e:
        print(f"  -> [エラー] {law_name}: {e}")
        # 【修正箇所】例外発生時もシステムを止めず、エラー結果として台帳に必ず残す
        results.append({
            "法令名": law_name,
            "最終改正（公布）法令": f"取得失敗（例外発生: {type(e).__name__}）",
            "確認ステータス": "システムエラー",
            "最終確認日": datetime.now().strftime("%Y-%m-%d")
        })

# --- 3. 出力層（Excel台帳の生成） ---
# 【新設】outputディレクトリへの隔離
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True) # フォルダがなければ自動で作成する

df = pd.DataFrame(results)
output_file = os.path.join(OUTPUT_DIR, f"法令更新監視台帳_{datetime.now().strftime('%Y%m%d')}.xlsx")
df.to_excel(output_file, index=False)

print(f"\n--- 走査完了。結果を {output_file} に出力しました ---")