import win32com.client

try:
    # Outlookアプリを呼び出してみる
    outlook = win32com.client.Dispatch("Outlook.Application")
    print("成功：Outlookを認識できました！")
except Exception as e:
    print(f"エラー：{e}")