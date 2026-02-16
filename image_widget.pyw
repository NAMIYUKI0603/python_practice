import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

class DesktopWidget:
    def __init__(self, root):
        self.root = root
        
        # 1. 画像を選択
        file_path = filedialog.askopenfilename(
            title="表示するショートカット画像を選択",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        if not file_path:
            root.destroy()
            return

        # 画像読み込み
        self.original_image = Image.open(file_path)
        self.tk_image = ImageTk.PhotoImage(self.original_image)

        # 2. ウィンドウ設定
        self.root.attributes('-topmost', True)  # 常に最前面
        self.root.overrideredirect(True)       # タイトルバーを消す（フレームレス）
        
        # ウィンドウサイズを画像に合わせる
        w, h = self.original_image.size
        # 画面右上に配置する計算（お好みで調整可）
        screen_w = self.root.winfo_screenwidth()
        x_pos = screen_w - w - 50
        self.root.geometry(f"{w}x{h}+{x_pos}+50")

        # 3. 画像表示ラベル
        self.label = tk.Label(root, image=self.tk_image, bg='black')
        self.label.pack(fill='both', expand=True)

        # 4. イベント設定
        self.label.bind("<Button-1>", self.start_move)   # クリック開始
        self.label.bind("<B1-Motion>", self.do_move)     # ドラッグ中
        self.label.bind("<Double-1>", self.close_app)    # ダブルクリックで終了
        
        # 右クリックメニュー
        self.menu = tk.Menu(root, tearoff=0)
        self.menu.add_command(label="閉じる", command=self.close_app)
        self.label.bind("<Button-3>", self.show_menu)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def show_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def close_app(self, event=None):
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    # 起動時に一瞬出る白い枠を消すための設定
    root.withdraw()
    app = DesktopWidget(root)
    root.deiconify()
    root.mainloop()