import os
import requests
from requests.exceptions import RequestException, Timeout
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime
import time

# --- 1. 空間設計：監視対象と接続先 ---
TARGET_LAWS = [
    "大気汚染防止法", "大気汚染防止法施行令", "大気汚染防止法施行規則",
    "水質汚濁防止法", "水質汚濁防止法施行令", "水質汚濁防止法施行規則",
    "土壌汚染対策法", "土壌汚染対策法施行令", "土壌汚染対策法施行規則",
    "騒音規制法", "騒音規制法施行令", "騒音規制法施行規則", 
    "振動規制法", "振動規制法施行令", "振動規制法施行規則",  
    "悪臭防止法",   
    "廃棄物の処理及び清掃に関する法律", "廃棄物の処理及び清掃に関する法律施行令", "廃棄物の処理及び清掃に関する法律施行規則", 
    "下水道法", 
    "浄化槽法", 
    "環境基本法", 
    "災害対策基本法", "災害対策基本法施行令", "災害対策基本法施行規則", 
    "化学物質の審査及び製造等の規制に関する法律",  
    "特定化学物質の環境への排出量の把握等及び管理の改善の促進に関する法律", 
    "特定化学物質の環境への排出量の把握等及び管理の改善の促進に関する法律施行令",
    "消防法", "消防法施行令", "消防法施行規則",  
    "外国為替及び外国貿易法", 
    "エネルギーの使用の合理化及び非化石エネルギーへの転換等に関する法律", "エネルギーの使用の合理化及び非化石エネルギーへの転換等に関する法律施行令", "エネルギーの使用の合理化及び非化石エネルギーへの転換等に関する法律施行規則",  
    "地球温暖化対策の推進に関する法律", "地球温暖化対策の推進に関する法律施行令", "地球温暖化対策の推進に関する法律施行規則",  
    "建築物のエネルギー消費性能の向上等に関する法律", 
    "建築物のエネルギー消費性能の向上等に関する法律施行令", 
    "建築物のエネルギー消費性能の向上等に関する法律施行規則", 
    "フロン類の使用の合理化及び管理の適正化に関する法律", "フロン類の使用の合理化及び管理の適正化に関する法律施行令", "フロン類の使用の合理化及び管理の適正化に関する法律施行規則"
    "特定家庭用機器再商品化法", 
    "使用済小型電子機器等の再資源化の促進に関する法律", 
    "使用済自動車の再資源化等に関する法律", 
    "ポリ塩化ビフェニル廃棄物の適正な処理の推進に関する特別措置法", 
    "ポリ塩化ビフェニル廃棄物の適正な処理の推進に関する特別措置法施行令",
    "ポリ塩化ビフェニル廃棄物の適正な処理の推進に関する特別措置法施行規則", 
    "毒物及び劇物取締法", "毒物及び劇物取締法施行令", "毒物及び劇物指定令", "毒物及び劇物取締法施行規則", 
    "労働安全衛生法", "労働安全衛生法施行令", "労働安全衛生規則", 
    "特定工場における公害防止組織の整備に関する法律", "特定工場における公害防止組織の整備に関する法律施行令", "特定工場における公害防止組織の整備に関する法律施行規則",
]

API_LAWMAP_URL = "https://laws.e-gov.go.jp/api/1/lawlists/1"
API_LAWDATA_URL = "https://laws.e-gov.go.jp/api/1/lawdata/"

# --- 2. 第1フェーズ：法令インデックス（辞書）の構築 ---
print("--- [フェーズ1] e-Gov APIから「全法令の目次データ」を取得中... ---")
law_dict = {}

try:
    # ここにも10秒の安全弁を設置
    response_list = requests.get(API_LAWMAP_URL, timeout=10)
    response_list.raise_for_status()
    response_list.encoding = 'utf-8'
    root_list = ET.fromstring(response_list.text)
    
    for law in root_list.findall(".//LawNameListInfo"):
        name = law.find("LawName").text
        law_id = law.find("LawId").text
        if name and law_id:
            law_dict[name] = law_id
            
    print(f"[OK] {len(law_dict)} 件の法令インデックスを構築完了。\n")

except (Timeout, RequestException) as e:
    print(f"[致命的エラー] 目次データの通信に失敗しました。ネットワークを確認してください: {e}")
    exit()
except Exception as e:
    print(f"[致命的エラー] 目次データの解析に失敗しました: {e}")
    exit()

# --- 3. 第2フェーズ：メインパイプライン（更新レーダー走査） ---
print(f"--- [フェーズ2] 全 {len(TARGET_LAWS)} 件のターゲット法令の走査を開始 ---")
results = []

for law_name in TARGET_LAWS:
    print(f"[{law_name}] を照会中...")
    
    # 辞書に存在しない場合のスキップ処理
    if law_name not in law_dict:
        print(f"  -> [警告] e-Govデータベースに名称が存在しません。")
        results.append({
            "法令名": law_name,
            "最終改正（公布）法令": "取得失敗（名称不一致）",
            "確認ステータス": "要確認",
            "最終確認日": datetime.now().strftime("%Y-%m-%d")
        })
        continue

    law_id = law_dict[law_name]
    
    try:
        # 【中核の改修】timeout=10 を設定し、無限フリーズを物理的に遮断する
        response = requests.get(API_LAWDATA_URL + law_id, timeout=10)
        response.raise_for_status() # 200番台以外のHTTPエラーを検知して例外に飛ばす
        response.encoding = 'utf-8'
        
        root = ET.fromstring(response.text)
        
        # XML構造のエラー確認
        result_code = root.find(".//Result/Code")
        if result_code is not None and result_code.text != "0":
            print(f"  -> [警告] APIが有効なデータを返しませんでした。")
            results.append({
                "法令名": law_name,
                "最終改正（公布）法令": "データ取得エラー（API応答異常）",
                "確認ステータス": "要確認",
                "最終確認日": datetime.now().strftime("%Y-%m-%d")
            })
            continue

        # 改正履歴（附則）の抽出
        suppl_provisions = root.findall(".//SupplProvision")
        amend_law_num_text = "改正履歴なし"
        
        if suppl_provisions:
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

    except Timeout:
        print(f"  -> [エラー] 応答がタイムアウトしました。この法令はスキップします。")
        results.append({
            "法令名": law_name,
            "最終改正（公布）法令": "取得失敗（タイムアウト）",
            "確認ステータス": "システムエラー",
            "最終確認日": datetime.now().strftime("%Y-%m-%d")
        })
    except RequestException as e:
        print(f"  -> [エラー] 通信障害が発生しました。")
        results.append({
            "法令名": law_name,
            "最終改正（公布）法令": "取得失敗（通信障害）",
            "確認ステータス": "システムエラー",
            "最終確認日": datetime.now().strftime("%Y-%m-%d")
        })
    except Exception as e:
        print(f"  -> [エラー] 予期せぬエラー: {e}")
        results.append({
            "法令名": law_name,
            "最終改正（公布）法令": f"取得失敗（例外発生: {type(e).__name__}）",
            "確認ステータス": "システムエラー",
            "最終確認日": datetime.now().strftime("%Y-%m-%d")
        })
    finally:
        # 【中核の改修】成功・失敗にかかわらず、ここで必ず冷却期間を設ける
        time.sleep(1.5)

# --- 4. 第3フェーズ：出力層（Excel台帳の生成） ---
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.DataFrame(results)
output_file = os.path.join(OUTPUT_DIR, f"法令更新監視台帳_{datetime.now().strftime('%Y%m%d')}.xlsx")
df.to_excel(output_file, index=False)

print(f"\n--- 走査完了。結果を {output_file} に出力しました ---")