#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script quản lý dữ liệu tổng hợp cho laptop recommender system
Bao gồm: seed data, cập nhật benchmark, quản lý hình ảnh, tạo user/admin
Sử dụng: python manage_data.py
"""

from app import create_app
from models import db, Laptop, User
import os
import re
import uuid
from PIL import Image
import io

# ========== DỮ LIỆU MẪU ==========
SAMPLE_LAPTOPS = [
    # Gaming laptops
    dict(name="ASUS TUF Gaming F15", brand="ASUS", cpu="Core i5-11400H", ram_gb=16, gpu="RTX 3050", storage="512GB SSD", screen="15.6 FHD 144Hz", price=21000000, category="gaming", image_url=""),
    dict(name="HP Victus 16", brand="HP", cpu="Ryzen 7 7840HS", ram_gb=16, gpu="RTX 4060", storage="512GB SSD", screen="16.1 FHD 144Hz", price=36000000, category="gaming", image_url=""),
    dict(name="MSI Katana 15", brand="MSI", cpu="Core i7-13620H", ram_gb=16, gpu="RTX 4070", storage="1TB SSD", screen="15.6 FHD 144Hz", price=42000000, category="gaming", image_url=""),
    dict(name="Lenovo Legion 5", brand="Lenovo", cpu="Ryzen 5 7640H", ram_gb=16, gpu="RTX 4050", storage="512GB SSD", screen="15.6 FHD 165Hz", price=28000000, category="gaming", image_url=""),
    
    # Design laptops
    dict(name="MSI Creator M16", brand="MSI", cpu="Core i7-12650H", ram_gb=16, gpu="RTX 4050", storage="1TB SSD", screen="16 2.5K 120Hz", price=35000000, category="design", image_url=""),
    dict(name="ASUS ProArt StudioBook", brand="ASUS", cpu="Core i7-13700H", ram_gb=32, gpu="RTX 4060", storage="1TB SSD", screen="16 2.5K 120Hz", price=45000000, category="design", image_url=""),
    dict(name="Dell XPS 15", brand="Dell", cpu="Core i7-13700H", ram_gb=16, gpu="RTX 4050", storage="512GB SSD", screen="15.6 3.5K OLED", price=48000000, category="design", image_url=""),
    dict(name="MacBook Pro 14 M3", brand="Apple", cpu="Apple M3", ram_gb=16, gpu="Integrated", storage="512GB SSD", screen="14.2 Liquid Retina", price=52000000, category="design", image_url=""),
    
    # Development laptops
    dict(name="Acer Swift Go 14", brand="Acer", cpu="Intel Core Ultra 5", ram_gb=16, gpu="Arc iGPU", storage="512GB SSD", screen="14 OLED 2.8K", price=28000000, category="dev", image_url=""),
    dict(name="Lenovo ThinkPad X1", brand="Lenovo", cpu="Core i7-1355U", ram_gb=16, gpu="Iris Xe", storage="512GB SSD", screen="14 2.2K", price=32000000, category="dev", image_url=""),
    dict(name="Dell Precision 5570", brand="Dell", cpu="Core i7-12700H", ram_gb=32, gpu="RTX A1000", storage="1TB SSD", screen="15.6 FHD", price=38000000, category="dev", image_url=""),
    dict(name="HP ZBook Studio", brand="HP", cpu="Core i7-13700H", ram_gb=16, gpu="RTX A2000", storage="512GB SSD", screen="15.6 4K", price=42000000, category="dev", image_url=""),
    
    # Student laptops
    dict(name="Acer Aspire 7 A715", brand="Acer", cpu="Ryzen 5 5500U", ram_gb=8, gpu="GTX 1650", storage="512GB SSD", screen="15.6 FHD 60Hz", price=14500000, category="student", image_url=""),
    dict(name="MacBook Air 13 M2", brand="Apple", cpu="Apple M2", ram_gb=8, gpu="Integrated", storage="256GB SSD", screen="13.6 60Hz", price=26000000, category="student", image_url=""),
    dict(name="ASUS VivoBook 15", brand="ASUS", cpu="Core i5-1235U", ram_gb=8, gpu="Iris Xe", storage="256GB SSD", screen="15.6 FHD", price=12000000, category="student", image_url=""),
    dict(name="Lenovo IdeaPad 3", brand="Lenovo", cpu="Ryzen 5 7520U", ram_gb=8, gpu="Radeon Graphics", storage="256GB SSD", screen="15.6 FHD", price=11000000, category="student", image_url=""),
    
    # Office laptops
    dict(name="Dell Inspiron 14", brand="Dell", cpu="Core i5-1235U", ram_gb=16, gpu="Iris Xe", storage="512GB SSD", screen="14 FHD", price=18500000, category="office", image_url=""),
    dict(name="Lenovo IdeaPad 5", brand="Lenovo", cpu="Ryzen 5 7530U", ram_gb=16, gpu="Radeon", storage="512GB SSD", screen="15.6 FHD", price=17900000, category="office", image_url=""),
    dict(name="HP Pavilion 14", brand="HP", cpu="Core i5-1335U", ram_gb=8, gpu="Iris Xe", storage="256GB SSD", screen="14 FHD", price=15000000, category="office", image_url=""),
    dict(name="Acer Aspire 3", brand="Acer", cpu="Ryzen 3 7320U", ram_gb=8, gpu="Radeon Graphics", storage="256GB SSD", screen="15.6 FHD", price=8500000, category="office", image_url="aceraspire3.jpg"),
    
    # Budget options
    dict(name="ASUS E410", brand="ASUS", cpu="Celeron N4020", ram_gb=4, gpu="Intel UHD", storage="128GB eMMC", screen="14 FHD", price=6500000, category="office", image_url=""),
    dict(name="Lenovo IdeaPad 1", brand="Lenovo", cpu="Athlon Silver 3050U", ram_gb=4, gpu="Radeon Graphics", storage="128GB SSD", screen="14 FHD", price=7000000, category="student", image_url=""),
    dict(name="HP 15s", brand="HP", cpu="Core i3-1215U", ram_gb=8, gpu="Intel UHD", storage="256GB SSD", screen="15.6 FHD", price=9500000, category="office", image_url=""),
    dict(name="Acer Aspire 1", brand="Acer", cpu="Celeron N4500", ram_gb=4, gpu="Intel UHD", storage="128GB eMMC", screen="15.6 FHD", price=6000000, category="office", image_url="")
]

# ========== DỮ LIỆU BENCHMARK ==========
BENCHMARK_DATA = {
    # ASUS TUF Gaming F15
    "ASUS TUF Gaming F15": {
        "battery_capacity": 90,
        "battery_life_office": 420,  # 7 giờ
        "battery_life_gaming": 180,  # 3 giờ
        "cpu_single_core_plugged": 2117,
        "cpu_multi_core_plugged": 6718,
        "cpu_single_core_battery": 1850,
        "cpu_multi_core_battery": 5800,
        "gpu_score_plugged": 8500,
        "gpu_score_battery": 6500
    },
    
    # HP Victus 16
    "HP Victus 16": {
        "battery_capacity": 83,
        "battery_life_office": 480,  # 8 giờ
        "battery_life_gaming": 210,  # 3.5 giờ
        "cpu_single_core_plugged": 2050,
        "cpu_multi_core_plugged": 7200,
        "cpu_single_core_battery": 1800,
        "cpu_multi_core_battery": 6200,
        "gpu_score_plugged": 9200,
        "gpu_score_battery": 7000
    },
    
    # MSI Katana 15
    "MSI Katana 15": {
        "battery_capacity": 76,
        "battery_life_office": 360,  # 6 giờ
        "battery_life_gaming": 150,  # 2.5 giờ
        "cpu_single_core_plugged": 1980,
        "cpu_multi_core_plugged": 6800,
        "cpu_single_core_battery": 1750,
        "cpu_multi_core_battery": 5900,
        "gpu_score_plugged": 7800,
        "gpu_score_battery": 5800
    },
    
    # Lenovo Legion 5
    "Lenovo Legion 5": {
        "battery_capacity": 80,
        "battery_life_office": 450,  # 7.5 giờ
        "battery_life_gaming": 200,  # 3.3 giờ
        "cpu_single_core_plugged": 2100,
        "cpu_multi_core_plugged": 7500,
        "cpu_single_core_battery": 1850,
        "cpu_multi_core_battery": 6500,
        "gpu_score_plugged": 9500,
        "gpu_score_battery": 7200
    },
    
    # MSI Creator M16
    "MSI Creator M16": {
        "battery_capacity": 99,
        "battery_life_office": 600,  # 10 giờ
        "battery_life_gaming": 240,  # 4 giờ
        "cpu_single_core_plugged": 2250,
        "cpu_multi_core_plugged": 8500,
        "cpu_single_core_battery": 2000,
        "cpu_multi_core_battery": 7500,
        "gpu_score_plugged": 12000,
        "gpu_score_battery": 9000
    },
    
    # ASUS ProArt StudioBook
    "ASUS ProArt StudioBook": {
        "battery_capacity": 92,
        "battery_life_office": 540,  # 9 giờ
        "battery_life_gaming": 180,  # 3 giờ
        "cpu_single_core_plugged": 2200,
        "cpu_multi_core_plugged": 8200,
        "cpu_single_core_battery": 1950,
        "cpu_multi_core_battery": 7200,
        "gpu_score_plugged": 11000,
        "gpu_score_battery": 8500
    },
    
    # Dell XPS 15
    "Dell XPS 15": {
        "battery_capacity": 86,
        "battery_life_office": 510,  # 8.5 giờ
        "battery_life_gaming": 180,  # 3 giờ
        "cpu_single_core_plugged": 2180,
        "cpu_multi_core_plugged": 8000,
        "cpu_single_core_battery": 1900,
        "cpu_multi_core_battery": 7000,
        "gpu_score_plugged": 10500,
        "gpu_score_battery": 8000
    },
    
    # MacBook Pro 14 M3
    "MacBook Pro 14 M3": {
        "battery_capacity": 72,
        "battery_life_office": 1200,  # 20 giờ
        "battery_life_gaming": 480,  # 8 giờ
        "cpu_single_core_plugged": 2400,
        "cpu_multi_core_plugged": 12000,
        "cpu_single_core_battery": 2350,
        "cpu_multi_core_battery": 11500,
        "gpu_score_plugged": 15000,
        "gpu_score_battery": 14000
    },
    
    # Acer Swift Go 14
    "Acer Swift Go 14": {
        "battery_capacity": 65,
        "battery_life_office": 480,  # 8 giờ
        "battery_life_gaming": 120,  # 2 giờ
        "cpu_single_core_plugged": 1800,
        "cpu_multi_core_plugged": 5500,
        "cpu_single_core_battery": 1600,
        "cpu_multi_core_battery": 4800,
        "gpu_score_plugged": 3500,
        "gpu_score_battery": 2800
    },
    
    # Lenovo ThinkPad X1
    "Lenovo ThinkPad X1": {
        "battery_capacity": 57,
        "battery_life_office": 540,  # 9 giờ
        "battery_life_gaming": 90,  # 1.5 giờ
        "cpu_single_core_plugged": 1900,
        "cpu_multi_core_plugged": 6000,
        "cpu_single_core_battery": 1700,
        "cpu_multi_core_battery": 5200,
        "gpu_score_plugged": 4000,
        "gpu_score_battery": 3200
    },
    
    # Dell Precision 5570
    "Dell Precision 5570": {
        "battery_capacity": 86,
        "battery_life_office": 480,  # 8 giờ
        "battery_life_gaming": 180,  # 3 giờ
        "cpu_single_core_plugged": 2100,
        "cpu_multi_core_plugged": 7800,
        "cpu_single_core_battery": 1850,
        "cpu_multi_core_battery": 6800,
        "gpu_score_plugged": 9500,
        "gpu_score_battery": 7200
    },
    
    # HP ZBook Studio
    "HP ZBook Studio": {
        "battery_capacity": 83,
        "battery_life_office": 450,  # 7.5 giờ
        "battery_life_gaming": 150,  # 2.5 giờ
        "cpu_single_core_plugged": 2050,
        "cpu_multi_core_plugged": 7500,
        "cpu_single_core_battery": 1800,
        "cpu_multi_core_battery": 6500,
        "gpu_score_plugged": 9000,
        "gpu_score_battery": 6800
    },
    
    # Acer Aspire 7 A715
    "Acer Aspire 7 A715": {
        "battery_capacity": 50,
        "battery_life_office": 300,  # 5 giờ
        "battery_life_gaming": 90,  # 1.5 giờ
        "cpu_single_core_plugged": 1600,
        "cpu_multi_core_plugged": 4800,
        "cpu_single_core_battery": 1400,
        "cpu_multi_core_battery": 4200,
        "gpu_score_plugged": 2800,
        "gpu_score_battery": 2200
    },
    
    # MacBook Air 13 M2
    "MacBook Air 13 M2": {
        "battery_capacity": 52,
        "battery_life_office": 900,  # 15 giờ
        "battery_life_gaming": 360,  # 6 giờ
        "cpu_single_core_plugged": 2200,
        "cpu_multi_core_plugged": 8500,
        "cpu_single_core_battery": 2150,
        "cpu_multi_core_battery": 8200,
        "gpu_score_plugged": 8000,
        "gpu_score_battery": 7500
    },
    
    # ASUS VivoBook 15
    "ASUS VivoBook 15": {
        "battery_capacity": 42,
        "battery_life_office": 360,  # 6 giờ
        "battery_life_gaming": 60,  # 1 giờ
        "cpu_single_core_plugged": 1400,
        "cpu_multi_core_plugged": 4200,
        "cpu_single_core_battery": 1200,
        "cpu_multi_core_battery": 3600,
        "gpu_score_plugged": 2000,
        "gpu_score_battery": 1500
    },
    
    # Lenovo IdeaPad 3
    "Lenovo IdeaPad 3": {
        "battery_capacity": 45,
        "battery_life_office": 330,  # 5.5 giờ
        "battery_life_gaming": 75,  # 1.25 giờ
        "cpu_single_core_plugged": 1350,
        "cpu_multi_core_plugged": 4000,
        "cpu_single_core_battery": 1150,
        "cpu_multi_core_battery": 3500,
        "gpu_score_plugged": 1800,
        "gpu_score_battery": 1300
    },
    
    # Dell Inspiron 14
    "Dell Inspiron 14": {
        "battery_capacity": 54,
        "battery_life_office": 420,  # 7 giờ
        "battery_life_gaming": 90,  # 1.5 giờ
        "cpu_single_core_plugged": 1500,
        "cpu_multi_core_plugged": 4500,
        "cpu_single_core_battery": 1300,
        "cpu_multi_core_battery": 3900,
        "gpu_score_plugged": 2200,
        "gpu_score_battery": 1700
    },
    
    # Lenovo IdeaPad 5
    "Lenovo IdeaPad 5": {
        "battery_capacity": 57,
        "battery_life_office": 480,  # 8 giờ
        "battery_life_gaming": 120,  # 2 giờ
        "cpu_single_core_plugged": 1600,
        "cpu_multi_core_plugged": 4800,
        "cpu_single_core_battery": 1400,
        "cpu_multi_core_battery": 4200,
        "gpu_score_plugged": 2500,
        "gpu_score_battery": 2000
    },
    
    # HP Pavilion 14
    "HP Pavilion 14": {
        "battery_capacity": 43,
        "battery_life_office": 390,  # 6.5 giờ
        "battery_life_gaming": 75,  # 1.25 giờ
        "cpu_single_core_plugged": 1450,
        "cpu_multi_core_plugged": 4300,
        "cpu_single_core_battery": 1250,
        "cpu_multi_core_battery": 3700,
        "gpu_score_plugged": 2100,
        "gpu_score_battery": 1600
    },
    
    # Acer Aspire 3
    "Acer Aspire 3": {
        "battery_capacity": 36,
        "battery_life_office": 300,  # 5 giờ
        "battery_life_gaming": 60,  # 1 giờ
        "cpu_single_core_plugged": 1200,
        "cpu_multi_core_plugged": 3500,
        "cpu_single_core_battery": 1000,
        "cpu_multi_core_battery": 3000,
        "gpu_score_plugged": 1500,
        "gpu_score_battery": 1100
    },
    
    # ASUS E410
    "ASUS E410": {
        "battery_capacity": 42,
        "battery_life_office": 360,  # 6 giờ
        "battery_life_gaming": 45,  # 0.75 giờ
        "cpu_single_core_plugged": 1100,
        "cpu_multi_core_plugged": 3200,
        "cpu_single_core_battery": 900,
        "cpu_multi_core_battery": 2800,
        "gpu_score_plugged": 1200,
        "gpu_score_battery": 800
    },
    
    # Lenovo IdeaPad 1
    "Lenovo IdeaPad 1": {
        "battery_capacity": 45,
        "battery_life_office": 420,  # 7 giờ
        "battery_life_gaming": 30,  # 0.5 giờ
        "cpu_single_core_plugged": 1000,
        "cpu_multi_core_plugged": 2800,
        "cpu_single_core_battery": 800,
        "cpu_multi_core_battery": 2400,
        "gpu_score_plugged": 800,
        "gpu_score_battery": 500
    },
    
    # HP 15s
    "HP 15s": {
        "battery_capacity": 41,
        "battery_life_office": 390,  # 6.5 giờ
        "battery_life_gaming": 60,  # 1 giờ
        "cpu_single_core_plugged": 1150,
        "cpu_multi_core_plugged": 3300,
        "cpu_single_core_battery": 950,
        "cpu_multi_core_battery": 2900,
        "gpu_score_plugged": 1300,
        "gpu_score_battery": 900
    },
    
    # Acer Aspire 1
    "Acer Aspire 1": {
        "battery_capacity": 36,
        "battery_life_office": 330,  # 5.5 giờ
        "battery_life_gaming": 30,  # 0.5 giờ
        "cpu_single_core_plugged": 900,
        "cpu_multi_core_plugged": 2500,
        "cpu_single_core_battery": 700,
        "cpu_multi_core_battery": 2100,
        "gpu_score_plugged": 600,
        "gpu_score_battery": 400
    }
}

# ========== MAPPING HÌNH ẢNH ==========
IMAGE_MAPPINGS = {
    # ASUS
    'asustufgamingf15': ['tuff15_1.webp', 'tuff15_2.webp'],
    'asusproartstudiobook': ['proartstudiobook_1.webp', 'proartstudiobook_2.webp'],
    'asusvivobook15': ['asusvivobook15_1.webp', 'asusvivobook15_2.webp'],
    'asuse410': ['asusE410_1.webp', 'asusE410_2.webp'],
    
    # HP
    'hpvictus16': ['victus16_1.webp', 'victus16_2.webp'],
    'hpzbookstudio': ['zbookstu_1.webp', 'zbookstu_2.webp'],
    'hppavilion14': ['Pavilion14_1.webp', 'Pavilion14_2.webp'],
    'hp15s': ['HP15s_1.webp', 'HP15s_2.webp'],
    
    # MSI
    'msikatana15': ['msikatana15_1.webp', 'msikatana15_2.webp'],
    'msicreatorm16': ['creator16_1.webp', 'creator16_2.webp'],
    
    # Lenovo
    'lenovolegion5': ['legion5_1.webp', 'legion5_2.webp'],
    'lenovothinkpadx1': ['thinkpadx1_1.webp', 'thinkpadx1_2.webp'],
    'lenovoideapad3': ['ideapad3_1.webp', 'ideapad3_2.webp'],
    'lenovoideapad5': ['ideapad5_1.webp', 'ideapad5_2.webp'],
    'lenovoideapad1': ['lenovoIdeaPad_1.webp', 'lenovoIdeaPad_2.webp'],
    
    # Dell
    'dellxps15': ['xps15_1.webp', 'xps15_2.webp'],
    'dellprecision5570': ['dellprecision5570_1.webp', 'dellprecision5570_2.webp'],
    'dellinspiron14': ['Dellinspiron14_1.webp', 'Dellinspiron14_2.webp'],
    
    # Apple
    'macbookpro14m3': ['macbookpro14m3_1.webp', 'macbookpro14m3_2.webp'],
    'macbookair13m2': ['air13M2_1.webp', 'air13M2_2.webp'],
    
    # Acer
    'acerswiftgo14': ['acerswiftgo14_1.webp', 'acerswiftgo14_2.webp'],
    'aceraspire7a715': ['aspire7a715_1.webp', 'aspire7a715_2.webp'],
    'aceraspire3': ['aspire3_1.webp', 'aspire3_2.webp', 'aceraspire3.webp'],
    'aceraspire1': ['Aspire1_1.webp', 'Aspire1_2.webp', 'Aspire1_3.webp'],
}

# ========== CÁC HÀM TIỆN ÍCH ==========
def normalize_name(name):
    """Chuẩn hóa tên để so sánh"""
    name = name.lower()
    name = re.sub(r'[^a-z0-9]', '', name)
    return name

def find_best_image_match(laptop_name, image_files):
    """Tìm hình ảnh phù hợp nhất cho laptop"""
    laptop_normalized = normalize_name(laptop_name)
    
    # Tìm match chính xác
    for key, images in IMAGE_MAPPINGS.items():
        if key in laptop_normalized or laptop_normalized in key:
            for img in images:
                if img in image_files:
                    return img
    
    # Tìm match theo từ khóa
    keywords = {
        'tuf': ['tuff15_1.webp', 'tuff15_2.webp'],
        'gaming': ['tuff15_1.webp', 'victus16_1.webp', 'legion5_1.webp'],
        'creator': ['creator16_1.webp', 'creator16_2.webp'],
        'proart': ['proartstudiobook_1.webp', 'proartstudiobook_2.webp'],
        'xps': ['xps15_1.webp', 'xps15_2.webp'],
        'precision': ['dellprecision5570_1.webp', 'dellprecision5570_2.webp'],
        'thinkpad': ['thinkpadx1_1.webp', 'thinkpadx1_2.webp'],
        'swift': ['acerswiftgo14_1.webp', 'acerswiftgo14_2.webp'],
        'aspire': ['aspire3_1.webp', 'aspire7a715_1.webp'],
        'vivobook': ['asusvivobook15_1.webp', 'asusvivobook15_2.webp'],
        'ideapad': ['ideapad3_1.webp', 'ideapad5_1.webp'],
        'pavilion': ['Pavilion14_1.webp', 'Pavilion14_2.webp'],
        'victus': ['victus16_1.webp', 'victus16_2.webp'],
        'legion': ['legion5_1.webp', 'legion5_2.webp'],
        'zbook': ['zbookstu_1.webp', 'zbookstu_2.webp'],
        'macbook': ['macbookpro14m3_1.webp', 'air13M2_1.webp'],
        'inspiron': ['Dellinspiron14_1.webp', 'Dellinspiron14_2.webp'],
    }
    
    for keyword, images in keywords.items():
        if keyword in laptop_normalized:
            for img in images:
                if img in image_files:
                    return img
    
    return None

# ========== CÁC CHỨC NĂNG CHÍNH ==========
def seed_database():
    """Tạo dữ liệu mẫu cho database"""
    app = create_app()
    with app.app_context():
        print("🔄 Đang tạo dữ liệu mẫu...")
        
        # Xóa và tạo lại database
        db.drop_all()
        db.create_all()
        
        # Thêm dữ liệu laptop
        for laptop_data in SAMPLE_LAPTOPS:
            db.session.add(Laptop(**laptop_data))
        
        db.session.commit()
        print(f"✅ Đã tạo {len(SAMPLE_LAPTOPS)} laptop mẫu!")

def update_benchmark_data():
    """Cập nhật dữ liệu benchmark cho laptop"""
    app = create_app()
    with app.app_context():
        print("🔄 Đang cập nhật dữ liệu benchmark...")
        updated_count = 0
        
        for laptop_name, data in BENCHMARK_DATA.items():
            laptop = Laptop.query.filter_by(name=laptop_name).first()
            if laptop:
                # Cập nhật dữ liệu
                laptop.battery_capacity = data["battery_capacity"]
                laptop.battery_life_office = data["battery_life_office"]
                laptop.battery_life_gaming = data["battery_life_gaming"]
                laptop.cpu_single_core_plugged = data["cpu_single_core_plugged"]
                laptop.cpu_multi_core_plugged = data["cpu_multi_core_plugged"]
                laptop.cpu_single_core_battery = data["cpu_single_core_battery"]
                laptop.cpu_multi_core_battery = data["cpu_multi_core_battery"]
                laptop.gpu_score_plugged = data["gpu_score_plugged"]
                laptop.gpu_score_battery = data["gpu_score_battery"]
                
                updated_count += 1
                print(f"✅ {laptop_name}")
            else:
                print(f"❌ Không tìm thấy: {laptop_name}")
        
        # Lưu thay đổi
        db.session.commit()
        
        print(f"\n🎉 Hoàn thành! Đã cập nhật {updated_count} laptop")
        
        # Thống kê
        total = Laptop.query.count()
        with_battery = Laptop.query.filter(Laptop.battery_capacity.isnot(None)).count()
        with_cpu_scores = Laptop.query.filter(Laptop.cpu_single_core_plugged.isnot(None)).count()
        with_gpu_scores = Laptop.query.filter(Laptop.gpu_score_plugged.isnot(None)).count()
        
        print(f"\n📊 Thống kê dữ liệu:")
        print(f"   🔋 Có dữ liệu pin: {with_battery}/{total}")
        print(f"   🖥️  Có điểm CPU: {with_cpu_scores}/{total}")
        print(f"   🎮 Có điểm GPU: {with_gpu_scores}/{total}")

def update_all_images():
    """Cập nhật hình ảnh cho tất cả laptop"""
    app = create_app()
    with app.app_context():
        # Lấy danh sách file hình ảnh
        image_dir = 'static/images'
        image_files = [f for f in os.listdir(image_dir) if f.endswith(('.webp', '.jpg', '.png', '.jpeg'))]
        
        print(f"📁 Tìm thấy {len(image_files)} file hình ảnh")
        print("🔄 Đang cập nhật hình ảnh cho laptop...")
        print("=" * 60)
        
        # Lấy tất cả laptop
        laptops = Laptop.query.all()
        updated_count = 0
        
        for laptop in laptops:
            # Tìm hình ảnh phù hợp
            best_image = find_best_image_match(laptop.name, image_files)
            
            if best_image:
                # Cập nhật đường dẫn hình ảnh
                laptop.image_url = f'/static/images/{best_image}'
                updated_count += 1
                print(f"✅ {laptop.name}")
                print(f"   📸 {best_image}")
            else:
                # Giữ nguyên placeholder nếu không tìm thấy
                if not laptop.image_url or 'placeholder' in laptop.image_url:
                    print(f"❌ {laptop.name} - Không tìm thấy hình ảnh phù hợp")
                else:
                    print(f"⚠️  {laptop.name} - Giữ nguyên hình ảnh hiện tại")
        
        # Lưu thay đổi
        db.session.commit()
        
        print("=" * 60)
        print(f"🎉 Hoàn thành! Đã cập nhật {updated_count}/{len(laptops)} laptop")
        
        # Hiển thị thống kê
        print("\n📊 Thống kê:")
        laptops_with_images = Laptop.query.filter(Laptop.image_url.like('%webp%')).count()
        laptops_with_placeholders = Laptop.query.filter(Laptop.image_url.like('%placeholder%')).count()
        laptops_without_images = len(laptops) - laptops_with_images - laptops_with_placeholders
        
        print(f"   🖼️  Có hình thật: {laptops_with_images}")
        print(f"   🎨 Có placeholder: {laptops_with_placeholders}")
        print(f"   ❌ Không có hình: {laptops_without_images}")

def create_admin_user():
    """Tạo admin user"""
    app = create_app()
    with app.app_context():
        # Kiểm tra xem đã có admin chưa
        admin = User.query.filter_by(role='admin').first()
        if admin:
            print(f"⚠️  Đã có admin: {admin.username}")
            return
        
        # Tạo admin mới
        admin = User(
            username='admin',
            email='admin@laptop.com',
            role='admin'
        )
        admin.set_password('admin123')
        
        try:
            db.session.add(admin)
            db.session.commit()
            print("✅ Đã tạo admin thành công!")
            print("📋 Thông tin đăng nhập:")
            print("   👤 Username: admin")
            print("   🔑 Password: admin123")
            print("   📧 Email: admin@laptop.com")
            print("\n🔗 Truy cập: http://localhost:5000/admin")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Lỗi khi tạo admin: {e}")

def create_test_users():
    """Tạo các user test"""
    app = create_app()
    with app.app_context():
        # Kiểm tra xem đã có user nào chưa
        existing_users = User.query.all()
        if existing_users:
            print("Đã có tài khoản trong hệ thống:")
            for user in existing_users:
                print(f"- {user.username} ({user.email})")
            return
        
        # Tạo tài khoản test
        test_users = [
            {
                'username': 'admin',
                'email': 'admin@example.com',
                'password': 'admin123',
                'role': 'admin'
            },
            {
                'username': 'user1',
                'email': 'user1@example.com',
                'password': 'user123',
                'role': 'user'
            },
            {
                'username': 'test',
                'email': 'test@example.com',
                'password': 'test123',
                'role': 'user'
            }
        ]
        
        for user_data in test_users:
            user = User(
                username=user_data['username'], 
                email=user_data['email'],
                role=user_data['role']
            )
            user.set_password(user_data['password'])
            db.session.add(user)
            print(f"Đã tạo tài khoản: {user_data['username']} (Mật khẩu: {user_data['password']})")
        
        db.session.commit()
        print("\n✅ Đã tạo thành công các tài khoản test!")
        print("\n📋 Thông tin đăng nhập:")
        print("=" * 40)
        for user_data in test_users:
            print(f"👤 {user_data['username']}")
            print(f"📧 {user_data['email']}")
            print(f"🔑 {user_data['password']}")
            print("-" * 20)

def show_image_mapping():
    """Hiển thị mapping hình ảnh hiện tại"""
    app = create_app()
    with app.app_context():
        laptops = Laptop.query.all()
        
        print("📋 MAPPING HÌNH ẢNH HIỆN TẠI:")
        print("=" * 80)
        
        for laptop in laptops:
            status = "✅" if laptop.image_url and "placeholder" not in laptop.image_url else "❌"
            image_name = laptop.image_url.split('/')[-1] if laptop.image_url else "Không có"
            print(f"{status} {laptop.name}")
            print(f"   📸 {image_name}")
            print()

def show_database_stats():
    """Hiển thị thống kê database"""
    app = create_app()
    with app.app_context():
        total_laptops = Laptop.query.count()
        total_users = User.query.count()
        admin_users = User.query.filter_by(role='admin').count()
        
        laptops_with_images = Laptop.query.filter(Laptop.image_url.like('%webp%')).count()
        laptops_with_benchmark = Laptop.query.filter(Laptop.battery_capacity.isnot(None)).count()
        
        print("📊 THỐNG KÊ DATABASE:")
        print("=" * 40)
        print(f"🖥️  Tổng số laptop: {total_laptops}")
        print(f"👥 Tổng số user: {total_users}")
        print(f"👑 Admin users: {admin_users}")
        print(f"🖼️  Laptop có hình ảnh: {laptops_with_images}")
        print(f"📈 Laptop có benchmark: {laptops_with_benchmark}")
        
        # Thống kê theo brand
        brands = db.session.query(Laptop.brand, db.func.count(Laptop.id)).group_by(Laptop.brand).all()
        print(f"\n🏷️  Thống kê theo thương hiệu:")
        for brand, count in brands:
            print(f"   {brand}: {count}")

def full_setup():
    """Thiết lập đầy đủ hệ thống"""
    print("🚀 BẮT ĐẦU THIẾT LẬP ĐẦY ĐỦ HỆ THỐNG")
    print("=" * 50)
    
    # 1. Tạo dữ liệu mẫu
    seed_database()
    
    # 2. Cập nhật benchmark
    update_benchmark_data()
    
    # 3. Cập nhật hình ảnh
    update_all_images()
    
    # 4. Tạo admin
    create_admin_user()
    
    print("\n🎉 HOÀN THÀNH THIẾT LẬP!")
    print("=" * 50)
    show_database_stats()

# ========== AUTO RUN ==========
def main():
    """Tự động chạy thiết lập đầy đủ hệ thống"""
    print("🚀 TỰ ĐỘNG THIẾT LẬP HỆ THỐNG LAPTOP RECOMMENDER")
    print("=" * 60)
    
    try:
        # Chạy thiết lập đầy đủ
        full_setup()
        
        print("\n🎉 HOÀN THÀNH! Hệ thống đã sẵn sàng sử dụng.")
        print("=" * 60)
        print("📋 Thông tin đăng nhập:")
        print("   👤 Username: admin")
        print("   🔑 Password: admin123")
        print("   📧 Email: admin@laptop.com")
        print("\n🔗 Truy cập:")
        print("   - Website: http://localhost:5000")
        print("   - Admin Panel: http://localhost:5000/admin")
        print("   - API Documentation: Xem file API_DOCUMENTATION.md")
        print("\n💡 Để chạy ứng dụng: python app.py")
        
    except Exception as e:
        print(f"\n❌ Lỗi khi thiết lập hệ thống: {e}")
        print("💡 Hãy kiểm tra:")
        print("   - Đã cài đặt dependencies: pip install -r requirements.txt")
        print("   - Có quyền ghi file trong thư mục dự án")
        print("   - Không có ứng dụng nào đang sử dụng database")

if __name__ == "__main__":
    main()
