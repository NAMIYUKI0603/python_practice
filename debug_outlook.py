import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import win32com.client
import pythoncom

class OutlookDebugApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Outlookフォルダ構造診断ツール")
        self.root.geometry("600x500")

        self.accounts = []
        try:
            outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
            for store in outlook.Stores:
                self.accounts.append(store.DisplayName)
        except Exception:
            self.accounts = ["エラー: 接続不可"]

        tk.Label(root, text="調子が悪いアカウントを選択してください:").pack(anchor="w", padx=10, pady=10)
        self.account_combo = ttk.Combobox(root, values=self.accounts, width=60)
        if self.accounts: self.account_combo.current(0)
        self.account_combo.pack(anchor="w", padx=10)

        tk.Button(root, text="フォルダ構造を確認", command=self.run_diagnosis, bg="#ffcccc").pack(pady=10)

        self.log_area = scrolledtext.ScrolledText(root, height=20)
        self.log_area.pack(fill="both", expand=True, padx=10, pady=5)

    def log(self, msg):
        self.log_area.insert(tk.END, msg + "\n")
        self.log_area.see(tk.END)

    def run_diagnosis(self):
        target = self.account_combo.get()
        self.log_area.delete(1.0, tk.END)
        self.log(f"--- 診断開始: {target} ---")
        
        try:
            outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
            target_store = next((s for s in outlook.Stores if s.DisplayName == target), None)
            
            if not target_store:
                self.log("エラー: アカウントが見つかりません")
                return

            root = target_store.GetRootFolder()
            self.log(f"ルートフォルダ名: {root.Name}")
            self.log(f"ルートパス: {root.FolderPath}")
            self.log("-" * 30)

            # 第1階層のフォルダをすべてリストアップ
            if len(root.Folders) == 0:
                self.log("【異常検知】ルート直下にフォルダが1つもありません。")
                self.log("→ 原因可能性: アカウント設定の同期期間制限、またはアクセス権限。")
            else:
                for f in root.Folders:
                    # フォルダの種類 (0=Mail, 1=Appt, 2=Contact...)
                    type_str = "その他"
                    if f.DefaultItemType == 0: type_str = "メール"
                    elif f.DefaultItemType == 1: type_str = "予定表"
                    elif f.DefaultItemType == 2: type_str = "連絡先"

                    count = 0
                    try: count = f.Items.Count
                    except: count = "?"
                    
                    self.log(f"フォルダ: [{f.Name}] (種類: {type_str}, アイテム数: {count})")
                    
                    # 受信トレイの中身を少し覗く
                    if f.Name == "受信トレイ" or f.Name == "Inbox":
                        self.log("  → 受信トレイを発見しました。サブフォルダを確認します...")
                        for sub in f.Folders:
                            self.log(f"    - サブフォルダ: {sub.Name}")

            self.log("-" * 30)
            self.log("診断完了")

        except Exception as e:
            self.log(f"エラー発生: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    OutlookDebugApp(root)
    root.mainloop()