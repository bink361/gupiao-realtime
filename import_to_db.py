import sqlite3
import sys
import os

DB_PATH = r'D:\python\opencode\gupiao\stock.db'
TXT_DIR = r'D:\python\opencode\gitcode-deploy\gupiao-realtime'


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def check_and_update_stock(code, trade_date, data):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 更新时间 FROM stocks 
        WHERE 股票代码 = ? AND 交易日期 = ?
    ''', (code, trade_date))
    
    result = cursor.fetchone()
    
    if result:
        existing_time = result[0]
        new_time = data.get('更新时间', '')
        
        if new_time > existing_time:
            cursor.execute('''
                UPDATE stocks SET 
                    股票名称 = ?, 当前价 = ?, 昨收价 = ?, 开盘价 = ?, 
                    最高价 = ?, 最低价 = ?, 成交量 = ?, 成交额 = ?,
                    总市值 = ?, 流通市值 = ?, 市盈率 = ?, 市净率 = ?,
                    换手率 = ?, 买盘总量 = ?, 卖盘总量 = ?,
                    更新时间 = ?
                WHERE 股票代码 = ? AND 交易日期 = ?
            ''', (
                data.get('股票名称'), data.get('当前价'), data.get('昨收价'),
                data.get('开盘价'), data.get('最高价'), data.get('最低价'),
                data.get('成交量'), data.get('成交额'), data.get('总市值'),
                data.get('流通市值'), data.get('市盈率'), data.get('市净率'),
                data.get('换手率'), data.get('买盘总量'), data.get('卖盘总量'),
                data.get('更新时间'), code, trade_date
            ))
            conn.commit()
            conn.close()
            return 'updated'
        else:
            conn.close()
            return 'skipped'
    else:
        cursor.execute('''
            INSERT INTO stocks (股票代码, 股票名称, 当前价, 昨收价, 开盘价, 最高价, 最低价, 成交量, 成交额,
                               总市值, 流通市值, 市盈率, 市净率, 换手率, 买盘总量, 卖盘总量,
                               交易日期, 更新时间)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            code, data.get('股票名称'), data.get('当前价'), data.get('昨收价'),
            data.get('开盘价'), data.get('最高价'), data.get('最低价'),
            data.get('成交量'), data.get('成交额'), data.get('总市值'),
            data.get('流通市值'), data.get('市盈率'), data.get('市净率'),
            data.get('换手率'), data.get('买盘总量'), data.get('卖盘总量'),
            data.get('交易日期'), data.get('更新时间')
        ))
        conn.commit()
        conn.close()
        return 'inserted'


def import_txt_to_db(txt_file):
    if not os.path.exists(txt_file):
        print(f"文件不存在: {txt_file}")
        return 0
    
    import pandas as pd
    
    df = pd.read_csv(txt_file, encoding='utf-8')
    print(f"读取到 {len(df)} 条数据")
    
    inserted = 0
    updated = 0
    skipped = 0
    
    for _, row in df.iterrows():
        code = str(row.get('股票代码', '')).strip()
        trade_date = str(row.get('交易日期', '')).strip()
        
        if not code or not trade_date:
            continue
        
        data = {
            '股票名称': row.get('股票名称'),
            '当前价': row.get('当前价'),
            '昨收价': row.get('昨收价'),
            '开盘价': row.get('开盘价'),
            '最高价': row.get('最高价'),
            '最低价': row.get('最低价'),
            '成交量': row.get('成交量'),
            '成交额': row.get('成交额'),
            '总市值': row.get('总市值'),
            '流通市值': row.get('流通市值'),
            '市盈率': row.get('市盈率'),
            '市净率': row.get('市净率'),
            '换手率': row.get('换手率'),
            '买盘总量': row.get('买盘总量'),
            '卖盘总量': row.get('卖盘总量'),
            '交易日期': trade_date,
            '更新时间': row.get('更新时间', '')
        }
        
        result = check_and_update_stock(code, trade_date, data)
        
        if result == 'inserted':
            inserted += 1
        elif result == 'updated':
            updated += 1
        else:
            skipped += 1
    
    print(f"导入完成: 新增 {inserted}, 更新 {updated}, 跳过 {skipped}")
    return inserted + updated


def main():
    txt_dir = TXT_DIR
    txt_files = [f for f in os.listdir(txt_dir) if f.endswith('_stocks.txt')]
    
    if not txt_files:
        print("没有找到股票数据文件")
        return
    
    print(f"找到 {len(txt_files)} 个数据文件:")
    for f in txt_files:
        print(f"  - {f}")
    
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
        txt_path = os.path.join(txt_dir, target_file)
        import_txt_to_db(txt_path)
    else:
        latest_file = sorted(txt_files)[-1]
        txt_path = os.path.join(txt_dir, latest_file)
        print(f"导入最新文件: {latest_file}")
        import_txt_to_db(txt_path)


if __name__ == '__main__':
    main()