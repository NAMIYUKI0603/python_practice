import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import win32com.client
import pythoncom  # 【追加】これが必要です
import datetime
import threading
import os

class OutlookSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Outlookメール履歴抽出ツール")
        self.root.geometry("600x550")

        # アカウント一覧取得用の一時的な接続
        self.accounts = []
        try:
            temp_outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
            for store in temp_outlook.Stores:
                self.accounts.append(store.DisplayName)
        except Exception as e:
            messagebox.showerror("エラー", f"Outlookに接続できませんでした。\n{e}")

        # --- GUIの配置 ---
        
        # 1. 対象アカウント選択
        tk.Label(root, text="1. 対象アカウント（メールアドレス）:").pack(anchor="w", padx=10, pady=(10, 0))
        self.account_combo = ttk.Combobox(root, values=self.accounts, width=50)
        if self.accounts:
            self.account_combo.current(0)
        self.account_combo.pack(anchor="w", padx=10, pady=5)

        # 2. 検索期間
        tk.Label(root, text="2. 検索期間 (yyyy/mm/dd):").pack(anchor="w", padx=10, pady=(10, 0))
        date_frame = tk.Frame(root)
        date_frame.pack(anchor="w", padx=10)
        
        today = datetime.date.today()
        last_year = today - datetime.timedelta(days=365)
        
        self.start_date_entry = tk.Entry(date_frame, width=15)
        self.start_date_entry.insert(0, last_year.strftime("%Y/%m/%d"))
        self.start_date_entry.pack(side="left")
        
        tk.Label(date_frame, text=" ～ ").pack(side="left")
        
        self.end_date_entry = tk.Entry(date_frame, width=15)
        self.end_date_entry.insert(0, today.strftime("%Y/%m/%d"))
        self.end_date_entry.pack(side="left")

        # 3. 検索キーワード
        tk.Label(root, text="3. 検索キーワード (相手のアドレス、社名、氏名の一部):").pack(anchor="w", padx=10, pady=(10, 0))
        self.keyword_entry = tk.Entry(root, width=60)
        self.keyword_entry.pack(anchor="w", padx=10, pady=5)

        # 4. 保存ファイル名
        tk.Label(root, text="4. 保存ファイル名 (.txt):").pack(anchor="w", padx=10, pady=(10, 0))
        self.filename_entry = tk.Entry(root, width=60)
        self.filename_entry.insert(0, "mail_history_result.txt")
        self.filename_entry.pack(anchor="w", padx=10, pady=5)

        # 実行ボタン
        self.run_button = tk.Button(root, text="検索開始", command=self.start_search_thread, bg="#dddddd", height=2)
        self.run_button.pack(fill="x", padx=10, pady=15)

        # ログ表示エリア
        tk.Label(root, text="処理ログ:").pack(anchor="w", padx=10)
        self.log_area = scrolledtext.ScrolledText(root, height=10)
        self.log_area.pack(fill="both", expand=True, padx=10, pady=5)

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def start_search_thread(self):
        target_account = self.account_combo.get()
        keyword = self.keyword_entry.get()
        start_str = self.start_date_entry.get()
        end_str = self.end_date_entry.get()
        filename = self.filename_entry.get()

        if not keyword:
            messagebox.showwarning("警告", "検索キーワードを入力してください")
            return

        self.run_button.config(state="disabled", text="検索中...")
        self.log_area.delete(1.0, tk.END)
        
        thread = threading.Thread(target=self.run_search, args=(target_account, keyword, start_str, end_str, filename))
        thread.start()

    def run_search(self, target_account, keyword, start_str, end_str, filename):
        # 【修正】スレッド内でCOMを使うための初期化
        pythoncom.CoInitialize()
        
        try:
            # 【修正】スレッド内で再度Outlookに接続（これが安全です）
            outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")

            try:
                start_dt = datetime.datetime.strptime(start_str, "%Y/%m/%d")
                end_dt = datetime.datetime.strptime(end_str, "%Y/%m/%d") + datetime.timedelta(days=1)
            except ValueError:
                self.log("エラー: 日付の形式が正しくありません (yyyy/mm/dd)")
                self.run_button.config(state="normal", text="検索開始")
                return

            self.log(f"--- 開始: {target_account} 内を検索 ---")
            self.log(f"キーワード: {keyword}")

            target_store = None
            for store in outlook.Stores:
                if store.DisplayName == target_account:
                    target_store = store
                    break
            
            if not target_store:
                self.log("エラー: 指定されたアカウントが見つかりません")
                return

            root_folder = target_store.GetRootFolder()
            found_count = 0

            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"検索条件: {keyword} ({start_str} - {end_str})\n")
                f.write("="*50 + "\n\n")

                def search_recursive(folder):
                    nonlocal found_count
                    try:
                        items = folder.Items
                        items.Sort("[ReceivedTime]", False)

                        for item in items:
                            try:
                                if item.Class != 43: continue
                                
                                # 日付比較（簡易版）
                                received_time = item.ReceivedTime
                                received_dt_naive = received_time.replace(tzinfo=None)

                                if not (start_dt <= received_dt_naive < end_dt):
                                    continue

                                try: sender = item.SenderName
                                except: sender = ""
                                try: sender_addr = item.SenderEmailAddress
                                except: sender_addr = ""
                                subject = item.Subject
                                body = item.Body
                                
                                full_text = f"{sender} {sender_addr} {subject} {body}"

                                if keyword.lower() in full_text.lower():
                                    found_count += 1
                                    
                                    attachments_list = []
                                    for attachment in item.Attachments:
                                        attachments_list.append(attachment.FileName)
                                    attachment_str = ", ".join(attachments_list) if attachments_list else "なし"

                                    timestamp_str = received_time.strftime("%Y/%m/%d %H:%M:%S")
                                    
                                    header = f"[{found_count}] 日時: {timestamp_str} | 場所: {folder.Name}"
                                    self.log(f"発見: {timestamp_str} - {subject[:15]}...")
                                    
                                    f.write(f"{header}\n")
                                    f.write(f"件名: {subject}\n")
                                    f.write(f"送信者: {sender} ({sender_addr})\n")
                                    f.write(f"添付ファイル: {attachment_str}\n")
                                    f.write("-" * 30 + "\n")
                                    f.write(body.strip()[:2000])
                                    f.write("\n" + "="*50 + "\n\n")

                            except Exception:
                                continue

                        for sub in folder.Folders:
                            search_recursive(sub)

                    except Exception as e:
                        self.log(f"フォルダアクセス警告: {folder.Name} - {e}")

                for folder in root_folder.Folders:
                    search_recursive(folder)

            self.log(f"--- 完了 ---")
            self.log(f"合計 {found_count} 件抽出しました。")
            messagebox.showinfo("完了", f"検索が完了しました。\n{found_count}件抽出しました。")

        except Exception as e:
            self.log(f"致命的なエラー: {e}")
            messagebox.showerror("エラー", str(e))
        
        finally:
            # 【修正】後片付け
            pythoncom.CoUninitialize()
            self.run_button.config(state="normal", text="検索開始")

if __name__ == "__main__":
    root = tk.Tk()
    app = OutlookSearchApp(root)
    root.mainloop()