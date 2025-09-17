"""
Firestore 서비스 클래스
비동기 Firestore 작업을 위한 서비스 레이어
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    from google.cloud.firestore_v1.base_query import FieldFilter
    FIREBASE_AVAILABLE = True
except ImportError:
    print("Firebase Admin SDK를 설치해주세요: pip install firebase-admin")
    FIREBASE_AVAILABLE = False

class FirestoreService:
    """비동기 Firestore 서비스"""
    
    def __init__(self):
        self.db = None
        self.is_connected = False
        self.collection_name = 'news'
        
        if FIREBASE_AVAILABLE:
            self._init_firebase()
        else:
            print("⚠️ Firebase를 사용할 수 없습니다. Mock 모드로 실행됩니다.")
    
    def _init_firebase(self):
        """Firebase 초기화"""
        try:
            # 서비스 계정 키 설정
            service_account_path = self._get_service_account_path()
            
            if os.path.exists(service_account_path):
                # 파일에서 서비스 계정 키 로드
                if not firebase_admin._apps:
                    cred = credentials.Certificate(service_account_path)
                    firebase_admin.initialize_app(cred)
                    print("✅ Firebase 파일 기반 초기화 완료")

                else:
                    # Cloud Run에서 기본 인증 사용
                    if not firebase_admin._apps:
                        firebase_admin.initialize_app()
                        print("✅ Firebase 기본 인증 초기화 완료")

            
            self.db = firestore.client()
            self.is_connected = True
            
            # 연결 테스트
            asyncio.create_task(self._test_connection())
            
        except Exception as e:
            print(f"❌ Firebase 초기화 오류: {e}")
            self.db = None
            self.is_connected = False
    
    def _get_service_account_path(self) -> str:
        """서비스 계정 키 파일 경로 반환"""
        # 다양한 경로 시도
        possible_path = '../config/serviceAccountKey.json'     # 서버 실행 시
        
   
        if possible_path and os.path.exists(possible_path):
            return possible_path
        
        return 'config/serviceAccountKey.json'  # 기본값
    
    async def _test_connection(self):
        """비동기 연결 테스트"""
        try:
            if self.db:
                # 간단한 쿼리로 연결 테스트
                collection_ref = self.db.collection(self.collection_name)
                docs = collection_ref.limit(1).get()
                self.is_connected = True
                print("✅ Firestore 연결 테스트 성공")
        except Exception as e:
            print(f"❌ Firestore 연결 테스트 실패: {e}")
            self.is_connected = False
    
    # ========== CRUD Operations ==========
    
    async def get_all_news(self, limit: int = 100, offset: int = 0, category: str = None) -> List[Dict]:
        """모든 뉴스 조회"""
        if not self.is_connected or not self.db:
            return []
        
        try:
            query = self.db.collection(self.collection_name)
            
            # 카테고리 필터 적용
            if category:
                query = query.where('category', '==', category)
            
            # 정렬 및 페이징
            query = query.order_by('created_at', direction=firestore.Query.DESCENDING)
            query = query.limit(limit)
            
            if offset > 0:
                query = query.offset(offset)
            
            docs = query.get()
            
            news_list = []
            for doc in docs:
                news_data = doc.to_dict()
                news_data['id'] = doc.id
                
                # Timestamp를 ISO 문자열로 변환
                for field in ['created_at', 'updated_at', 'posted_at', 'published_date']:
                    if field in news_data and hasattr(news_data[field], 'isoformat'):
                        news_data[field] = news_data[field].isoformat()
                
                news_list.append(news_data)
            
            return news_list
            
        except Exception as e:
            print(f"❌ 뉴스 조회 오류: {e}")
            return []
    
    async def get_news_by_id(self, news_id: str) -> Optional[Dict]:
        """ID로 뉴스 조회"""
        if not self.is_connected or not self.db:
            return None
        
        try:
            doc = self.db.collection(self.collection_name).document(news_id).get()
            
            if doc.exists:
                news_data = doc.to_dict()
                news_data['id'] = doc.id
                
                # Timestamp 변환
                for field in ['created_at', 'updated_at', 'posted_at', 'published_date']:
                    if field in news_data and hasattr(news_data[field], 'isoformat'):
                        news_data[field] = news_data[field].isoformat()
                
                return news_data
            else:
                return None
                
        except Exception as e:
            print(f"❌ 뉴스 조회 오류 (ID: {news_id}): {e}")
            return None
    
    async def create_news(self, news_data: Dict) -> Optional[str]:
        """뉴스 생성"""
        if not self.is_connected or not self.db:
            return None
        
        try:
            # 생성 시간 추가
            now = datetime.now()
            news_data.update({
                'created_at': now,
                'updated_at': now
            })
            
            # # published_date가 문자열이면 datetime으로 변환
            # if isinstance(news_data.get('published_date'), str):
            #     try:
            #         news_data['published_date'] = datetime.now().strftime('%Y-%m-%d %H:%M')
            #     except:
            #         news_data['published_date'] = now
            
            # Firestore에 추가
            doc_ref = self.db.collection(self.collection_name).add(news_data)
            return doc_ref[1].id
            
        except Exception as e:
            print(f"❌ 뉴스 생성 오류: {e}")
            return None
    
    async def update_news(self, news_id: str, update_data: Dict) -> bool:
        """뉴스 업데이트"""
        if not self.is_connected or not self.db:
            return False
        
        try:
            # 업데이트 시간 추가
            update_data['updated_at'] = datetime.now()
            
            # 불필요한 필드 제거
            update_data_clean = {k: v for k, v in update_data.items() 
                               if k not in ['id', 'created_at'] and v is not None}
            
            self.db.collection(self.collection_name).document(news_id).update(update_data_clean)
            return True
            
        except Exception as e:
            print(f"❌ 뉴스 업데이트 오류 (ID: {news_id}): {e}")
            return False
    
    async def delete_news(self, news_id: str) -> bool:
        """뉴스 삭제"""
        if not self.is_connected or not self.db:
            return False
        
        try:
            self.db.collection(self.collection_name).document(news_id).delete()
            return True
            
        except Exception as e:
            print(f"❌ 뉴스 삭제 오류 (ID: {news_id}): {e}")
            return False
    
    async def get_unposted_news(self, limit: int = 10) -> List[Dict]:
        """미포스팅 뉴스 조회"""
        if not self.is_connected or not self.db:
            return []
        
        try:
            docs = (self.db.collection(self.collection_name)
                   .where('posted_to_blog', '==', False)
                   .order_by('created_at', direction=firestore.Query.DESCENDING)
                   .limit(limit)
                   .get())
            
            news_list = []
            for doc in docs:
                news_data = doc.to_dict()
                news_data['id'] = doc.id
                
                # Timestamp 변환
                for field in ['created_at', 'updated_at', 'posted_at', 'published_date']:
                    if field in news_data and hasattr(news_data[field], 'isoformat'):
                        news_data[field] = news_data[field].isoformat()
                
                news_list.append(news_data)
            
            return news_list
            
        except Exception as e:
            print(f"❌ 미포스팅 뉴스 조회 오류: {e}")
            return []
    
    async def mark_as_posted(self, news_id: str, blog_url: str, posted_at: str = None) -> bool:
        """뉴스를 포스팅 완료로 표시"""
        try:
            update_data = {
                'posted_to_blog': True,
                'blog_url': blog_url,
                'posted_at': datetime.fromisoformat(posted_at) if posted_at else datetime.now(),
                'updated_at': datetime.now()
            }
            
            return await self.update_news(news_id, update_data)
            
        except Exception as e:
            print(f"❌ 포스팅 상태 업데이트 오류 (ID: {news_id}): {e}")
            return False
    
    async def search_news(self, query: str, category: str = None, limit: int = 50) -> List[Dict]:
        """뉴스 검색"""
        if not self.is_connected or not self.db:
            return []
        
        try:
            # Firestore는 부분 문자열 검색을 직접 지원하지 않으므로
            # 모든 뉴스를 가져와서 클라이언트에서 필터링
            all_news = await self.get_all_news(limit=1000, category=category)
            
            # 제목과 내용에서 검색
            filtered_news = []
            query_lower = query.lower()
            
            for news in all_news:
                if (query_lower in news.get('title', '').lower() or 
                    query_lower in news.get('content', '').lower()):
                    filtered_news.append(news)
                
                if len(filtered_news) >= limit:
                    break
            
            return filtered_news
            
        except Exception as e:
            print(f"❌ 뉴스 검색 오류: {e}")
            return []
    
    # ========== Bulk Operations ==========
    
    async def create_multiple_news(self, news_list: List[Dict]) -> List[str]:
        """뉴스 일괄 생성"""
        if not self.is_connected or not self.db:
            return []
        
        created_ids = []
        batch = self.db.batch()
        
        try:
            now = datetime.now()
            
            for news_data in news_list:
                # 시간 필드 추가
                news_data.update({
                    'created_at': now,
                    'updated_at': now
                })
                
                # # published_date 처리
                # if isinstance(news_data.get('published_date'), str):
                #     try:
                #         news_data['published_date'] = )
                #     except:
                #         news_data['published_date'] = now
                
                doc_ref = self.db.collection(self.collection_name).document()
                batch.set(doc_ref, news_data)
                created_ids.append(doc_ref.id)
            
            # 배치 커밋
            batch.commit()
            return created_ids
            
        except Exception as e:
            print(f"❌ 뉴스 일괄 생성 오류: {e}")
            return []
    
    async def update_multiple_news(self, updates: List[Dict]) -> int:
        """뉴스 일괄 업데이트"""
        if not self.is_connected or not self.db:
            return 0
        
        batch = self.db.batch()
        updated_count = 0
        
        try:
            now = datetime.now()
            
            for update_item in updates:
                doc_id = update_item.get('id')
                update_data = update_item.get('data', {})
                
                if doc_id and update_data:
                    update_data['updated_at'] = now
                    
                    # 불필요한 필드 제거
                    update_data_clean = {k: v for k, v in update_data.items() 
                                       if k not in ['id', 'created_at'] and v is not None}
                    
                    doc_ref = self.db.collection(self.collection_name).document(doc_id)
                    batch.update(doc_ref, update_data_clean)
                    updated_count += 1
            
            batch.commit()
            return updated_count
            
        except Exception as e:
            print(f"❌ 뉴스 일괄 업데이트 오류: {e}")
            return 0
    
    # ========== Statistics ==========
    
    async def get_statistics(self) -> Dict:
        """뉴스 통계 조회"""
        if not self.is_connected or not self.db:
            return {}
        
        try:
            # 전체 뉴스 수
            all_docs = self.db.collection(self.collection_name).get()
            total_count = len(all_docs)
            
            # 포스팅된 뉴스 수
            posted_docs = (self.db.collection(self.collection_name)
                          .where('posted_to_blog', '==', True)
                          .get())
            posted_count = len(posted_docs)
            
            # 카테고리별 통계
            category_stats = {}
            daily_stats = {}
            
            for doc in all_docs:
                data = doc.to_dict()
                
                # 카테고리별
                category = data.get('category', '기타')
                category_stats[category] = category_stats.get(category, 0) + 1
                
                # 일별 통계 (최근 7일)
                created_at = data.get('created_at')
                if created_at:
                    date_str = created_at.date().isoformat() if hasattr(created_at, 'date') else str(created_at)[:10]
                    daily_stats[date_str] = daily_stats.get(date_str, 0) + 1
            
            # 최근 활동 통계
            today = datetime.now().date()
            week_ago = today - timedelta(days=7)
            
            recent_activity = {
                'created_today': 0,
                'posted_today': 0,
                'created_this_week': 0,
                'posted_this_week': 0
            }
            
            for doc in all_docs:
                data = doc.to_dict()
                created_at = data.get('created_at')
                posted_at = data.get('posted_at')
                
                if created_at and hasattr(created_at, 'date'):
                    created_date = created_at.date()
                    if created_date == today:
                        recent_activity['created_today'] += 1
                    if created_date >= week_ago:
                        recent_activity['created_this_week'] += 1
                
                if posted_at and hasattr(posted_at, 'date'):
                    posted_date = posted_at.date()
                    if posted_date == today:
                        recent_activity['posted_today'] += 1
                    if posted_date >= week_ago:
                        recent_activity['posted_this_week'] += 1
            
            return {
                'total_news': total_count,
                'posted_news': posted_count,
                'unposted_news': total_count - posted_count,
                'categories': category_stats,
                'daily_stats': dict(list(daily_stats.items())[-7:]),  # 최근 7일
                'recent_activity': recent_activity
            }
            
        except Exception as e:
            print(f"❌ 통계 조회 오류: {e}")
            return {}
    
    async def get_posting_statistics(self) -> Dict:
        """포스팅 통계 조회"""
        if not self.is_connected or not self.db:
            return {}
        
        try:
            posted_docs = (self.db.collection(self.collection_name)
                          .where('posted_to_blog', '==', True)
                          .get())
            
            posting_stats = {
                'total_posted': len(posted_docs),
                'posting_rate': 0,
                'categories': {},
                'daily_posting': {}
            }
            
            # 전체 뉴스 수 대비 포스팅 비율
            all_count = len(self.db.collection(self.collection_name).get())
            if all_count > 0:
                posting_stats['posting_rate'] = len(posted_docs) / all_count
            
            # 카테고리별 포스팅 통계
            for doc in posted_docs:
                data = doc.to_dict()
                category = data.get('category', '기타')
                posting_stats['categories'][category] = posting_stats['categories'].get(category, 0) + 1
                
                # 일별 포스팅
                posted_at = data.get('posted_at')
                if posted_at and hasattr(posted_at, 'date'):
                    date_str = posted_at.date().isoformat()
                    posting_stats['daily_posting'][date_str] = posting_stats['daily_posting'].get(date_str, 0) + 1
            
            return posting_stats
            
        except Exception as e:
            print(f"❌ 포스팅 통계 조회 오류: {e}")
            return {}
    
    def close(self):
        """서비스 종료"""
        if self.db:
            self.db = None
        self.is_connected = False
        print("🔒 Firestore 서비스가 종료되었습니다.")