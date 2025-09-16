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
    
    def get_server_status(self) -> Dict:
        """서버 상태 정보 조회"""
        try:
            response = self.session.get(
                f"{self.base_url}/status",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"서버 상태 조회 실패: {e}")
            return {}
    
    # ========== NEWS CRUD API ==========
    
    def get_all_news(self) -> List[Dict]:
        """모든 뉴스 조회"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/news",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"뉴스 목록 조회 실패: {e}")
            return []
    
    def get_news_by_id(self, news_id: str) -> Optional[Dict]:
        """ID로 뉴스 조회"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/news/{news_id}",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"뉴스 조회 실패 (ID: {news_id}): {e}")
            return None
    
    def create_news(self, news_data: Dict) -> Optional[str]:
        """뉴스 생성"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/news",
                json=news_data,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return result.get('id')
        except Exception as e:
            print(f"뉴스 생성 실패: {e}")
            return None
    
    def update_news(self, news_id: str, news_data: Dict) -> bool:
        """뉴스 업데이트"""
        try:
            response = self.session.put(
                f"{self.base_url}/api/news/{news_id}",
                json=news_data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"뉴스 업데이트 실패 (ID: {news_id}): {e}")
            return False
    
    def delete_news(self, news_id: str) -> bool:
        """뉴스 삭제"""
        try:
            response = self.session.delete(
                f"{self.base_url}/api/news/{news_id}",
                timeout=self.timeout
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"뉴스 삭제 실패 (ID: {news_id}): {e}")
            return False
    
    # def get_unposted_news(self, limit: int = 10) -> List[Dict]:
    #     """미포스팅 뉴스 조회"""
    #     try:
    #         response = self.session.get(
    #             f"{self.base_url}/api/news/unposted",
    #             params={'limit': limit},
    #             timeout=self.timeout
    #         )
    #         response.raise_for_status()
    #         return response.json()
    #     except Exception as e:
    #         print(f"미포스팅 뉴스 조회 실패: {e}")
    #         return []
    
    # def mark_as_posted(self, news_id: str, blog_url: str) -> bool:
    #     """뉴스를 포스팅 완료로 표시"""
    #     try:
    #         data = {
    #             'posted_to_blog': True,
    #             'blog_url': blog_url,
    #             'posted_at': datetime.now().isoformat()
    #         }
    #         response = self.session.patch(
    #             f"{self.base_url}/api/news/{news_id}/posted",
    #             json=data,
    #             timeout=self.timeout
    #         )
    #         response.raise_for_status()
    #         return True
    #     except Exception as e:
    #         print(f"포스팅 상태 업데이트 실패 (ID: {news_id}): {e}")
    #         return False
    
    def search_news(self, query: str, category: str = None) -> List[Dict]:
        """뉴스 검색"""
        try:
            params = {'q': query}
            if category:
                params['category'] = category
            
            response = self.session.get(
                f"{self.base_url}/api/news/search",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"뉴스 검색 실패: {e}")
            return []
    
    # ========== BULK OPERATIONS ==========
    
    def create_multiple_news(self, news_list: List[Dict]) -> List[str]:
        """뉴스 일괄 생성"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/news/bulk",
                json={'news_list': news_list},
                timeout=60  # 일괄 작업은 더 긴 timeout
            )
            response.raise_for_status()
            result = response.json()
            return result.get('created_ids', [])
        except Exception as e:
            print(f"뉴스 일괄 생성 실패: {e}")
            return []
    
    def update_multiple_news(self, updates: List[Dict]) -> int:
        """뉴스 일괄 업데이트"""
        try:
            response = self.session.put(
                f"{self.base_url}/api/news/bulk",
                json={'updates': updates},
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            return result.get('updated_count', 0)
        except Exception as e:
            print(f"뉴스 일괄 업데이트 실패: {e}")
            return 0
    
    # ========== STATISTICS ==========
    
    def get_news_statistics(self) -> Dict:
        """뉴스 통계 정보 조회"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/news/stats",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"뉴스 통계 조회 실패: {e}")
            return {}
    
    def get_posting_statistics(self) -> Dict:
        """포스팅 통계 정보 조회"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/posting/stats",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"포스팅 통계 조회 실패: {e}")
            return {}
    
    # ========== CRAWLING API ==========
    
    def trigger_crawling(self) -> Dict:
        """크롤링 트리거"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/crawl/trigger",
                timeout=120  # 크롤링은 시간이 오래 걸릴 수 있음
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"크롤링 트리거 실패: {e}")
            return {}
    
    def get_crawling_status(self) -> Dict:
        """크롤링 상태 조회"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/crawl/status",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"크롤링 상태 조회 실패: {e}")
            return {}
    
    # # ========== BLOG POSTING API ==========
    
    # def trigger_blog_posting(self, news_ids: List[str] = None) -> Dict:
    #     """블로그 포스팅 트리거"""
    #     try:
    #         data = {'news_ids': news_ids} if news_ids else {}
    #         response = self.session.post(
    #             f"{self.base_url}/api/blog/post",
    #             json=data,
    #             timeout=180  # 블로그 포스팅은 시간이 많이 걸림
    #         )
    #         response.raise_for_status()
    #         return response.json()
    #     except Exception as e:
    #         print(f"블로그 포스팅 트리거 실패: {e}")
    #         return {}
    
    # def get_blog_posting_status(self) -> Dict:
    #     """블로그 포스팅 상태 조회"""
    #     try:
    #         response = self.session.get(
    #             f"{self.base_url}/api/blog/status",
    #             timeout=self.timeout
    #         )
    #         response.raise_for_status()
    #         return response.json()
    #     except Exception as e:
    #         print(f"블로그 포스팅 상태 조회 실패: {e}")
    #         return {}
    
    # ========== UTILITY METHODS ==========
    
    def ping(self) -> bool:
        """서버 ping 테스트"""
        try:
            response = self.session.get(
                f"{self.base_url}/ping",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def get_api_info(self) -> Dict:
        """API 정보 조회"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/info",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"API 정보 조회 실패: {e}")
            return {}
    
    def set_base_url(self, url: str):
        """Base URL 설정"""
        self.base_url = url.rstrip('/')
    
    def set_timeout(self, timeout: int):
        """Timeout 설정"""
        self.timeout = timeout
    
    def close(self):
        """세션 종료"""
        self.session.close()



# API 클라이언트 팩토리
def create_api_client(base_url: str = None) -> APIClient:
    """API 클라이언트 생성"""
    return APIClient(base_url)