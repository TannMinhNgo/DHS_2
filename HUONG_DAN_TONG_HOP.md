# 📚 HƯỚNG DẪN TỔNG HỢP - LAPTOP RECOMMENDER SYSTEM

## 🚀 KHỞI ĐỘNG NHANH

### 1. Cài Đặt Dependencies
```bash
pip install -r requirements.txt
```

### 2. Thiết Lập Database và Dữ Liệu
```bash
python manage_data.py
```
Script sẽ tự động thiết lập đầy đủ hệ thống (tạo dữ liệu mẫu, benchmark, hình ảnh, admin user).

### 3. Chạy Ứng Dụng
```bash
python app.py
```

### 4. Truy Cập
- **Website**: http://localhost:5000
- **Admin Panel**: http://localhost:5000/admin
- **API Documentation**: Xem file `API_DOCUMENTATION.md`

## 📋 THÔNG TIN ĐĂNG NHẬP MẶC ĐỊNH

### Admin
- **Username**: admin
- **Password**: admin123
- **Email**: admin@laptop.com

### Test Users
- **Username**: user1, **Password**: user123
- **Username**: test, **Password**: test123

---

## 🛠️ QUẢN LÝ DỮ LIỆU

### File `manage_data.py` - Script Tổng Hợp
Script tự động thiết lập toàn bộ hệ thống:

```bash
python manage_data.py
```

**Tự động thực hiện:**
1. ✅ **Tạo dữ liệu mẫu** - Tạo 24 laptop mẫu
2. ✅ **Cập nhật benchmark** - Thêm dữ liệu hiệu năng chi tiết
3. ✅ **Cập nhật hình ảnh** - Tự động gán hình ảnh cho laptop
4. ✅ **Tạo admin user** - Tạo tài khoản admin (admin/admin123)
5. ✅ **Hiển thị thống kê** - Thống kê database sau khi hoàn thành

### Database Migration
```bash
python migrate_database_indexes.py
```
Thêm indexes để cải thiện performance database.

---

## 🌐 API ENDPOINTS

### Upload Hình Ảnh
```bash
POST /api/upload-image
Content-Type: multipart/form-data
```

### Quản Lý Sản Phẩm
```bash
GET    /api/products          # Lấy danh sách
POST   /api/products          # Tạo mới (admin)
GET    /api/products/{id}     # Chi tiết
PUT    /api/products/{id}     # Cập nhật (admin)
DELETE /api/products/{id}     # Xóa (admin)
```

### API Hỗ Trợ
```bash
GET /api/brands              # Danh sách thương hiệu
GET /api/categories          # Danh sách danh mục
GET /api/search_suggest      # Tìm kiếm gợi ý
GET /api/compare_data        # Dữ liệu so sánh
```

### Test API
```bash
python test_api_endpoints.py
```

---

## 🎯 TÍNH NĂNG CHÍNH

### ✅ Đã Hoàn Thành
- ✅ Web API cho upload hình ảnh và quản lý sản phẩm
- ✅ Không cần Firebase - sử dụng local storage
- ✅ RESTful API endpoints
- ✅ Validation và resize hình ảnh tự động
- ✅ Quản lý dữ liệu tổng hợp
- ✅ Tài liệu API đầy đủ
- ✅ Test scripts

### 🎯 Tính Năng API
- **Upload hình ảnh** với validation và resize
- **CRUD operations** cho sản phẩm
- **Filter và search** sản phẩm
- **Phân trang** dữ liệu
- **Error handling** chuẩn
- **Authentication** cho admin

---

## 🔐 HỆ THỐNG ĐĂNG NHẬP/ĐĂNG KÝ

### ✅ Tính Năng Đã Có
- **Đăng ký tài khoản** với validation đầy đủ
- **Đăng nhập** với form đẹp mắt
- **Quản lý tài khoản** với dropdown menu
- **Trang hồ sơ cá nhân** với thống kê
- **Yêu thích laptop** và so sánh
- **Đăng xuất an toàn**

### 🔒 Bảo Mật
- **Validation**: Username, email, password
- **Mật khẩu**: Hash bằng werkzeug.security
- **Session**: Sử dụng Flask-Login
- **CSRF Protection**: Bảo vệ khỏi CSRF attacks (đã sửa lỗi 400)
- **Rate Limiting**: Giới hạn số lần đăng nhập
- **Forms**: Sử dụng Flask-WTF với validation đầy đủ

---

## 🛠️ HỆ THỐNG QUẢN TRỊ (ADMIN)

### ✅ Tính Năng Admin
1. **Dashboard Admin** - Quản lý tổng quan hệ thống
2. **CRUD Laptop** - Thêm/Sửa/Xóa laptop
3. **Upload hình ảnh** - Quản lý hình ảnh laptop
4. **Phân quyền** - Chỉ admin mới có quyền truy cập
5. **Giao diện đẹp** - Responsive và user-friendly

### 🎯 Cách Sử Dụng Admin
1. **Truy cập**: http://localhost:5000/admin
2. **Đăng nhập**: admin/admin123
3. **Dashboard**: Xem thống kê tổng quan
4. **Quản lý laptop**: Thêm/sửa/xóa laptop
5. **Upload hình ảnh**: Quản lý hình ảnh sản phẩm

### 📊 Giao Diện Dashboard
- **Thống kê laptop**: Tổng số laptop trong hệ thống
- **Thống kê người dùng**: Số lượng user đã đăng ký
- **Thống kê yêu thích**: Tổng số laptop được yêu thích
- **Thống kê thương hiệu**: Số lượng thương hiệu khác nhau

---

## 📊 TRANG SO SÁNH LAPTOP

### ✅ Tính Năng So Sánh
1. **So sánh thời gian dùng pin** 🔋
2. **So sánh điểm số CPU** (dùng pin vs cắm sạc) 🖥️
3. **So sánh điểm số GPU** (dùng pin vs cắm sạc) 🎮
4. **Bảng so sánh chi tiết** 📊

### 🎯 Cách Sử Dụng
1. **Truy cập**: http://localhost:5000/compare?id=1&id=2
2. **Chuyển đổi dữ liệu**: Nhấn nút "Dùng pin"/"Cắm sạc"
3. **Sắp xếp**: Tăng dần/Giảm dần theo tiêu chí
4. **Tương tác**: Progress bars thay đổi real-time

### 📈 Dữ Liệu Benchmark
- **Thông tin pin**: Dung lượng, thời gian văn phòng/gaming
- **Điểm số CPU**: Single/Multi Core (cắm sạc/dùng pin)
- **Điểm số GPU**: Score (cắm sạc/dùng pin)

---

## 🖼️ QUẢN LÝ HÌNH ẢNH

### ✅ Kết Quả Đã Đạt Được
- **24/24 laptop** đã có hình ảnh thật
- **0 placeholder** còn lại
- **0 laptop** thiếu hình ảnh

### 🛠️ Scripts Hỗ Trợ
- **`manage_data.py`**: Tự động cập nhật tất cả hình ảnh
- **Mapping thông minh**: Theo tên laptop và từ khóa
- **Hỗ trợ nhiều định dạng**: .webp, .jpg, .png, .jpeg

### 📁 Cấu Trúc Hình Ảnh
```
static/images/
├── tuff15_1.webp          # ASUS TUF Gaming F15
├── victus16_1.webp        # HP Victus 16
├── msikatana15_1.webp     # MSI Katana 15
├── legion5_1.webp         # Lenovo Legion 5
└── ... (24 hình ảnh)
```

---

## 🔧 CẢI THIỆN DỰ ÁN

### ✅ Đã Hoàn Thành
1. **🗂️ Dọn dẹp**: Xóa 11 file không cần thiết
2. **🗄️ Database**: Thêm 13 indexes, tối ưu queries
3. **🔒 Bảo mật**: CSRF, Rate Limiting, Input Validation
4. **🛠️ Error Handling**: Logging, Error pages
5. **🔧 Utils**: Tạo utility functions
6. **📦 Dependencies**: Cập nhật và sửa lỗi version

### 📊 Kết Quả
- **Performance**: Database queries nhanh hơn nhờ indexes
- **Security**: Bảo vệ khỏi CSRF, rate limiting, input validation
- **User Experience**: Error pages thân thiện, validation rõ ràng
- **Maintainability**: Code được tổ chức tốt hơn, dễ bảo trì

---

## 📁 CẤU TRÚC FILE

```
laptop_recommender/
├── app.py                   # Ứng dụng chính
├── models.py               # Database models (đã cải thiện)
├── forms.py                # Form validation (mới)
├── utils.py                # Utility functions (mới)
├── config.py               # Configuration (đã cải thiện)
├── manage_data.py          # Quản lý dữ liệu (tổng hợp)
├── migrate_database_indexes.py  # Database migration (mới)
├── test_api_endpoints.py   # Test API
├── API_DOCUMENTATION.md    # Tài liệu API
├── CAI_THIEN_DU_AN.md      # Tài liệu cải thiện
├── requirements.txt        # Dependencies (đã cập nhật)
├── static/
│   ├── css/
│   └── images/            # Hình ảnh sản phẩm (24 hình)
└── templates/             # HTML templates
    ├── errors/            # Error pages (mới)
    │   ├── 404.html
    │   └── 500.html
    └── ... (các template khác)
```

---

## 🚨 LƯU Ý QUAN TRỌNG

### ⚠️ Lưu Ý
1. **Hình ảnh** được lưu trong `static/images/`
2. **Database** sử dụng SQLite (có thể chuyển sang PostgreSQL/MySQL)
3. **Admin functions** yêu cầu đăng nhập với quyền admin
4. **API responses** đều có format JSON chuẩn
5. **File upload** hỗ trợ PNG, JPG, JPEG, GIF, WEBP

### 🔧 Tùy Chỉnh
- Có thể điều chỉnh rate limits trong `config.py`
- Có thể thay đổi image quality trong `utils.py`
- Có thể thêm validation rules trong `forms.py`

---

## 🔍 TROUBLESHOOTING

### Lỗi Thường Gặp

1. **Không thể truy cập admin:**
   - Kiểm tra đã đăng nhập chưa
   - Kiểm tra user có role='admin' không
   - Chạy `python manage_data.py`

2. **Upload hình ảnh lỗi:**
   - Kiểm tra thư mục static/images có tồn tại
   - Kiểm tra quyền ghi file
   - Kiểm tra kích thước file < 10MB

3. **API không hoạt động:**
   - Đảm bảo server đang chạy
   - Kiểm tra port 5000
   - Chạy `python test_api_endpoints.py`

4. **Lỗi 400 khi đăng nhập (CSRF):**
   - Đã sửa: Thêm CSRF token vào forms
   - Templates đã được cập nhật với `{{ form.hidden_tag() }}`
   - Sử dụng Flask-WTF forms thay vì HTML thuần

### Debug
```bash
# Kiểm tra admin user
python -c "from app import create_app; from models import User; app = create_app(); app.app_context().push(); admin = User.query.filter_by(role='admin').first(); print(admin.username if admin else 'No admin')"

# Kiểm tra database
python manage_data.py

# Test API
python test_api_endpoints.py
```

---

## 📞 HỖ TRỢ

Nếu gặp vấn đề, hãy kiểm tra:
1. Đã cài đặt đầy đủ dependencies chưa
2. Database đã được tạo chưa (`python manage_data.py`)
3. Port 5000 có bị chiếm dụng không
4. File hình ảnh có trong thư mục `static/images/` không

---

## 🎉 KẾT LUẬN

Dự án Laptop Recommender System đã được cải thiện toàn diện với:
- **11 files** đã được xóa (dọn dẹp)
- **13 database indexes** đã được thêm
- **5 file mới** được tạo (forms, utils, error pages, migration)
- **Bảo mật** được tăng cường đáng kể
- **Performance** cải thiện rõ rệt
- **Code quality** được nâng cao

Dự án giờ đây sẵn sàng cho production với các tính năng bảo mật, hiệu suất và khả năng bảo trì tốt hơn nhiều! 🚀