# -*- coding: utf-8 -*-
"""
项目名称: 多Agent协同量化因子自动挖掘系统
文件名: llm_provider.py
描述: 统一大模型路由客户端（兼容Ollama API），支持同步/流式调用与硬核容错机制
环境: Mac 本地运行，连接 Windows 算力端
数据源上下文: 全面转为美股市场及 Yahoo Finance (yfinance) 数据链
"""

import os
import sys
import logging
from typing import Generator, Dict, Any, List
from openai import OpenAI, APIConnectionError, APITimeoutError

# 配置工业级日志追踪
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('llm_provider.log', encoding='utf-8')
    ]
)
logger = logging.getLogger("LLMProvider")

class HybridLLMClient:
    """统一大模型通信路由客户端"""
    def __init__(self, windows_ip: str = "192.168.1.108", port: int = 11434, default_model: str = "deepseek-r1:8b"):
        """
        初始化大模型客户端
        :param windows_ip: Windows 算力机的局域网 IP
        :param port: Ollama 默认端口
        :param default_model: 调用的目标本地模型名称
        """
        self.base_url = f"http://{windows_ip}:{port}/v1"
        self.default_model = default_model
        
        logger.info(f"正在初始化大模型客户端，路由指向 Windows 算力端: {self.base_url}")
        try:
            # 使用 openai 库兼容 Ollama/vLLM 的 v1 接口
            self.client = OpenAI(
                base_url=self.base_url,
                api_key="ollama_local_bypass"
            )
            logger.info("OpenAI 兼容客户端句柄初始化成功。")
        except Exception as e:
            logger.error(f"客户端句柄初始化异常失败: {str(e)}")
            raise e

    def invoke(self, messages: List[Dict[str, str]], temperature: float = 0.0, max_tokens: int = 4096) -> str:
        """
        标准同步阻塞调用
        """
        logger.info(f"发起同步模型调用请求，目标模型: {self.default_model}, Temperature: {temperature}")
        try:
            response = self.client.chat.completions.create(
                model=self.default_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            content = response.choices[0].message.content
            logger.info("同步调用成功，数据已完整接收。")
            return content
        except APIConnectionError as ce:
            logger.error(f"网络连接崩溃：无法触达 Windows 端大模型，请检查局域网IP、防火墙端口。错误详情: {str(ce)}")
            return "ERROR_CONNECTION_FAILED"
        except APITimeoutError as te:
            logger.error(f"大模型响应超时：Windows 端算力过载。错误详情: {str(te)}")
            return "ERROR_TIMEOUT"
        except Exception as e:
            logger.error(f"未知的 LLM 运行时异常: {str(e)}")
            return f"ERROR_UNKNOWN: {str(e)}"

    def invoke_stream(self, messages: List[Dict[str, str]], temperature: float = 0.0, max_tokens: int = 4096) -> Generator[str, None, None]:
        """
        流式生成调用
        """
        logger.info(f"发起流式模型调用请求，目标模型: {self.default_model}")
        try:
            response_stream = self.client.chat.completions.create(
                model=self.default_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            for chunk in response_stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except APIConnectionError as ce:
            logger.error(f"流式传输中途断开，网络连接异常: {str(ce)}")
            yield "\n[ERROR_STREAM_INTERRUPTED_CONNECTION]"
        except Exception as e:
            logger.error(f"流式传输未知异常: {str(e)}")
            yield f"\n[ERROR_STREAM_UNKNOWN: {str(e)}]"

if __name__ == "__main__":
    print("\n" + "="*50)
    print("开始执行 llm_provider.py 模块冒烟测试（美股雅虎生态定制版）")
    print("="*50)
    
    # 实例化
    llm = HybridLLMClient(windows_ip="192.168.1.108", default_model="deepseek-r1:8b")
    
    # 将测试用例更新为面向美股（雅虎财经数据源）的量化因子指令测试
    test_messages = [
        {"role": "system", "content": "你是一个精通美股多因子选股体系的资深量化金融专家。你的任务是编写基于 pandas/numpy 的高性能矢量化算子。"},
        {"role": "user", "content": "我们要针对从 Yahoo Finance 抓取的标普500成分股历史行情（包含 Open, High, Low, Close, Volume, Adj Close 字段）计算一个 20 日动量排名截面因子 (Cross-sectional Momentum Rank)。请用一句话描述编写该算子时应如何利用 pandas.groupby 避免产生截面时间死循环。"}
    ]
    
    # 1. 测试同步接口
    print("\n--- [测试 1] 验证同步阻塞调用接口 ---")
    sync_res = llm.invoke(messages=test_messages, temperature=0.1)
    print(f"【模型同步回复】:\n{sync_res}\n")
    
    # 2. 测试流式接口
    print("\n--- [测试 2] 验证流式吐字调用接口 ---")
    print("【模型流式回复】: ", end="", flush=True)
    for chunk in llm.invoke_stream(messages=test_messages, temperature=0.1):
        print(chunk, end="", flush=True)
    print("\n\n" + "="*50)
    print("=== 1.3 统一大模型路由客户端冒烟测试全部结束 ===")
    print("="*50)