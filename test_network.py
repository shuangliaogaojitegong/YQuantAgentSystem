import logging
import sys
import json
import requests

# 1. 初始化标准生产级 Logging 体系
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("NetworkTester")

def verify_cross_platform_connection(windows_ip: str, port: int = 11434):
    """
    测试 Mac 本地到 Windows 大模型服务器的握手与基础连通性
    """
    target_url = f"http://{windows_ip}:{port}/api/tags"
    logger.info(f"正在尝试与 Windows 端 Ollama 服务建立握手，目标地址: {target_url} ...")
    
    try:
        # 设置 5 秒超时，避免局域网路由阻塞导致无限期挂起
        response = requests.get(target_url, timeout=5)
        
        if response.status_code == 200:
            logger.info("恭喜！Mac 与 Windows 局域网物理连通性测试【成功】。")
            data = response.json()
            models = [m.get('name') for m in data.get('models', [])]
            logger.info(f"Windows 端当前已下载并可调用的本地大模型列表: {models}")
        else:
            logger.error(f"网络已连通，但 Ollama 返回了非预期状态码: {response.status_code}, 详情: {response.text}")
            
    except requests.exceptions.Timeout:
        logger.error("连接超时！请检查 Windows 的防火墙设置（是否放行了 11434 端口），或确认两台电脑是否在同一路由器下。")
    except requests.exceptions.ConnectionError as ce:
        logger.error(f"连接被拒绝！请求未到达目标。请确认 Windows 的网络地址没有发生变更。错误详情: {ce}")
    except Exception as e:
        logger.error(f"发生未知的系统级通信异常: {str(e)}", exc_info=True)

if __name__ == "__main__":
    # 硬核硬编码：直接绑定上一步在 Windows 上获取的局域网 IP
    WINDOWS_LAN_IP = "192.168.1.108"
    verify_cross_platform_connection(WINDOWS_LAN_IP)
