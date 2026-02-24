import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import win32com.client
import pythoncom
import datetime
import threading
import os

class OutlookSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Outlookメール履歴抽出ツール (Final)")
        self.root.geometry("650x600")

        # アカウント一覧取得
        self.accounts = []
        try:
            temp_outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
            for store in temp_outlook.Stores:
                self.accounts.append(store.DisplayName)
        except Exception as e:
            messagebox.showerror("エラー", f"Outlookに接続できませんでした。\n{e}")

        # --- GUI配置 ---
        
        # 1. アカウント
        tk.Label(root, text="1. 対象アカウント:").pack(anchor="w", padx=10, pady=(10, 0))
        self.account_combo = ttk.Combobox(root, values=self.accounts, width=60)
        if self.accounts: self.account_combo.current(0)
        self.account_combo.pack(anchor="w", padx=10, pady=5)

        # 2. 期間
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

        # 3. キーワード
        tk.Label(root, text="3. 検索キーワード (アドレス, 社名, 件名, 本文):").pack(anchor="w", padx=10, pady=(10, 0))
        self.keyword_entry = tk.Entry(root, width=70)
        self.keyword_entry.pack(anchor="w", padx=10, pady=5)

        # 4. 保存先
        tk.Label(root, text="4. 保存ファイル名:").pack(anchor="w", padx=10, pady=(10, 0))
        self.filename_entry = tk.Entry(root, width=70)
        self.filename_entry.insert(0, "mail_history_result.txt")
        self.filename_entry.pack(anchor="w", padx=10, pady=5)

        # ボタン
        self.run_button = tk.Button(root, text="検索開始", command=self.start_search_thread, bg="#e0e0e0", height=2)
        self.run_button.pack(fill="x", padx=10, pady=15)

        # ログ
        tk.Label(root, text="処理ログ:").pack(anchor="w", padx=10)
        self.log_area = scrolledtext.ScrolledText(root, height=12)
        self.log_area.pack(fill="both", expand=True, padx=10, pady=5)

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def start_search_thread(self):
        target = self.account_combo.get()
        keyword = self.keyword_entry.get()
        start = self.start_date_entry.get()
        end = self.end_date_entry.get()
        filename = self.filename_entry.get()

        if not keyword:
            messagebox.showwarning("警告", "キーワードを入力してください")
            return

        self.run_button.config(state="disabled", text="検索中...")
        self.log_area.delete(1.0, tk.END)
        threading.Thread(target=self.run_search, args=(target, keyword, start, end, filename)).start()

    def run_search(self, target_account, keyword, start_str, end_str, filename):
        pythoncom.CoInitialize()
        try:
            outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
            
            try:
                start_dt = datetime.datetime.strptime(start_str, "%Y/%m/%d")
                end_dt = datetime.datetime.strptime(end_str, "%Y/%m/%d") + datetime.timedelta(days=1)
            except ValueError:
                self.log("エラー: 日付形式が不正です")
                return

            self.log(f"--- 開始: {target_account} ---")
            
            target_store = next((s for s in outlook.Stores if s.DisplayName == target_account), None)
            if not target_store:
                self.log("エラー: アカウントが見つかりません")
                return

            root_folder = target_store.GetRootFolder()
            found_count = 0

            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"検索条件: {keyword} ({start_str} - {end_str})\n{'='*50}\n\n")

                def search_recursive(folder):
                    nonlocal found_count
                    
                    # 【改良点】メールフォルダ(Type=0)以外は無視してスキップ
                    # 0=Mail, 1=Appt, 2=Contact, 3=Task
                    if folder.DefaultItemType != 0:
                        return

                    try:
                        items = folder.Items
                        items.Sort("[ReceivedTime]", False) # ここでのエラーが消えます

                        for item in items:
                            try:
                                if item.Class != 43: continue # メール以外除外
                                
                                # 日付判定
                                r_time = item.ReceivedTime
                                if not (start_dt <= r_time.replace(tzinfo=None) < end_dt):
                                    continue
                                
                                # 検索判定
                                sender = getattr(item, "SenderName", "")
                                sender_addr = getattr(item, "SenderEmailAddress", "")
                                subject = getattr(item, "Subject", "")
                                body = getattr(item, "Body", "")
                                
                                full_text = f"{sender} {sender_addr} {subject} {body}"
                                
                                if keyword.lower() in full_text.lower():
                                    found_count += 1
                                    
                                    # 添付ファイル
                                    atts = [a.FileName for a in item.Attachments]
                                    att_str = ", ".join(atts) if atts else "なし"
                                    
                                    time_str = r_time.strftime("%Y/%m/%d %H:%M")
                                    self.log(f"発見: {time_str} | {subject[:20]}...")
                                    
                                    f.write(f"[{found_count}] {time_str} | {folder.Name}\n")
                                    f.write(f"件名: {subject}\n")
                                    f.write(f"送信: {sender} ({sender_addr})\n")
                                    f.write(f"添付: {att_str}\n")
                                    f.write("-" * 30 + "\n")
                                    f.write(body.strip()[:3000]) # 3000文字制限
                                    f.write("\n" + "="*50 + "\n\n")

                            except Exception:
                                continue # 個別の読み取りエラーは無視

                        for sub in folder.Folders:
                            search_recursive(sub)

                    except Exception as e:
                        # それでもアクセス権限などでエラーが出た場合のみログ出力
                        self.log(f"Skip: {folder.Name} ({e})")

                for folder in root_folder.Folders:
                    search_recursive(folder)

            self.log("--- 完了 ---")
            self.log(f"合計 {found_count} 件抽出。")
            messagebox.showinfo("完了", f"{found_count}件 抽出しました。")

        except Exception as e:
            self.log(f"エラー: {e}")
            messagebox.showerror("エラー", str(e))
        finally:
            pythoncom.CoUninitialize()
            self.run_button.config(state="normal", text="検索開始")

if __name__ == "__main__":
    root = tk.Tk()
    OutlookSearchApp(root)
    root.mainloop()