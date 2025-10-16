"""
AI Chatbot Service for Laptop Recommender
Enhanced with conversation memory, intent recognition, smart context, and security
"""

import re
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from models import Laptop, db
import anthropic

class SecurityFilter:
    """
    Security filter to prevent disclosure of sensitive information
    Blocks queries about passwords, personal data, and security vulnerabilities
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Sensitive topics that should be blocked
        self.blocked_patterns = {
            'password': [
                r'password|mật khẩu|pass|pwd',
                r'login.*credential|thông tin.*đăng nhập',
                r'authentication.*secret|bí mật.*xác thực'
            ],
            'personal_info': [
                r'personal.*information|thông tin.*cá nhân',
                r'private.*data|dữ liệu.*riêng tư',
                r'user.*profile|hồ sơ.*người dùng',
                r'email.*address|địa chỉ.*email',
                r'phone.*number|số.*điện thoại',
                r'credit.*card|thẻ.*tín dụng',
                r'bank.*account|tài khoản.*ngân hàng'
            ],
            'security': [
                r'security.*vulnerability|lỗ hổng.*bảo mật|vulnerabilities',
                r'system.*admin|quản trị.*hệ thống',
                r'database.*access|truy cập.*cơ sở dữ liệu',
                r'api.*key|khóa.*api',
                r'secret.*token|mã.*bí mật',
                r'encryption.*key|khóa.*mã hóa',
                r'hack|hacker|exploit'
            ],
            'system_info': [
                r'server.*config|cấu hình.*máy chủ',
                r'system.*file|tệp.*hệ thống',
                r'internal.*network|mạng.*nội bộ',
                r'infrastructure|cơ sở.*hạ tầng'
            ]
        }
        
        # Safe response templates
        self.blocked_responses = {
            'password': "Tôi không thể hỗ trợ các câu hỏi liên quan đến mật khẩu hoặc thông tin đăng nhập. Để được hỗ trợ về tài khoản, vui lòng liên hệ bộ phận CSKH.",
            'personal_info': "Tôi không thể truy cập hoặc thảo luận về thông tin cá nhân của người dùng. Tôi chỉ có thể tư vấn về laptop và thông số kỹ thuật.",
            'security': "Tôi không thể thảo luận về các vấn đề bảo mật hệ thống. Tôi được thiết kế để tư vấn laptop và giải đáp thắc mắc kỹ thuật.",
            'system_info': "Tôi không thể cung cấp thông tin về hệ thống nội bộ. Tôi chỉ có thể tư vấn về laptop và công nghệ tiêu dùng.",
            'general': "Tôi chỉ có thể tư vấn về laptop, thông số kỹ thuật và giúp bạn chọn laptop phù hợp. Bạn có thể hỏi về CPU, RAM, GPU, giá cả hoặc so sánh các mẫu laptop."
        }
    
    def is_query_blocked(self, message: str) -> tuple[bool, str, str]:
        """
        Check if query contains sensitive content
        Returns: (is_blocked, category, response)
        """
        message_lower = message.lower().strip()
        
        # Check for blocked patterns
        for category, patterns in self.blocked_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    self.logger.warning(f"Blocked query - Category: {category}, Pattern: {pattern}, Query: {message[:50]}...")
                    return True, category, self.blocked_responses.get(category, self.blocked_responses['general'])
        
        return False, '', ''
    
    def sanitize_input(self, message: str) -> str:
        """
        Sanitize user input to prevent injection attacks
        """
        if not message or not isinstance(message, str):
            return ""
        
        # Remove potentially dangerous characters
        message = re.sub(r'[<>"\;\(\){}]', '', message)
        
        # Limit message length
        if len(message) > 1000:
            message = message[:1000]
        
        # Remove excessive whitespace
        message = re.sub(r'\s+', ' ', message).strip()
        
        return message
    
    def validate_response(self, response: str) -> str:
        """
        Validate AI response to ensure no sensitive info leakage
        """
        if not response or not isinstance(response, str):
            return "Xin lỗi, tôi không thể tạo phản hồi phù hợp. Vui lòng thử lại với câu hỏi về laptop."
        
        # Check for potential sensitive info in response
        response_lower = response.lower()
        
        sensitive_keywords = [
            'password', 'mật khẩu', 'api key', 'secret', 'token',
            'admin', 'root', 'database', 'server config'
        ]
        
        for keyword in sensitive_keywords:
            if keyword in response_lower:
                self.logger.warning(f"Potentially sensitive response blocked containing: {keyword}")
                return "Tôi chỉ có thể tư vấn về laptop và thông số kỹ thuật. Bạn có câu hỏi nào về laptop không?"
        
        return response

class ChatbotService:
    def __init__(self, anthropic_api_key: str):
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        self.max_tokens = 1000
        self.temperature = 0.7
        self.security_filter = SecurityFilter()
        self.logger = logging.getLogger(__name__)
        
        # Intent patterns for Vietnamese
        self.intent_patterns = {
            'recommend': [
                r'tư vấn|gợi ý|đề xuất|nên mua|phù hợp|tốt nhất',
                r'laptop.*cho.*(gaming|game|chơi game)',
                r'laptop.*cho.*(học|sinh viên|student)',
                r'laptop.*cho.*(văn phòng|office|làm việc)',
                r'laptop.*cho.*(thiết kế|design|đồ họa)',
                r'laptop.*cho.*(lập trình|dev|programming)'
            ],
            'compare': [
                r'so sánh|khác nhau|tốt hơn|nên chọn|giữa',
                r'laptop.*vs.*laptop|laptop.*và.*laptop'
            ],
            'explain': [
                r'giải thích|nghĩa là|tức là|là gì|hoạt động',
                r'cpu.*là|ram.*là|gpu.*là|ssd.*là'
            ],
            'search': [
                r'tìm|tìm kiếm|tìm laptop|mua laptop',
                r'laptop.*giá|laptop.*dưới|laptop.*trên'
            ],
            'price': [
                r'giá|giá cả|tiền|chi phí|ngân sách',
                r'đắt|rẻ|phù hợp.*giá|trong tầm giá'
            ]
        }
        
        # Category keywords
        self.category_keywords = {
            'gaming': ['gaming', 'game', 'chơi game', 'rtx', 'gtx', 'gpu mạnh'],
            'design': ['design', 'thiết kế', 'đồ họa', 'photoshop', 'illustrator', 'premiere'],
            'dev': ['lập trình', 'dev', 'programming', 'coding', 'development'],
            'student': ['học', 'sinh viên', 'student', 'học tập', 'nghiên cứu'],
            'office': ['văn phòng', 'office', 'làm việc', 'word', 'excel', 'powerpoint']
        }

    def classify_intent(self, message: str) -> str:
        """Classify user intent from message"""
        message_lower = message.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent
        
        return 'general'

    def extract_user_preferences(self, message: str, conversation_history: List[Dict]) -> Dict:
        """Extract user preferences from message and conversation history"""
        preferences = {
            'budget_min': None,
            'budget_max': None,
            'category': None,
            'brand': None,
            'ram_min': None,
            'gpu_required': False
        }
        
        message_lower = message.lower()
        
        # Extract budget
        budget_patterns = [
            r'(\d+)\s*(triệu|tr|million)',
            r'(\d+)\s*(nghìn|k)',
            r'giá.*(\d+)',
            r'dưới.*(\d+)',
            r'trên.*(\d+)'
        ]
        
        for pattern in budget_patterns:
            match = re.search(pattern, message_lower)
            if match:
                amount = int(match.group(1))
                if 'triệu' in match.group(0) or 'tr' in match.group(0) or 'million' in match.group(0):
                    amount *= 1000000
                elif 'nghìn' in match.group(0) or 'k' in match.group(0):
                    amount *= 1000
                
                if 'dưới' in match.group(0):
                    preferences['budget_max'] = amount
                elif 'trên' in match.group(0):
                    preferences['budget_min'] = amount
                else:
                    preferences['budget_max'] = amount * 1.2  # 20% buffer
                    preferences['budget_min'] = amount * 0.8
        
        # Extract category
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    preferences['category'] = category
                    break
        
        # Extract brand
        brands = ['asus', 'dell', 'hp', 'lenovo', 'acer', 'msi', 'macbook', 'apple']
        for brand in brands:
            if brand in message_lower:
                preferences['brand'] = brand.title()
                break
        
        # Extract RAM requirement
        ram_match = re.search(r'(\d+)\s*gb.*ram|ram.*(\d+)\s*gb', message_lower)
        if ram_match:
            ram_amount = int(ram_match.group(1) or ram_match.group(2))
            preferences['ram_min'] = ram_amount
        
        # Check for GPU requirement
        gpu_keywords = ['gpu', 'card đồ họa', 'rtx', 'gtx', 'gaming', 'thiết kế']
        preferences['gpu_required'] = any(keyword in message_lower for keyword in gpu_keywords)
        
        return preferences

    def get_relevant_laptops(self, preferences: Dict, limit: int = 15) -> List[Dict]:
        """Get relevant laptops based on user preferences"""
        query = Laptop.query
        
        # Apply filters based on preferences
        if preferences['budget_min']:
            query = query.filter(Laptop.price >= preferences['budget_min'])
        if preferences['budget_max']:
            query = query.filter(Laptop.price <= preferences['budget_max'])
        if preferences['category']:
            query = query.filter(Laptop.category == preferences['category'])
        if preferences['brand']:
            query = query.filter(Laptop.brand == preferences['brand'])
        if preferences['ram_min']:
            query = query.filter(Laptop.ram_gb >= preferences['ram_min'])
        if preferences['gpu_required']:
            query = query.filter(
                ~Laptop.gpu.like('%Intel UHD%'),
                ~Laptop.gpu.like('%AMD Radeon Graphics%'),
                ~Laptop.gpu.like('%Intel Graphics%')
            )
        
        # Get laptops and convert to dict
        laptops = query.order_by(Laptop.price.asc()).limit(limit).all()
        
        laptop_data = []
        for laptop in laptops:
            laptop_info = {
                "id": laptop.id,
                "name": laptop.name,
                "brand": laptop.brand,
                "cpu": laptop.cpu,
                "ram_gb": laptop.ram_gb,
                "gpu": laptop.gpu,
                "storage": laptop.storage,
                "screen": laptop.screen,
                "price": laptop.price,
                "category": laptop.category,
                "image_url": laptop.image_url,
                "battery_life_office": laptop.battery_life_office,
                "cpu_single_core_plugged": laptop.cpu_single_core_plugged,
                "cpu_multi_core_plugged": laptop.cpu_multi_core_plugged,
                "gpu_score_plugged": laptop.gpu_score_plugged
            }
            laptop_data.append(laptop_info)
        
        return laptop_data

    def create_dynamic_system_prompt(self, intent: str, preferences: Dict, 
                                   relevant_laptops: List[Dict], 
                                   conversation_history: List[Dict]) -> str:
        """Create dynamic system prompt based on context"""
        
        base_prompt = """Bạn là AI tư vấn laptop chuyên nghiệp với dữ liệu thực tế từ website. Hãy trả lời ngắn gọn, rõ ràng bằng tiếng Việt.

**QUY TẮC NGHIÊM NGẶT:**
- CHỈ gợi ý laptop có trong dữ liệu được cung cấp
- KHÔNG được tự tạo hoặc bịa đặt laptop không có trong database
- Nếu không có laptop phù hợp, hãy nói rõ "Không tìm thấy laptop phù hợp"
- Tối đa 3-4 câu
- Sử dụng bullet points (•) cho danh sách
- In đậm (**text**) cho thông tin quan trọng
- Đưa ra lời khuyên cụ thể dựa trên dữ liệu thực tế
- Sử dụng xuống hàng (\\n) để tách các ý chính
- Mỗi ý chính nên ở một dòng riêng

**Chuyên môn:**
• Tư vấn laptop theo nhu cầu (gaming, văn phòng, học tập, thiết kế)
• So sánh hiệu năng và giá cả dựa trên dữ liệu thực tế
• Giải thích thông số kỹ thuật đơn giản
• Đưa ra lựa chọn tốt nhất trong ngân sách"""

        # Add context based on intent
        if intent == 'recommend':
            if relevant_laptops:
                base_prompt += f"""

**Nhiệm vụ hiện tại: Tư vấn laptop phù hợp**
- Ngân sách: {preferences['budget_min'] or 'Không giới hạn'} - {preferences['budget_max'] or 'Không giới hạn'} VND
- Danh mục: {preferences['category'] or 'Tất cả'}
- Thương hiệu: {preferences['brand'] or 'Tất cả'}
- RAM tối thiểu: {preferences['ram_min'] or 'Không yêu cầu'} GB
- GPU rời: {'Có' if preferences['gpu_required'] else 'Không yêu cầu'}

**CHỈ GỢI Ý CÁC LAPTOP SAU ĐÂY (có trong database):**
{json.dumps(relevant_laptops[:5], ensure_ascii=False, indent=2)}

**LƯU Ý:** Chỉ được gợi ý laptop có trong danh sách trên. KHÔNG được tự tạo laptop khác."""
            else:
                base_prompt += f"""

**Nhiệm vụ hiện tại: Tư vấn laptop phù hợp**
- Ngân sách: {preferences['budget_min'] or 'Không giới hạn'} - {preferences['budget_max'] or 'Không giới hạn'} VND
- Danh mục: {preferences['category'] or 'Tất cả'}
- Thương hiệu: {preferences['brand'] or 'Tất cả'}
- RAM tối thiểu: {preferences['ram_min'] or 'Không yêu cầu'} GB
- GPU rời: {'Có' if preferences['gpu_required'] else 'Không yêu cầu'}

**KHÔNG TÌM THẤY LAPTOP PHÙ HỢP** trong database với tiêu chí trên.
Hãy thông báo cho user rằng không có laptop phù hợp và đề xuất mở rộng tiêu chí tìm kiếm."""

        elif intent == 'compare':
            base_prompt += """

**Nhiệm vụ hiện tại: So sánh laptop**
- Hãy so sánh chi tiết các laptop được đề cập
- Đưa ra ưu nhược điểm của từng mẫu
- Gợi ý laptop phù hợp nhất"""

        elif intent == 'explain':
            base_prompt += """

**Nhiệm vụ hiện tại: Giải thích thông số**
- Giải thích đơn giản, dễ hiểu
- So sánh với các mẫu laptop khác
- Đưa ra lời khuyên thực tế"""

        elif intent == 'price':
            base_prompt += """

**Nhiệm vụ hiện tại: Tư vấn giá cả**
- Phân tích giá trị/tiền
- So sánh với các mẫu tương tự
- Đưa ra lựa chọn tốt nhất trong ngân sách"""

        # Add conversation context if available
        if conversation_history:
            base_prompt += f"""

**Context cuộc trò chuyện:**
{json.dumps(conversation_history[-3:], ensure_ascii=False, indent=2)}"""

        return base_prompt

    def generate_response(self, message: str, conversation_history: List[Dict] = None) -> Dict:
        """Generate AI response with enhanced context and security"""
        if conversation_history is None:
            conversation_history = []
        
        try:
            # Sanitize input first
            sanitized_message = self.security_filter.sanitize_input(message)
            
            if not sanitized_message:
                return {
                    "success": False,
                    "error": "Tin nhắn không hợp lệ. Vui lòng nhập câu hỏi về laptop.",
                    "blocked": True,
                    "category": "invalid_input"
                }
            
            # Check for blocked content
            is_blocked, block_category, block_response = self.security_filter.is_query_blocked(sanitized_message)
            
            if is_blocked:
                return {
                    "success": True,
                    "response": block_response,
                    "blocked": True,
                    "category": block_category,
                    "intent": "blocked"
                }
            
            # Classify intent
            intent = self.classify_intent(sanitized_message)
            
            # Extract preferences
            preferences = self.extract_user_preferences(sanitized_message, conversation_history)
            
            # Get relevant laptops
            relevant_laptops = self.get_relevant_laptops(preferences)
            
            # Create dynamic system prompt
            system_prompt = self.create_dynamic_system_prompt(
                intent, preferences, relevant_laptops, conversation_history
            )
            
            # Prepare messages for API
            messages = []
            
            # Add conversation history (last 5 messages to stay within token limit)
            for msg in conversation_history[-5:]:
                # Sanitize historical messages too
                sanitized_content = self.security_filter.sanitize_input(msg.get("content", ""))
                if sanitized_content:
                    messages.append({
                        "role": msg["role"],
                        "content": sanitized_content
                    })
            
            # Add current message
            messages.append({
                "role": "user",
                "content": sanitized_message
            })
            
            # Get response from Anthropic
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=messages
            )
            
            bot_response = response.content[0].text
            
            # Validate response for security
            validated_response = self.security_filter.validate_response(bot_response)
            
            # Add product recommendations if intent is recommend and we have laptops
            if intent == 'recommend' and relevant_laptops and len(relevant_laptops) > 0:
                validated_response += self._format_product_recommendations(relevant_laptops[:3])
            
            return {
                "success": True,
                "response": validated_response,
                "intent": intent,
                "preferences": preferences,
                "relevant_laptops": relevant_laptops,
                "relevant_laptops_count": len(relevant_laptops),
                "model": "claude-3-haiku",
                "blocked": False
            }
            
        except Exception as e:
            self.logger.error(f"AI generation error: {str(e)}")
            return {
                "success": False,
                "error": "Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại sau.",
                "blocked": False
            }

    def _format_product_recommendations(self, laptops: List[Dict]) -> str:
        """Format product recommendations for AI response"""
        if not laptops:
            return ""
        
        # Validate laptops have required fields
        valid_laptops = []
        for laptop in laptops:
            if (laptop.get('id') and laptop.get('name') and 
                laptop.get('price') and laptop.get('cpu')):
                valid_laptops.append(laptop)
        
        if not valid_laptops:
            return ""
        
        recommendations = "\n\n**💻 Laptop phù hợp nhất:**\n"
        
        for i, laptop in enumerate(valid_laptops, 1):
            price_formatted = f"{laptop['price']:,}".replace(',', '.')
            recommendations += f"\n**{i}. {laptop['name']}**\n"
            recommendations += f"• **Giá:** {price_formatted} VND\n"
            recommendations += f"• **CPU:** {laptop['cpu']}\n"
            recommendations += f"• **RAM:** {laptop['ram_gb']}GB\n"
            if laptop.get('gpu'):
                recommendations += f"• **GPU:** {laptop['gpu']}\n"
            recommendations += f"• **Storage:** {laptop['storage']}\n"
            recommendations += f"• **Màn hình:** {laptop['screen']}\n"
        
        recommendations += "\n💡 **Gợi ý:** Bạn có thể xem chi tiết và so sánh các laptop này trên website!"
        
        return recommendations

    def search_laptops(self, query: str, limit: int = 10) -> List[Dict]:
        """Enhanced laptop search with better matching and security"""
        try:
            # Sanitize search query
            sanitized_query = self.security_filter.sanitize_input(query)
            
            if not sanitized_query:
                return []
            
            # Check for blocked content in search
            is_blocked, _, _ = self.security_filter.is_query_blocked(sanitized_query)
            if is_blocked:
                self.logger.warning(f"Blocked search query: {query[:50]}...")
                return []
            
            # Extract search terms
            search_terms = re.findall(r'\b\w+\b', sanitized_query.lower())
            
            # Build search query
            search_conditions = []
            for term in search_terms:
                if len(term) > 2:  # Ignore short terms
                    search_conditions.append(
                        db.or_(
                            Laptop.name.contains(term),
                            Laptop.brand.contains(term),
                            Laptop.category.contains(term),
                            Laptop.cpu.contains(term),
                            Laptop.gpu.contains(term),
                            Laptop.storage.contains(term)
                        )
                    )
            
            if search_conditions:
                query_obj = Laptop.query.filter(db.or_(*search_conditions))
            else:
                query_obj = Laptop.query
            
            laptops = query_obj.order_by(Laptop.price.asc()).limit(limit).all()
            
            results = []
            for laptop in laptops:
                result = {
                    "id": laptop.id,
                    "name": laptop.name,
                    "brand": laptop.brand,
                    "price": laptop.price,
                    "category": laptop.category,
                    "cpu": laptop.cpu,
                    "ram_gb": laptop.ram_gb,
                    "gpu": laptop.gpu,
                    "storage": laptop.storage,
                    "screen": laptop.screen,
                    "image_url": laptop.image_url
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Search error: {str(e)}")
            return []
