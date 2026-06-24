# -*- coding: utf-8 -*-
"""
项目名称: 多Agent协同量化因子自动挖掘系统
文件名: data_fetcher.py
描述: 金融行情数据获取与本地固化模块（基于 Yahoo Finance），遵循“一次下载，本地只读”原则。
环境: Mac 本地运行
"""

import os
import sys
import logging
import yfinance as yf
import pandas as pd
import numpy as np

# 配置工业级日志追踪
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data_fetcher.log', encoding='utf-8')
    ]
)
logger = logging.getLogger("DataFetcher")

class YahooDataFetcher:
    def __init__(self, storage_dir: str = "./data/parquet_storage"):
        """
        初始化数据抓取模块
        :param storage_dir: 本地 Parquet 数据固化存储目录
        """
        self.storage_dir = storage_dir
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
            logger.info(f"创建本地数据存储目录: {self.storage_dir}")

    def fetch_and_save_history(self, tickers: list, start_date: str, end_date: str) -> bool:
        """
        从 yfinance 批量下载历史日线数据，并分别固化为本地 Parquet 文件
        :param tickers: 股票代码列表 (例如 ['AAPL', 'MSFT'])
        :param start_date: 开始日期 'YYYY-MM-DD'
        :param end_date: 结束日期 'YYYY-MM-DD'
        """
        logger.info(f"开始从 Yahoo Finance 下载数据，标的数量: {len(tickers)}，区间: {start_date} ~ {end_date}")
        
        success_count = 0
        
        for ticker in tickers:
            try:
                logger.info(f"正在抓取标的: {ticker} ...")
                # 下载历史日线数据
                stock = yf.Ticker(ticker)
                df = stock.history(start=start_date, end=end_date, interval="1d")
                
                if df.empty:
                    logger.warning(f"标的 {ticker} 未获取到有效数据，跳过该股票。")
                    continue
                
                # 数据重洗与规范化
                df = df.reset_index()
                
                # yfinance 返回的 Date 默认带有时区信息（例如 UTC-5），沙箱内格式处理建议转换为无时区或字符串
                df['Date'] = pd.to_datetime(df['Date']).dt.date
                
                # 统一列名规范，方便算子库（operators.py）统一调用
                rename_dict = {
                    'Date': 'date',
                    'Open': 'open',
                    'High': 'high',
                    'Low': 'low',
                    'Close': 'close',
                    'Volume': 'volume'
                }
                df.rename(columns=rename_dict, inplace=True)
                
                # 仅保留核心六字段，清除可能存在的 Dividends 或 Stock Splits 等无关列
                core_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
                df = df[core_cols]
                
                # 工业级防御：填充可能存在的 NaN / Inf
                df.replace([np.inf, -np.inf], np.nan, inplace=True)
                df.fillna(method='ffill', inplace=True) # 前向填充
                df.fillna(0, inplace=True) # 兜底填充
                
                # 添加股票代码列（横截面算子可能需要）
                df['code'] = ticker
                
                # 固化为 Parquet 文件
                file_path = os.path.join(self.storage_dir, f"{ticker}_daily.parquet")
                df.to_parquet(file_path, index=False, engine='pyarrow')
                
                logger.info(f"成功固化数据至本地 -> {file_path} | 记录数: {len(df)}")
                success_count += 1
                
            except Exception as e:
                logger.error(f"抓取标的 {ticker} 发生异常，错误详情: {str(e)}", exc_info=True)
                
        logger.info(f"数据下载及本地固化任务执行完毕！成功数: {success_count}/{len(tickers)}")
        return success_count == len(tickers)


if __name__ == "__main__":
    print("\n" + "="*50)
    print("开始执行 data_fetcher.py 模块冒烟测试")
    print("="*50)
    
    # 定义测试样本（美股核心科技股与标普500ETF）
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'SPY']
    
    # 历史区间定义
    start = "2023-01-01"
    end = "2023-12-31"
    
    # 运行抓取器
    fetcher = YahooDataFetcher(storage_dir="./data/parquet_storage")
    status = fetcher.fetch_and_save_history(tickers=test_tickers, start_date=start, end_date=end)
    
    # 验证本地读取（模拟沙箱无网环境下的操作）
    if status:
        print("\n" + "="*50)
        print("模拟无网沙箱：从本地 Parquet 文件加载并验证数据")
        print("="*50)
        verify_file = "./data/parquet_storage/AAPL_daily.parquet"
        
        if os.path.exists(verify_file):
            loaded_df = pd.read_parquet(verify_file)
            print(f"成功读取本地 AAPL Parquet 文件！")
            print(f"数据结构 (Columns): {loaded_df.columns.tolist()}")
            print(f"数据前 3 行预览:")
            print(loaded_df.head(3))
            print("-" * 50)
            print("冒烟测试通过！本地行情底座数据完全固化成功。")
        else:
            print("错误：未找到本地生成的 Parquet 验证文件！")
    else:
        print("冒烟测试失败：部分或全部标的数据未成功固化。")