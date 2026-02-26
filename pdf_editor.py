import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pypdf import PdfReader, PdfWriter
import os

class SimplePDFEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("簡易PDFエディタ (回転・分割)")
        self.root.geometry("500x400")
        self.root.resizable(False, False)

        # UI要素の配置 (上から下へのフロー)
        
        # 1. 入力ファイル
        tk.Label(root, text="1. 対象のPDFファイル:").pack(anchor="w", padx=15, pady=(15, 5))
        frame_in = tk.Frame(root)
        frame_in.pack(fill="x", padx=15)
        self.entry_in = tk.Entry(frame_in, width=50)
        self.entry_in.pack(side="left", fill="x", expand=True)
        tk.Button(frame_in, text="参照...", command=self.select_input).pack(side="left", padx=5)

        # 2. 対象ページ
        tk.Label(root, text="2. 対象ページ (例: 1-3, 5 または all):").pack(anchor="w", padx=15, pady=(15, 5))
        self.entry_pages = tk.Entry(root)
        self.entry_pages.insert(0, "all")
        self.entry_pages.pack(fill="x", padx=15)

        # 3. 処理アクション
        tk.Label(root, text="3. 実行する処理:").pack(anchor="w", padx=15, pady=(15, 5))
        self.action_var = tk.StringVar(value="rot90R")
        frame_action = tk.Frame(root)
        frame_action.pack(anchor="w", padx=15)
        
        ttk.Radiobutton(frame_action, text="右に90度回転", variable=self.action_var, value="rot90R").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Radiobutton(frame_action, text="左に90度回転", variable=self.action_var, value="rot90L").grid(row=0, column=1, sticky="w", padx=5, pady=5)
        ttk.Radiobutton(frame_action, text="180度回転", variable=self.action_var, value="rot180").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Radiobutton(frame_action, text="指定ページのみ抽出(分割)", variable=self.action_var, value="extract").grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # 4. 実行ボタン
        tk.Button(root, text="名前を付けて保存＆実行", command=self.process_pdf, bg="#4CAF50", fg="white", font=("", 12, "bold"), height=2).pack(fill="x", padx=15, pady=25)

    def select_input(self):
        filepath = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if filepath:
            self.entry_in.delete(0, tk.END)
            self.entry_in.insert(0, filepath)

    def parse_pages(self, page_str, total_pages):
        """ページ指定の文字列をパースし、0始まりのインデックスリストを返す"""
        pages = set()
        page_str = page_str.replace(" ", "").lower()
        
        if page_str == "all" or page_str == "":
            return list(range(total_pages))
            
        try:
            for part in page_str.split(','):
                if '-' in part:
                    start, end = part.split('-')
                    # ユーザー入力は1始まりなので、-1して0始まりのインデックスに合わせる
                    start_idx = max(0, int(start) - 1)
                    end_idx = min(total_pages, int(end))
                    pages.update(range(start_idx, end_idx))
                else:
                    idx = int(part) - 1
                    if 0 <= idx < total_pages:
                        pages.add(idx)
            return sorted(list(pages))
        except ValueError:
            raise ValueError("ページ指定の形式が不正です。")

    def process_pdf(self):
        in_path = self.entry_in.get()
        if not os.path.exists(in_path):
            messagebox.showerror("エラー", "入力ファイルが見つかりません。")
            return

        out_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")], title="保存先を選択")
        if not out_path:
            return # キャンセル時

        action = self.action_var.get()
        page_str = self.entry_pages.get()

        try:
            reader = PdfReader(in_path)
            writer = PdfWriter()
            total_pages = len(reader.pages)
            
            target_indices = self.parse_pages(page_str, total_pages)
            if not target_indices:
                messagebox.showwarning("警告", "対象となるページがありません。")
                return

            if action == "extract":
                # 分割抽出：指定されたページのみを新しいPDFに書き出す
                for i in target_indices:
                    writer.add_page(reader.pages[i])
            else:
                # 回転：全ページを出力対象とするが、指定ページのみ回転を適用する
                for i in range(total_pages):
                    page = reader.pages[i]
                    if i in target_indices:
                        if action == "rot90R":
                            page.rotate(90)
                        elif action == "rot90L":
                            page.rotate(-90)
                        elif action == "rot180":
                            page.rotate(180)
                    writer.add_page(page)

            with open(out_path, "wb") as f:
                writer.write(f)
                
            messagebox.showinfo("完了", f"処理が完了しました。\n保存先: {out_path}")

        except Exception as e:
            messagebox.showerror("エラー", f"処理中にエラーが発生しました:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SimplePDFEditor(root)
    root.mainloop()