from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user', index=True)  # 'user' hoặc 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    favorites = db.relationship("Favorite", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Chuyển đổi user thành dictionary cho API"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Laptop(db.Model):
    __tablename__ = "laptops"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    brand = db.Column(db.String(80), nullable=False, index=True)
    cpu = db.Column(db.String(120), nullable=False)
    ram_gb = db.Column(db.Integer, nullable=False, index=True)
    gpu = db.Column(db.String(120), nullable=True)
    storage = db.Column(db.String(120), nullable=False)
    screen = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Integer, nullable=False, index=True)  # VND
    category = db.Column(db.String(80), nullable=False, index=True)  # office, student, gaming, design, dev
    image_url = db.Column(db.String(500), nullable=True)
    
    # Thông tin pin
    battery_capacity = db.Column(db.Integer, nullable=True)  # Wh
    battery_life_office = db.Column(db.Integer, nullable=True)  # phút
    battery_life_gaming = db.Column(db.Integer, nullable=True)  # phút
    
    # Điểm số CPU (Geekbench 6)
    cpu_single_core_plugged = db.Column(db.Integer, nullable=True)
    cpu_multi_core_plugged = db.Column(db.Integer, nullable=True)
    cpu_single_core_battery = db.Column(db.Integer, nullable=True)
    cpu_multi_core_battery = db.Column(db.Integer, nullable=True)
    
    # Điểm số GPU (3DMark hoặc Geekbench)
    gpu_score_plugged = db.Column(db.Integer, nullable=True)
    gpu_score_battery = db.Column(db.Integer, nullable=True)

    favorites = db.relationship("Favorite", back_populates="laptop", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Chuyển đổi laptop thành dictionary cho API"""
        return {
            'id': self.id,
            'name': self.name,
            'brand': self.brand,
            'cpu': self.cpu,
            'ram_gb': self.ram_gb,
            'gpu': self.gpu,
            'storage': self.storage,
            'screen': self.screen,
            'price': self.price,
            'category': self.category,
            'image_url': self.image_url,
            'battery_capacity': self.battery_capacity,
            'battery_life_office': self.battery_life_office,
            'battery_life_gaming': self.battery_life_gaming,
            'cpu_single_core_plugged': self.cpu_single_core_plugged,
            'cpu_multi_core_plugged': self.cpu_multi_core_plugged,
            'cpu_single_core_battery': self.cpu_single_core_battery,
            'cpu_multi_core_battery': self.cpu_multi_core_battery,
            'gpu_score_plugged': self.gpu_score_plugged,
            'gpu_score_battery': self.gpu_score_battery
        }
    
    @staticmethod
    def get_filtered_laptops(brand=None, price_min=None, price_max=None, 
                           ram_gb=None, category=None, search=None, 
                           page=1, per_page=20):
        """Tối ưu hóa query với filters và pagination"""
        query = Laptop.query
        
        if brand:
            query = query.filter(Laptop.brand == brand)
        if price_min is not None:
            query = query.filter(Laptop.price >= price_min)
        if price_max is not None:
            query = query.filter(Laptop.price <= price_max)
        if ram_gb is not None:
            query = query.filter(Laptop.ram_gb >= ram_gb)
        if category:
            query = query.filter(Laptop.category == category)
        if search:
            query = query.filter(Laptop.name.contains(search))
        
        return query.paginate(page=page, per_page=per_page, error_out=False)

class Favorite(db.Model):
    __tablename__ = "favorites"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    laptop_id = db.Column(db.Integer, db.ForeignKey("laptops.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Composite unique constraint để tránh duplicate favorites
    __table_args__ = (db.UniqueConstraint('user_id', 'laptop_id', name='unique_user_laptop_favorite'),)

    user = db.relationship("User", back_populates="favorites")
    laptop = db.relationship("Laptop", back_populates="favorites")
    
    def to_dict(self):
        """Chuyển đổi favorite thành dictionary cho API"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'laptop_id': self.laptop_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'laptop': self.laptop.to_dict() if self.laptop else None
        }
