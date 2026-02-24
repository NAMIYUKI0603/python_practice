import pandas as pd

def analyze_data():
    # 1. データの読み込み
    # Excelを開く操作に相当
    input_file = 'production_log.xlsx'
    df = pd.read_excel(input_file)
    
    print("--- 元データ（最初の5行） ---")
    print(df.head())

    # 2. データの監査（重要）
    # データの型や欠損値を確認（会計実務での「データの整合性チェック」に相当）
    print("\n--- データの情報 ---")
    print(df.info())

    # 3. 列単位での計算（ベクトル演算）
    # VBAならForループを使うところを、Pandasなら1行で全行処理します
    # Excelの F列 = D列 * E列 に相当
    df['Total_Amount'] = df['Quantity'] * df['Unit_Price']

    # 4. 集計（ピボットテーブル）
    # 工場ごと、製品ごとの合計金額を算出
    summary = df.groupby(['Factory', 'Product'])[['Quantity', 'Total_Amount']].sum()
    
    print("\n--- 集計結果 ---")
    print(summary)

    # 5. 結果の出力
    output_file = 'production_summary.xlsx'
    summary.to_excel(output_file)
    print(f"\n集計結果を保存しました: {output_file}")

if __name__ == "__main__":
    analyze_data()