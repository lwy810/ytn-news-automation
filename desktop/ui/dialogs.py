"""
다이얼로그 클래스들
뉴스 추가/수정을 위한 다이얼로그
"""

from datetime import datetime
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                            QLineEdit, QTextEdit, QPushButton, QLabel, 
                            QDialogButtonBox, QMessageBox, QComboBox, QDateTimeEdit)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QFont

class NewsDialog(QDialog):
    """뉴스 추가/수정 다이얼로그"""
    
    def __init__(self, news_data=None, parent=None):
        super().__init__(parent)
        self.news_data = news_data
        self.is_edit_mode = news_data is not None
        self.init_ui()
        self.populate_fields()
    
    def init_ui(self):
        """UI 초기화"""
        title = "뉴스 수정" if self.is_edit_mode else "뉴스 추가"
        self.setWindowTitle(f"📝 {title}")
        self.setModal(True)
        self.resize(600, 500)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # 제목
        title_label = QLabel(f"📰 {title}")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2E86C1; margin: 10px;")
        main_layout.addWidget(title_label)
        
        # 폼 레이아웃
        form_layout = QFormLayout()
        
        # 뉴스 제목
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("뉴스 제목을 입력하세요")
        form_layout.addRow("📰 제목:", self.title_edit)
        
        # 뉴스 내용
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("뉴스 내용을 입력하세요")
        self.content_edit.setMinimumHeight(150)
        form_layout.addRow("📄 내용:", self.content_edit)
        

        # 카테고리 (콤보박스)
        self.category_combo = QComboBox()
        self.category_combo.addItems(["정치", "경제", "사회", "문화", "스포츠", "국제", "IT/과학", "기타"])
        self.category_combo.setEditable(True)
        form_layout.addRow("🏷️ 카테고리:", self.category_combo)
        
        # 발행일
        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        form_layout.addRow("📅 발행일:", self.datetime_edit)
        
        # 원본 URL
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("원본 뉴스 URL을 입력하세요")
        form_layout.addRow("🔗 원본 URL:", self.url_edit)
        
        main_layout.addLayout(form_layout)
        
        # 버튼들
        button_layout = QHBoxLayout()
        
        # 저장 버튼
        self.save_btn = QPushButton("💾 저장")
        self.save_btn.clicked.connect(self.accept)
        self.save_btn.setDefault(True)
        
        # 취소 버튼
        self.cancel_btn = QPushButton("❌ 취소")
        self.cancel_btn.clicked.connect(self.reject)
        
        # 미리보기 버튼
        self.preview_btn = QPushButton("👁️ 미리보기")
        self.preview_btn.clicked.connect(self.show_preview)
        
        button_layout.addWidget(self.preview_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(button_layout)
        
        # 스타일 적용
        self.apply_styles()
        
        # 제목 필드에 포커스
        self.title_edit.setFocus()
    
    def apply_styles(self):
        """스타일 적용"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f9f9f9;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 4px;
                font-size: 11pt;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
            QTextEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 4px;
                font-size: 11pt;
            }
            QTextEdit:focus {
                border-color: #4CAF50;
            }
            QComboBox {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 4px;
                font-size: 11pt;
            }
            QDateTimeEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 4px;
                font-size: 11pt;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:default {
                background-color: #2196F3;
            }
            QPushButton:default:hover {
                background-color: #1976D2;
            }
        """)
    
    def populate_fields(self):
        """기존 데이터로 필드 채우기 (수정 모드)"""
        if not self.is_edit_mode or not self.news_data:
            return
        
        self.title_edit.setText(self.news_data.get('title', ''))
        self.content_edit.setText(self.news_data.get('content', ''))
        
        # 카테고리 설정
        category = self.news_data.get('category', '')
        index = self.category_combo.findText(category)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)
        else:
            self.category_combo.setCurrentText(category)
        
        # 발행일 설정
        published_date = self.news_data.get('published_date', '')
        if published_date:
            try:
                dt = QDateTime.fromString(published_date, "yyyy-MM-dd hh:mm:ss")
                if dt.isValid():
                    self.datetime_edit.setDateTime(dt)
            except:
                pass
        
        self.url_edit.setText(self.news_data.get('url', ''))
    
    def validate_input(self):
        """입력 데이터 검증"""
        title = self.title_edit.text().strip()
        content = self.content_edit.toPlainText().strip()
        
        if not title:
            QMessageBox.warning(self, "입력 오류", "뉴스 제목을 입력해주세요.")
            self.title_edit.setFocus()
            return False
        
        if not content:
            QMessageBox.warning(self, "입력 오류", "뉴스 내용을 입력해주세요.")
            self.content_edit.setFocus()
            return False
        
        if len(title) > 200:
            QMessageBox.warning(self, "입력 오류", "제목은 200자 이내로 입력해주세요.")
            self.title_edit.setFocus()
            return False
        
        if len(content) > 5000:
            QMessageBox.warning(self, "입력 오류", "내용은 5000자 이내로 입력해주세요.")
            self.content_edit.setFocus()
            return False
        
        return True
    
    def get_news_data(self):
        """입력된 뉴스 데이터 반환"""
        return {
            'title': self.title_edit.text().strip(),
            'content': self.content_edit.toPlainText().strip(),
            'category': self.category_combo.currentText().strip(),
            'published_date': self.datetime_edit.dateTime().toString("yyyy-MM-dd hh:mm:ss"),
            'url': self.url_edit.text().strip(),
            'posted_to_blog': self.news_data.get('posted_to_blog', False) if self.news_data else False,
            'blog_url': self.news_data.get('blog_url', '') if self.news_data else ''
        }
    
    def show_preview(self):
        """뉴스 미리보기"""
        if not self.validate_input():
            return
        
        preview_dialog = NewsPreviewDialog(self.get_news_data(), self)
        preview_dialog.exec_()
    
    def accept(self):
        """저장 버튼 클릭 시"""
        if self.validate_input():
            super().accept()


class NewsPreviewDialog(QDialog):
    """뉴스 미리보기 다이얼로그"""
    
    def __init__(self, news_data, parent=None):
        super().__init__(parent)
        self.news_data = news_data
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("👁️ 뉴스 미리보기")
        self.setModal(True)
        self.resize(700, 600)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 제목
        title_label = QLabel("📰 뉴스 미리보기")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2E86C1; margin: 10px;")
        layout.addWidget(title_label)
        
        # 미리보기 텍스트
        preview_text = QTextEdit()
        preview_text.setReadOnly(True)
        
        # HTML 형식으로 뉴스 미리보기 생성
        preview_html = self.generate_preview_html()
        preview_text.setHtml(preview_html)
        
        layout.addWidget(preview_text)
        
        # 닫기 버튼
        close_btn = QPushButton("✅ 닫기")
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        # 스타일 적용
        self.setStyleSheet("""
            QDialog {
                background-color: #f9f9f9;
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 100px;
            }
        """)
    
    def generate_preview_html(self):
        """미리보기 HTML 생성"""
        return f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                }}
                .header {{
                    border-bottom: 2px solid #2E86C1;
                    padding-bottom: 10px;
                    margin-bottom: 20px;
                }}
                .title {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #333;
                    margin-bottom: 10px;
                }}
                .meta {{
                    color: #666;
                    font-size: 14px;
                    margin-bottom: 5px;
                }}
                .content {{
                    font-size: 16px;
                    line-height: 1.8;
                    margin-top: 20px;
                    text-align: justify;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    color: #666;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="title">{self.news_data['title']}</div>
                <div class="meta">📅 발행일: {self.news_data['published_date']}</div>
                <div class="meta">🏷️ 카테고리: {self.news_data['category']}</div>
                <div class="meta">🔗 원본: <a href="{self.news_data['url']}">{self.news_data['url']}</a></div>
            </div>
            
            <div class="content">
                {self.news_data['content'].replace(chr(10), '<br>')}
            </div>
            
            <div class="footer">
                <p>📝 이 뉴스는 YTN 뉴스 자동화 시스템을 통해 관리됩니다.</p>
                <p>🏢 트리플송(Triple Song) - 생성형 AI 기반 업무 자동화 솔루션</p>
            </div>
        </body>
        </html>
        """