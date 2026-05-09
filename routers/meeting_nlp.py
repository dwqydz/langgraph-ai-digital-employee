"""
会议室NLP智能处理路由
实现自然语言预订和取消功能
"""
from fastapi import APIRouter, HTTPException, Depends
import datetime
from typing import Dict, List

# 导入Pydantic模式
from schemas.meeting_schemas import (
    NLPBookingRequest, NLPCommandResponse,
    MeetingRoom as MeetingRoomSchema,
    BookingItem, CancelBookingData, CancelBookingResponse
)

# 导入数据库配置
from config.db_config import get_database

# 导入CRUD操作
from crud import meeting_crud

# 导入Session Token认证
from utils.session_auth import get_current_user_id_from_session

# 导入MeetingAgent
from agent.meeting_agent import meeting_agent

router = APIRouter(
    prefix="/meeting",
    tags=["会议室NLP模块"]
)


@router.post("/nlp-command", response_model=NLPCommandResponse)
async def nlp_command_handler(
    request: NLPBookingRequest,
    db = Depends(get_database),
    current_user_id: int = Depends(get_current_user_id_from_session)
):
    """
    NLP智能命令处理 - 支持预订和取消
    
    流程:
    1. Agent解析用户指令
    2. 根据意图执行相应操作:
       - book: 筛选推荐会议室
       - cancel/complete: 查找匹配的预约记录
    3. 返回结果给前端
    """
    try:
        user_input = request.text
        
        # 1. 使用Agent解析用户指令
        parse_result = await meeting_agent.parse_command(user_input)
        
        intent = parse_result.get("intent", "unknown")
        action_type = parse_result.get("action_type", "unknown")
        confidence = parse_result.get("confidence", 0.0)
        explanation = parse_result.get("explanation", "")
        
        # 置信度过低,返回错误
        if confidence < 0.6:
            return NLPCommandResponse(
                code=400,
                message=f"无法理解您的指令: {explanation}",
                data={
                    "intent": "unknown",
                    "action_type": "unknown",
                    "booking_info": None,
                    "cancel_info": None,
                    "confidence": confidence,
                    "explanation": explanation,
                    "recommended_rooms": []
                }
            )
        
        # 2. 根据意图执行不同操作
        if intent == "book":
            # 预订会议室
            result = await handle_booking_intent(
                db, parse_result, current_user_id
            )
            
        elif intent in ["cancel", "complete"]:
            # 取消或完成预约
            result = await handle_cancel_complete_intent(
                db, parse_result, current_user_id, intent
            )
            
        else:
            result = {
                "intent": intent,
                "action_type": action_type,
                "booking_info": None,
                "cancel_info": None,
                "confidence": confidence,
                "explanation": f"不支持的意图: {intent}",
                "recommended_rooms": []
            }
        
        return NLPCommandResponse(
            code=200,
            message="解析成功",
            data=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NLP处理失败: {str(e)}")


async def handle_booking_intent(
    db, 
    parse_result: Dict, 
    user_id: int
) -> Dict:
    """
    处理预订意图
    
    1. 提取用户需求
    2. 查询所有可申请的会议室
    3. 根据需求筛选匹配度高的会议室
    4. 返回推荐列表
    """
    booking_info = parse_result.get("booking_info", {})
    
    if not booking_info:
        return {
            **parse_result,
            "recommended_rooms": [],
            "explanation": "未能提取到预订信息"
        }
    
    # 1. 获取所有可申请的会议室(不分页,获取全部)
    all_rooms, total = await meeting_crud.get_available_rooms(db, page=1, page_size=1000)
    
    # 转换为字典格式
    rooms_dict = []
    for room in all_rooms:
        rooms_dict.append({
            "id": room.id,
            "name": room.name,
            "location": room.location,
            "capacity": room.capacity,
            "floor": room.floor,
            "building": room.building,
            "equipment": room.equipment or [],
            "status": room.status,
            "description": room.description,
            "lighting": room.lighting,
            "has_window": room.has_window,
            "environment": room.environment
        })
    
    # 2. 使用Agent筛选匹配的会议室
    recommended_rooms = meeting_agent.filter_rooms_by_requirements(
        rooms_dict, booking_info
    )
    
    # 3. 格式化推荐结果
    formatted_rooms = []
    for room in recommended_rooms:
        formatted_rooms.append({
            "id": room["id"],
            "name": room["name"],
            "location": room["location"],
            "capacity": room["capacity"],
            "floor": room["floor"],
            "building": room["building"],
            "equipment": room["equipment"],
            "match_score": room["match_score"],
            "match_explanation": room.get("match_explanation", ""),
            "suggested_time": generate_suggested_time(booking_info)
        })
    
    return {
        **parse_result,
        "recommended_rooms": formatted_rooms,
        "explanation": f"为您找到{len(formatted_rooms)}个匹配的会议室"
    }


async def handle_cancel_complete_intent(
    db,
    parse_result: Dict,
    user_id: int,
    intent: str
) -> Dict:
    """
    处理取消/完成意图
    
    1. 提取取消信息
    2. 查询用户的预约记录
    3. 匹配符合条件的预约
    4. 返回待确认的预约列表
    """
    cancel_info = parse_result.get("cancel_info", {})
    
    if not cancel_info:
        return {
            **parse_result,
            "explanation": "未能提取到取消信息"
        }
    
    # 1. 获取用户的所有预约记录
    bookings_with_rooms, total = await meeting_crud.get_rooms_with_bookings(
        db, user_id, page=1, page_size=100
    )
    
    # 2. 匹配符合条件的预约
    matched_bookings = []
    for item in bookings_with_rooms:
        booking = item["booking"]
        room = item["room"]
        
        # 只处理confirmed状态的预约
        if booking.status != "confirmed":
            continue
        
        # 匹配条件
        is_match = True
        
        # 匹配会议室名称
        room_name = cancel_info.get("room_name")
        if room_name and room_name not in (room.name if room else ""):
            is_match = False
        
        # 匹配日期
        cancel_date = cancel_info.get("date")
        if cancel_date and cancel_date != "null":
            booking_date = booking.start_time.strftime("%Y-%m-%d")
            if cancel_date not in booking_date:
                is_match = False
        
        if is_match:
            matched_bookings.append({
                "booking_id": booking.id,
                "room_id": booking.room_id,
                "room_name": room.name if room else "未知会议室",
                "start_time": booking.start_time.isoformat(),
                "end_time": booking.end_time.isoformat(),
                "date": booking.start_time.strftime("%Y-%m-%d"),
                "time_slot": f"{booking.start_time.strftime('%H:%M')}-{booking.end_time.strftime('%H:%M')}",
                "status": "已申请",
                "action": intent  # cancel 或 complete
            })
    
    return {
        **parse_result,
        "matched_bookings": matched_bookings,
        "explanation": f"找到{len(matched_bookings)}个待{ '取消' if intent == 'cancel' else '完成' }的预约"
    }


def generate_suggested_time(booking_info: Dict) -> Dict:
    """生成建议的时间段"""
    date_str = booking_info.get("date")
    time_str = booking_info.get("time", "15:00")
    duration = booking_info.get("duration", 1)
    
    # 如果没有指定日期,默认为明天
    if not date_str or date_str == "null":
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        date_str = tomorrow.strftime("%Y-%m-%d")
    
    # 解析时间
    try:
        hour, minute = map(int, time_str.split(":"))
    except:
        hour, minute = 15, 0
    
    # 计算开始和结束时间
    start_dt = datetime.datetime.strptime(f"{date_str} {hour:02d}:{minute:02d}", "%Y-%m-%d %H:%M")
    end_dt = start_dt + datetime.timedelta(hours=duration)
    
    return {
        "start_time": start_dt.isoformat(),
        "end_time": end_dt.isoformat(),
        "display": f"{date_str} {start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')}"
    }
