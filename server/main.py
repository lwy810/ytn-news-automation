"""
YTN 뉴스 자동화 시스템 FastAPI 서버
Cloud Run에서 실행되는 REST API 서버
"""

import os
import sys
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from services.firestore_service import FirestoreService

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from desktop.core.crawler import CrawlerThread

# 기본 모델 정의 (모듈 임포트 실패 시 사용)
class NewsCreate(BaseModel):
    title: str
    content: str
    category: str = "기타"
    url: Optional[str] = None
    published_date: Optional[str] = None
    posted_to_blog: bool = False
    blog_url: Optional[str] = None

class NewsUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    url: Optional[str] = None
    published_date: Optional[str] = None
    posted_to_blog: Optional[bool] = None
    blog_url: Optional[str] = None

class NewsResponse(BaseModel):
    id: str
    title: str
    content: str
    category: str
    url: Optional[str] = None
    published_date: str
    posted_to_blog: bool = False
    blog_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class StandardResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M'))

class AsyncCrawlingService:
    def __init__(self):
        self.crawler = CrawlerThread()
    
    async def crawl_ytn_news(self):
        import asyncio
        import concurrent.futures
        
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        executor, 
                        self._run_sync_crawling
                    ),
                    timeout=30.0
                )
                return result
        except Exception as e:
            return {
                'success': False,
                'message': f'크롤링 오류: {str(e)}',
                'news_list': [],
                'crawled_count': 0
            }
    
    def _run_sync_crawling(self):
        try:
            news_list = self.crawler.crawl_ytn_news()  # 리스트 반환
            
            # 리스트를 딕셔너리로 래핑
            return {
                'success': True,
                'message': f'크롤링 완료: {len(news_list)}개 뉴스 수집',
                'news_list': news_list,
                'crawled_count': len(news_list)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'크롤링 오류: {str(e)}',
                'news_list': [],
                'crawled_count': 0
            }


# 전역 서비스 인스턴스
firestore_service = None
crawling_service = None
blog_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    global firestore_service, crawling_service, blog_service
    
    print("🚀 YTN 뉴스 자동화 시스템 API 서버 시작...")
    
    # Mock 서비스 초기화
    firestore_service = FirestoreService()
    crawling_service = AsyncCrawlingService()
    # blog_service = MockBlogService()
  
    print("✅ 서비스 초기화 및 샘플 데이터 생성 완료")

    yield

    # 종료 시 정리
    print("👋 API 서버를 종료합니다...")
    if firestore_service:
        firestore_service.close()

# FastAPI 앱 생성
app = FastAPI(
    title="YTN 뉴스 자동화 시스템 API",
    description="생성형 AI 기반 업무 자동화 솔루션",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 배포 시에는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 의존성 함수들
def get_firestore_service():
    if firestore_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firestore 서비스를 사용할 수 없습니다"
        )
    return firestore_service

def get_crawling_service():
    if crawling_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="크롤링 서비스를 사용할 수 없습니다"
        )
    return crawling_service

def get_blog_service():
    if blog_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="블로그 서비스를 사용할 수 없습니다"
        )
    return blog_service

# ========== 기본 헬스체크 엔드포인트 ==========

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "🏢 YTN 뉴스 자동화 시스템 API",
        "version": "1.0.0",
        "status": "running",
        "description": "생성형 AI 기반 업무 자동화 솔루션",
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M'),
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "status": "/status",
            "api": "/api/"
        }
    }

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M'),
        "services": {
            "firestore": firestore_service is not None and firestore_service.is_connected,
            "crawling": crawling_service is not None,
            "blog": blog_service is not None
        },
        "system": {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "environment": os.getenv("ENVIRONMENT", "production")
        }
    }

@app.get("/ping")
async def ping():
    """간단한 ping 응답"""
    return {
        "message": "pong",
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M')
    }

@app.get("/status")
async def get_status():
    """시스템 상태 정보"""
    return {
        "system": "YTN 뉴스 자동화 시스템",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "production"),
        "uptime": datetime.now().strftime('%Y-%m-%d %H:%M'),
        "services": {
            "firestore": {
                "available": firestore_service is not None,
                "connected": firestore_service.is_connected if firestore_service else False,
                "type": "mock" if isinstance(firestore_service, FirestoreService) else "real"
            },
            "crawling": {
                "available": crawling_service is not None,
                "type": "mock" if isinstance(crawling_service, CrawlerThread) else "real"
            },
            # "blog": {
            #     "available": blog_service is not None,
            #     "type": "mock" if isinstance(blog_service, MockBlogService) else "real"
            # }
        }
    }

# ========== 뉴스 CRUD API ==========

@app.get("/api/news", response_model=List[NewsResponse])
async def get_all_news(
    limit: int = Query(100, ge=1, le=1000, description="조회할 뉴스 개수"),
    offset: int = Query(0, ge=0, description="시작 위치"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    firestore_svc = Depends(get_firestore_service)
):
    """모든 뉴스 조회"""
    try:
        news_list = await firestore_svc.get_all_news(limit=limit, offset=offset, category=category)
        return news_list
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"뉴스 조회 중 오류가 발생했습니다: {str(e)}"
        )

@app.get("/api/news/{news_id}", response_model=NewsResponse)
async def get_news_by_id(
    news_id: str,
    firestore_svc = Depends(get_firestore_service)
):
    """특정 뉴스 조회"""
    try:
        news = await firestore_svc.get_news_by_id(news_id)
        if not news:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="뉴스를 찾을 수 없습니다"
            )
        return news
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"뉴스 조회 중 오류가 발생했습니다: {str(e)}"
        )

@app.post("/api/news", response_model=StandardResponse)
async def create_news(
    news: NewsCreate,
    firestore_svc = Depends(get_firestore_service)
):
    """뉴스 생성"""
    try:
        news_id = await firestore_svc.create_news(news)
        return StandardResponse(
            success=True,
            message="뉴스가 성공적으로 생성되었습니다",
            data={"id": news_id}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"뉴스 생성 중 오류가 발생했습니다: {str(e)}"
        )

@app.put("/api/news/{news_id}", response_model=StandardResponse)
async def update_news(
    news_id: str,
    news: NewsUpdate,
    firestore_svc = Depends(get_firestore_service)
):
    """뉴스 업데이트"""
    try:
        # 뉴스 존재 확인
        existing_news = await firestore_svc.get_news_by_id(news_id)
        if not existing_news:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="뉴스를 찾을 수 없습니다"
            )
        
        # 업데이트 실행
        success = await firestore_svc.update_news(news_id, news)
        if success:
            return StandardResponse(
                success=True,
                message="뉴스가 성공적으로 업데이트되었습니다"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="뉴스 업데이트에 실패했습니다"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"뉴스 업데이트 중 오류가 발생했습니다: {str(e)}"
        )

@app.delete("/api/news/{news_id}", response_model=StandardResponse)
async def delete_news(
    news_id: str,
    firestore_svc = Depends(get_firestore_service)
):
    """뉴스 삭제"""
    try:
        # 뉴스 존재 확인
        existing_news = await firestore_svc.get_news_by_id(news_id)
        if not existing_news:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="뉴스를 찾을 수 없습니다"
            )
        
        # 삭제 실행
        success = await firestore_svc.delete_news(news_id)
        if success:
            return StandardResponse(
                success=True,
                message="뉴스가 성공적으로 삭제되었습니다"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="뉴스 삭제에 실패했습니다"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"뉴스 삭제 중 오류가 발생했습니다: {str(e)}"
        )

@app.get("/api/news/unposted", response_model=List[NewsResponse])
async def get_unposted_news(
    limit: int = Query(10, ge=1, le=50, description="조회할 미포스팅 뉴스 개수"),
    firestore_svc = Depends(get_firestore_service)
):
    """미포스팅 뉴스 조회"""
    try:
        news_list = await firestore_svc.get_unposted_news(limit=limit)
        return news_list
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"미포스팅 뉴스 조회 중 오류가 발생했습니다: {str(e)}"
        )

@app.patch("/api/news/{news_id}/posted", response_model=StandardResponse)
async def mark_as_posted(
    news_id: str,
    data: dict,
    firestore_svc = Depends(get_firestore_service)
):
    """뉴스를 포스팅 완료로 표시"""
    try:
        success = await firestore_svc.mark_as_posted(
            news_id, 
            data.get("blog_url", ""),
            data.get("posted_at")
        )
        if success:
            return StandardResponse(
                success=True,
                message="뉴스가 포스팅 완료로 표시되었습니다"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="뉴스를 찾을 수 없거나 업데이트에 실패했습니다"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"포스팅 상태 업데이트 중 오류가 발생했습니다: {str(e)}"
        )

@app.get("/api/news/search", response_model=List[NewsResponse])
async def search_news(
    q: str = Query(..., min_length=1, description="검색어"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    limit: int = Query(50, ge=1, le=200, description="결과 개수 제한"),
    firestore_svc = Depends(get_firestore_service)
):
    """뉴스 검색"""
    try:
        news_list = await firestore_svc.search_news(q, category=category, limit=limit)
        return news_list
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"뉴스 검색 중 오류가 발생했습니다: {str(e)}"
        )

# ========== 일괄 작업 API ==========

@app.post("/api/news/bulk", response_model=StandardResponse)
async def create_multiple_news(
    data: dict,
    firestore_svc = Depends(get_firestore_service)
):
    """뉴스 일괄 생성"""
    try:
        news_list = data.get("news_list", [])
        if not news_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="뉴스 목록이 비어있습니다"
            )
        
        created_ids = await firestore_svc.create_multiple_news(news_list)
        return StandardResponse(
            success=True,
            message=f"{len(created_ids)}개 뉴스가 생성되었습니다",
            data={"created_ids": created_ids, "created_count": len(created_ids)}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"뉴스 일괄 생성 중 오류가 발생했습니다: {str(e)}"
        )

@app.put("/api/news/bulk", response_model=StandardResponse)
async def update_multiple_news(
    data: dict,
    firestore_svc = Depends(get_firestore_service)
):
    """뉴스 일괄 업데이트"""
    try:
        updates = data.get("updates", [])
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="업데이트 목록이 비어있습니다"
            )
        
        updated_count = await firestore_svc.update_multiple_news(updates)
        return StandardResponse(
            success=True,
            message=f"{updated_count}개 뉴스가 업데이트되었습니다",
            data={"updated_count": updated_count}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"뉴스 일괄 업데이트 중 오류가 발생했습니다: {str(e)}"
        )

# ========== 통계 API ==========

@app.get("/api/news/stats")
async def get_news_statistics(
    firestore_svc = Depends(get_firestore_service)
):
    """뉴스 통계 정보"""
    try:
        stats = await firestore_svc.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"통계 조회 중 오류가 발생했습니다: {str(e)}"
        )

@app.get("/api/posting/stats")
async def get_posting_statistics(
    firestore_svc = Depends(get_firestore_service)
):
    """포스팅 통계 정보"""
    try:
        stats = await firestore_svc.get_posting_statistics()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"포스팅 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )

# ========== 크롤링 API ==========

@app.post("/api/crawl/trigger", response_model=StandardResponse)
async def trigger_crawling(
    crawling_svc = Depends(get_crawling_service),
    firestore_svc = Depends(get_firestore_service)
):
    """YTN 크롤링 트리거"""
    try:
        # result = await crawling_svc.crawl_ytn_news()
        result = await crawling_svc.crawl_ytn_news()
        print(f'result : {result}')
        print("1. 크롤링 시작")

        # 크롤링된 뉴스를 Firestore에 저장
        if result.get("success") and result.get("news_list"):
            print("2. 크롤링 시작")
            created_ids = await firestore_svc.create_multiple_news(result["news_list"])
            result["saved_count"] = len(created_ids)
            result["created_ids"] = created_ids
        
        return StandardResponse(
            success=result.get("success", False),
            message=result.get("message", "크롤링 완료"),
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"크롤링 실행 중 오류가 발생했습니다: {str(e)}"
        )

@app.get("/api/crawl/status")
async def get_crawling_status(
    crawling_svc = Depends(get_crawling_service)
):
    """크롤링 상태 조회"""
    try:
        status_info = await crawling_svc.get_status()
        return status_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"크롤링 상태 조회 중 오류가 발생했습니다: {str(e)}"
        )

# ========== 블로그 포스팅 API ==========

@app.post("/api/blog/post", response_model=StandardResponse)
async def trigger_blog_posting(
    data: dict = None,
    blog_svc = Depends(get_blog_service),
    firestore_svc = Depends(get_firestore_service)
):
    """블로그 포스팅 트리거"""
    try:
        news_ids = data.get("news_ids") if data else None
        
        # 포스팅할 뉴스 조회
        if news_ids:
            news_list = []
            for news_id in news_ids:
                news = await firestore_svc.get_news_by_id(news_id)
                if news:
                    news_list.append(news)
        else:
            # 미포스팅 뉴스 3개 조회
            news_list = await firestore_svc.get_unposted_news(limit=3)
        
        if not news_list:
            return StandardResponse(
                success=False,
                message="포스팅할 뉴스가 없습니다"
            )
        
        # 블로그 포스팅 실행
        result = await blog_svc.post_to_blog(news_list)
        
        # 포스팅 성공한 뉴스들의 상태 업데이트
        if result.get("success") and result.get("posted_news"):
            for posted_news in result["posted_news"]:
                await firestore_svc.mark_as_posted(
                    posted_news["id"],
                    posted_news["blog_url"]
                )
        
        return StandardResponse(
            success=result.get("success", False),
            message=result.get("message", "블로그 포스팅 완료"),
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"블로그 포스팅 중 오류가 발생했습니다: {str(e)}"
        )

@app.get("/api/blog/status")
async def get_blog_posting_status(
    blog_svc = Depends(get_blog_service)
):
    """블로그 포스팅 상태 조회"""
    try:
        status_info = await blog_svc.get_status()
        return status_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"블로그 포스팅 상태 조회 중 오류가 발생했습니다: {str(e)}"
        )

# ========== API 정보 ==========

@app.get("/api/info")
async def get_api_info():
    """API 정보 조회"""
    return {
        "name": "YTN 뉴스 자동화 시스템 API",
        "version": "1.0.0",
        "description": "생성형 AI 기반 업무 자동화 솔루션",
        "developer": "이우영",
        "endpoints": {
            "news": {
                "GET /api/news": "모든 뉴스 조회",
                "GET /api/news/{id}": "특정 뉴스 조회",
                "POST /api/news": "뉴스 생성",
                "PUT /api/news/{id}": "뉴스 업데이트",
                "DELETE /api/news/{id}": "뉴스 삭제",
                "GET /api/news/unposted": "미포스팅 뉴스 조회",
                "GET /api/news/search": "뉴스 검색",
                "POST /api/news/bulk": "뉴스 일괄 생성",
                "PUT /api/news/bulk": "뉴스 일괄 업데이트"
            },
            "crawling": {
                "POST /api/crawl/trigger": "크롤링 실행",
                "GET /api/crawl/status": "크롤링 상태 조회"
            },
            "blog": {
                "POST /api/blog/post": "블로그 포스팅 실행",
                "GET /api/blog/status": "블로그 포스팅 상태 조회"
            },
            "stats": {
                "GET /api/news/stats": "뉴스 통계",
                "GET /api/posting/stats": "포스팅 통계"
            },
            "system": {
                "GET /health": "헬스체크",
                "GET /status": "시스템 상태",
                "GET /ping": "Ping 테스트",
                "GET /api/info": "API 정보",
                "GET /api/version": "버전 정보"
            },
            "test": {
                "POST /api/test/news": "테스트 뉴스 생성",
                "DELETE /api/test/cleanup": "테스트 데이터 정리"
            }
        },
        "docs": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "contact": {
            "project": "YTN 뉴스 자동화 시스템",
            "purpose": "development",
            "github": "https://github.com/your-username/ytn-news-automation"
        }
    }

@app.get("/api/version")
async def get_version():
    """API 버전 정보"""
    return {
        "api_version": "1.0.0",
        "system": "YTN 뉴스 자동화 시스템",
        "build_date": "2024-01-15",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "environment": os.getenv("ENVIRONMENT", "production"),
        "features": {
            "ytn_crawling": True,
            "blog_posting": True,
            "firestore_crud": True,
            "rest_api": True,
            "mock_services": True
        }
    }

@app.get("/api/config")
async def get_config():
    """시스템 설정 정보"""
    return {
        "cors_enabled": True,
        "docs_enabled": True,
        "max_news_limit": 1000,
        "default_crawl_count": 10,
        "default_post_count": 3,
        "supported_categories": [
            "정치", "경제", "사회", "문화", "스포츠", 
            "국제", "과학", "환경", "교육", "기타"
        ],
        "limits": {
            "news_per_request": 1000,
            "search_results": 200,
            "bulk_operations": 100,
            "unposted_news": 50
        }
    }

@app.get("/api/metrics")
async def get_metrics():
    """시스템 메트릭스"""
    try:
        metrics = {
            "uptime": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "requests_total": 0,
            "errors_total": 0,
            "response_time_avg": 0.15,
            "service_status": {
                "firestore": "healthy" if firestore_service else "unavailable",
                "crawling": "healthy" if crawling_service else "unavailable",
                "blog": "healthy" if blog_service else "unavailable"
            }
        }
        
        # Firestore 통계 추가
        if firestore_service:
            try:
                stats = await firestore_service.get_statistics()
                metrics.update({
                    "total_news": stats.get("total_news", 0),
                    "posted_news": stats.get("posted_news", 0),
                    "unposted_news": stats.get("unposted_news", 0),
                    "categories": stats.get("categories", {})
                })
            except:
                pass
        
        return metrics
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M')
        }

# ========== 테스트 엔드포인트 ==========

@app.post("/api/test/news", response_model=StandardResponse)
async def create_test_news(
    firestore_svc = Depends(get_firestore_service)
):
    """테스트용 뉴스 생성"""
    try:
        test_news = {
            "title": f"테스트 뉴스 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "content": "이것은 API 테스트를 위한 샘플 뉴스입니다. 실제 뉴스가 아니므로 참고용으로만 사용하세요. 시스템의 CRUD 기능을 테스트하기 위해 생성된 데이터입니다.",
            "category": "기타",
            "url": f"https://www.ytn.co.kr/news/test_{int(datetime.now().strftime('%Y-%m-%d %H:%M'))}",
            "published_date": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "posted_to_blog": False,
            "blog_url": ""
        }
        
        news_id = await firestore_svc.create_news(test_news)
        
        return StandardResponse(
            success=True,
            message="테스트 뉴스가 성공적으로 생성되었습니다",
            data={"id": news_id, "news": test_news}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"테스트 뉴스 생성 실패: {str(e)}"
        )

@app.delete("/api/test/cleanup", response_model=StandardResponse)
async def cleanup_test_data(
    firestore_svc = Depends(get_firestore_service)
):
    """테스트 데이터 정리"""
    try:
        # 테스트 뉴스만 삭제 (제목에 "테스트"가 포함된 뉴스)
        all_news = await firestore_svc.get_all_news(limit=1000)
        test_news = [news for news in all_news if "테스트" in news.get("title", "")]
        
        deleted_count = 0
        for news in test_news:
            if await firestore_svc.delete_news(news["id"]):
                deleted_count += 1
        
        return StandardResponse(
            success=True,
            message=f"{deleted_count}개 테스트 뉴스가 삭제되었습니다",
            data={"deleted_count": deleted_count}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"테스트 데이터 정리 실패: {str(e)}"
        )

# @app.post("/api/test/sample-data", response_model=StandardResponse)
# async def create_sample_data(
#     count: int = Query(5, ge=1, le=20, description="생성할 샘플 뉴스 개수"),
#     firestore_svc = Depends(get_firestore_service)
# ):
#     """샘플 데이터 생성"""
#     try:
#         categories = ['정치', '경제', '사회', '문화', '스포츠', '국제', '과학']
#         sample_titles = [
#             "국회에서 새로운 법안 통과",
#             "경제 성장률 전년 대비 상승",
#             "사회 복지 제도 개선 방안 발표",
#             "문화예술 지원 사업 확대",
#             "스포츠 선수 국제대회 우수 성적",
#             "국제 외교 관계 강화 협의",
#             "과학기술 발전 새로운 전환점"
#         ]
        
#         created_news = []
#         for i in range(count):
#             category = categories[i % len(categories)]
#             title = f"{sample_titles[i % len(sample_titles)]} - 샘플 {i+1}"
            
#             news_data = {
#                 "title": title,
#                 "content": f"{category} 분야의 중요한 소식을 전해드립니다. 이것은 시스템 테스트를 위한 샘플 뉴스 데이터입니다. 실제 뉴스 내용과 동일한 형식으로 구성되어 있어 시스템 기능 테스트에 활용할 수 있습니다.",
#                 "category": category,
#                 "url": f"https://www.ytn.co.kr/news/sample_{i+1}",
#                 "published_date": datetime.now().isoformat(),
#                 "posted_to_blog": i % 3 == 0,  # 3개 중 1개는 포스팅됨으로 설정
#                 "blog_url": f"https://blog.naver.com/sample_post_{i+1}" if i % 3 == 0 else ""
#             }
            
#             news_id = await firestore_svc.create_news(news_data)
#             news_data['id'] = news_id
#             created_news.append(news_data)
        
#         return StandardResponse(
#             success=True,
#             message=f"{len(created_news)}개 샘플 뉴스가 생성되었습니다",
#             data={
#                 "created_count": len(created_news),
#                 "sample_news": created_news
#             }
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"샘플 데이터 생성 실패: {str(e)}"
#         )

# ========== 에러 핸들러 ==========

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 예외 처리"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "error": {
                "type": "HTTPException",
                "status_code": exc.status_code,
                "detail": exc.detail
            },
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M')
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """일반 예외 처리"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "내부 서버 오류가 발생했습니다",
            "error": {
                "type": type(exc).__name__,
                "details": str(exc)
            },
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M')
        }
    )

# ========== 개발 환경에서만 실행 ==========

if __name__ == "__main__":
    import uvicorn
    
    # 환경 변수에서 설정 읽기
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("ENVIRONMENT", "development") == "development"
    
    print("=" * 70)
    print("🚀 YTN 뉴스 자동화 시스템 API 서버")
    print("=" * 70)
    print(f"📍 서버 주소: http://{host}:{port}")
    print(f"📚 API 문서: http://{host}:{port}/docs")
    print(f"🔍 ReDoc: http://{host}:{port}/redoc")
    print(f"🏥 헬스체크: http://{host}:{port}/health")
    print(f"📊 시스템 정보: http://{host}:{port}/status")
    print(f"ℹ️ API 정보: http://{host}:{port}/api/info")
    print("=" * 70)
    print("🏢 생성형 AI 기반 업무 자동화 솔루션")
    print("💡 Mock 서비스 모드로 실행 중 (실제 Firebase 연동 시 정상 동작)")
    print("=" * 70)
    
    # 서버 실행
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,  # 개발 환경에서만 True
        log_level="info"
    )