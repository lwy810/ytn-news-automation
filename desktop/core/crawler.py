"""
YTN 뉴스 크롤러
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

from PyQt5.QtCore import QThread, pyqtSignal

class CrawlerThread(QThread) :

    progress_updated = pyqtSignal(str)
    crawling_finished = pyqtSignal(list)

    def __init__(self):
        super().__init__()  # 이 줄을 추가해야 합니다
        self.target_count = 1  # 테스트용으로 줄임
        self.delay_range = (0.5, 1)  # 테스트용으로 줄임
        print("1 - 초기화 완료")    


    def run(self):  # QThread의 표준 메서드
        """메인 실행 메서드"""
        if not WEB_SCRAPING_AVAILABLE:
            print("2 - 라이브러리 없음")    
            self.progress_updated.emit("❌ 웹 스크레이핑 라이브러리가 설치되지 않았습니다.")
            self.crawling_finished.emit([])
            return
        
        try:
            print("4 - 크롤링 시작")  
            news_list = self.crawl_ytn_news()
            print("5 - 크롤링 완료")  
            self.crawling_finished.emit(news_list)  # 시그널로 결과 전달
        except Exception as e:
            print(f"❌ 크롤링 오류: {str(e)}")
            self.progress_updated.emit(f"❌ 크롤링 오류: {str(e)}")
            self.crawling_finished.emit([])


    def emit_progress(self, message):
        """진행상황 출력 (실제로는 시그널 emit)"""
        print(f"Progress: {message}")
        self.progress_updated.emit(message)  # 이 줄 추가

    def crawl_ytn_news(self) -> List[Dict]:
        """YTN 뉴스 크롤링 메인 함수"""
        self.emit_progress("🌐 YTN 웹사이트에 접속하는 중...")
        news_list = []
        
        try:
            print("6 - URL 수집 시작")  
            news_urls = self.get_news_urls()
            print("10 - URL 수집 완료") 
            
            if not news_urls:
                self.emit_progress("⚠️ 뉴스 링크를 찾을 수 없습니다. 더미 데이터를 생성합니다.")
            
            self.emit_progress(f"📰 {len(news_urls)}개 뉴스 링크를 발견했습니다.")
            
            # 각 뉴스 처리
            for i, url in enumerate(news_urls[:self.target_count]):
                self.emit_progress(f"📄 뉴스 {i+1}/{min(len(news_urls), self.target_count)} 수집 중...")
                
                try:
                    print("11-1. 뉴스 처리 시작")
                    print(f'0. url : {url}')
                    news_list = self.crawl_single_news(url)
                    print("20 - news 수집 완료") 
                    print(f'21. news_list : {news_list}')

                    if news_list:

                        self.emit_progress(f"✅ '{len(news_list)}'개 수집 완료")
                
                except Exception as e:
                    print("11-2. 뉴스 처리 오류")
                    self.emit_progress(f"❌ 뉴스 {i+1} 처리 오류: {str(e)}")
                # 지연

                time.sleep(random.uniform(*self.delay_range))
                
            self.emit_progress(f"🎉 크롤링 완료! 총 {len(news_list)}개 뉴스를 수집했습니다.")
            return news_list
            
        except Exception as e:
            self.emit_progress(f"❌ 크롤링 실패: {str(e)}")
            return news_list
        
    def get_news_urls(self) -> List[str]:
        """YTN에서 뉴스 URL 목록 추출"""

        try:
            headers = self.get_headers()
            
            # YTN 메인 페이지 접속
            print("7 - 메인 페이지 ") 
            response = requests.get('https://www.ytn.co.kr', timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            news_urls = []
            
            # 다양한 뉴스 섹션에서 링크 추출
            selectors = [
                '.top_menu > .menu > li > a'
            ]
            
            for selector in selectors[:]:
                links = soup.select(selector)
                # print(f'links: {links}')
                for link in links:
                    href = link.get('href', '')
                    print(f'href : {href}')
                    news_urls.append(href)
            
            return news_urls  # 최대 15개 반환
            
        except Exception as e:
            print(f"뉴스 URL 수집 오류: {e}")
            return []
        
    def crawl_single_news(self, url: str) -> list:
        """개별 뉴스 페이지 크롤링"""
        try:
            print("12-1. 개별 뉴스 크롤링 시작")
            headers = self.get_headers()
            print(f'headers : {headers}')
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            print("12-2. 개별 뉴스 크롤링 시작")
            print(f'crawl_url : {url}')
            # 뉴스 정보 추출

            news_list = [
                self.extract_category(url, soup),
                self.extract_title(soup),
                self.extract_content(soup),
                self.extract_news_url(soup),
                [False],
                [''],
                self.extract_published_date(soup)
            ]
            
            print(f'news_list[category] : {news_list[0]}')
            print(f'news_list[title] : {news_list[1]}')
            print(f'news_list[content] : {news_list[2]}')
            print(f'news_list[url] : {news_list[3]}')
            print(f'news_list[published_date] : {news_list[6]}')
            
            final_news_list = []
            max_length = len(news_list[0]) if news_list[0] else 0

            for i in range(max_length):
                news = {
                    'no': '',
                    'category': news_list[0][i] if i < len(news_list[0]) else '',
                    'title': news_list[1][i] if i < len(news_list[1]) else '',
                    'content': news_list[2][i] if i < len(news_list[2]) else '',
                    'url': news_list[3][i] if i < len(news_list[3]) else '',
                    'posted_to_blog': news_list[4][i] if i < len(news_list[4]) else False,
                    'blog_url': news_list[5][i] if i < len(news_list[5]) else '',
                    'published_date': news_list[6][i] if i < len(news_list[6]) else '',
                }
                final_news_list.append(news)

            print(f'news_list : {final_news_list}')

            print("13. 개별 뉴스 크롤링 완료")

            return final_news_list

        except Exception as e:
            print(f"개별 뉴스 크롤링 오류 ({url}): {e}")
            return None

    def get_headers(self) -> Dict:
        """HTTP 요청 헤더 반환"""
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

    def extract_title(self, soup: BeautifulSoup) :
        """제목 추출"""
        selectors = ['.news_list_wrap > .news_list > .text_area > .title > a']
        titles = []

        print("111. 제목 추출 시작") 
        for selector in selectors:
            elements = soup.select(selector)

            if elements :
                print("112. 제목 추출 시작")  
                for element in elements :
                    title = element.get_text()
                    titles.append(title)        

        titles = self.clean_content(titles)

        print(titles)
        print("=========================================================================================")

        return titles
    
    def extract_content(self, soup: BeautifulSoup) :
        """본문 추출"""

        print("222. 본문 추출 시작")
        selectors = ['.news_list_wrap > .news_list > .text_area > .content' ]
        contents = []

        for selector in selectors:
            elements = soup.select(selector)

            if elements :
                for element in elements :    
                    content = element.get_text()
                    
                    contents.append(content)
        # 내용 정제
        
        contents = self.clean_content(contents)

        print(contents)
        print("=========================================================================================")

        return contents if contents else "뉴스 본문을 추출할 수 없습니다."
    
    def extract_category(self, url, soup: BeautifulSoup) :
        """카테고리 추출"""
        extract_count = 10

        category_url = url
        selector = f'.top_menu > .menu > li > a[href="{category_url}"]'
        
        print("카테고리 추출 시작1")
        element = soup.select_one(selector)
        categorys = []

        print("카테고리 추출 시작2")
        if element:
            category = element.get_text()
            print(category)
            for i in range(0, extract_count) :
                categorys.append(category)
        else :
            print("카테고리 추출 오류")
        
        print(categorys)
        print("=========================================================================================")

        return categorys   

    
    def extract_published_date(self, soup: BeautifulSoup) :
        """발행일 추출"""

        selectors = ['.news_list_wrap > .news_list > .text_area > .info > .date']
        date_texts = []
        print("14. 발행일 추출 시작 ")

        for selector in selectors:
            elements = soup.select(selector)

            if elements:
                for element in elements :    
                    date_text = element.get_text()
                    date_texts.append(date_text)

        print(date_texts)
        print("=========================================================================================")

        return date_texts

    def extract_news_url(self, soup: BeautifulSoup) :
        """뉴스 URL 추출"""
        print("15-1. 뉴스 url 시작 ")

        selectors = ['.news_list_wrap > .news_list > .text_area > .title > a']

        print("15-2. 뉴스 url 시작 ")

        news_urls = []
        for selector in selectors:
            elements = soup.select(selector)

            if elements:
                for element in elements :    
                    news_url = element.get('href')
                    news_urls.append(news_url)

        print(news_urls)
        print("=========================================================================================")

        return news_urls

    def clean_content(self, contents: list) -> list :
        """본문 내용 정제"""

        cleaned_contents = []
        print("본문 내용 정제 시작")

        if not contents:
            return ""
        
        # 불필요한 텍스트 패턴 제거
        unwanted_patterns = [
            r'▶.*?◀',  # YTN 특수 기호 패턴
            r'※.*?※',  # 주석 패턴
            r'\[.*?\]',  # 대괄호 패턴
            r'<.*?>',   # HTML 태그
            r'&[^;]+;', # HTML 엔티티
            r'광고|배너|클릭|바로가기|더보기',  # 광고 관련
            r'기자\s*=|뉴스\d+',  # 기자 서명
            r'ⓒ.*?YTN.*',  # 저작권 표시
            r'www\.ytn\.co\.kr',  # URL
            r'\s{2,}'  # 연속된 공백
            r'\s+' # 연속 공백 제거
            r'\\' # \ 문자 패턴
        ]
        
        for content in contents :
            for pattern in unwanted_patterns:
                content = re.sub(pattern, ' ', content, flags=re.IGNORECASE)
        
            # 추가 정제
                cleaned_content = content.strip()
            cleaned_contents.append(cleaned_content)

        # 길이 제한 (500자)
        
        return cleaned_contents

    async def get_status(self):
        return {
            'status': 'ready',
            'service': 'crawler_thread',
            'last_run': None,
            'total_crawled': 0,
            'success_rate': 1.0
        }

# 테스트 실행
if __name__ == "__main__":

    print("=== 크롤러 테스트 시작 ===")
    
    crawler = CrawlerThread()
    result = crawler.run()
    
    print("\n=== 결과 ===")
    for i, news in enumerate(result, 1):
        print(f"{i}. {news['title']}")
    
    print(f"\n총 {len(result)}개 뉴스 수집됨")