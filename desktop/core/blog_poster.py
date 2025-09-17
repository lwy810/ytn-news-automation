"""
네이버 블로그 자동 포스팅 모듈 (완전 작동 버전 + 병렬 처리)
Playwright를 사용하여 네이버 블로그에 자동으로 포스팅하는 모듈
"""

import time
import random
import warnings
import sys
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv
from pathlib import Path
import os
import concurrent.futures
from threading import Lock

from playwright.sync_api import sync_playwright, Page

# PyQt5 deprecation warning 무시
warnings.filterwarnings("ignore", category=DeprecationWarning, module=".*sip.*")

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication

# .env 파일 로드
env_file = Path(__file__).parent.parent.parent / 'config' / '.env'
print(env_file)

load_dotenv(env_file)

naver_id = os.getenv('NAVER_ID')
naver_password = os.getenv('NAVER_PASSWORD')

print(naver_id)
print(naver_password)

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    print("Playwright를 설치해주세요: pip install playwright")
    print("설치 후 다음 명령어도 실행하세요: playwright install")
    PLAYWRIGHT_AVAILABLE = False

class BlogPostThread(QThread):
    """네이버 블로그 포스팅 스레드"""
    
    progress_updated = pyqtSignal(str)  # 진행 상황 업데이트
    posting_finished = pyqtSignal(list)  # 포스팅 완료 시 업데이트된 뉴스 리스트 전달
    
    def __init__(self, news_list: List[Dict], use_simulation=True, use_parallel=False):
        super().__init__()
        self.news_list = news_list[:9]  # 최대 9개 (3배치 * 3개)
        self.posted_news = []
        self.use_simulation = use_simulation
        self.use_parallel = use_parallel  # 병렬 처리 여부 선택
        self.progress_lock = Lock()  # 스레드 안전성을 위한 락
    
    def run(self):
        """스레드 실행 메서드"""
        if not PLAYWRIGHT_AVAILABLE:
            self.progress_updated.emit("❌ Playwright가 설치되지 않았습니다.")
            return
        
        try:
            if self.use_parallel:
                self.post_to_naver_blog_parallel()
            else:
                self.post_to_naver_blog()
        except Exception as e:
            self.progress_updated.emit(f"❌ 블로그 포스팅 오류: {str(e)}")
            self.posting_finished.emit([])
    
    def post_to_naver_blog(self):
        """순차적 네이버 블로그 포스팅 (기존 방식)"""
        self.progress_updated.emit("🌐 브라우저를 시작하는 중...")
        
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=False, slow_mo=1000)
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = context.new_page()
                
                success_count = 0
                
                for i, news in enumerate(self.news_list):
                    try:
                        self.progress_updated.emit(f"📝 포스팅 {i+1}/{len(self.news_list)} 준비 중: {news['title'][:40]}...")
                        
                        blog_url = self.post_single_news(page, news, i+1)
                        
                        if blog_url:
                            updated_news = news.copy()
                            updated_news['posted_to_blog'] = True
                            updated_news['blog_url'] = blog_url
                            updated_news['posted_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            
                            self.posted_news.append(updated_news)
                            success_count += 1
                            
                            self.progress_updated.emit(f"✅ 포스팅 성공 {i+1}/{len(self.news_list)}: {blog_url}")

                        else:
                            self.progress_updated.emit(f"❌ 포스팅 실패 {i+1}/{len(self.news_list)}")
                    
                    except Exception as e:
                        self.progress_updated.emit(f"❌ 포스팅 {i+1} 오류: {str(e)}")
                        continue
                
                browser.close()
                
                self.progress_updated.emit(f"🎊 포스팅 완료! {success_count}/{len(self.news_list)}개 성공")
                self.posting_finished.emit(self.posted_news)
                
            except Exception as e:
                self.progress_updated.emit(f"❌ 브라우저 오류: {str(e)}")
                self.posting_finished.emit([])

    def post_to_naver_blog_parallel(self):
        """병렬로 네이버 블로그 포스팅"""
        self.progress_updated.emit("🚀 병렬 포스팅 시작 (최대 3개 동시)...")
        
        success_count = 0
        total_count = len(self.news_list)
        self.posted_news = []
        
        # 뉴스를 3개씩 배치로 나누기
        max_workers = 3
        batches = [self.news_list[i:i + max_workers] 
                  for i in range(0, len(self.news_list), max_workers)]
        
        try:
            for batch_idx, batch in enumerate(batches):
                self.progress_updated.emit(f"📦 배치 {batch_idx + 1}/{len(batches)} 처리 중...")
                
                # 배치를 병렬 처리
                batch_results = self._process_batch_parallel(batch, batch_idx * max_workers)
                
                # 성공한 포스팅 카운트
                success_count += len([r for r in batch_results if r])
                
                # 배치 간 대기 (서버 부하 방지)
                if batch_idx < len(batches) - 1:
                    self.progress_updated.emit("⏰ 다음 배치까지 5초 대기...")
                    time.sleep(5)
            
            self.progress_updated.emit(f"🎊 병렬 포스팅 완료! {success_count}/{total_count}개 성공")
            self.posting_finished.emit(self.posted_news)
            
        except Exception as e:
            self.progress_updated.emit(f"❌ 병렬 처리 오류: {str(e)}")
            self.posting_finished.emit(self.posted_news)

    def _process_batch_parallel(self, batch, start_index):
        """3개씩 배치를 병렬로 처리하는 내부 메서드"""
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # 각 뉴스에 대해 Future 생성
            future_to_news = {}
            for i, news in enumerate(batch):
                future = executor.submit(self._post_single_threaded, news, start_index + i + 1)
                future_to_news[future] = (news, start_index + i + 1)
            
            # 완료된 순서대로 결과 수집
            for future in concurrent.futures.as_completed(future_to_news, timeout=600):
                news, index = future_to_news[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    with self.progress_lock:
                        completed = len([r for r in results if r is not None])
                        self.progress_updated.emit(f"✅ 배치 진행률: {completed}/{len(batch)}")
                        
                except Exception as e:
                    with self.progress_lock:
                        self.progress_updated.emit(f"❌ {index}번 포스팅 오류: {str(e)}")
                    results.append(None)
        
        return results

    def _post_single_threaded(self, news, index):
        """스레드에서 단일 뉴스 포스팅"""
        thread_id = f"T{index:02d}"
        
        try:
            with self.progress_lock:
                self.progress_updated.emit(f"🧵 [{thread_id}] 시작: {news['title'][:30]}...")
            
            # 개별 브라우저 인스턴스 생성
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=False, 
                    slow_mo=800,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                
                page = context.new_page()
                
                try:
                    # 기존의 post_single_news 메서드 사용
                    blog_url = self.post_single_news(page, news, index)
                    
                    if blog_url:
                        # 성공한 경우
                        updated_news = news.copy()
                        updated_news['posted_to_blog'] = True
                        updated_news['blog_url'] = blog_url
                        updated_news['posted_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        with self.progress_lock:
                            self.posted_news.append(updated_news)
                            self.progress_updated.emit(f"✅ [{thread_id}] 성공: {blog_url}")
                        
                        return blog_url
                    else:
                        with self.progress_lock:
                            self.progress_updated.emit(f"❌ [{thread_id}] 포스팅 실패")
                        return None
                        
                finally:
                    browser.close()
                    
        except Exception as e:
            with self.progress_lock:
                self.progress_updated.emit(f"❌ [{thread_id}] 오류: {str(e)}")
            return None

    def post_single_news(self, page, news: Dict, post_number: int) -> str:
        """개별 뉴스 포스팅"""
        try:
            self.progress_updated.emit(f"🌐 네이버 블로그 에디터 접속 중...")
            print("1 - 페이지 접속")
            page.goto(f'https://blog.naver.com/{naver_id}?Redirect=Write&', wait_until='networkidle')
            
            # 로그인 체크

            if page.locator('#id').is_visible and page.locator('#pw').is_visible():
                print("2-2 id 입력")
                time.sleep(random.uniform(0.5, 1))
                page.locator('#id').fill(naver_id)
                time.sleep(random.uniform(0.5, 1))
                print("2-2 pw 입력")
                page.locator('#pw').fill(naver_password)
                time.sleep(random.uniform(0.5, 1))
                page.click(f'button[type="submit"]')
                time.sleep(2)

                if page.locator('.btn_upload > .btn').is_visible :
                    print('등록 버튼 클릭')
                    page.click('.btn_upload > .btn')
                    time.sleep(1)
            else :
                    print("ID/PW 입력 필드를 찾을 수 없습니다")
            
            # 글쓰기
            print("3 - 글쓰기")
            self.progress_updated.emit("✏️ 새 글 작성 시작...")
            page.goto(f'https://blog.naver.com/{naver_id}?Redirect=Write&', wait_until='networkidle')
            time.sleep(5)

            mainframe = page.frame_locator('#mainFrame')
           
            # 제목 입력
            self.progress_updated.emit("📝 제목 입력 중...")

            print("4-1 - 도움말 닫기 버튼 확인")
            help_close_click = mainframe.locator('.se-help-panel-close-button')
            print("4-2 - 도움말 닫기 버튼 클릭")
            help_close_click.click()
            time.sleep(1)

            print("4-3. 제목 확인")
            title_click = mainframe.locator('.se-content > section > article > div:nth-child(1)')
            print(f'title_click : {title_click}')
            title_click.click()
            print("4-4. 제목 클릭")
            time.sleep(2)
            print("5. 두번째 iframe 체크")
            sub_mainframe = mainframe.frame_locator('iframe')

            print("6. title 체크 시작")
            title_input = sub_mainframe.locator('body')
            print(f'title_input : {title_input}')
           
            try:
                # 방법 1: type() 사용
                title_input.type(news['title'], delay=10)
                print("7. ✅ type() 성공")
            except:
                try:
                    # 방법 2: evaluate() 사용
                    title_input.evaluate(f'el => el.textContent = "{news["title"]}"')
                    print("✅ evaluate() 성공")
                except Exception as e:
                    print(f"❌ 제목 입력 실패: {e}")

            time.sleep(1)

            # 본문 입력
            self.progress_updated.emit("📄 본문 입력 중...")
            blog_content = self.generate_blog_content(news)
            content_click = mainframe.locator('.se-content > section > article > div:nth-child(2)')
            content_click.click()
            print("8. 본문 클릭")

            print("9. 본문 체크 시작")
            content_input = sub_mainframe.locator('body')
            print(f'blog_content : {blog_content}')            

            try:
                # 방법 1: type() 사용
                content_input.type(blog_content, delay=10)
                print("10. ✅ type() 성공")
            except:
                try:
                    # 방법 2: evaluate() 사용
                    content_input.evaluate(f'el => el.textContent = "{blog_content}"')
                    print("✅ evaluate() 성공")
                except Exception as e:
                    print(f"❌ 본문 입력 실패: {e}")
            time.sleep(1)
    
            print("11. ✅ sub 발행 버튼 체크")
            sub_publish_button = mainframe.locator('button[data-click-area="tpb.publish"]')
            print("12. ✅ sub 발행 버튼 클릭")
            print(f'sub_publish_button : {sub_publish_button}')
            sub_publish_button.click()

            time.sleep(1)
            print("13. ✅ final 발행 버튼 체크")
            final_publish_button = mainframe.locator('button[data-testid="seOnePublishBtn"]')
            print("14. ✅ final 발행 버튼 클릭")
            print(f'final_publish_button : {final_publish_button}')
            final_publish_button.click()

            time.sleep(4)

            blog_url = page.url
            return blog_url
                
        except Exception as e:
            self.progress_updated.emit(f"❌ 포스팅 오류: {str(e)}")
            return None
    
    def generate_blog_content(self, news: Dict) -> str:
        """블로그 포스팅용 콘텐츠 생성"""
        content = f"""
        🔥 YTN 뉴스 자동화 시스템 포스팅 🔥

        📰 {news['title']}

        📅 발행일: {news['published_date']}
        👤 기자: {news['author']}
        🏷️ 카테고리: {news['category']}

        📄 뉴스 내용:
        {news['content']}

        🔗 원본 뉴스: {news['url']}

        ---
        이 포스팅은 YTN 뉴스 자동화 시스템을 통해 자동으로 생성되었습니다.
        🏢 트리플송(Triple Song) - 생성형 AI 기반 업무 자동화 솔루션

        #YTN뉴스 #자동화 #트리플송 #{news['category']} #뉴스
                """.strip()
            
        return content

class BlogPostManager:
    """블로그 포스팅 매니저 - QApplication을 관리하는 클래스"""
    
    def __init__(self):
        self.app = None
        self.thread = None
        self.posted_news = []
        self.progress_callback = None
        self.finished_callback = None
    
    def set_progress_callback(self, callback):
        """진행 상황 콜백 설정"""
        self.progress_callback = callback
    
    def set_finished_callback(self, callback):
        """완료 콜백 설정"""
        self.finished_callback = callback
    
    def post_news(self, news_list: List[Dict], use_simulation=False, use_parallel=False):
        """뉴스 포스팅 시작"""
        # QApplication이 없으면 생성
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()
        
        # 스레드 생성 (병렬 처리 옵션 추가)
        self.thread = BlogPostThread(news_list, use_simulation, use_parallel)
        
        # 시그널 연결
        self.thread.progress_updated.connect(self._on_progress_updated)
        self.thread.posting_finished.connect(self._on_posting_finished)
        
        # 스레드 시작
        self.thread.start()
        
        # 이벤트 루프 실행 (블로킹)
        self.app.exec_()
        
        return self.posted_news
    
    def _on_progress_updated(self, message):
        """진행 상황 업데이트 처리"""
        if self.progress_callback:
            self.progress_callback(message)
        else:
            print(f"[진행상황] {message}")
    
    def _on_posting_finished(self, posted_news):
        """포스팅 완료 처리"""
        self.posted_news = posted_news
        
        if self.finished_callback:
            self.finished_callback(posted_news)
        else:
            print(f"[완료] {len(posted_news)}개 포스팅 완료!")
            for i, news in enumerate(posted_news, 1):
                print(f"  {i}. {news['title']}")
                if 'blog_url' in news:
                    print(f"     URL: {news['blog_url']}")
        
        # QApplication 종료
        if self.app:
            self.app.quit()


# 편의 함수들
def post_news_to_blog(news_list: List[Dict], use_simulation=False, use_parallel=False, progress_callback=None, finished_callback=None):
    """뉴스를 블로그에 포스팅하는 편의 함수"""
    manager = BlogPostManager()
    
    if progress_callback:
        manager.set_progress_callback(progress_callback)
    
    if finished_callback:
        manager.set_finished_callback(finished_callback)
    
    return manager.post_news(news_list, use_simulation, use_parallel)


def create_test_news():
    """테스트용 뉴스 데이터 생성"""
    return [
        {
            'title': '테스트 뉴스 1 - 자동화 시스템 개발 완료',
            'content': 'YTN 뉴스 자동화 시스템이 성공적으로 개발되었습니다. 이 시스템은 실시간으로 뉴스를 수집하고 네이버 블로그에 자동으로 포스팅합니다.',
            'author': '기술팀 기자',
            'published_date': '2024-01-15 14:30:00',
            'category': '기술',
            'url': 'https://ytn.co.kr/news/tech/1'
        },
        {
            'title': '테스트 뉴스 2 - AI 기반 콘텐츠 생성 기술',
            'content': '인공지능을 활용한 자동 콘텐츠 생성 기술이 발전하고 있습니다. 이를 통해 효율적인 미디어 운영이 가능해집니다.',
            'author': 'AI 전문 기자',
            'published_date': '2024-01-15 15:00:00',
            'category': 'AI',
            'url': 'https://ytn.co.kr/news/ai/2'
        },
        {
            'title': '테스트 뉴스 3 - 디지털 전환 가속화',
            'content': '디지털 기술의 발전으로 다양한 산업 분야에서 자동화가 가속화되고 있습니다.',
            'author': '산업 기자',
            'published_date': '2024-01-15 15:30:00',
            'category': '산업',
            'url': 'https://ytn.co.kr/news/industry/3'
        }
    ]


# 메인 실행 부분
if __name__ == "__main__":
    print("=" * 60)
    print("YTN 뉴스 블로그 자동 포스팅 시스템")
    print("=" * 60)
    
    # 테스트 뉴스 생성
    test_news = create_test_news()
    print(f"📰 {len(test_news)}개의 테스트 뉴스를 준비했습니다.")
    
    print("-" * 60)
    print("포스팅 방식을 선택하세요:")
    print("1. 순차 처리 (기존 방식)")
    print("2. 병렬 처리 (최대 3개 동시)")
    
    choice = input("선택 (1 또는 2): ").strip()
    use_parallel = choice == "2"
    
    if use_parallel:
        print("🚀 병렬 처리 모드로 실행합니다.")
    else:
        print("📝 순차 처리 모드로 실행합니다.")
    
    print("-" * 60)
    
    try:
        # 포스팅 실행
        result = post_news_to_blog(test_news, use_parallel=use_parallel)
        
        print("-" * 60)
        print(f"🎊 모든 작업이 완료되었습니다! ({len(result)}개 포스팅)")
        
    except KeyboardInterrupt:
        print("\n\n사용자가 작업을 취소했습니다.")
    except Exception as e:
        print(f"\n❌ 오류가 발생했습니다: {e}")