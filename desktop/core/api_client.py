"""
Cloud Run API 클라이언트
FastAPI 서버와 통신하는 클라이언트 모듈
"""

import requests
import json
from typing import List, Dict, Optional
from datetime import datetime

class APIClient:
    """Cloud Run API 클라이언트"""
    
    def __init__(self, base_url: str = None):
        # 실제 배포 시에는 Cloud Run URL로 변경
        # self.base_url = base_url or "https://ytn-news-api-xxx.run.app"  # 실제 배포 URL
        self.base_url = base_url or "http://localhost:8001"  # 실제 배포 URL
        self.session = requests.Session()
        self.timeout = 10
        
        # 기본 헤더 설정
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'YTN-News-Automation-Client/1.0'
        })
    
    def test_connection(self) -> bool:
        """API 서버 연결 테스트"""
        try:
            print(f'base_url : {self.base_url}')
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            print(f'response : {response}')
            if response.status_code == 200 :
                return True
            
        except Exception as e:
            print(f"API 연결 테스트 실패: {e}")
            return False
    

# API 클라이언트 팩토리
def create_api_client(base_url: str = None) -> APIClient:
    """API 클라이언트 생성"""
    return APIClient(base_url)