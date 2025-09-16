"""
Firestore 데이터베이스 관리자
Firebase Admin SDK를 사용한 CRUD 작업
"""

import sys, os
import json
from datetime import datetime
from typing import List, Dict, Optional

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    print("Firebase Admin SDK를 설치해주세요: pip install firebase-admin")
    FIREBASE_AVAILABLE = False

class FirestoreManager:
    """Firestore 데이터베이스 관리 클래스"""
    
    def __init__(self):
        self.db = None
        self.is_connected = False
        self.collection_name = 'news'
        
        if FIREBASE_AVAILABLE:
            self.init_firebase()
        else:
            print("⚠️ Firebase를 사용할 수 없습니다. 로컬 모드로 실행됩니다.")
    
    def init_firebase(self):
        """Firebase 초기화"""
        try:
            # 서비스 계정 키 파일 경로
            service_account_path = self._get_service_account_path()
            print(f'service_account_path : {service_account_path}')
            
            if not os.path.exists(service_account_path):
                print(f"⚠️ Firebase 서비스 계정 키 파일을 찾을 수 없습니다: {service_account_path}")
                print("config/serviceAccountKey.json 파일을 생성해주세요.")
                return
            
            # Firebase 앱이 이미 초기화되어 있는지 확인
            if not firebase_admin._apps:
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
                print("✅ Firebase 앱이 초기화되었습니다.")
            
            # Firestore 클라이언트 생성
            self.db = firestore.client()
            self.is_connected = True
            
            # 연결 테스트
            self._test_connection()
            
            print("✅ Firestore 연결이 성공했습니다.")
            
        except Exception as e:
            print(f"❌ Firebase 초기화 오류: {e}")
            self.db = None
            self.is_connected = False
    
    def _get_service_account_path(self):
        if getattr(sys, 'frozen', False):
        # exe 실행 시
            base_path = sys._MEIPASS
            return os.path.join(base_path, "config", "serviceAccountKey.json")

        else :
            """서비스 계정 키 파일 경로 반환"""
            # 현재 파일 기준으로 프로젝트 루트 찾기
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            print(f'project_root : {project_root}')
            return os.path.join(project_root, 'config', 'serviceAccountKey.json')
        
    def _test_connection(self):
        """연결 테스트"""
        if not self.db:
            return False
        
        try:
            # 간단한 쿼리로 연결 테스트
            docs = self.db.collection(self.collection_name).get()
            return True
        except Exception as e:
            print(f"연결 테스트 실패2222: {e}")
            return False
    
    def is_available(self) -> bool:
        """Firestore 사용 가능 여부 반환"""
        return self.is_connected and self.db is not None
    
    # ========== CREATE ==========
    
    def add_news(self, news_data: Dict) -> Optional[str]:
        """뉴스 추가"""
        if not self.is_available():
            print("❌ Firestore에 연결되어 있지 않습니다.")
            return None
        
        try:
            # 데이터 검증
            validated_data = self._validate_news_data(news_data)
            if not validated_data:
                return None
            
            # 생성 시간 추가
            validated_data['created_at'] = datetime.now()
            validated_data['updated_at'] = datetime.now()
            
            # Firestore에 추가
            doc_ref = self.db.collection(self.collection_name).add(validated_data)
            doc_id = doc_ref[1].id
            
            print(f"✅ 뉴스가 추가되었습니다: {doc_id}")
            return doc_id
            
        except Exception as e:
            print(f"❌ 뉴스 추가 오류: {e}")
            return None
    
    def add_multiple_news(self, news_list: List[Dict]) -> List[str]:
        """여러 뉴스를 일괄 추가"""
        if not self.is_available():
            print("❌ Firestore에 연결되어 있지 않습니다.")
            return []
        
        added_ids = []
        batch = self.db.batch()
        
        try:
            for news_data in news_list:
                validated_data = self._validate_news_data(news_data)
                if validated_data:
                    validated_data['created_at'] = datetime.now()
                    validated_data['updated_at'] = datetime.now()
                    
                    doc_ref = self.db.collection(self.collection_name).document()
                    batch.set(doc_ref, validated_data)
                    added_ids.append(doc_ref.id)
            
            # 배치 커밋
            batch.commit()
            print(f"✅ {len(added_ids)}개 뉴스가 일괄 추가되었습니다.")
            return added_ids
            
        except Exception as e:
            print(f"❌ 일괄 뉴스 추가 오류: {e}")
            return []
    
    # ========== READ ==========
    
    def get_all_news(self) -> List[Dict]:
        """모든 뉴스 조회"""
        if not self.is_available():
            print("❌ Firestore에 연결되어 있지 않습니다.")
            return []
        
        try:
            # docs = self.db.collection(self.collection_name).order_by('created_at', direction=firestore.Query.DESCENDING).get()
            docs = self.db.collection(self.collection_name).get()
            
            news_list = []
            for doc in docs:
                news_data = doc.to_dict()
                news_data['id'] = doc.id
                
                # Timestamp를 문자열로 변환
                if 'created_at' in news_data and hasattr(news_data['created_at'], 'strftime'):
                    news_data['created_at'] = news_data['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                if 'updated_at' in news_data and hasattr(news_data['updated_at'], 'strftime'):
                    news_data['updated_at'] = news_data['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
                
                news_list.append(news_data)
            
            print(f"✅ {len(news_list)}개 뉴스를 조회했습니다.")
            return news_list
            
        except Exception as e:
            print(f"❌ 뉴스 조회 오류: {e}")
            return []
    
    def get_news_by_id(self, doc_id: str) -> Optional[Dict]:
        """ID로 특정 뉴스 조회"""
        if not self.is_available():
            return None
        
        try:
            doc = self.db.collection(self.collection_name).document(doc_id).get()
            
            if doc.exists:
                news_data = doc.to_dict()
                news_data['id'] = doc.id
                
                # Timestamp를 문자열로 변환
                if 'created_at' in news_data and hasattr(news_data['created_at'], 'strftime'):
                    news_data['created_at'] = news_data['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                if 'updated_at' in news_data and hasattr(news_data['updated_at'], 'strftime'):
                    news_data['updated_at'] = news_data['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
                
                return news_data
            else:
                print(f"⚠️ ID {doc_id}에 해당하는 뉴스를 찾을 수 없습니다.")
                return None
                
        except Exception as e:
            print(f"❌ 뉴스 조회 오류: {e}")
            return None
    
    def get_unposted_news(self, limit: int = 10) -> List[Dict]:
        """아직 블로그에 포스팅되지 않은 뉴스 조회"""
        if not self.is_available():
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
                
                # Timestamp를 문자열로 변환
                if 'created_at' in news_data and hasattr(news_data['created_at'], 'strftime'):
                    news_data['created_at'] = news_data['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                if 'updated_at' in news_data and hasattr(news_data['updated_at'], 'strftime'):
                    news_data['updated_at'] = news_data['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
                
                news_list.append(news_data)
            
            print(f"✅ {len(news_list)}개 미포스팅 뉴스를 조회했습니다.")
            return news_list
            
        except Exception as e:
            print(f"❌ 미포스팅 뉴스 조회 오류: {e}")
            return []
    
    def search_news(self, keyword: str) -> List[Dict]:
        """키워드로 뉴스 검색 (제목 기준)"""
        if not self.is_available():
            return []
        
        try:
            # Firestore는 부분 문자열 검색을 직접 지원하지 않으므로
            # 모든 데이터를 가져와서 클라이언트에서 필터링
            all_news = self.get_all_news()
            
            filtered_news = []
            for news in all_news:
                if keyword.lower() in news.get('title', '').lower():
                    filtered_news.append(news)
            
            print(f"✅ '{keyword}'로 {len(filtered_news)}개 뉴스를 검색했습니다.")
            return filtered_news
            
        except Exception as e:
            print(f"❌ 뉴스 검색 오류: {e}")
            return []
    
    # ========== UPDATE ==========
    
    def update_news(self, doc_id: str, update_data: Dict) -> bool:
        """뉴스 업데이트"""
        if not self.is_available():
            print("❌ Firestore에 연결되어 있지 않습니다.")
            return False
        
        try:
            # 업데이트 시간 추가
            update_data = update_data.copy()
            update_data['updated_at'] = datetime.now()
            
            # 불필요한 필드 제거
            if 'id' in update_data:
                del update_data['id']
            if 'created_at' in update_data:
                del update_data['created_at']
            
            self.db.collection(self.collection_name).document(doc_id).update(update_data)
            print(f"✅ 뉴스가 업데이트되었습니다: {doc_id}")
            return True
            
        except Exception as e:
            print(f"❌ 뉴스 업데이트 오류: {e}")
            return False
    
    def mark_as_posted(self, doc_id: str, blog_url: str) -> bool:
        """뉴스를 블로그 포스팅 완료로 표시"""
        update_data = {
            'posted_to_blog': True,
            'blog_url': blog_url,
            'posted_at': datetime.now()
        }
        return self.update_news(doc_id, update_data)
    
    def update_multiple_news(self, updates: List[Dict]) -> int:
        """여러 뉴스를 일괄 업데이트"""
        if not self.is_available():
            return 0
        
        batch = self.db.batch()
        updated_count = 0
        
        try:
            for update_item in updates:
                doc_id = update_item.get('id')
                update_data = update_item.get('data', {})
                
                if doc_id and update_data:
                    update_data['updated_at'] = datetime.now()
                    
                    # 불필요한 필드 제거
                    if 'id' in update_data:
                        del update_data['id']
                    if 'created_at' in update_data:
                        del update_data['created_at']
                    
                    doc_ref = self.db.collection(self.collection_name).document(doc_id)
                    batch.update(doc_ref, update_data)
                    updated_count += 1
            
            batch.commit()
            print(f"✅ {updated_count}개 뉴스가 일괄 업데이트되었습니다.")
            return updated_count
            
        except Exception as e:
            print(f"❌ 일괄 업데이트 오류: {e}")
            return 0
    
    # ========== DELETE ==========
    
    def delete_news(self, doc_id: str) -> bool:
        """뉴스 삭제"""
        if not self.is_available():
            print("❌ Firestore에 연결되어 있지 않습니다.")
            return False
        
        try:
            self.db.collection(self.collection_name).document(doc_id).delete()
            print(f"✅ 뉴스가 삭제되었습니다: {doc_id}")
            return True
            
        except Exception as e:
            print(f"❌ 뉴스 삭제 오류: {e}")
            return False
    
    def delete_multiple_news(self, doc_ids: List[str]) -> int:
        """여러 뉴스를 일괄 삭제"""
        if not self.is_available():
            return 0
        
        batch = self.db.batch()
        deleted_count = 0
        
        try:
            for doc_id in doc_ids:
                doc_ref = self.db.collection(self.collection_name).document(doc_id)
                batch.delete(doc_ref)
                deleted_count += 1
            
            batch.commit()
            print(f"✅ {deleted_count}개 뉴스가 일괄 삭제되었습니다.")
            return deleted_count
            
        except Exception as e:
            print(f"❌ 일괄 삭제 오류: {e}")
            return 0
    
    def delete_old_news(self, days: int = 30) -> int:
        """오래된 뉴스 삭제"""
        if not self.is_available():
            return 0
        
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            docs = (self.db.collection(self.collection_name)
                   .where('created_at', '<', cutoff_date)
                   .get())
            
            deleted_count = 0
            batch = self.db.batch()
            
            for doc in docs:
                batch.delete(doc.reference)
                deleted_count += 1
                
                # 배치 크기 제한 (500개)
                if deleted_count % 500 == 0:
                    batch.commit()
                    batch = self.db.batch()
            
            if deleted_count % 500 != 0:
                batch.commit()
            
            print(f"✅ {days}일 이상 된 뉴스 {deleted_count}개를 삭제했습니다.")
            return deleted_count
            
        except Exception as e:
            print(f"❌ 오래된 뉴스 삭제 오류: {e}")
            return 0
    
    # ========== 유틸리티 메서드 ==========
    
    def _validate_news_data(self, news_data: Dict) -> Optional[Dict]:
        """뉴스 데이터 검증"""
        if not isinstance(news_data, dict):
            print("❌ 뉴스 데이터는 딕셔너리 형태여야 합니다.")
            return None
        
        required_fields = ['title', 'content', 'url']
        for field in required_fields:
            if field not in news_data or not news_data[field]:
                print(f"❌ 필수 필드가 누락되었습니다: {field}")
                return None
        
        # 데이터 복사 및 기본값 설정
        validated_data = news_data.copy()
        
        # 기본값 설정
        validated_data.setdefault('category', '기타')
        validated_data.setdefault('url', '')
        validated_data.setdefault('posted_to_blog', False)
        validated_data.setdefault('blog_url', '')
        validated_data.setdefault('published_date', '')
        
        # 발행일 처리
        if 'published_date' not in validated_data:
            validated_data['published_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 문자열 길이 제한
        if len(validated_data['title']) > 500:
            validated_data['title'] = validated_data['title'][:500]
            print("⚠️ 제목이 500자로 잘렸습니다.")
        
        if len(validated_data['content']) > 10000:
            validated_data['content'] = validated_data['content'][:10000]
            print("⚠️ 내용이 10000자로 잘렸습니다.")
        
        return validated_data
    
    def get_collection_stats(self) -> Dict:
        """컬렉션 통계 정보 반환"""
        if not self.is_available():
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
            for doc in all_docs:
                data = doc.to_dict()
                category = data.get('category', '기타')
                category_stats[category] = category_stats.get(category, 0) + 1
            
            return {
                'total_news': total_count,
                'posted_news': posted_count,
                'unposted_news': total_count - posted_count,
                'categories': category_stats
            }
            
        except Exception as e:
            print(f"❌ 통계 조회 오류: {e}")
            return {}
    
    def clear_all_news(self) -> bool:
        """모든 뉴스 삭제 (주의!)"""
        if not self.is_available():
            return False
        
        try:
            docs = self.db.collection(self.collection_name).get()
            batch = self.db.batch()
            
            for doc in docs:
                batch.delete(doc.reference)
            
            batch.commit()
            print("⚠️ 모든 뉴스가 삭제되었습니다.")
            return True
            
        except Exception as e:
            print(f"❌ 전체 삭제 오류: {e}")
            return False
    
    def backup_to_json(self, file_path: str) -> bool:
        """뉴스 데이터를 JSON 파일로 백업"""
        try:
            news_list = self.get_all_news()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(news_list, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"✅ {len(news_list)}개 뉴스를 {file_path}로 백업했습니다.")
            return True
            
        except Exception as e:
            print(f"❌ 백업 오류: {e}")
            return False
    
    def restore_from_json(self, file_path: str) -> bool:
        """JSON 파일에서 뉴스 데이터 복원"""
        try:
            if not os.path.exists(file_path):
                print(f"❌ 백업 파일을 찾을 수 없습니다: {file_path}")
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                news_list = json.load(f)
            
            # ID 제거 (새로 생성하도록)
            for news in news_list:
                if 'id' in news:
                    del news['id']
            
            created_ids = self.add_multiple_news(news_list)
            
            print(f"✅ {len(created_ids)}개 뉴스를 복원했습니다.")
            return True
            
        except Exception as e:
            print(f"❌ 복원 오류: {e}")
            return False
    
    def close(self):
        """연결 종료"""
        if self.db:
            # Firebase Admin SDK는 명시적 close가 필요 없음
            self.db = None
        self.is_connected = False
        print("🔒 Firestore 연결이 종료되었습니다.")
    
    def __del__(self):
        """소멸자"""
        self.close()