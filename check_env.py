import sys
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def inspect_ide_environment():
    logging.info("================ IDE 运行环境硬核检测 ================")
    
    # 1. 打印当前真正执行代码的 Python 解释器绝对路径
    executable_path = sys.executable
    logging.info(f"【当前实际使用的 Python 解释器路径】: {executable_path}")
    
    # 2. 打印当前系统找包的全部搜索路径
    logging.info("【当前系统查找第三方库库的路径 sys.path】:")
    for path in sys.path:
        if path:
            logging.info(f"  -> {path}")
            
    # 3. 尝试在 IDE 内部捕获 pandas
    try:
        import pandas as pd
        logging.info(f"【成功】IDE 内部已成功识别 pandas，版本: {pd.__version__}")
        logging.info("======================================================")
        return True
    except ModuleNotFoundError as e:
        logging.error(f"【失败】IDE 内部确实无法加载 pandas，错误信息: {str(e)}")
        logging.info("======================================================")
        return False

if __name__ == "__main__":
    inspect_ide_environment()