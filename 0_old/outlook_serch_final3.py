import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import win32com.client
import pythoncom
import datetime
import threading
import os
import csv

class OutlookSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Outlookメール履歴抽出ツール (Final v3)")
        self.root.geometry("650x650")

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

        # 4. 保存先（拡張子で分岐）
        tk.Label(root, text="4. 保存先 (拡張子 .txt または .csv を選択):").pack(anchor="w", padx=10, pady=(10, 0))
        save_frame = tk.Frame(root)
        save_frame.pack(anchor="w", padx=10, fill="x")

        self.filename_entry = tk.Entry(save_frame)
        self.filename_entry.pack(side="left", fill="x", expand=True)
        
        # デフォルトパス（デスクトップ）
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "mail_history_result.csv")
        self.filename_entry.insert(0, desktop_path)

        # 「参照」ボタン
        self.browse_button = tk.Button(save_frame, text="参照...", command=self.browse_save_location)
        self.browse_button.pack(side="left", padx=(5, 0))

        # 実行ボタン
        self.run_button = tk.Button(root, text="検索開始", command=self.start_search_thread, bg="#e0e0e0", height=2)
        self.run_button.pack(fill="x", padx=10, pady=15)

        # ログ
        tk.Label(root, text="処理ログ:").pack(anchor="w", padx=10)
        self.log_area = scrolledtext.ScrolledText(root, height=12)
        self.log_area.pack(fill="both", expand=True, padx=10, pady=5)

    def browse_save_location(self):
        """保存先ダイアログを開く"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile="mail_history_result.csv",
            title="保存先と形式を選択してください"
        )
        if file_path:
            self.filename_entry.delete(0, tk.END)
            self.filename_entry.insert(0, file_path)

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
        results = []  # 検索結果を一時保存するリスト

        try:
            outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
            
            try:
                start_dt = datetime.datetime.strptime(start_str, "%Y/%m/%d")
                end_dt = datetime.datetime.strptime(end_str, "%Y/%m/%d") + datetime.timedelta(days=1)
            except ValueError:
                self.log("エラー: 日付形式が不正です")
                return

            self.log(f"--- 検索開始: {target_account} ---")
            
            target_store = next((s for s in outlook.Stores if s.DisplayName == target_account), None)
            if not target_store:
                self.log("エラー: アカウントが見つかりません")
                return

            root_folder = target_store.GetRootFolder()

            # 再帰検索処理（ここでは書き込まず、resultsリストに追加するだけ）
            def search_recursive(folder):
                if folder.DefaultItemType != 0: return

                try:
                    items = folder.Items
                    # 検索段階ではソート不要（最後に一括ソートするため）
                    
                    for item in items:
                        try:
                            if item.Class != 43: continue 
                            r_time = item.ReceivedTime
                            if not (start_dt <= r_time.replace(tzinfo=None) < end_dt): continue
                            
                            sender = getattr(item, "SenderName", "")
                            sender_addr = getattr(item, "SenderEmailAddress", "")
                            subject = getattr(item, "Subject", "")
                            body = getattr(item, "Body", "")
                            
                            full_text = f"{sender} {sender_addr} {subject} {body}"
                            
                            if keyword.lower() in full_text.lower():
                                # ヒットしたらリストに追加
                                atts = [a.FileName for a in item.Attachments]
                                att_str = ", ".join(atts) if atts else "なし"
                                
                                # 結果辞書を作成
                                results.append({
                                    "datetime": r_time, # ソート用（datetimeオブジェクト）
                                    "date_str": r_time.strftime("%Y/%m/%d"), # CSV用
                                    "time_str": r_time.strftime("%H:%M:%S"), # CSV用
                                    "full_time_str": r_time.strftime("%Y/%m/%d %H:%M"), # txt用
                                    "subject": subject,
                                    "sender": f"{sender} ({sender_addr})",
                                    "body": body,
                                    "attachments": att_str,
                                    "folder": folder.Name
                                })
                                
                                # リアルタイムログ（50件ごとに表示など調整も可）
                                self.log(f"発見: {r_time.strftime('%Y/%m/%d %H:%M')} | {subject[:15]}...")

                        except Exception: continue
                    
                    for sub in folder.Folders: search_recursive(sub)
                except Exception as e: self.log(f"Skip: {folder.Name}")

            # 検索実行
            for folder in root_folder.Folders:
                search_recursive(folder)

            # --- 全検索終了後の処理 ---
            
            self.log("検索完了。時系列順に並び替え中...")
            
            # 1. 日付順にソート（古い順）
            results.sort(key=lambda x: x["datetime"])
            
            count = len(results)
            self.log(f"合計 {count} 件。ファイル書き込み中...")

            # 2. ファイル書き込み（拡張子で分岐）
            _, ext = os.path.splitext(filename)
            is_csv = ext.lower() == ".csv"

            if is_csv:
                # CSVモード (UTF-8 with BOM でExcel文字化け回避)
                with open(filename, "w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.writer(f)
                    # ヘッダー
                    writer.writerow(["年月日", "時刻", "件名", "内容", "送信者", "添付ファイル", "フォルダ"])
                    
                    for row in results:
                        writer.writerow([
                            row["date_str"],     # A列
                            row["time_str"],     # B列
                            row["subject"],      # C列
                            row["body"].strip(), # D列
                            row["sender"],       # E列（補足）
                            row["attachments"],  # F列（補足）
                            row["folder"]        # G列（補足）
                        ])
            else:
                # テキストモード
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"検索条件: {keyword} ({start_str} - {end_str})\n{'='*50}\n\n")
                    for i, row in enumerate(results, 1):
                        f.write(f"[{i}] {row['full_time_str']} | {row['folder']}\n")
                        f.write(f"件名: {row['subject']}\n")
                        f.write(f"送信: {row['sender']}\n")
                        f.write(f"添付: {row['attachments']}\n")
                        f.write("-" * 30 + "\n")
                        f.write(row['body'].strip()[:3000])
                        f.write("\n" + "="*50 + "\n\n")

            self.log(f"書き込み完了。")
            self.log(f"保存先: {filename}")
            messagebox.showinfo("完了", f"{count}件 抽出しました。\n\n保存先:\n{filename}")

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