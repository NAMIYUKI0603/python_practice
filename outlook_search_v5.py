import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import win32com.client
import pythoncom
import datetime
import threading
import os
import csv
import traceback

class OutlookSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Outlookメール履歴抽出ツール (Final v5)")
        self.root.geometry("650x700") # 少し縦長に

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

        # 4. オプション（削除済み検索）
        option_frame = tk.Frame(root)
        option_frame.pack(anchor="w", padx=10, pady=5)
        
        self.search_deleted_var = tk.BooleanVar()
        self.search_deleted_var.set(False) # デフォルトはOFF
        
        self.chk_deleted = tk.Checkbutton(option_frame, text="削除済みアイテムも検索する（※時間がかかります）", variable=self.search_deleted_var)
        self.chk_deleted.pack(side="left")

        # 5. 保存先
        tk.Label(root, text="5. 保存先:").pack(anchor="w", padx=10, pady=(10, 0))
        save_frame = tk.Frame(root)
        save_frame.pack(anchor="w", padx=10, fill="x")

        self.filename_entry = tk.Entry(save_frame)
        self.filename_entry.pack(side="left", fill="x", expand=True)
        
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "mail_history_result.csv")
        self.filename_entry.insert(0, desktop_path)

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
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile="mail_history_result.csv",
            title="保存先を選択"
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
        is_search_deleted = self.search_deleted_var.get()

        if not keyword:
            messagebox.showwarning("警告", "キーワードを入力してください")
            return

        self.run_button.config(state="disabled", text="検索中...")
        self.log_area.delete(1.0, tk.END)
        
        # スレッド起動
        threading.Thread(target=self.run_search, args=(target, keyword, start, end, filename, is_search_deleted)).start()

    def run_search(self, target_account, keyword, start_str, end_str, filename, is_search_deleted):
        pythoncom.CoInitialize()
        results = []
        error_log_path = os.path.join(os.path.dirname(filename), "error_debug_log.txt")

        try:
            outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
            
            try:
                start_dt = datetime.datetime.strptime(start_str, "%Y/%m/%d")
                end_dt = datetime.datetime.strptime(end_str, "%Y/%m/%d") + datetime.timedelta(days=1)
            except ValueError:
                self.log("エラー: 日付形式が不正です")
                return

            self.log(f"--- 検索開始: {target_account} ---")
            if is_search_deleted:
                self.log("※削除済みアイテムも検索対象です（処理時間が長くなります）")
            
            target_store = next((s for s in outlook.Stores if s.DisplayName == target_account), None)
            if not target_store:
                self.log("エラー: アカウントが見つかりません")
                return

            root_folder = target_store.GetRootFolder()

            # 再帰検索関数
            def search_recursive(folder):
                # フォルダ判定
                folder_name_lower = folder.Name.lower()
                is_deleted_folder = "削除" in folder.Name or "deleted" in folder_name_lower
                is_junk_folder = "迷惑" in folder.Name or "junk" in folder_name_lower

                # 迷惑メールは常にスキップ（必要なら外してください）
                if is_junk_folder:
                    return

                # 削除済みアイテムのスキップ判定
                if is_deleted_folder and not is_search_deleted:
                    self.log(f"スキップ: {folder.Name} (チェックOFFのため)")
                    return

                if folder.DefaultItemType != 0: return

                try:
                    items = folder.Items
                    item_count = items.Count
                    
                    # 大量アイテム時のログ表示
                    if item_count > 1000:
                        self.log(f"フォルダ [{folder.Name}] をスキャン中... (全 {item_count} 件)")
                    
                    # カウンタ（進捗表示用）
                    scanned = 0
                    
                    # ループ処理（新しい順に取得したほうがヒットしやすいので逆順推奨だが、全件走査のためそのまま回す）
                    for item in items:
                        scanned += 1
                        # 500件ごとにログ更新（フリーズ防止の生存報告）
                        if scanned % 500 == 0:
                            self.log(f"  ... {scanned} / {item_count} 件目を確認中")

                        try:
                            if item.Class != 43: continue 
                            r_time = item.ReceivedTime
                            
                            # 日付フィルタ（ここで弾くのが高速化の鍵）
                            # タイムゾーン情報を除去して比較
                            if not (start_dt <= r_time.replace(tzinfo=None) < end_dt): continue
                            
                            # ここまで来て初めて重いテキスト取得を行う
                            sender = getattr(item, "SenderName", "")
                            sender_addr = getattr(item, "SenderEmailAddress", "")
                            subject = getattr(item, "Subject", "")
                            body = getattr(item, "Body", "")
                            
                            full_text = f"{sender} {sender_addr} {subject} {body}"
                            
                            if keyword.lower() in full_text.lower():
                                atts = [a.FileName for a in item.Attachments]
                                att_str = ", ".join(atts) if atts else "なし"
                                
                                results.append({
                                    "datetime": r_time,
                                    "date_str": r_time.strftime("%Y/%m/%d"),
                                    "time_str": r_time.strftime("%H:%M:%S"),
                                    "full_time_str": r_time.strftime("%Y/%m/%d %H:%M"),
                                    "subject": subject,
                                    "sender": f"{sender} ({sender_addr})",
                                    "body": body,
                                    "attachments": att_str,
                                    "folder": folder.Name
                                })
                                self.log(f"発見: {r_time.strftime('%Y/%m/%d %H:%M')} | {subject[:15]}...")

                        except Exception:
                            continue # 個別の破損メールは無視
                    
                    # サブフォルダも探索
                    for sub in folder.Folders: search_recursive(sub)

                except Exception as e:
                    # フォルダ自体にアクセスできない場合のエラー処理
                    err_msg = f"フォルダアクセスエラー [{folder.Name}]: {str(e)}\n"
                    with open(error_log_path, "a", encoding="utf-8") as err_f:
                        err_f.write(err_msg)
                    self.log(f"警告: {folder.Name} をスキップしました (ログ参照)")

            # 検索実行
            for folder in root_folder.Folders:
                search_recursive(folder)

            # --- 終了処理 ---
            self.log("検索完了。並び替え中...")
            results.sort(key=lambda x: x["datetime"])
            
            count = len(results)
            self.log(f"合計 {count} 件。ファイル書き込み中...")

            _, ext = os.path.splitext(filename)
            is_csv = ext.lower() == ".csv"

            if is_csv:
                with open(filename, "w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["年月日", "時刻", "件名", "内容", "送信者", "添付ファイル", "フォルダ"])
                    for row in results:
                        writer.writerow([row["date_str"], row["time_str"], row["subject"], row["body"].strip(), row["sender"], row["attachments"], row["folder"]])
            else:
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

            self.log(f"保存先: {filename}")
            messagebox.showinfo("完了", f"{count}件 抽出しました。\n\n保存先:\n{filename}")

        except Exception as e:
            # 全体エラー
            err_msg = f"全体エラー: {str(e)}\n{traceback.format_exc()}\n"
            with open(error_log_path, "a", encoding="utf-8") as err_f:
                err_f.write(err_msg)
            self.log(f"エラー発生: {e}")
            messagebox.showerror("エラー", f"エラーが発生しました。\n{e}")

        finally:
            pythoncom.CoUninitialize()
            self.run_button.config(state="normal", text="検索開始")

if __name__ == "__main__":
    root = tk.Tk()
    OutlookSearchApp(root)
    root.mainloop()