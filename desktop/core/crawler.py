"""
YTN 뉴스 크롤러 (병렬 처리 안전 버전)
YTN 웹사이트에서 뉴스를 자동으로 수집하는 모듈
"""

try:
    import requests
    from bs4 import BeautifulSoup
    WEB_SCRAPING_AVAILABLE = True
except ImportError:
    print("웹 스크레이핑 라이브러리를 설치해주세요: pip install requests beautifulsoup4")
    WEB_SCRAPING_AVAILABLE = False

import re
import time
import random
from datetime import datetime
from typing import List, Dict
import json
import concurrent.futures
import threading

from PyQt5.QtCore import QThread, pyqtSignal

class CrawlerThread(QThread):

    progress_updated = pyqtSignal(str)
    crawling_finished = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.target_count = 10
        self.delay_range = (0.1, 0.3)  # 지연시간 단축: 0.5-1초 → 0.1-0.3초
        
        # ✅ 스레드 안전을 위한 락 추가
        self.progress_lock = threading.Lock()
        self.counter_lock = threading.Lock()
        self.completed_count = 0
        
        print("1 - 초기화 완료")    

    def run(self):  # QThread의 표준 메서드
        """메인 실행 메서드"""
        if not WEB_SCRAPING_AVAILABLE:
            self.emit_progress("❌ 웹 스크레이핑 라이브러리가 설치되지 않았습니다.")
            self.crawling_finished.emit([])
            return
        
        try:
            news_list = self.crawl_ytn_news()
            self.crawling_finished.emit(news_list)  # 시그널로 결과 전달
        except Exception as e:
            error_msg = f"❌ 크롤링 오류: {str(e)}"
            print(error_msg)
            self.emit_progress(error_msg)
            self.crawling_finished.emit([])

    def emit_progress(self, message):
        """✅ 스레드 안전 진행상황 출력"""
        # 스레드 ID 포함하여 디버깅 가능하게 수정
        thread_id = threading.current_thread().ident
        
        with self.progress_lock:
            timestamped_message = f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
            print(f"[Thread-{thread_id}] {timestamped_message}")
            self.progress_updated.emit(timestamped_message)

    def crawl_ytn_news(self) -> List[Dict]:
        """YTN 뉴스 크롤링 메인 함수"""
        self.emit_progress("🌐 YTN 웹사이트에 접속하는 중...")
        news_list = []
        
        try:
            news_urls = self.get_news_urls()
            print(f'news_urls : {news_urls}')
          
            if not news_urls:
                self.emit_progress("⚠️ 뉴스 링크를 찾을 수 없습니다.")
                return []
            
            self.emit_progress(f"📰 {len(news_urls)}개 뉴스 링크를 발견했습니다.")
            
            # ✅ 카운터 초기화
            with self.counter_lock:
                self.completed_count = 0
                 
            # === 병렬처리로 각 뉴스 수집 (스레드 안전 버전) ===
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:  # 동시 스레드 수 줄임
                # 각 URL에 대해 future 생성
                futures = []
                target_urls = news_urls[:self.target_count]
                
                for i, url in enumerate(target_urls):
                    self.emit_progress(f"📄 뉴스 {i+1}/{len(target_urls)} 수집 시작...")
                    future = executor.submit(self.crawl_single_news_safe, url, i+1)
                    futures.append(future)
                
                # ✅ 결과를 스레드 안전하게 수집
                results = []
                for future in concurrent.futures.as_completed(futures):
                    try:
                        news = future.result()
                        if news:
                            results.append(news)
                            
                            # ✅ 스레드 안전 카운터 업데이트
                            with self.counter_lock:
                                self.completed_count += 1
                                current_count = self.completed_count
                            
                            self.emit_progress(f"✅ 뉴스 {current_count}개 수집 완료")
                    except Exception as e:
                        self.emit_progress(f"❌ 뉴스 처리 오류: {str(e)}")
                
                # ✅ 결과를 안전하게 추가
                news_list.extend(results)
                
            self.emit_progress(f"🎉 크롤링 완료! 총 {len(news_list)}개 뉴스를 수집했습니다.")
            return news_list
            
        except Exception as e:
            self.emit_progress(f"❌ 크롤링 실패: {str(e)}")
            return news_list
        
    def get_news_urls(self) -> List[str]:
        """YTN에서 뉴스 URL 목록 추출 (스레드 안전)"""
        # ✅ 모든 변수를 로컬로 처리
        api_url = 'https://www.ytn.co.kr/ajax/getManyNews.php'
    
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://www.ytn.co.kr',
            'Referer': 'https://www.ytn.co.kr/',
            'X-Requested-With': 'XMLHttpRequest',
            'Sec-Ch-Ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Priority': 'u=1, i'
        }
        
        # Form Data
        form_data = {
            'mcd': 'total'
        }
        
        try:
            start_time = time.time()
            
            # POST 요청 (Form Data와 함께)
            response = requests.post(api_url, headers=headers, data=form_data, timeout=10)
            response.raise_for_status()
            
            # 응답 디버깅
            print(f"응답 상태: {response.status_code}")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            print(f"응답 길이: {len(response.text)}")
            print(f"응답 내용 (처음 100자): {response.text[:100]}")
            
            # 응답이 비어있거나 null인 경우 체크
            if not response.text or response.text.strip() in ['null', '', 'false']:
                print("❌ 빈 응답 또는 null 응답")
                return []
            
            # JSON 파싱 (한국어 유니코드 자동 디코딩)
            try:
                articles = response.json()
            except json.JSONDecodeError as e:
                print(f"❌ JSON 파싱 실패: {e}")
                print(f"응답 전체 내용: {response.text}")
                return []
            
            # articles가 None인지 체크
            if articles is None:
                print("❌ articles가 None입니다")
                return []
            
            # articles가 리스트가 아닌 경우 체크
            if not isinstance(articles, list):
                print(f"❌ 예상치 못한 응답 타입: {type(articles)}")
                print(f"응답 내용: {articles}")
                return []
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            print(f"크롤링 완료! 소요시간: {elapsed_time:.2f}초")
            print(f"수집된 기사 수: {len(articles)}개")
            print("-" * 60)
            
            # ✅ 로컬 변수로 URL 리스트 생성
            news_urls = []
            for i, article in enumerate(articles[:10], 1):
                join_key = article.get('join_key', '')
                mcd = article.get('mcd', '')
                
                # YTN 기사 URL 생성
                news_url = f"https://www.ytn.co.kr/_ln/{mcd}_{join_key}"
                news_urls.append(news_url)
                
            return news_urls
            
        except requests.RequestException as e:
            print(f"요청 에러: {e}")
            return []
        except Exception as e:
            print(f"알 수 없는 에러: {e}")
            return []

    def crawl_single_news_safe(self, url: str, index: int) -> dict:
        """✅ 스레드 안전 개별 뉴스 페이지 크롤링"""
        thread_id = threading.current_thread().ident
        
        try:
            self.emit_progress(f"[Thread-{thread_id}] 뉴스 {index} 처리 시작: {url}")
            
            # ✅ 모든 변수를 로컬로 생성
            headers = self.get_headers()
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # ✅ 각 추출 메서드를 독립적으로 호출하고 로컬 변수에 저장
            local_category = self.extract_category(url, soup, thread_id)
            local_title = self.extract_title(soup, thread_id)
            local_content = self.extract_content(soup, thread_id)
            local_published_date = self.extract_published(soup, thread_id)
            
            # ✅ author와 email 추출도 로컬 변수로
            local_author = self.extract_author(local_content, thread_id)
            local_email = self.extract_email(local_content, thread_id)
            
            # ✅ 뉴스 객체를 로컬 변수로만 구성
            news = {
                'category': local_category,
                'title': local_title,
                'content': local_content,
                'author': local_author,
                'email': local_email,
                'url': url,
                'posted_to_blog': False,
                'blog_url': '',
                'published_date': local_published_date,
                'thread_id': thread_id,  # 디버깅용 스레드 ID 포함
                'index': index  # 디버깅용 인덱스 포함
            }
            
            self.emit_progress(f"[Thread-{thread_id}] 뉴스 {index} 완료: {local_title[:50]}...")
            return news

        except Exception as e:
            error_msg = f"[Thread-{thread_id}] 개별 뉴스 크롤링 오류 ({url}): {e}"
            print(error_msg)
            self.emit_progress(error_msg)
            return None

    def get_headers(self) -> Dict:
        """HTTP 요청 헤더 반환 (스레드 안전)"""
        # ✅ 로컬 변수로 처리
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59'
        ]
        
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    def extract_title(self, soup: BeautifulSoup, thread_id: int):
        """✅ 스레드 안전 제목 추출"""
        selector = '.news_title_wrap > .news_title > span:last-child'
        element = soup.select_one(selector)

        if element:
            # ✅ 모든 처리를 로컬 변수로
            local_title = element.get_text()
            local_title = self.clean_content(local_title)
            print(f'[Thread-{thread_id}] title : {local_title}')
            return local_title
        
        return "제목을 찾을 수 없습니다"
    
    def extract_content(self, soup: BeautifulSoup, thread_id: int):
        """✅ 스레드 안전 본문 추출"""
        selector = '#CmAdContent > span'
        element = soup.select_one(selector)

        if element:
            # ✅ 모든 처리를 로컬 변수로
            local_content = element.get_text()
            local_content = self.clean_content(local_content)
            print(f'[Thread-{thread_id}] content length: {len(local_content)}')
            return local_content
                
        return "뉴스 본문을 추출할 수 없습니다."
    
    def extract_category(self, url, soup: BeautifulSoup, thread_id: int):
        """✅ 스레드 안전 카테고리 추출"""
        selector = '.top_menu > .menu > li.on > a'
        element = soup.select_one(selector)

        if element:
            # ✅ 로컬 변수로 처리
            local_category = element.get_text()
            print(f'[Thread-{thread_id}] category : {local_category}')
            return local_category
        else:
            print(f"[Thread-{thread_id}] 카테고리 추출 오류")
            return "기타"
    
    def extract_published(self, soup: BeautifulSoup, thread_id: int):
        """✅ 스레드 안전 발행일 추출"""
        selector = '.news_title_wrap inner > .news_info > .date'
        element = soup.select_one(selector)

        if element:
            # ✅ 로컬 변수로 처리
            local_date_text = element.get_text()
            print(f'[Thread-{thread_id}] date_text : {local_date_text}')
            return local_date_text
        
        # ✅ 기본값도 로컬에서 생성
        default_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        return default_date

    def extract_author(self, content, thread_id: int):
        """✅ 스레드 안전 기자명 추출"""
        # ✅ 모든 변수를 로컬로 처리
        local_text = content
        
        print(f'[Thread-{thread_id}] author 추출 시작, 텍스트 길이: {len(local_text)}')
        
        # ✅ 개선된 패턴으로 정확한 매칭
        patterns = [
            r'YTN(?:\s+[a-z]+)?\s+([가-힣]{2,4})(?=입니다|였습니다|습니다|기자|\s|$)',  # 전방탐색
            r'YTN(?:\s+[a-z]+)?\s+([가-힣]{2,4})',  # 일반 패턴
        ]
        
        local_author = None
        for pattern in patterns:
            author_match = re.search(pattern, local_text)
            if author_match:
                local_author = author_match.group(1)
                print(f'[Thread-{thread_id}] 패턴 매칭: "{pattern}" → "{local_author}"')
                break
        
        if not local_author:
            print(f'[Thread-{thread_id}] author 매칭 실패')
            return None
        
        # ✅ 접미사 제거도 로컬 변수로
        original_author = local_author
        suffixes = ['입니다', '였습니다', '습니다', '기자입니다', '기자', '입', '였']
        
        for suffix in suffixes:
            if local_author.endswith(suffix):
                local_author = local_author[:-len(suffix)]
                print(f'[Thread-{thread_id}] 접미사 "{suffix}" 제거: "{original_author}" → "{local_author}"')
                break
        
        # ✅ 추가 검증 - 취재 관련 단어 제외
        forbidden_words = ['취재', '취재진', '취재팀', '취재부', '편집', '제작', '기획']
        if local_author in forbidden_words:
            print(f'[Thread-{thread_id}] 금지된 단어 제외: "{local_author}"')
            return None
        
        # ✅ 검증: 2-4글자 한글 이름만
        if 2 <= len(local_author) <= 4 and re.match(r'^[가-힣]+$', local_author):
            print(f'[Thread-{thread_id}] author 최종 결과: {local_author}')
            return local_author
        
        print(f'[Thread-{thread_id}] author 검증 실패: "{local_author}" (길이: {len(local_author)})')
        return None

    def extract_email(self, content, thread_id: int):
        """✅ 스레드 안전 이메일 추출"""
        # ✅ 모든 변수를 로컬로 처리
        local_text = content
        
        print(f'[Thread-{thread_id}] email 추출 시작')
        
        # ✅ 이메일 패턴 매칭
        email_match = re.search(r'\(([a-zA-Z0-9._%+-]+@ytn\.co\.kr)\)', local_text)
        local_email = email_match.group(1) if email_match else None
        
        print(f'[Thread-{thread_id}] email 결과: {local_email}')
        return local_email

    def clean_content(self, content):
        """본문 내용 정제 (스레드 안전)"""
        if not content:
            return ""
        
        # ✅ 로컬 변수로 처리
        cleaned = re.sub(r'\s+', ' ', content).strip()
        return cleaned

    async def get_status(self):
        """상태 정보 반환"""
        return {
            'status': 'ready',
            'service': 'crawler_thread',
            'last_run': None,
            'total_crawled': 0,
            'success_rate': 1.0
        }

# 테스트 실행
if __name__ == "__main__":
    print("=== 스레드 안전 크롤러 테스트 시작 ===")
    
    crawler = CrawlerThread()
    
    result = crawler.crawl_ytn_news()
    
    print("\n=== 결과 ===")
    if result:
        for i, news in enumerate(result, 1):
            print(f"{i}. [{news.get('thread_id', 'Unknown')}] {news['title']} - {news['author']}")
        print(f"\n총 {len(result)}개 뉴스 수집됨")
    else:
        print("크롤링 결과가 없습니다.")