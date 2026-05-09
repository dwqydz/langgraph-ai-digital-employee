"""
会议室智能助手 - MeetingAgent
负责解析自然语言指令,实现智能预订和取消功能
"""
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from langchain_core.prompts import PromptTemplate
from sqlalchemy.ext.asyncio import AsyncSession
from agent.llm import get_qwen_llm
from agent.prompt_loader import get_prompt_manager
from crud import meeting_crud


class MeetingAgent:
    """会议室智能助手"""
    
    def __init__(self):
        self.llm = get_qwen_llm()
        self.prompt_template = self._load_prompt()
    
    def _load_prompt(self) -> PromptTemplate:
        """加载Prompt模板"""
        prompt_manager = get_prompt_manager()
        prompt_text = prompt_manager.get_meeting_agent_prompt()
        prompt_text = prompt_text.replace('{user_input}', '{{ user_input }}')
        prompt_text = prompt_text.replace('{{', '【').replace('}}', '】')
        
        return PromptTemplate.from_template(prompt_text, template_format="jinja2")
    
    async def parse_command(self, user_input: str) -> Dict:
        """
        解析用户自然语言指令
        
        Args:
            user_input: 用户输入的自然语言
            
        Returns:
            解析结果字典
        """
        try:
            # 构建完整prompt
            prompt = self.prompt_template.format(user_input=user_input)
            
            # 调用LLM (注意: invoke是同步方法,不需要await)
            response = self.llm.invoke(prompt)
            
            # 获取响应内容
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            # 解析JSON响应
            result = self._parse_json_response(response_text)
            
            return result
            
        except Exception as e:
            print(f"[MeetingAgent] 解析失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "intent": "unknown",
                "action_type": "unknown",
                "booking_info": None,
                "cancel_info": None,
                "confidence": 0.0,
                "explanation": f"解析失败: {str(e)}"
            }
    
    def _parse_json_response(self, response: str) -> Dict:
        """解析LLM返回的JSON字符串"""
        import json
        
        # 尝试直接解析
        try:
            # 提取JSON部分(可能包含在markdown代码块中)
            json_str = response.strip()
            
            # 移除markdown代码块标记
            if '```json' in json_str:
                json_str = json_str.split('```json')[1].split('```')[0].strip()
            elif '```' in json_str:
                json_str = json_str.split('```')[1].split('```')[0].strip()
            
            result = json.loads(json_str)
            return result
        except Exception as e:
            raise ValueError(f"JSON解析失败: {str(e)}, 原始响应: {response}")
    
    def filter_rooms_by_requirements(
        self, 
        rooms: List[Dict], 
        requirements: Dict,
        weight_config: Dict = None
    ) -> List[Dict]:
        """
        根据需求和动态权重筛选会议室
        
        Args:
            rooms: 候选会议室列表(已通过SQL粗筛)
            requirements: 用户需求
            weight_config: LLM生成的动态权重配置
            
        Returns:
            匹配的会议室列表(按匹配度排序)
        """
        if not requirements:
            return rooms[:5]  # 默认返回前5个
        
        # 默认权重配置
        default_weights = {
            "capacity_weight": 30,
            "equipment_weight": 25,
            "floor_weight": 15,
            "building_weight": 10,
            "lighting_weight": 15,
            "room_type_weight": 5
        }
        weights = weight_config or default_weights
        
        capacity = requirements.get("capacity", 5)
        scored_rooms = []
        
        for room in rooms:
            score = 0
            max_score = sum(weights.values())
            
            # 1. 容量匹配 (使用动态权重)
            if weights.get("capacity_weight", 0) > 0 and capacity:
                if room["capacity"] <= capacity * 1.5:
                    score += weights["capacity_weight"]
                else:
                    score += weights["capacity_weight"] * 0.5
            
            # 2. 设备匹配 (使用动态权重)
            required_equipment = requirements.get("equipment", [])
            if weights.get("equipment_weight", 0) > 0 and required_equipment:
                room_equipment = room.get("equipment", [])
                matched_count = sum(1 for eq in required_equipment if eq in room_equipment)
                score += weights["equipment_weight"] * (matched_count / len(required_equipment))
            
            # 3. 楼层匹配 (使用动态权重)
            preferred_floor = requirements.get("floor")
            if weights.get("floor_weight", 0) > 0 and preferred_floor:
                if room.get("floor") == preferred_floor:
                    score += weights["floor_weight"]
            
            # 4. 楼栋匹配 (使用动态权重)
            preferred_building = requirements.get("building")
            if weights.get("building_weight", 0) > 0 and preferred_building:
                if preferred_building in room.get("building", ""):
                    score += weights["building_weight"]
            
            # 5. 采光匹配 (使用动态权重)
            if weights.get("lighting_weight", 0) > 0 and requirements.get("prefer_lighting", False):
                if room.get("lighting") == "good":
                    score += weights["lighting_weight"]
                elif room.get("has_window") == True:
                    score += weights["lighting_weight"] * 0.8
                elif room.get("lighting") == "normal":
                    score += weights["lighting_weight"] * 0.3
            
            # 计算匹配度百分比
            match_rate = (score / max_score * 100) if max_score > 0 else 50
            
            scored_rooms.append({
                **room,
                "match_score": round(match_rate, 2),
                "match_explanation": self._generate_match_explanation(room, requirements, score, max_score)
            })
        
        # 按匹配度降序排序
        scored_rooms.sort(key=lambda x: x["match_score"], reverse=True)
        
        # 返回所有符合条件的会议室,最多10个
        return scored_rooms[:10]
    
    def _generate_match_explanation(
        self, 
        room: Dict, 
        requirements: Dict, 
        score: float, 
        max_score: float
    ) -> str:
        """生成匹配说明"""
        explanations = []
        
        # 容量说明(必显示)
        capacity = requirements.get("capacity", 5)
        if capacity:
            if room.get("capacity", 0) >= capacity:
                explanations.append(f"✓ 容量{room['capacity']}人,满足{capacity}人需求")
        
        # 设备匹配
        required_equipment = requirements.get("equipment", [])
        if required_equipment:
            room_equipment = room.get("equipment", [])
            matched = [eq for eq in required_equipment if eq in room_equipment]
            if matched:
                explanations.append(f"✓ 设备匹配: {', '.join(matched)}")
            else:
                explanations.append(f"✗ 缺少设备: {', '.join(required_equipment)}")
        
        # 楼层匹配
        preferred_floor = requirements.get("floor")
        if preferred_floor:
            if room.get("floor") == preferred_floor:
                explanations.append(f"✓ 楼层匹配: {preferred_floor}楼")
            else:
                explanations.append(f"✗ 楼层不匹配: 需要{preferred_floor}楼,实际{room.get('floor')}楼")
        
        # 楼栋匹配
        preferred_building = requirements.get("building")
        if preferred_building:
            if preferred_building in room.get("building", ""):
                explanations.append(f"✓ 楼栋匹配: {room.get('building')}")
            else:
                explanations.append(f"✗ 楼栋不匹配: 需要{preferred_building},实际{room.get('building')}")
        
        # 采光匹配 - 使用prefer_lighting字段
        if requirements.get("prefer_lighting", False):
            if room.get("lighting") == "good":
                explanations.append("✓ 采光良好")
            elif room.get("has_window") == True:
                explanations.append("✓ 有窗户")
            else:
                explanations.append("✗ 采光一般")
        
        return "; ".join(explanations) if explanations else "基本匹配"
    
    async def process(self, message: str, db: AsyncSession, user_id: int) -> Dict:
        """
        处理会议室相关指令 - LangGraph工作流调用入口
        
        Args:
            message: 用户自然语言输入
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            {
                "success": True/False,
                "message": "执行结果消息",
                "intent": "book/cancel/complete",
                "action_type": "book/cancel/complete",
                "recommended_rooms": [...],  # 仅预订意图
                "matched_bookings": [...]     # 仅取消/完成意图
            }
        """
        try:
            print(f"[MeetingAgent] 开始处理: {message}")
            
            # 1. 解析用户指令
            parse_result = await self.parse_command(message)
            
            intent = parse_result.get("intent", "unknown")
            action_type = parse_result.get("action_type", "unknown")
            confidence = parse_result.get("confidence", 0.0)
            explanation = parse_result.get("explanation", "")
            
            print(f"[MeetingAgent] 解析结果: intent={intent}, confidence={confidence}")
            
            # 置信度过低
            if confidence < 0.6:
                return {
                    "success": False,
                    "message": f"无法理解您的指令: {explanation}",
                    "intent": intent,
                    "action_type": action_type,
                    "recommended_rooms": [],
                    "matched_bookings": []
                }
            
            # 2. 根据意图执行不同操作
            if intent == "book":
                # 预订会议室
                result = await self._handle_booking_intent(db, parse_result, user_id)
                
            elif intent in ["cancel", "complete"]:
                # 取消或完成预约
                result = await self._handle_cancel_complete_intent(db, parse_result, user_id, intent)
                
            else:
                result = {
                    "success": False,
                    "message": f"不支持的意图: {intent}",
                    "intent": intent,
                    "action_type": action_type,
                    "recommended_rooms": [],
                    "matched_bookings": []
                }
            
            print(f"[MeetingAgent] 处理完成: {result.get('message', '')}")
            return result
            
        except Exception as e:
            print(f"[MeetingAgent] 处理失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"会议室指令处理失败: {str(e)}",
                "intent": "error",
                "action_type": "error",
                "recommended_rooms": [],
                "matched_bookings": []
            }
    
    async def _handle_booking_intent(
        self,
        db: AsyncSession,
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
                "success": False,
                "message": "未能提取到预订信息",
                "intent": "book",
                "action_type": "book",
                "recommended_rooms": [],
                "matched_bookings": []
            }
        
        # 1. 获取候选会议室(使用SQL动态粗筛)
        filter_params = parse_result.get("filter_params", {})
        all_rooms = await meeting_crud.get_filtered_rooms(db, filter_params)
        
        print(f"[MeetingAgent] SQL粗筛后剩余: {len(all_rooms)}个会议室")
        
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
        
        # 2. 使用动态权重进行内存精算
        weight_config = parse_result.get("weight_config")
        
        # ✅ 新增：时间冲突预检测
        suggested_time = self._generate_suggested_time(booking_info)
        start_dt = datetime.fromisoformat(suggested_time["start_time"])
        end_dt = datetime.fromisoformat(suggested_time["end_time"])
        
        available_rooms_dict = []
        for room in rooms_dict:
            # 检查该房间在指定时间段是否有冲突
            conflict = await meeting_crud.check_time_conflict(db, room["id"], start_dt, end_dt)
            if not conflict:
                available_rooms_dict.append(room)
        
        print(f"[MeetingAgent] 时间冲突过滤后剩余: {len(available_rooms_dict)}个可用会议室")
        
        if not available_rooms_dict:
            return {
                "success": False,
                "message": f"抱歉，在 {suggested_time['display']} 时段没有符合条件的空闲会议室",
                "intent": "book",
                "action_type": "book",
                "recommended_rooms": [],
                "matched_bookings": []
            }

        recommended_rooms = self.filter_rooms_by_requirements(
            available_rooms_dict, booking_info, weight_config
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
                "suggested_time": self._generate_suggested_time(booking_info)
            })
        
        return {
            "success": True,
            "message": f"为您找到{len(formatted_rooms)}个匹配的会议室",
            "intent": "book",
            "action_type": "book",
            "recommended_rooms": formatted_rooms,
            "matched_bookings": []
        }
    
    async def _handle_cancel_complete_intent(
        self,
        db: AsyncSession,
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
        
        print(f"[MeetingAgent] cancel_info: {cancel_info}")
        
        if not cancel_info:
            return {
                "success": False,
                "message": "未能提取到取消信息",
                "intent": intent,
                "action_type": intent,
                "recommended_rooms": [],
                "matched_bookings": []
            }
        
        # 1. 获取用户的所有预约记录
        bookings_with_rooms, total = await meeting_crud.get_rooms_with_bookings(
            db, user_id, page=1, page_size=100
        )
        
        print(f"[MeetingAgent] 查询到 {len(bookings_with_rooms)} 条预约记录")
        
        # 2. 匹配符合条件的预约
        matched_bookings = []
        for item in bookings_with_rooms:
            booking = item["booking"]
            room = item["room"]
            
            print(f"[MeetingAgent] 检查预约: booking_id={booking.id}, status={booking.status}, room_name={room.name if room else 'None'}")
            
            # 只处理confirmed状态的预约
            if booking.status != "confirmed":
                print(f"[MeetingAgent]   跳过: status不是confirmed")
                continue
            
            # 匹配条件
            is_match = True
            
            # 匹配会议室名称
            room_name = cancel_info.get("room_name")
            print(f"[MeetingAgent]   检查会议室名称: cancel_info.room_name={room_name}, room.name={room.name if room else 'None'}")
            if room_name and room_name != "null":
                # 使用包含匹配,而不是严格相等
                if room and room_name.lower() not in room.name.lower():
                    is_match = False
                    print(f"[MeetingAgent]   不匹配: '{room_name}' not in '{room.name}'")
            
            # 匹配日期
            cancel_date = cancel_info.get("date")
            print(f"[MeetingAgent]   检查日期: cancel_info.date={cancel_date}")
            if cancel_date and cancel_date != "null":
                booking_date = booking.start_time.strftime("%Y-%m-%d")
                print(f"[MeetingAgent]   booking_date={booking_date}")
                # 支持多种日期格式匹配
                if cancel_date not in booking_date:
                    # 尝试解析"明天"等相对日期
                    if cancel_date == "明天":
                        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                        if tomorrow != booking_date:
                            is_match = False
                            print(f"[MeetingAgent]   不匹配: 明天({tomorrow}) != {booking_date}")
                    else:
                        is_match = False
                        print(f"[MeetingAgent]   不匹配: '{cancel_date}' not in '{booking_date}'")
            
            if is_match:
                print(f"[MeetingAgent]   ✓ 匹配成功!")
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
            else:
                print(f"[MeetingAgent]   ✗ 不匹配")
        
        action_text = "取消" if intent == "cancel" else "完成"
        print(f"[MeetingAgent] 最终匹配结果: {len(matched_bookings)} 个")
        
        return {
            "success": True,
            "message": f"找到{len(matched_bookings)}个待{action_text}的预约",
            "intent": intent,
            "action_type": intent,
            "recommended_rooms": [],
            "matched_bookings": matched_bookings
        }
    
    def _generate_suggested_time(self, booking_info: Dict) -> Dict:
        """生成建议的时间段"""
        
        date_str = booking_info.get("date")
        time_str = booking_info.get("time", "15:00")
        duration = booking_info.get("duration", 1)
        
        # 如果没有指定日期,默认为明天
        if not date_str or date_str == "null":
            tomorrow = datetime.now() + timedelta(days=1)
            date_str = tomorrow.strftime("%Y-%m-%d")
        
        # 解析时间
        try:
            hour, minute = map(int, time_str.split(":"))
        except:
            hour, minute = 15, 0
        
        # 计算开始和结束时间
        start_dt = datetime.strptime(f"{date_str} {hour:02d}:{minute:02d}", "%Y-%m-%d %H:%M")
        end_dt = start_dt + timedelta(hours=duration)
        
        return {
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "display": f"{date_str} {start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')}"
        }


# 全局实例
meeting_agent = MeetingAgent()


def get_meeting_agent():
    """
    获取MeetingAgent实例(用于LangGraph工作流)
    
    TODO: 实现完整的LangGraph MeetingAgent
    目前返回一个简化版本
    """
    return meeting_agent
