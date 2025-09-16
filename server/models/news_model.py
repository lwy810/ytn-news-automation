"""
뉴스 데이터 모델
Pydantic을 사용한 데이터 검증 및 직렬화
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl, EmailStr, validator

class NewsBase(BaseModel):
    """뉴스 기본 모델"""
    title: str = Field(..., min_length=5, max_length=500, description="뉴스 제목")
    content: str = Field(..., min_length=10, max_length=10000, description="뉴스 내용")
    category: str = Field(default="기타", max_length=50, description="뉴스 카테고리")
    url: Optional[HttpUrl] = Field(None, description="원본 뉴스 URL")
    
    @validator('category')
    def validate_category(cls, v):
        """카테고리 검증"""
        allowed_categories = [
            '정치', '경제', '사회', '문화', '스포츠', 
            '국제', '과학', '환경', '교육', '기타'
        ]
        if v not in allowed_categories:
            return '기타'
        return v
    
    @validator('title', 'content')
    def validate_not_empty(cls, v):
        """빈 문자열 검증"""
        if not v or not v.strip():
            raise ValueError('필수 필드는 비어있을 수 없습니다')
        return v.strip()

class NewsCreate(NewsBase):
    """뉴스 생성 모델"""
    published_date: Optional[datetime] = Field(default_factory=datetime.now, description="발행일")
    posted_to_blog: bool = Field(default=False, description="블로그 포스팅 여부")
    blog_url: Optional[HttpUrl] = Field(None, description="블로그 포스트 URL")
    
    class Config:
        schema_extra = {
            "example": {
                "title": "YTN 뉴스 - 경제 성장률 전망 발표",
                "content": "정부가 올해 경제 성장률 전망을 상향 조정했다고 발표했습니다...",
                "category": "경제",
                "url": "https://www.ytn.co.kr/news/example",
                "published_date": "2024-01-15T10:30:00",
                "posted_to_blog": False,
                "blog_url": None
            }
        }

class NewsUpdate(BaseModel):
    """뉴스 업데이트 모델"""
    title: Optional[str] = Field(None, min_length=5, max_length=500, description="뉴스 제목")
    content: Optional[str] = Field(None, min_length=10, max_length=10000, description="뉴스 내용")
    category: Optional[str] = Field(None, max_length=50, description="뉴스 카테고리")
    url: Optional[HttpUrl] = Field(None, description="원본 뉴스 URL")
    published_date: Optional[datetime] = Field(None, description="발행일")
    posted_to_blog: Optional[bool] = Field(None, description="블로그 포스팅 여부")
    blog_url: Optional[HttpUrl] = Field(None, description="블로그 포스트 URL")
    
    @validator('category')
    def validate_category(cls, v):
        """카테고리 검증"""
        if v is None:
            return v
        allowed_categories = [
            '정치', '경제', '사회', '문화', '스포츠', 
            '국제', '과학', '환경', '교육', '기타'
        ]
        if v not in allowed_categories:
            return '기타'
        return v

class NewsResponse(NewsBase):
    """뉴스 응답 모델"""
    id: str = Field(..., description="뉴스 ID")
    published_date: datetime = Field(..., description="발행일")
    posted_to_blog: bool = Field(default=False, description="블로그 포스팅 여부")
    blog_url: Optional[HttpUrl] = Field(None, description="블로그 포스트 URL")
    created_at: Optional[datetime] = Field(None, description="생성일")
    updated_at: Optional[datetime] = Field(None, description="수정일")
    posted_at: Optional[datetime] = Field(None, description="포스팅일")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "abc123def456",
                "title": "YTN 뉴스 - 경제 성장률 전망 발표",
                "content": "정부가 올해 경제 성장률 전망을 상향 조정했다고 발표했습니다...",
                "category": "경제",
                "url": "https://www.ytn.co.kr/news/example",
                "published_date": "2024-01-15T10:30:00",
                "posted_to_blog": True,
                "blog_url": "https://blog.naver.com/ytn_auto/post_123",
                "created_at": "2024-01-15T09:00:00",
                "updated_at": "2024-01-15T11:00:00",
                "posted_at": "2024-01-15T11:30:00"
            }
        }

class NewsModel(NewsResponse):
    """완전한 뉴스 모델 (내부 사용)"""
    pass

# class NewsBulkCreate(BaseModel):
#     """뉴스 일괄 생성 모델"""
#     news_list: list[NewsCreate] = Field(..., min_items=1, max_items=50, description="뉴스 목록")
    
#     class Config:
#         schema_extra = {
#             "example": {
#                 "news_list": [
#                     {
#                         "title": "YTN 뉴스 1",
#                         "content": "첫 번째 뉴스 내용...",
#                         "category": "정치"
#                     },
#                     {
#                         "title": "YTN 뉴스 2", 
#                         "content": "두 번째 뉴스 내용...",
#                         "category": "경제"
#                     }
#                 ]
#             }
#         }

# class NewsBulkUpdate(BaseModel):
#     """뉴스 일괄 업데이트 모델"""
#     updates: list[dict] = Field(..., min_items=1, max_items=50, description="업데이트 목록")
    
#     class Config:
#         schema_extra = {
#             "example": {
#                 "updates": [
#                     {
#                         "id": "abc123",
#                         "data": {
#                             "posted_to_blog": True,
#                             "blog_url": "https://blog.naver.com/post_1"
#                         }
#                     },
#                     {
#                         "id": "def456",
#                         "data": {
#                             "category": "경제"
#                         }
#                     }
#                 ]
#             }
#         }

class NewsSearchQuery(BaseModel):
    """뉴스 검색 쿼리 모델"""
    query: str = Field(..., min_length=1, max_length=100, description="검색어")
    category: Optional[str] = Field(None, description="카테고리 필터")
    posted_only: Optional[bool] = Field(None, description="포스팅된 뉴스만 검색")
    start_date: Optional[datetime] = Field(None, description="시작 날짜")
    end_date: Optional[datetime] = Field(None, description="종료 날짜")
    limit: int = Field(default=50, ge=1, le=200, description="결과 개수 제한")
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        """날짜 범위 검증"""
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('종료 날짜는 시작 날짜보다 늦어야 합니다')
        return v

class NewsStatistics(BaseModel):
    """뉴스 통계 모델"""
    total_news: int = Field(..., description="전체 뉴스 수")
    posted_news: int = Field(..., description="포스팅된 뉴스 수")
    unposted_news: int = Field(..., description="미포스팅 뉴스 수")
    categories: dict[str, int] = Field(..., description="카테고리별 뉴스 수")
    daily_stats: dict[str, int] = Field(default={}, description="일별 통계")
    recent_activity: dict[str, int] = Field(default={}, description="최근 활동 통계")
    
    class Config:
        schema_extra = {
            "example": {
                "total_news": 150,
                "posted_news": 45,
                "unposted_news": 105,
                "categories": {
                    "정치": 25,
                    "경제": 30,
                    "사회": 35,
                    "문화": 20,
                    "스포츠": 15,
                    "국제": 25
                },
                "daily_stats": {
                    "2024-01-15": 10,
                    "2024-01-14": 8,
                    "2024-01-13": 12
                },
                "recent_activity": {
                    "created_today": 10,
                    "posted_today": 3,
                    "created_this_week": 45,
                    "posted_this_week": 15
                }
            }
        }