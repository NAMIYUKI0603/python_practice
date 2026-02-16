import pandas as pd
import random
from datetime import datetime, timedelta

def create_sample_excel():
    # データ生成の設定
    rows = 100
    products = ['Product_A', 'Product_B', 'Product_C']
    factories = ['Factory_1', 'Factory_2']
    
    data = []
    base_date = datetime(2025, 11, 1)
    
    for i in range(rows):
        date = base_date + timedelta(days=random.randint(0, 30))
        product = random.choice(products)
        factory = random.choice(factories)
        quantity = random.randint(10, 100)
        unit_price = {'Product_A': 1000, 'Product_B': 2000, 'Product_C': 5000}[product]
        
        data.append([date, factory, product, quantity, unit_price])
    
    # DataFrameの作成（Excelのシートのようなもの）
    df = pd.DataFrame(data, columns=['Date', 'Factory', 'Product', 'Quantity', 'Unit_Price'])
    
    # Excelとして保存
    output_file = 'production_log.xlsx'
    df.to_excel(output_file, index=False)
    print(f"作成完了: {output_file}")

if __name__ == "__main__":
    create_sample_excel()