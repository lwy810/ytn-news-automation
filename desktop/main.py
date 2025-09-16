"""
YTN 뉴스 자동화 시스템 메인 애플리케이션
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QDir

# 프로젝트 루트 경로를 Python 패스에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from ui.main_window import MainWindow

def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    
    # 애플리케이션 정보 설정
    app.setApplicationName("YTN 뉴스 자동화 시스템")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("트리플송")
    
    # 메인 윈도우 생성 및 표시
    try:
        window = MainWindow()
        window.show()
        
        # 애플리케이션 실행
        return app.exec_()
        
    except Exception as e:
        print(f"애플리케이션 시작 오류: {e}")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)