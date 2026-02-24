import sys
import os

def main():
    """実行環境の情報を表示するスクリプト"""
    
    print("-" * 30)
    print("VS Code Python 環境検証")
    print("-" * 30)
    
    # Pythonのバージョン確認
    print(f"Python Version : {sys.version.split()[0]}")
    
    # 実行ファイルの場所（パス）確認
    print(f"Current Path   : {os.getcwd()}")
    
    print("-" * 30)
    print("SUCCESS: 正常に動作しています。")
    print("-" * 30)

if __name__ == "__main__":
    main()