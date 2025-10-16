#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Các hàm tiện ích cho ứng dụng
"""

import os
import uuid
import re
from PIL import Image
import io
from werkzeug.utils import secure_filename
from flask import current_app

def allowed_file(filename):
    """Kiểm tra file có được phép upload không"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def generate_unique_filename(original_filename):
    """Tạo tên file duy nhất"""
    # Lấy extension
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
    
    # Tạo tên file duy nhất
    unique_id = str(uuid.uuid4())[:8]
    return f"laptop_{unique_id}.{ext}"

def resize_image(image_data, max_size=(800, 600), quality=85):
    """Resize và tối ưu hóa hình ảnh"""
    try:
        # Mở hình ảnh
        image = Image.open(io.BytesIO(image_data))
        
        # Chuyển đổi sang RGB nếu cần
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        
        # Resize giữ nguyên tỷ lệ
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Lưu vào buffer
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        return output.getvalue()
    except Exception as e:
        current_app.logger.error(f"Error resizing image: {e}")
        return None

def save_uploaded_image(file, folder='images'):
    """Lưu file upload và trả về đường dẫn"""
    try:
        if file and allowed_file(file.filename):
            # Đọc dữ liệu file
            file_data = file.read()
            
            # Resize hình ảnh
            resized_data = resize_image(file_data)
            if not resized_data:
                return None
            
            # Tạo tên file duy nhất
            filename = generate_unique_filename(file.filename)
            
            # Đường dẫn đầy đủ
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            
            # Lưu file
            with open(upload_path, 'wb') as f:
                f.write(resized_data)
            
            # Trả về đường dẫn URL
            return f'/static/{folder}/{filename}'
        
        return None
    except Exception as e:
        current_app.logger.error(f"Error saving uploaded image: {e}")
        return None

def validate_price_range(price_min, price_max):
    """Validate price range"""
    if price_min is not None and price_max is not None:
        return price_min <= price_max
    return True

def sanitize_search_query(query):
    """Làm sạch query tìm kiếm"""
    if not query:
        return ""
    
    # Loại bỏ ký tự đặc biệt nguy hiểm
    query = re.sub(r'[<>"\';]', '', query)
    
    # Giới hạn độ dài
    query = query[:100]
    
    return query.strip()

def format_price(price):
    """Format giá tiền VND"""
    if price is None:
        return "Liên hệ"
    
    return f"{price:,} VND".replace(',', '.')

def calculate_performance_score(laptop):
    """Tính điểm performance tổng thể"""
    score = 0
    factors = 0
    
    # CPU Score (40% trọng số)
    if laptop.cpu_single_core_plugged and laptop.cpu_multi_core_plugged:
        cpu_score = (laptop.cpu_single_core_plugged * 0.3 + laptop.cpu_multi_core_plugged * 0.7) / 100
        score += cpu_score * 0.4
        factors += 0.4
    
    # GPU Score (30% trọng số)
    if laptop.gpu_score_plugged:
        gpu_score = laptop.gpu_score_plugged / 1000
        score += gpu_score * 0.3
        factors += 0.3
    
    # RAM Score (20% trọng số)
    if laptop.ram_gb:
        ram_score = min(laptop.ram_gb / 32, 1)  # Normalize to 32GB
        score += ram_score * 0.2
        factors += 0.2
    
    # Battery Score (10% trọng số)
    if laptop.battery_life_office:
        battery_score = min(laptop.battery_life_office / 600, 1)  # Normalize to 10 hours
        score += battery_score * 0.1
        factors += 0.1
    
    if factors == 0:
        return 0
    
    # Normalize score to 0-100
    return min(score / factors * 100, 100)

def get_price_category(price):
    """Phân loại laptop theo giá"""
    if price < 10000000:
        return "budget"
    elif price < 20000000:
        return "mid-range"
    elif price < 35000000:
        return "premium"
    else:
        return "flagship"

def get_ram_category(ram_gb):
    """Phân loại laptop theo RAM"""
    if ram_gb <= 4:
        return "basic"
    elif ram_gb <= 8:
        return "standard"
    elif ram_gb <= 16:
        return "good"
    else:
        return "excellent"

def get_battery_category(battery_life):
    """Phân loại laptop theo thời lượng pin"""
    if not battery_life:
        return "unknown"
    elif battery_life < 300:  # < 5 hours
        return "poor"
    elif battery_life < 480:  # < 8 hours
        return "average"
    elif battery_life < 720:  # < 12 hours
        return "good"
    else:
        return "excellent"
