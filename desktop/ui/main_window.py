"""
메인 윈도우 클래스
PyQt5를 사용한 데스크톱 애플리케이션의 메인 UI
"""

import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QTableWidget, QTableWidgetItem, QTextEdit, 
                            QLabel, QWidget, QProgressBar, QMessageBox, QHeaderView,
                            QSplitter)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QFont, QIcon


# 프로젝트 내부 모듈 임포트
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.firestore_manager import FirestoreManager
from core.crawler import CrawlerThread
from core.blog_poster import BlogPostThread
from core.api_client import APIClient
from ui.dialogs import NewsDialog

class MainWindow(QMainWindow):
    """메인 윈도우 클래스"""
    
    def __init__(self):
        super().__init__()
        
        # 매니저 및 클라이언트 초기화
        self.firestore_manager = FirestoreManager()
        self.api_client = APIClient()
        
        # 데이터 저장소
        self.news_data = []
        
        # 스레드 참조
        self.crawler_thread = None
        self.blog_thread = None
        
        # UI 초기화
        self.init_ui()
        
        # 초기 데이터 로드
        self.load_initial_data()
        
        # 상태 업데이트 타이머
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # 5초마다 상태 업데이트
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("🏢 YTN 뉴스 자동화 시스템 v1.0 - 트리플송")
        self.setGeometry(100, 100, 1400, 900)
        
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 상단 헤더 생성
        self.create_header(main_layout)
        
        # 버튼 패널 생성
        self.create_button_panel(main_layout)
        
        # 프로그레스 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 20px;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        # 스플리터로 테이블과 로그 분할
        splitter = QSplitter(Qt.Vertical)
        
        # 뉴스 테이블 생성
        self.create_news_table(splitter)
        
        # 로그 패널 생성
        self.create_log_panel(splitter)
        
        # 스플리터 비율 설정
        splitter.setSizes([600, 200])
        main_layout.addWidget(splitter)
        
        # 상태바
        self.create_status_bar()
        
        # 스타일 적용
        self.apply_styles()
        
        # 초기 로그 메시지
        self.log_message("🚀 YTN 뉴스 자동화 시스템이 시작되었습니다.")
        self.log_message("💾 Firestore 연결 상태를 확인하는 중...")
    
    def create_header(self, layout):
        """헤더 생성"""
        header_widget = QWidget()
        header_layout = QVBoxLayout()
        header_widget.setLayout(header_layout)
        
        # 메인 타이틀
        title_label = QLabel("📰 YTN 뉴스 자동화 시스템")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2E86C1; margin: 10px;")
        
        # 서브타이틀
        subtitle_label = QLabel("생성형 AI 기반 업무 자동화 솔루션")
        subtitle_label.setFont(QFont("Arial", 10))
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        
        layout.addWidget(header_widget)
    
    def create_button_panel(self, layout):
        """버튼 패널 생성"""
        button_widget = QWidget()
        button_layout = QVBoxLayout()
        button_widget.setLayout(button_layout)
        
        # 메인 액션 버튼들
        main_button_layout = QHBoxLayout()
        
        self.crawl_btn = QPushButton("📡 YTN 크롤링 실행")
        self.crawl_btn.setToolTip("YTN에서 최신 뉴스 10개를 자동으로 수집합니다")
        self.crawl_btn.clicked.connect(self.start_crawling)
        
        self.blog_btn = QPushButton("📝 네이버 블로그 포스팅")
        self.blog_btn.setToolTip("수집된 뉴스를 네이버 블로그에 자동으로 포스팅합니다")
        self.blog_btn.clicked.connect(self.start_blog_posting)
        
        self.api_test_btn = QPushButton("☁️ Cloud Run API 테스트")
        self.api_test_btn.setToolTip("Cloud Run API 서버 연결을 테스트합니다")
        self.api_test_btn.clicked.connect(self.test_api_connection)
        
        main_button_layout.addWidget(self.crawl_btn)
        main_button_layout.addWidget(self.blog_btn)
        main_button_layout.addWidget(self.api_test_btn)
        
        # CRUD 버튼들
        crud_button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 데이터 새로고침")
        self.refresh_btn.setToolTip("Firestore에서 최신 데이터를 다시 로드합니다")
        self.refresh_btn.clicked.connect(self.refresh_data)
        
        self.add_btn = QPushButton("➕ 뉴스 추가")
        self.add_btn.setToolTip("새로운 뉴스를 수동으로 추가합니다")
        self.add_btn.clicked.connect(self.add_news)
        
        self.edit_btn = QPushButton("✏️ 뉴스 수정")
        self.edit_btn.setToolTip("선택한 뉴스를 수정합니다")
        self.edit_btn.clicked.connect(self.edit_news)
        
        self.delete_btn = QPushButton("🗑️ 뉴스 삭제")
        self.delete_btn.setToolTip("선택한 뉴스를 삭제합니다")
        self.delete_btn.clicked.connect(self.delete_news)
        
        crud_button_layout.addWidget(self.refresh_btn)
        crud_button_layout.addWidget(self.add_btn)
        crud_button_layout.addWidget(self.edit_btn)
        crud_button_layout.addWidget(self.delete_btn)
        
        button_layout.addLayout(main_button_layout)
        button_layout.addLayout(crud_button_layout)
        
        layout.addWidget(button_widget)
    
    def create_news_table(self, parent):
        """뉴스 테이블 생성"""
        table_widget = QWidget()
        table_layout = QVBoxLayout()
        table_widget.setLayout(table_layout)
        
        # 테이블 제목
        table_title = QLabel("📋 뉴스 데이터베이스")
        table_title.setFont(QFont("Arial", 12, QFont.Bold))
        table_layout.addWidget(table_title)
        
        # 테이블 생성
        self.news_table = QTableWidget()
        self.news_table.setColumnCount(9)
        self.news_table.setHorizontalHeaderLabels([
            "카테고리", "기사 제목", "기사 내용", "기자명", "기자 email", "원본 URL", "블로그 포스팅", "블로그 URL", "기사 발행일"
        ])
        
        # 테이블 헤더 설정
        header = self.news_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 카테고리
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # 기사 제목
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 기사 내용
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 기자명
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 기자 email
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 원본 URL
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # 블로그 포스팅
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # 블로그 URL
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)  # 기사 발행일
        
        # 테이블 스타일 설정
        self.news_table.setAlternatingRowColors(True)
        self.news_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        table_layout.addWidget(self.news_table)
        parent.addWidget(table_widget)
    
    def create_log_panel(self, parent):
        """로그 패널 생성"""
        log_widget = QWidget()
        log_layout = QVBoxLayout()
        log_widget.setLayout(log_layout)
        
        # 로그 제목
        log_title_layout = QHBoxLayout()
        log_title = QLabel("📋 실행 로그")
        log_title.setFont(QFont("Arial", 12, QFont.Bold))
        
        # 로그 클리어 버튼
        clear_log_btn = QPushButton("🧹 로그 클리어")
        clear_log_btn.setMaximumWidth(100)
        clear_log_btn.clicked.connect(self.clear_log)
        
        log_title_layout.addWidget(log_title)
        log_title_layout.addStretch()
        log_title_layout.addWidget(clear_log_btn)
        
        # 로그 텍스트
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        
        log_layout.addLayout(log_title_layout)
        log_layout.addWidget(self.log_text)
        
        parent.addWidget(log_widget)
    
    def create_status_bar(self):
        """상태바 생성"""
        status_bar = self.statusBar()
        
        self.connection_status = QLabel("🔌 Firestore: 연결 확인 중...")
        self.api_status = QLabel("☁️ Cloud Run: 연결 확인 중...")
        self.news_count_status = QLabel("📊 뉴스: 0개")
        
        status_bar.addWidget(self.connection_status)
        status_bar.addPermanentWidget(self.api_status)
        status_bar.addPermanentWidget(self.news_count_status)
    
    def apply_styles(self):
        """스타일 적용"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 140px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
                alternate-background-color: #f9f9f9;
                selection-background-color: #e3f2fd;
            }
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #ddd;
                font-family: Consolas, monospace;
                font-size: 9pt;
            }
            QLabel {
                color: #333;
            }
        """)
    
    def load_initial_data(self):
        """초기 데이터 로드"""
        self.log_message("📊 초기 데이터를 로드하는 중...")
        
        try:
            # Firestore에서 데이터 로드 시도
            news_data = self.firestore_manager.get_all_news()
            
            if news_data:
                self.news_data = news_data
                self.log_message(f"✅ Firestore에서 {len(news_data)}개 뉴스를 성공적으로 로드했습니다.")
                self.connection_status.setText("🔌 Firestore: 연결됨")
            else:
                # 더미 데이터 생성
                # self.create_sample_data()
                self.log_message("⚠️ Firestore 연결 실패. 샘플 데이터를 생성했습니다.")
                self.connection_status.setText("🔌 Firestore: 연결 실패 (로컬 모드)")
            
            self.update_news_table()
            self.update_status()
            
        except Exception as e:
            self.log_message(f"❌ 초기 데이터 로드 오류: {str(e)}")
            self.update_news_table()
    

    def update_news_table(self):
        """뉴스 테이블 업데이트"""

        current_row_count = self.news_table.rowCount()+1
        print(f'현재 테이블 행 개수: {current_row_count}')
        print(f'새로 설정할 데이터 개수: {len(self.news_data)}')

        self.news_table.setRowCount(len(self.news_data))
        
        new_row_count = self.news_table.rowCount()
        print(f'설정 후 테이블 행 개수: {new_row_count}')
    
        for i, news in enumerate(self.news_data):
            no = i + current_row_count
            print(f'window news : {news}')
             # 누적 번호 계산: i는 0부터 시작하므로 i+1이 실제 번호
            # display_no = i + 1
            
            # # 번호 컬럼
            # item = QTableWidgetItem(str(display_no))
            # item.setData(Qt.UserRole, display_no)
            # self.news_table.setItem(i, 0, item)

            self.news_table.setItem(i, 0, QTableWidgetItem(news.get('category', '')))
            self.news_table.setItem(i, 1, QTableWidgetItem(news.get('title', '')))
            self.news_table.setItem(i, 2, QTableWidgetItem(news.get('content', '')))
            self.news_table.setItem(i, 3, QTableWidgetItem(news.get('author', '')))
            self.news_table.setItem(i, 4, QTableWidgetItem(news.get('email', '')))
            self.news_table.setItem(i, 5, QTableWidgetItem(news.get('url', '')))
            
            # 블로그 포스팅 상태 표시
            posted_status = "✅ 완료" if news.get('posted_to_blog') else "❌ 대기"
            self.news_table.setItem(i, 6, QTableWidgetItem(posted_status))
            
            self.news_table.setItem(i, 7, QTableWidgetItem(news.get('blog_url', '')))
            self.news_table.setItem(i, 8, QTableWidgetItem(news.get('published_date', '')))
    
    def update_status(self):
        """상태바 업데이트"""
        # 뉴스 개수 업데이트
        total_news = len(self.news_data)
        posted_news = len([news for news in self.news_data if news.get('posted_to_blog')])
        self.news_count_status.setText(f"📊 뉴스: {total_news}개 (포스팅: {posted_news}개)")
    
    def log_message(self, message):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.append(formatted_message)
        
        # 자동 스크롤
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """로그 클리어"""
        self.log_text.clear()
        self.log_message("🧹 로그가 클리어되었습니다.")
    
    # ========== 크롤링 관련 메서드 ==========
    
    def start_crawling(self):
        """YTN 크롤링 시작"""
        self.crawl_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 무한 프로그레스
        
        self.log_message("🕷️ YTN 뉴스 크롤링을 시작합니다...")
        
        # 크롤링 스레드 시작
        self.crawler_thread = CrawlerThread()
        self.crawler_thread.progress_updated.connect(self.log_message)
        self.crawler_thread.crawling_finished.connect(self.on_crawling_finished)
        self.crawler_thread.start()
    
    def on_crawling_finished(self, news_list):
        """크롤링 완료 처리"""
        self.crawl_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if news_list:
            saved_count = 0
            for news in news_list:
                # Firestore에 저장 시도
                doc_id = self.firestore_manager.add_news(news)
                if doc_id:
                    news['id'] = doc_id
                    saved_count += 1
                else:
                    # Firestore 실패 시 로컬 ID 생성
                    news['id'] = f'local_{len(self.news_data) + saved_count}'
            
            # 로컬 데이터에 추가
            self.news_data.extend(news_list)
            self.update_news_table()
            self.update_status()
            
            self.log_message(f"🎉 크롤링 완료! {len(news_list)}개 뉴스 수집 (Firestore 저장: {saved_count}개)")
            
            # 성공 메시지 박스
            QMessageBox.information(self, "크롤링 완료", 
                                   f"YTN에서 {len(news_list)}개의 뉴스를 성공적으로 수집했습니다!")
        else:
            self.log_message("❌ 크롤링 실패: 뉴스를 수집할 수 없습니다.")
            QMessageBox.warning(self, "크롤링 실패", "뉴스 수집에 실패했습니다. 네트워크 연결을 확인해주세요.")
    
    # ========== 블로그 포스팅 관련 메서드 ==========
    
    def start_blog_posting(self):
        """네이버 블로그 포스팅 시작"""
        # 아직 포스팅되지 않은 뉴스 찾기
        unposted_news = [news for news in self.news_data if not news.get('posted_to_blog')]
        
        if not unposted_news:
            QMessageBox.information(self, "알림", "포스팅할 뉴스가 없습니다.\n먼저 크롤링을 실행해주세요.")
            return
        
        # 최대 3개만 포스팅
        news_to_post = unposted_news[:3]
        
        reply = QMessageBox.question(self, "블로그 포스팅 확인", 
                                   f"{len(news_to_post)}개의 뉴스를 네이버 블로그에 포스팅하시겠습니까?")
        
        if reply != QMessageBox.Yes:
            return
        
        self.blog_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        self.log_message(f"📝 네이버 블로그 포스팅 시작 ({len(news_to_post)}개 뉴스)")
        
        # 블로그 포스팅 스레드 시작
        # # self.blog_thread = BlogPostThread(news_to_post)
        # self.blog_thread.progress_updated.connect(self.log_message)
        # self.blog_thread.posting_finished.connect(self.on_posting_finished)
        # self.blog_thread.start()
    
    def on_posting_finished(self, posted_news_list):
        """블로그 포스팅 완료 처리"""
        self.blog_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if posted_news_list:
            updated_count = 0
            
            # 포스팅된 뉴스들의 상태 업데이트
            for posted_news in posted_news_list:
                for i, news in enumerate(self.news_data):
                    if news.get('id') == posted_news.get('id'):
                        # 로컬 데이터 업데이트
                        self.news_data[i].update(posted_news)
                        
                        # Firestore 업데이트
                        update_data = {
                            'posted_to_blog': True,
                            'blog_url': posted_news['blog_url']
                        }
                        if self.firestore_manager.update_news(posted_news['id'], update_data):
                            updated_count += 1
            
            self.update_news_table()
            self.update_status()
            
            self.log_message(f"🎊 블로그 포스팅 완료! {len(posted_news_list)}개 포스팅 (DB 업데이트: {updated_count}개)")
            
            # 성공 메시지
            QMessageBox.information(self, "포스팅 완료", 
                                   f"{len(posted_news_list)}개 뉴스를 성공적으로 포스팅했습니다!")
        else:
            self.log_message("❌ 블로그 포스팅 실패")
            QMessageBox.warning(self, "포스팅 실패", "블로그 포스팅에 실패했습니다.")
    
    # ========== API 관련 메서드 ==========
    
    def test_api_connection(self):
        """Cloud Run API 연결 테스트"""
        self.log_message("☁️ Cloud Run API 연결을 테스트하는 중...")
        
        try:
            result = self.api_client.test_connection()
            if result:
                self.log_message("✅ Cloud Run API 연결 성공!")
                self.api_status.setText("☁️ Cloud Run: 연결됨")
                QMessageBox.information(self, "API 테스트", "Cloud Run API 연결이 성공했습니다!")
            else:
                self.log_message("❌ Cloud Run API 연결 실패")
                self.api_status.setText("☁️ Cloud Run: 연결 실패")
                QMessageBox.warning(self, "API 테스트", "Cloud Run API 연결에 실패했습니다.")
        except Exception as e:
            self.log_message(f"❌ API 테스트 오류: {str(e)}")
            self.api_status.setText("☁️ Cloud Run: 오류")
    
    # ========== CRUD 관련 메서드 ==========
    
    def refresh_data(self):
        """데이터 새로고침"""
        self.log_message("🔄 데이터를 새로고침하는 중...")
        self.load_initial_data()
    
    def add_news(self):
        """뉴스 추가"""
        dialog = NewsDialog(parent=self)
        if dialog.exec_() == dialog.Accepted:
            news_data = dialog.get_news_data()
            
            # Firestore에 저장 시도
            doc_id = self.firestore_manager.add_news(news_data)
            if doc_id:
                news_data['id'] = doc_id
                self.log_message(f"✅ 새 뉴스가 Firestore에 저장되었습니다: {news_data['title']}")
            else:
                # 로컬 ID 생성
                news_data['id'] = f'local_{len(self.news_data)}'
                self.log_message(f"⚠️ 새 뉴스가 로컬에 저장되었습니다: {news_data['title']}")
            
            # 로컬 데이터에 추가
            self.news_data.append(news_data)
            self.update_news_table()
            self.update_status()
    
    def edit_news(self):
        """뉴스 수정"""
        current_row = self.news_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "경고", "수정할 뉴스를 선택해주세요.")
            return
        
        news_data = self.news_data[current_row]
        dialog = NewsDialog(news_data, parent=self)
        
        if dialog.exec_() == dialog.Accepted:
            updated_data = dialog.get_news_data()
            updated_data['id'] = news_data['id']  # ID 유지
            
            # Firestore 업데이트
            if self.firestore_manager.update_news(news_data['id'], updated_data):
                self.log_message(f"✅ 뉴스가 Firestore에서 업데이트되었습니다: {updated_data['title']}")
            else:
                self.log_message(f"⚠️ 뉴스가 로컬에서만 업데이트되었습니다: {updated_data['title']}")
            
            # 로컬 데이터 업데이트
            self.news_data[current_row] = updated_data
            self.update_news_table()
            self.update_status()
    
    def delete_news(self):
        """뉴스 삭제"""
        current_row = self.news_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "경고", "삭제할 뉴스를 선택해주세요.")
            return
        
        news_data = self.news_data[current_row]
        reply = QMessageBox.question(self, "삭제 확인", 
                                   f"다음 뉴스를 삭제하시겠습니까?\n\n{news_data['title']}")
        
        if reply == QMessageBox.Yes:
            # Firestore에서 삭제
            if self.firestore_manager.delete_news(news_data['id']):
                self.log_message(f"✅ 뉴스가 Firestore에서 삭제되었습니다: {news_data['title']}")
            else:
                self.log_message(f"⚠️ 뉴스가 로컬에서만 삭제되었습니다: {news_data['title']}")
            
            # 로컬 데이터에서 삭제
            del self.news_data[current_row]
            self.update_news_table()
            self.update_status()
    
    def closeEvent(self, event):
        """애플리케이션 종료 시 처리"""
        reply = QMessageBox.question(self, '종료 확인', 
                                   '애플리케이션을 종료하시겠습니까?',
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.log_message("👋 애플리케이션을 종료합니다...")
            
            # 실행 중인 스레드 정리
            if self.crawler_thread and self.crawler_thread.isRunning():
                self.crawler_thread.terminate()
                self.crawler_thread.wait()
            
            if self.blog_thread and self.blog_thread.isRunning():
                self.blog_thread.terminate()
                self.blog_thread.wait()
            
            event.accept()
        else:
            event.ignore()

