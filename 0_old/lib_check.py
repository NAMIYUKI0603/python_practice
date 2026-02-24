import pandas as pd
import openpyxl
import xlsxwriter

def main():
    print("-" * 40)
    print("Library Install Check")
    print("-" * 40)
    print(f"Pandas Version     : {pd.__version__}")
    print(f"Openpyxl Version   : {openpyxl.__version__}")
    print(f"Xlsxwriter Version : {xlsxwriter.__version__}")
    print("-" * 40)
    print("SUCCESS: すべてのライブラリが正常に読み込まれました。")
    print("-" * 40)

if __name__ == "__main__":
    main()