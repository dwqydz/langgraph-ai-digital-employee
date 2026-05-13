"""
通用响应模型
定义统一的API响应格式
"""
from typing import Generic, TypeVar, Optional, Any, List
from pydantic import BaseModel

# 泛型类型变量
T = TypeVar('T')


class BaseResponse(BaseModel):
    """基础响应模型"""
    code: int = 200
    message: str = "success"


class ApiResponse(BaseResponse, Generic[T]):
    """通用API响应模型(带数据)"""
    data: Optional[T] = None


class MessageResponse(BaseResponse):
    """仅消息响应模型(无数据)"""
    data: Optional[Any] = None


class ErrorResponse(BaseResponse):
    """错误响应模型"""
    code: int = 400
    message: str = "error"
    data: Optional[Any] = None


class ListResponse(BaseResponse, Generic[T]):
    """列表响应模型"""
    data: List[T] = []


class PageData(BaseModel, Generic[T]):
    """分页数据结构"""
    total: int = 0
    page: int = 1
    page_size: int = 10
    items: List[T] = []


class PageResponse(BaseResponse, Generic[T]):
    """分页响应模型"""
    data: Optional[PageData[T]] = None
