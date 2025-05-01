#!/usr/bin/env python3
"""
EPNET 블록체인 부트스트랩 도구

이 도구는 EPNET 블록체인 노드를 쉽게 설정하고 네트워크에 연결하는 데 도움을 줍니다.
이는 사용자가 Replit 환경 외부에서도 EPNET 네트워크에 참여할 수 있게 합니다.
"""

import os
import sys
import json
import logging
import argparse
import requests
import socket
import time
from urllib.parse import urlparse

# 설정 모듈 불러오기
from config import (
    ensure_data_directory, 
    DATA_DIR, 
    BLOCKCHAIN_FILE, 
    WALLET_FILE, 
    PEERS_FILE,
    SEED_NODES_FILE,
    setup_logging,
    SEED_NODES
)

# 설정 초기화
setup_logging()

def check_network_connectivity():
    """
    인터넷 연결을 확인합니다.
    
    Returns:
        bool: 인터넷 연결 가능 여부
    """
    try:
        # 구글 DNS 서버에 연결 시도
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def discover_seed_nodes():
    """
    네트워크에서 시드 노드를 발견합니다.
    
    Returns:
        list: 발견된 시드 노드 목록
    """
    discovered_nodes = []
    
    # 설정된 시드 노드에서 시작
    for seed in SEED_NODES:
        try:
            # 각 시드 노드에서 피어 목록 요청
            url = f"http://{seed}/nodes"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                nodes_data = response.json()
                discovered_nodes.extend(nodes_data.get('nodes', []))
                logging.info(f"시드 노드 {seed}에서 {len(nodes_data.get('nodes', []))}개의 피어를 발견했습니다.")
        except Exception as e:
            logging.warning(f"시드 노드 {seed}에 연결할 수 없습니다: {e}")
    
    # 고유 노드 필터링
    unique_nodes = list(set(discovered_nodes))
    logging.info(f"총 {len(unique_nodes)}개의 고유 노드를 발견했습니다.")
    
    return unique_nodes

def save_seed_nodes(nodes):
    """
    발견된 시드 노드를 파일에 저장합니다.
    
    Args:
        nodes (list): 저장할 노드 목록
    """
    # 시드 노드에 기본 노드 추가
    all_nodes = list(set(nodes + SEED_NODES))
    
    # 노드 데이터 구성
    seed_data = {
        'nodes': all_nodes,
        'updated': time.time()
    }
    
    # 파일에 저장
    with open(SEED_NODES_FILE, 'w') as f:
        json.dump(seed_data, f, indent=2)
    
    logging.info(f"{len(all_nodes)}개의 시드 노드를 {SEED_NODES_FILE}에 저장했습니다.")

def sync_blockchain():
    """
    네트워크에서 최신 블록체인을 동기화합니다.
    """
    # 인터넷 연결 확인
    if not check_network_connectivity():
        logging.error("인터넷 연결이 없습니다. 블록체인 동기화를 건너뜁니다.")
        return
    
    # 시드 노드 발견
    nodes = discover_seed_nodes()
    if nodes:
        save_seed_nodes(nodes)
        logging.info("시드 노드가 성공적으로 업데이트되었습니다.")
    else:
        logging.warning("시드 노드를 찾을 수 없습니다. 기본 시드 노드를 사용합니다.")
        save_seed_nodes(SEED_NODES)

def check_environment():
    """
    환경 설정을 확인하고 필요한 디렉토리 및 파일을 생성합니다.
    """
    # 데이터 디렉토리 확인
    ensure_data_directory()
    logging.info(f"데이터 디렉토리 확인: {DATA_DIR}")
    
    # 기본 시드 노드 파일 생성
    if not os.path.exists(SEED_NODES_FILE):
        seed_data = {
            'nodes': SEED_NODES,
            'updated': time.time()
        }
        with open(SEED_NODES_FILE, 'w') as f:
            json.dump(seed_data, f, indent=2)
        logging.info(f"기본 시드 노드 파일을 생성했습니다: {SEED_NODES_FILE}")

def create_startup_script():
    """
    EPNET 블록체인 시작 스크립트를 생성합니다.
    이 스크립트는 사용자가 외부 환경에서 EPNET 노드를 쉽게 시작할 수 있게 합니다.
    """
    script_path = os.path.join(DATA_DIR, "start_epnet.py")
    
    script_content = '''#!/usr/bin/env python3
"""
EPNET 블록체인 노드 시작 스크립트
"""
import os
import sys
import logging
from config import setup_logging
from run import run_blockchain_node

if __name__ == "__main__":
    # 로깅 설정
    setup_logging()
    
    # 블록체인 노드 실행
    logging.info("EPNET 블록체인 노드를 시작합니다...")
    run_blockchain_node()
'''
    
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    # 스크립트를 실행 가능하게 설정
    os.chmod(script_path, 0o755)
    
    logging.info(f"시작 스크립트가 생성되었습니다: {script_path}")
    print(f"EPNET 노드를 시작하려면 다음 명령을 실행하세요: python3 {script_path}")

def main():
    """
    메인 함수
    """
    parser = argparse.ArgumentParser(description="EPNET 블록체인 부트스트랩 도구")
    parser.add_argument(
        "--sync", action="store_true", 
        help="네트워크에서 블록체인을 동기화합니다."
    )
    parser.add_argument(
        "--setup", action="store_true", 
        help="EPNET 환경을 설정합니다."
    )
    parser.add_argument(
        "--create-script", action="store_true", 
        help="EPNET 노드 시작 스크립트를 생성합니다."
    )
    
    args = parser.parse_args()
    
    # 적어도 하나의 옵션이 필요
    if not (args.sync or args.setup or args.create_script):
        parser.print_help()
        return
    
    # 환경 설정
    if args.setup:
        check_environment()
        print("EPNET 환경이 성공적으로 설정되었습니다.")
    
    # 블록체인 동기화
    if args.sync:
        sync_blockchain()
        print("블록체인 동기화가 완료되었습니다.")
    
    # 시작 스크립트 생성
    if args.create_script:
        create_startup_script()

if __name__ == "__main__":
    main()