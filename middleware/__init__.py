"""
中间件模块
提供请求日志、异常处理等中间件功能
"""
import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# 配置日志
logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件
    记录每个请求的详细信息，包括：
    - 请求方法、路径
    - 请求耗时
    - 响应状态码
    - 用户ID（如果已认证）
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并记录日志"""
        start_time = time.time()
        
        # 获取请求信息
        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else "unknown"
        
        # 尝试从请求头获取用户ID（用于审计）
        user_id = None
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            # 这里可以添加Token解析逻辑来获取user_id
            # 暂时标记为authenticated
            user_id = "authenticated"
        
        try:
            # 执行请求
            response = await call_next(request)
            
            # 计算耗时
            process_time = time.time() - start_time
            
            # 记录成功请求日志
            logger.info(
                f"[REQUEST] {method} {path} | "
                f"status={response.status_code} | "
                f"time={process_time:.3f}s | "
                f"client={client_host} | "
                f"user={user_id or 'anonymous'}"
            )
            
            # 添加响应头 - 请求处理时间
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # 计算耗时
            process_time = time.time() - start_time
            
            # 记录错误日志
            logger.error(
                f"[ERROR] {method} {path} | "
                f"time={process_time:.3f}s | "
                f"client={client_host} | "
                f"user={user_id or 'anonymous'} | "
                f"error={str(e)}",
                exc_info=True
            )
            
            # 返回统一的错误响应
            return JSONResponse(
                status_code=500,
                content={
                    "code": 500,
                    "message": "服务器内部错误",
                    "data": None
                }
            )


class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    """
    全局异常处理中间件
    捕获未处理的异常并返回统一格式的错误响应
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并捕获异常"""
        try:
            return await call_next(request)
        except Exception as e:
            # 记录详细的异常信息
            logger.error(
                f"[UNHANDLED_EXCEPTION] {request.method} {request.url.path} | "
                f"error_type={type(e).__name__} | "
                f"error_message={str(e)}",
                exc_info=True
            )
            
            # 返回统一的错误响应
            return JSONResponse(
                status_code=500,
                content={
                    "code": 500,
                    "message": f"服务器内部错误: {str(e)}",
                    "data": None
                }
            )


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    审计日志中间件
    记录关键操作的审计信息，用于安全审计和链路追踪
    """
    
    # 需要审计的操作路径前缀
    AUDIT_PATHS = [
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/logout",
        "/api/todo/",
        "/api/meeting/",
    ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并记录审计日志"""
        path = request.url.path
        
        # 检查是否需要审计
        needs_audit = any(path.startswith(audit_path) for audit_path in self.AUDIT_PATHS)
        
        if needs_audit:
            start_time = time.time()
            
            # 获取请求信息
            method = request.method
            client_host = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("User-Agent", "")
            
            # 尝试获取用户ID
            user_id = "anonymous"
            authorization = request.headers.get("Authorization")
            if authorization and authorization.startswith("Bearer "):
                user_id = "authenticated"
            
            try:
                # 执行请求
                response = await call_next(request)
                
                # 计算耗时
                process_time = time.time() - start_time
                
                # 记录审计日志
                logger.warning(
                    f"[AUDIT] action={method} {path} | "
                    f"user={user_id} | "
                    f"ip={client_host} | "
                    f"status={response.status_code} | "
                    f"time={process_time:.3f}s | "
                    f"ua={user_agent[:100]}"
                )
                
                return response
                
            except Exception as e:
                # 计算耗时
                process_time = time.time() - start_time
                
                # 记录失败的审计日志
                logger.error(
                    f"[AUDIT_FAIL] action={method} {path} | "
                    f"user={user_id} | "
                    f"ip={client_host} | "
                    f"error={str(e)} | "
                    f"time={process_time:.3f}s",
                    exc_info=True
                )
                
                raise
        else:
            # 不需要审计的路径，直接执行
            return await call_next(request)
