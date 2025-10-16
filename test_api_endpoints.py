#!/usr/bin/env python3
"""
Script test các API endpoints cho laptop recommender system
"""

import requests
import json
import os
from io import BytesIO
from PIL import Image

# Cấu hình
BASE_URL = "http://localhost:5000/api"
WEB_BASE_URL = "http://localhost:5000"
TEST_IMAGE_PATH = "static/images/favicon.ico"  # Sử dụng favicon có sẵn để test

# Session để lưu trữ authentication
session = requests.Session()

def create_test_image():
    """Tạo một hình ảnh test"""
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes

def login_admin():
    """Đăng nhập admin để test các API cần authentication"""
    print("\n=== Login Admin ===")
    
    try:
        # Lấy trang login
        login_page = session.get(f"{WEB_BASE_URL}/login")
        if login_page.status_code != 200:
            print("❌ Không thể truy cập trang login")
            return False
        
        # Đăng nhập
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        response = session.post(f"{WEB_BASE_URL}/login", data=login_data)
        
        # Kiểm tra đăng nhập thành công
        if response.status_code == 200 and ('Chào mừng' in response.text or 'admin' in response.text):
            print("✅ Đăng nhập admin thành công!")
            return True
        else:
            print("❌ Đăng nhập thất bại!")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi khi đăng nhập: {e}")
        return False

def test_upload_image():
    """Test API upload hình ảnh"""
    print("=== Test Upload Image ===")
    
    # Tạo hình ảnh test
    test_image = create_test_image()
    
    files = {'image': ('test_image.jpg', test_image, 'image/jpeg')}
    
    try:
        response = session.post(f"{BASE_URL}/upload-image", files=files)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Upload thành công!")
                print(f"Image URL: {result.get('image_url')}")
                return result.get('image_url')
            else:
                print("❌ Upload thất bại!")
        elif response.status_code == 403:
            print("❌ Không có quyền truy cập (cần đăng nhập admin)")
        else:
            print("❌ Upload thất bại!")
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")
    
    return None

def test_get_products():
    """Test API lấy danh sách sản phẩm"""
    print("\n=== Test Get Products ===")
    
    try:
        # Test lấy tất cả sản phẩm
        response = requests.get(f"{BASE_URL}/products")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                products = result.get('products', [])
                print(f"✅ Lấy được {len(products)} sản phẩm")
                if products:
                    print(f"Ví dụ sản phẩm đầu tiên: {products[0]['name']}")
            else:
                print("❌ Lỗi API")
        else:
            print("❌ Request thất bại!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")

def test_get_products_with_filters():
    """Test API lấy sản phẩm với filter"""
    print("\n=== Test Get Products with Filters ===")
    
    try:
        # Test với filter brand
        params = {
            'brand': 'Apple',
            'page': 1,
            'per_page': 5
        }
        
        response = requests.get(f"{BASE_URL}/products", params=params)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                products = result.get('products', [])
                print(f"✅ Lấy được {len(products)} sản phẩm Apple")
                for product in products:
                    print(f"  - {product['name']} - {product['price']:,} VND")
            else:
                print("❌ Lỗi API")
        else:
            print("❌ Request thất bại!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")

def test_get_product_detail():
    """Test API lấy chi tiết sản phẩm"""
    print("\n=== Test Get Product Detail ===")
    
    try:
        # Lấy danh sách sản phẩm trước để có ID thực tế
        products_response = requests.get(f"{BASE_URL}/products")
        if products_response.status_code == 200:
            products_data = products_response.json()
            if products_data.get('success') and products_data.get('products'):
                # Lấy ID của sản phẩm đầu tiên
                first_product_id = products_data['products'][0]['id']
                print(f"Testing với ID = {first_product_id}")
                
                # Test với ID thực tế
                response = requests.get(f"{BASE_URL}/products/{first_product_id}")
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        product = result.get('product')
                        print(f"✅ Lấy được chi tiết sản phẩm: {product['name']}")
                        print(f"  - Brand: {product['brand']}")
                        print(f"  - Price: {product['price']:,} VND")
                        print(f"  - CPU: {product['cpu']}")
                        return first_product_id  # Trả về ID để dùng cho test khác
                    else:
                        print("❌ Lỗi API")
                elif response.status_code == 404:
                    print(f"❌ Không tìm thấy sản phẩm với ID = {first_product_id}")
                else:
                    print("❌ Request thất bại!")
            else:
                print("❌ Không thể lấy danh sách sản phẩm")
        else:
            print("❌ Không thể lấy danh sách sản phẩm")
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")
    
    return None

def test_get_brands():
    """Test API lấy danh sách thương hiệu"""
    print("\n=== Test Get Brands ===")
    
    try:
        response = requests.get(f"{BASE_URL}/brands")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                brands = result.get('brands', [])
                print(f"✅ Lấy được {len(brands)} thương hiệu:")
                for brand in brands:
                    print(f"  - {brand}")
            else:
                print("❌ Lỗi API")
        else:
            print("❌ Request thất bại!")
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")

def test_get_categories():
    """Test API lấy danh sách danh mục"""
    print("\n=== Test Get Categories ===")
    
    try:
        response = requests.get(f"{BASE_URL}/categories")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                categories = result.get('categories', [])
                print(f"✅ Lấy được {len(categories)} danh mục:")
                for category in categories:
                    print(f"  - {category}")
            else:
                print("❌ Lỗi API")
        else:
            print("❌ Request thất bại!")
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")

def test_search_suggest():
    """Test API tìm kiếm gợi ý"""
    print("\n=== Test Search Suggest ===")
    
    try:
        params = {
            'q': 'macbook',
            'limit': 5
        }
        
        response = requests.get(f"{BASE_URL}/search_suggest", params=params)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            items = result.get('items', [])
            print(f"✅ Tìm được {len(items)} gợi ý cho 'macbook':")
            for item in items:
                print(f"  - {item['name']} - {item['price']:,} VND")
        else:
            print("❌ Request thất bại!")
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")

def test_compare_data():
    """Test API dữ liệu so sánh"""
    print("\n=== Test Compare Data ===")
    
    try:
        params = {
            'id': [1, 2, 3],  # Test với 3 sản phẩm
            'mode': 'plugged'
        }
        
        response = requests.get(f"{BASE_URL}/compare_data", params=params)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Lấy được dữ liệu so sánh:")
            print(f"  - CPU Single Core: {len(result.get('cpu_single_core', []))} sản phẩm")
            print(f"  - CPU Multi Core: {len(result.get('cpu_multi_core', []))} sản phẩm")
            print(f"  - GPU Score: {len(result.get('gpu_score', []))} sản phẩm")
        else:
            print("❌ Request thất bại!")
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")

def test_create_product():
    """Test API tạo sản phẩm mới (cần admin authentication)"""
    print("\n=== Test Create Product ===")
    
    try:
        # Dữ liệu sản phẩm test
        product_data = {
            "name": "Test Laptop API",
            "brand": "TestBrand",
            "cpu": "Intel Core i5-12345H",
            "ram_gb": 16,
            "gpu": "RTX 4050",
            "storage": "512GB SSD",
            "screen": "15.6 FHD",
            "price": 20000000,
            "category": "gaming"
        }
        
        response = session.post(
            f"{BASE_URL}/products",
            json=product_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            if result.get('success'):
                product = result.get('product')
                print(f"✅ Tạo sản phẩm thành công: {product['name']}")
                print(f"  - ID: {product['id']}")
                print(f"  - Brand: {product['brand']}")
                print(f"  - Price: {product['price']:,} VND")
            else:
                print("❌ Lỗi API")
        elif response.status_code == 403:
            print("❌ Không có quyền truy cập (cần đăng nhập admin)")
        else:
            print("❌ Request thất bại!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")

def test_update_product(product_id=None):
    """Test API cập nhật sản phẩm (cần admin authentication)"""
    print("\n=== Test Update Product ===")
    
    if not product_id:
        print("❌ Không có ID sản phẩm để test")
        return
    
    try:
        # Dữ liệu cập nhật
        update_data = {
            "name": "Updated Test Laptop",
            "price": 25000000
        }
        
        response = session.put(
            f"{BASE_URL}/products/{product_id}",
            json=update_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                product = result.get('product')
                print(f"✅ Cập nhật sản phẩm thành công: {product['name']}")
                print(f"  - Price: {product['price']:,} VND")
            else:
                print("❌ Lỗi API")
        elif response.status_code == 403:
            print("❌ Không có quyền truy cập (cần đăng nhập admin)")
        elif response.status_code == 404:
            print(f"❌ Không tìm thấy sản phẩm với ID = {product_id}")
        else:
            print("❌ Request thất bại!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")

def test_delete_product(product_id=None):
    """Test API xóa sản phẩm (cần admin authentication)"""
    print("\n=== Test Delete Product ===")
    
    if not product_id:
        print("❌ Không có ID sản phẩm để test")
        return
    
    try:
        response = session.delete(f"{BASE_URL}/products/{product_id}")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Xóa sản phẩm thành công: {result.get('message')}")
            else:
                print("❌ Lỗi API")
        elif response.status_code == 403:
            print("❌ Không có quyền truy cập (cần đăng nhập admin)")
        elif response.status_code == 404:
            print(f"❌ Không tìm thấy sản phẩm với ID = {product_id}")
        else:
            print("❌ Request thất bại!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")

def main():
    """Chạy tất cả các test"""
    print("🚀 Bắt đầu test API endpoints...")
    print(f"Base URL: {BASE_URL}")
    
    # Test các API không cần authentication
    test_get_products()
    test_get_products_with_filters()
    product_id = test_get_product_detail()  # Lấy ID thực tế
    test_get_brands()
    test_get_categories()
    test_search_suggest()
    test_compare_data()
    
    # Test các API cần admin authentication
    print("\n" + "="*50)
    print("🔒 TEST CÁC API CẦN ADMIN AUTHENTICATION")
    print("="*50)
    
    # Đăng nhập admin trước
    if login_admin():
        test_create_product()
        test_update_product(product_id)  # Sử dụng ID thực tế
        test_delete_product(product_id)  # Sử dụng ID thực tế
        test_upload_image()
    else:
        print("❌ Không thể đăng nhập admin, bỏ qua các test cần authentication")
        print("💡 Hãy đảm bảo:")
        print("   - Ứng dụng đang chạy (python app.py)")
        print("   - Đã tạo admin user (python manage_data.py)")
        print("   - Thông tin đăng nhập: admin/admin123")
    
    print("\n✅ Hoàn thành test!")
    print("\n📝 Lưu ý:")
    print("- Các API GET không cần authentication")
    print("- Các API POST/PUT/DELETE cần đăng nhập với quyền admin")
    print("- Để test đầy đủ, hãy đăng nhập admin trước khi chạy test")

if __name__ == "__main__":
    main()
