#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script migration để thêm indexes vào database
Chạy: python migrate_database_indexes.py
"""

from app import create_app
from models import db
import sqlite3
import os

def add_database_indexes():
    """Thêm indexes vào database để cải thiện performance"""
    app = create_app()
    with app.app_context():
        print("🔄 Đang thêm indexes vào database...")
        
        # Kết nối trực tiếp đến SQLite database
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Thêm indexes cho bảng users
            indexes_users = [
                "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
                "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);",
                "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);"
            ]
            
            # Thêm indexes cho bảng laptops
            indexes_laptops = [
                "CREATE INDEX IF NOT EXISTS idx_laptops_name ON laptops(name);",
                "CREATE INDEX IF NOT EXISTS idx_laptops_brand ON laptops(brand);",
                "CREATE INDEX IF NOT EXISTS idx_laptops_ram_gb ON laptops(ram_gb);",
                "CREATE INDEX IF NOT EXISTS idx_laptops_price ON laptops(price);",
                "CREATE INDEX IF NOT EXISTS idx_laptops_category ON laptops(category);",
                "CREATE INDEX IF NOT EXISTS idx_laptops_brand_category ON laptops(brand, category);",
                "CREATE INDEX IF NOT EXISTS idx_laptops_price_range ON laptops(price, category);"
            ]
            
            # Thêm indexes cho bảng favorites
            indexes_favorites = [
                "CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_favorites_laptop_id ON favorites(laptop_id);",
                "CREATE INDEX IF NOT EXISTS idx_favorites_created_at ON favorites(created_at);"
            ]
            
            all_indexes = indexes_users + indexes_laptops + indexes_favorites
            
            for index_sql in all_indexes:
                cursor.execute(index_sql)
                print(f"✅ {index_sql.split('idx_')[1].split(' ')[0]}")
            
            conn.commit()
            print("\n🎉 Hoàn thành! Đã thêm tất cả indexes.")
            
            # Hiển thị thống kê indexes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%';")
            indexes = cursor.fetchall()
            print(f"\n📊 Tổng số indexes: {len(indexes)}")
            
        except Exception as e:
            print(f"❌ Lỗi khi thêm indexes: {e}")
            conn.rollback()
        finally:
            conn.close()

def show_database_info():
    """Hiển thị thông tin database"""
    app = create_app()
    with app.app_context():
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n📊 THÔNG TIN DATABASE:")
        print("=" * 50)
        
        # Thống kê bảng
        tables = ['users', 'laptops', 'favorites']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            print(f"📋 {table}: {count} records")
        
        # Thống kê indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%';")
        indexes = cursor.fetchall()
        print(f"\n🔍 Indexes: {len(indexes)}")
        for idx in indexes:
            print(f"   - {idx[0]}")
        
        conn.close()

def main():
    """Chạy migration"""
    print("🚀 MIGRATION DATABASE - THÊM INDEXES")
    print("=" * 50)
    
    try:
        add_database_indexes()
        show_database_info()
        
        print("\n✅ Migration hoàn thành!")
        print("💡 Database đã được tối ưu hóa với indexes.")
        
    except Exception as e:
        print(f"\n❌ Lỗi migration: {e}")

if __name__ == "__main__":
    main()
