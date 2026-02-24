import win32com.client
import os

# ==========================================
# 【設定】ここだけ書き換えてください
# ==========================================
# 検索したい相手のアドレス、または名前、社名の一部
TARGET_KEYWORD = "info@smartlife.go.jp"

# 結果を保存するファイル名
OUTPUT_FILE = "mail_history_result.txt"
# ==========================================

def main():
    print("Outlookに接続中...")
    try:
        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        root_folder = outlook.Folders.Item(1) # 通常は1番目がメインアカウント
        print(f"対象アカウント: {root_folder.Name}")
    except Exception as e:
        print(f"エラー: Outlookが開いていないか、接続できません。Outlookを起動してから再試行してください。\n詳細: {e}")
        return

    print(f"キーワード '{TARGET_KEYWORD}' で検索を開始します...")
    print("※メール数によっては数分かかります。そのままお待ちください...")

    found_count = 0
    
    # 書き込みモード (utf-8で保存)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"【検索キーワード】 {TARGET_KEYWORD}\n")
        f.write(f"【実行日時】 {os.path.getmtime(os.getcwd())}\n") # ダミー日時ではなく現在時刻推奨ですがimport省略のため簡易化
        f.write("="*50 + "\n\n")

        # 再帰的に全フォルダを検索する関数
        def search_folders(folder):
            nonlocal found_count
            try:
                # フォルダ内のアイテムを取得
                items = folder.Items
                # 日付の新しい順に並べ替え
                items.Sort("[ReceivedTime]", True)

                for item in items:
                    try:
                        # メールアイテム以外（会議など）はスキップ
                        if item.Class != 43: continue

                        # 検索対象: 件名、本文、送信者名、送信元アドレス
                        # アドレス取得はエラーになりやすいので安全策をとる
                        try:
                            sender_addr = item.SenderEmailAddress
                        except:
                            sender_addr = ""
                        
                        full_text = f"{item.Subject} {item.SenderName} {sender_addr} {item.Body}"

                        if TARGET_KEYWORD.lower() in full_text.lower():
                            # ヒットした場合
                            received_time = str(item.ReceivedTime)[:19] # 秒まで取得
                            
                            f.write(f"日時: {received_time}\n")
                            f.write(f"件名: {item.Subject}\n")
                            f"送信者: {item.SenderName} ({sender_addr})\n"
                            f"--------------------------------------------------\n"
                            # 本文は長すぎる場合、最初の500文字だけにする等の調整も可（今回は全文）
                            f.write(item.Body.strip() + "\n") 
                            f.write("="*50 + "\n\n")
                            
                            found_count += 1
                            print(f"発見 ({found_count}件目): {received_time} - {item.Subject}")

                    except Exception:
                        continue # 個別の読み取りエラーは無視して次へ

                # サブフォルダも検索
                for sub in folder.Folders:
                    search_folders(sub)

            except Exception:
                pass # フォルダアクセス権限エラー等は無視

        # 検索実行（受信トレイなどを起点にする場合は root_folder.Folders['受信トレイ'] 等に変更可）
        # ここではアカウント全体を走査します
        for folder in root_folder.Folders:
            # 「削除済みアイテム」などは除外しても良い
            if "削除" in folder.Name: continue
            search_folders(folder)

    print(f"\n完了！ 合計 {found_count} 件のメールが見つかりました。")
    print(f"結果は '{OUTPUT_FILE}' に保存されました。")

if __name__ == "__main__":
    main()