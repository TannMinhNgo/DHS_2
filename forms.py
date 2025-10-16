#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Forms cho validation dữ liệu đầu vào
"""

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, SelectField, FileField, PasswordField, EmailField
from wtforms.validators import DataRequired, Length, NumberRange, Email, ValidationError, Optional
from wtforms.widgets import TextArea

class LaptopForm(FlaskForm):
    """Form cho tạo/cập nhật laptop"""
    name = StringField('Tên laptop', validators=[
        DataRequired(message='Tên laptop không được để trống'),
        Length(min=3, max=200, message='Tên laptop phải từ 3-200 ký tự')
    ])
    
    brand = SelectField('Thương hiệu', validators=[
        DataRequired(message='Vui lòng chọn thương hiệu')
    ], choices=[
        ('', 'Chọn thương hiệu'),
        ('ASUS', 'ASUS'),
        ('HP', 'HP'),
        ('Dell', 'Dell'),
        ('Lenovo', 'Lenovo'),
        ('MSI', 'MSI'),
        ('Acer', 'Acer'),
        ('Apple', 'Apple'),
        ('Samsung', 'Samsung'),
        ('LG', 'LG')
    ])
    
    cpu = StringField('CPU', validators=[
        DataRequired(message='CPU không được để trống'),
        Length(min=3, max=120, message='CPU phải từ 3-120 ký tự')
    ])
    
    ram_gb = IntegerField('RAM (GB)', validators=[
        DataRequired(message='RAM không được để trống'),
        NumberRange(min=1, max=128, message='RAM phải từ 1-128 GB')
    ])
    
    gpu = StringField('GPU', validators=[
        Optional(),
        Length(max=120, message='GPU không được quá 120 ký tự')
    ])
    
    storage = StringField('Ổ cứng', validators=[
        DataRequired(message='Ổ cứng không được để trống'),
        Length(min=3, max=120, message='Ổ cứng phải từ 3-120 ký tự')
    ])
    
    screen = StringField('Màn hình', validators=[
        DataRequired(message='Màn hình không được để trống'),
        Length(min=3, max=120, message='Màn hình phải từ 3-120 ký tự')
    ])
    
    price = IntegerField('Giá (VND)', validators=[
        DataRequired(message='Giá không được để trống'),
        NumberRange(min=1000000, max=100000000, message='Giá phải từ 1-100 triệu VND')
    ])
    
    category = SelectField('Danh mục', validators=[
        DataRequired(message='Vui lòng chọn danh mục')
    ], choices=[
        ('', 'Chọn danh mục'),
        ('gaming', 'Gaming'),
        ('design', 'Design'),
        ('dev', 'Development'),
        ('student', 'Student'),
        ('office', 'Office')
    ])
    
    # Thông tin pin
    battery_capacity = IntegerField('Dung lượng pin (Wh)', validators=[
        Optional(),
        NumberRange(min=10, max=200, message='Dung lượng pin phải từ 10-200 Wh')
    ])
    
    battery_life_office = IntegerField('Thời lượng pin văn phòng (phút)', validators=[
        Optional(),
        NumberRange(min=60, max=1440, message='Thời lượng pin phải từ 1-24 giờ')
    ])
    
    battery_life_gaming = IntegerField('Thời lượng pin gaming (phút)', validators=[
        Optional(),
        NumberRange(min=30, max=720, message='Thời lượng pin gaming phải từ 30 phút-12 giờ')
    ])
    
    # Điểm số CPU
    cpu_single_core_plugged = IntegerField('CPU Single Core (cắm sạc)', validators=[
        Optional(),
        NumberRange(min=500, max=5000, message='Điểm CPU phải từ 500-5000')
    ])
    
    cpu_multi_core_plugged = IntegerField('CPU Multi Core (cắm sạc)', validators=[
        Optional(),
        NumberRange(min=1000, max=20000, message='Điểm CPU Multi Core phải từ 1000-20000')
    ])
    
    cpu_single_core_battery = IntegerField('CPU Single Core (pin)', validators=[
        Optional(),
        NumberRange(min=400, max=4000, message='Điểm CPU pin phải từ 400-4000')
    ])
    
    cpu_multi_core_battery = IntegerField('CPU Multi Core (pin)', validators=[
        Optional(),
        NumberRange(min=800, max=16000, message='Điểm CPU Multi Core pin phải từ 800-16000')
    ])
    
    # Điểm số GPU
    gpu_score_plugged = IntegerField('GPU Score (cắm sạc)', validators=[
        Optional(),
        NumberRange(min=500, max=50000, message='Điểm GPU phải từ 500-50000')
    ])
    
    gpu_score_battery = IntegerField('GPU Score (pin)', validators=[
        Optional(),
        NumberRange(min=300, max=40000, message='Điểm GPU pin phải từ 300-40000')
    ])

class UserForm(FlaskForm):
    """Form cho tạo/cập nhật user"""
    username = StringField('Tên đăng nhập', validators=[
        DataRequired(message='Tên đăng nhập không được để trống'),
        Length(min=3, max=80, message='Tên đăng nhập phải từ 3-80 ký tự')
    ])
    
    email = EmailField('Email', validators=[
        DataRequired(message='Email không được để trống'),
        Email(message='Email không hợp lệ'),
        Length(max=120, message='Email không được quá 120 ký tự')
    ])
    
    password = PasswordField('Mật khẩu', validators=[
        DataRequired(message='Mật khẩu không được để trống'),
        Length(min=6, max=128, message='Mật khẩu phải từ 6-128 ký tự')
    ])
    
    role = SelectField('Vai trò', validators=[
        DataRequired(message='Vui lòng chọn vai trò')
    ], choices=[
        ('user', 'User'),
        ('admin', 'Admin')
    ])

class LoginForm(FlaskForm):
    """Form đăng nhập"""
    username = StringField('Tên đăng nhập', validators=[
        DataRequired(message='Tên đăng nhập không được để trống')
    ])
    
    password = PasswordField('Mật khẩu', validators=[
        DataRequired(message='Mật khẩu không được để trống')
    ])

class RegisterForm(FlaskForm):
    """Form đăng ký"""
    username = StringField('Tên đăng nhập', validators=[
        DataRequired(message='Tên đăng nhập không được để trống'),
        Length(min=3, max=80, message='Tên đăng nhập phải từ 3-80 ký tự')
    ])
    
    email = EmailField('Email', validators=[
        DataRequired(message='Email không được để trống'),
        Email(message='Email không hợp lệ')
    ])
    
    password = PasswordField('Mật khẩu', validators=[
        DataRequired(message='Mật khẩu không được để trống'),
        Length(min=6, max=128, message='Mật khẩu phải từ 6-128 ký tự')
    ])
    
    confirm_password = PasswordField('Xác nhận mật khẩu', validators=[
        DataRequired(message='Vui lòng xác nhận mật khẩu')
    ])
    
    def validate_confirm_password(self, field):
        if field.data != self.password.data:
            raise ValidationError('Mật khẩu xác nhận không khớp')

class ImageUploadForm(FlaskForm):
    """Form upload hình ảnh"""
    image = FileField('Hình ảnh', validators=[
        DataRequired(message='Vui lòng chọn file hình ảnh')
    ])
    
    def validate_image(self, field):
        if field.data:
            # Kiểm tra định dạng file
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            filename = field.data.filename.lower()
            if not any(filename.endswith(ext) for ext in allowed_extensions):
                raise ValidationError('Chỉ chấp nhận file hình ảnh: PNG, JPG, JPEG, GIF, WEBP')
            
            # Kiểm tra kích thước file (10MB)
            field.data.seek(0, 2)  # Di chuyển đến cuối file
            file_size = field.data.tell()
            field.data.seek(0)  # Di chuyển về đầu file
            if file_size > 10 * 1024 * 1024:  # 10MB
                raise ValidationError('Kích thước file không được vượt quá 10MB')

class SearchForm(FlaskForm):
    """Form tìm kiếm"""
    q = StringField('Tìm kiếm', validators=[
        Optional(),
        Length(max=100, message='Từ khóa tìm kiếm không được quá 100 ký tự')
    ])
    
    brand = SelectField('Thương hiệu', validators=[Optional()])
    category = SelectField('Danh mục', validators=[Optional()])
    price_min = IntegerField('Giá tối thiểu', validators=[
        Optional(),
        NumberRange(min=0, message='Giá tối thiểu không được âm')
    ])
    price_max = IntegerField('Giá tối đa', validators=[
        Optional(),
        NumberRange(min=0, message='Giá tối đa không được âm')
    ])
    ram_gb = IntegerField('RAM tối thiểu (GB)', validators=[
        Optional(),
        NumberRange(min=1, max=128, message='RAM phải từ 1-128 GB')
    ])
