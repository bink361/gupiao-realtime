"""
获取所有股票实时数据并保存为TXT文件
用于GitCode定时任务部署
"""
import easyquotation as eq
import pandas as pd
from datetime import datetime
import os
import sys


def load_stock_codes(excel_path='stock_data.xlsx'):
    """从Excel加载股票代码列表"""
    try:
        df = pd.read_excel(excel_path)
        codes = df['股票代码'].tolist()
    except FileNotFoundError:
        print(f"文件 {excel_path} 不存在，使用默认股票列表")
        codes = []
        # 沪市A股 600000-603999, 688000-688999
        for i in range(600000, 604000):
            codes.append(str(i))
        for i in range(688000, 689100):
            codes.append(str(i))
        # 深市A股 000000-003999, 300000-303999
        for i in range(1, 4000):
            codes.append(str(i).zfill(6))
        for i in range(300000, 304000):
            codes.append(str(i))
    
    # 清理代码格式：sz000001 -> 000001, sh600000 -> 600000
    stock_codes = []
    for code in codes:
        code = str(code)
        if code.startswith('sz'):
            stock_codes.append(code[2:])
        elif code.startswith('sh'):
            stock_codes.append(code[2:])
        elif code.isdigit() and len(code) == 6:
            stock_codes.append(code)
    
    return stock_codes


def convert_to_db_format(data):
    """
    将API返回的数据转换为数据库格式
    与stocks_api.py的convert_to_db_format保持一致
    """
    results = []
    
    for code, info in data.items():
        # 从datetime字段提取交易日期和更新时间
        datetime_obj = info.get('datetime')
        if datetime_obj:
            if isinstance(datetime_obj, str):
                if ' ' in datetime_obj:
                    trade_date = datetime_obj.split(' ')[0]
                    trade_time = datetime_obj.split(' ')[1]
                else:
                    trade_date = datetime_obj
                    trade_time = ''
            else:
                # datetime对象
                trade_date = datetime_obj.strftime('%Y-%m-%d')
                trade_time = datetime_obj.strftime('%H:%M:%S')
        else:
            trade_date = datetime.now().strftime('%Y-%m-%d')
            trade_time = datetime.now().strftime('%H:%M:%S')
        
        row = {
            '股票代码': code,
            '股票名称': info.get('name'),
            '当前价': info.get('now'),
            '昨收价': info.get('close'),
            '开盘价': info.get('open'),
            '最高价': info.get('high'),
            '最低价': info.get('low'),
            '成交量': info.get('volume', 0) / 100 if info.get('volume') else 0,
            '成交额': info.get('成交额(万)'),
            '总市值': info.get('总市值'),
            '流通市值': info.get('流通市值'),
            '市盈率': info.get('PE'),
            '市净率': info.get('PB'),
            '换手率': info.get('turnover'),
            '买盘总量': info.get('bid_volume'),
            '卖盘总量': info.get('ask_volume'),
            '交易日期': trade_date,
            '更新时间': trade_time,
        }
        results.append(row)
    
    return results


def fetch_and_save_txt(batch_size=100):
    """获取所有股票实时数据并保存为TXT文件"""
    print("加载股票代码列表...")
    codes = load_stock_codes()
    print(f"共 {len(codes)} 只股票")
    
    # 初始化easyquotation
    quotation = eq.use('tencent')
    all_data = []
    
    print("开始获取实时数据...")
    total_batches = (len(codes) + batch_size - 1) // batch_size
    
    for i in range(0, len(codes), batch_size):
        batch = codes[i:i+batch_size]
        batch_num = i // batch_size + 1
        
        try:
            data = quotation.real(batch)
            converted = convert_to_db_format(data)
            all_data.extend(converted)
            print(f"批次 {batch_num}/{total_batches}: 获取 {len(converted)} 条")
        except Exception as e:
            print(f"批次 {batch_num} 失败: {e}")
    
    print(f"\n共获取 {len(all_data)} 条数据")
    
    # 保存为TXT（CSV格式，UTF-8编码）
    df = pd.DataFrame(all_data)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    filename = f'{timestamp}_stocks.txt'
    df.to_csv(filename, index=False, encoding='utf-8')
    
    print(f"已保存到 {filename}")
    return filename


if __name__ == '__main__':
    try:
        fetch_and_save_txt()
    except Exception as e:
        print(f"执行失败: {e}")
        sys.exit(1)