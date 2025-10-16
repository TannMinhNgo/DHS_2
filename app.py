from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import uuid
import logging
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from models import db, User, Laptop, Favorite
from forms import LaptopForm, UserForm, LoginForm, RegisterForm, ImageUploadForm, SearchForm
from utils import save_uploaded_image, validate_price_range, sanitize_search_query, format_price, calculate_performance_score
from config import Config
from PIL import Image
import io
import anthropic
from chatbot_service import ChatbotService

def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config.from_object(Config)
    db.init_app(app)
    
    # Cấu hình logging
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)
    
    # CSRF Protection
    csrf = CSRFProtect(app)
    
    # Rate Limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )

    login_manager = LoginManager(app)
    login_manager.login_view = "login"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f'404 Error: {request.url}')
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'500 Error: {error}')
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(413)
    def too_large(error):
        app.logger.warning(f'413 Error: File too large - {request.url}')
        return jsonify({'error': 'File quá lớn. Kích thước tối đa 10MB.'}), 413

    @app.route("/")
    def index():
        brands = db.session.query(Laptop.brand).distinct().all()
        return render_template("index.html", brands=[b[0] for b in brands])

    @app.route("/laptops")
    def laptops():
        # Lấy parameters
        brand = request.args.get("brand")
        price_min = request.args.get("price_min", type=int)
        price_max = request.args.get("price_max", type=int)
        ram_gb = request.args.get("ram_gb", type=int)
        category = request.args.get("category")
        search = sanitize_search_query(request.args.get("q", ""))
        page = request.args.get("page", 1, type=int)
        
        # Validate price range
        if not validate_price_range(price_min, price_max):
            flash("Giá tối thiểu không được lớn hơn giá tối đa", "warning")
            price_min = None
            price_max = None
        
        # Sử dụng method tối ưu hóa
        laptops_pagination = Laptop.get_filtered_laptops(
            brand=brand,
            price_min=price_min,
            price_max=price_max,
            ram_gb=ram_gb,
            category=category,
            search=search,
            page=page,
            per_page=20
        )
        
        brands = db.session.query(Laptop.brand).distinct().all()
        return render_template("laptops.html", 
                             items=laptops_pagination.items, 
                             pagination=laptops_pagination,
                             brands=[b[0] for b in brands])

    @app.route("/laptop/<int:laptop_id>")
    def laptop_detail(laptop_id):
        item = Laptop.query.get_or_404(laptop_id)
        
        # Check if current user has this laptop in favorites
        is_favorite = False
        if current_user.is_authenticated:
            is_favorite = Favorite.query.filter_by(
                user_id=current_user.id, 
                laptop_id=laptop_id
            ).first() is not None
        
        return render_template("laptop_detail.html", item=item, is_favorite=is_favorite)

    @app.route("/compare")
    def compare():
        ids = request.args.getlist("id", type=int)
        items = Laptop.query.filter(Laptop.id.in_(ids)).all() if ids else []
        
        # Tính toán thống kê so sánh
        if len(items) >= 2:
            # Tìm laptop có hiệu năng tốt nhất
            best_performance = max(items, key=lambda x: calculate_performance_score(x))
            
            # Tìm laptop có giá trị tốt nhất
            best_value = min(items, key=lambda x: x.price)
            
            # Tìm laptop có giá cao nhất và thấp nhất
            price_range = {
                'min': min(items, key=lambda x: x.price),
                'max': max(items, key=lambda x: x.price)
            }
            
            # Phân tích theo nhu cầu
            category_analysis = {}
            for item in items:
                if item.category not in category_analysis:
                    category_analysis[item.category] = []
                category_analysis[item.category].append(item)
            
            # Nhận xét theo tiêu chí
            # Điểm hiệu năng tổng hợp dùng calculate_performance_score (đã có)
            # Tỷ lệ giá/hiệu năng: price_performance = price / (score + 1) để tránh chia 0
            scored = [(it, calculate_performance_score(it)) for it in items]
            best_price_performance = min(scored, key=lambda t: (t[0].price / (t[1] + 1)))[0]
            
            return render_template("compare.html", 
                                 items=items, 
                                 best_performance=best_performance,
                                 best_value=best_value,
                                 price_range=price_range,
                                 category_analysis=category_analysis,
                                 best_price_performance=best_price_performance)
        
        return render_template("compare.html", items=items)

    @app.route("/api/compare_data")
    def api_compare_data():
        """API để lấy dữ liệu so sánh theo mode"""
        laptop_ids = request.args.getlist('id')
        mode = request.args.get('mode', 'plugged')  # plugged hoặc battery
        
        items = []
        for laptop_id in laptop_ids:
            laptop = Laptop.query.get(laptop_id)
            if laptop:
                items.append(laptop)
        
        # Chuẩn bị dữ liệu theo mode
        data = {
            'cpu_single_core': [],
            'cpu_multi_core': [],
            'gpu_score': []
        }
        
        for laptop in items:
            if mode == 'battery':
                data['cpu_single_core'].append({
                    'name': laptop.name,
                    'score': laptop.cpu_single_core_battery or 0
                })
                data['cpu_multi_core'].append({
                    'name': laptop.name,
                    'score': laptop.cpu_multi_core_battery or 0
                })
                data['gpu_score'].append({
                    'name': laptop.name,
                    'score': laptop.gpu_score_battery or 0
                })
            else:  # plugged
                data['cpu_single_core'].append({
                    'name': laptop.name,
                    'score': laptop.cpu_single_core_plugged or 0
                })
                data['cpu_multi_core'].append({
                    'name': laptop.name,
                    'score': laptop.cpu_multi_core_plugged or 0
                })
                data['gpu_score'].append({
                    'name': laptop.name,
                    'score': laptop.gpu_score_plugged or 0
                })
        
        return jsonify(data)

    # Admin routes
    def admin_required(f):
        """Decorator để kiểm tra quyền admin"""
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != 'admin':
                flash('Bạn không có quyền truy cập trang này!', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function

    @app.route("/admin")
    @admin_required
    def admin_dashboard():
        """Trang dashboard admin"""
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        # Lấy danh sách laptop với phân trang
        pagination = Laptop.query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        laptops = pagination.items
        
        # Thống kê
        stats = {
            'total_laptops': Laptop.query.count(),
            'total_users': User.query.count(),
            'total_favorites': Favorite.query.count(),
            'total_brands': db.session.query(Laptop.brand).distinct().count()
        }
        
        # Danh sách thương hiệu
        brands = [brand[0] for brand in db.session.query(Laptop.brand).distinct().all()]
        
        return render_template('admin/dashboard.html', 
                             laptops=laptops, 
                             pagination=pagination,
                             stats=stats,
                             brands=brands)

    @app.route("/admin/laptop/add", methods=["GET", "POST"])
    @admin_required
    def admin_add_laptop():
        """Thêm laptop mới"""
        if request.method == "POST":
            try:
                # Lấy dữ liệu từ form
                laptop = Laptop(
                    name=request.form['name'],
                    brand=request.form['brand'],
                    cpu=request.form['cpu'],
                    ram_gb=int(request.form['ram_gb']),
                    gpu=request.form['gpu'] or None,
                    storage=request.form['storage'],
                    screen=request.form['screen'],
                    price=int(request.form['price']),
                    category=request.form['category'],
                    battery_capacity=int(request.form['battery_capacity']) if request.form['battery_capacity'] else None,
                    battery_life_office=int(request.form['battery_life_office']) if request.form['battery_life_office'] else None,
                    battery_life_gaming=int(request.form['battery_life_gaming']) if request.form['battery_life_gaming'] else None,
                    cpu_single_core_plugged=int(request.form['cpu_single_core_plugged']) if request.form['cpu_single_core_plugged'] else None,
                    cpu_multi_core_plugged=int(request.form['cpu_multi_core_plugged']) if request.form['cpu_multi_core_plugged'] else None,
                    cpu_single_core_battery=int(request.form['cpu_single_core_battery']) if request.form['cpu_single_core_battery'] else None,
                    cpu_multi_core_battery=int(request.form['cpu_multi_core_battery']) if request.form['cpu_multi_core_battery'] else None,
                    gpu_score_plugged=int(request.form['gpu_score_plugged']) if request.form['gpu_score_plugged'] else None,
                    gpu_score_battery=int(request.form['gpu_score_battery']) if request.form['gpu_score_battery'] else None
                )
                
                # Xử lý upload hình ảnh
                if 'image' in request.files:
                    file = request.files['image']
                    if file and file.filename:
                        filename = secure_filename(file.filename)
                        # Tạo tên file unique
                        import time
                        timestamp = int(time.time())
                        name_without_ext = os.path.splitext(filename)[0]
                        ext = os.path.splitext(filename)[1]
                        unique_filename = f"{name_without_ext}_{timestamp}{ext}"
                        
                        # Lưu file
                        file_path = os.path.join('static', 'images', unique_filename)
                        file.save(file_path)
                        laptop.image_url = f'/static/images/{unique_filename}'
                
                db.session.add(laptop)
                db.session.commit()
                
                flash(f'Đã thêm laptop "{laptop.name}" thành công!', 'success')
                return redirect(url_for('admin_dashboard'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi khi thêm laptop: {str(e)}', 'danger')
        
        return render_template('admin/laptop_form.html', laptop=None)

    @app.route("/admin/laptop/<int:laptop_id>/edit", methods=["GET", "POST"])
    @admin_required
    def admin_edit_laptop(laptop_id):
        """Sửa laptop"""
        laptop = Laptop.query.get_or_404(laptop_id)
        
        if request.method == "POST":
            try:
                # Cập nhật dữ liệu
                laptop.name = request.form['name']
                laptop.brand = request.form['brand']
                laptop.cpu = request.form['cpu']
                laptop.ram_gb = int(request.form['ram_gb'])
                laptop.gpu = request.form['gpu'] or None
                laptop.storage = request.form['storage']
                laptop.screen = request.form['screen']
                laptop.price = int(request.form['price'])
                laptop.category = request.form['category']
                laptop.battery_capacity = int(request.form['battery_capacity']) if request.form['battery_capacity'] else None
                laptop.battery_life_office = int(request.form['battery_life_office']) if request.form['battery_life_office'] else None
                laptop.battery_life_gaming = int(request.form['battery_life_gaming']) if request.form['battery_life_gaming'] else None
                laptop.cpu_single_core_plugged = int(request.form['cpu_single_core_plugged']) if request.form['cpu_single_core_plugged'] else None
                laptop.cpu_multi_core_plugged = int(request.form['cpu_multi_core_plugged']) if request.form['cpu_multi_core_plugged'] else None
                laptop.cpu_single_core_battery = int(request.form['cpu_single_core_battery']) if request.form['cpu_single_core_battery'] else None
                laptop.cpu_multi_core_battery = int(request.form['cpu_multi_core_battery']) if request.form['cpu_multi_core_battery'] else None
                laptop.gpu_score_plugged = int(request.form['gpu_score_plugged']) if request.form['gpu_score_plugged'] else None
                laptop.gpu_score_battery = int(request.form['gpu_score_battery']) if request.form['gpu_score_battery'] else None
                
                # Xử lý upload hình ảnh mới
                if 'image' in request.files:
                    file = request.files['image']
                    if file and file.filename:
                        filename = secure_filename(file.filename)
                        import time
                        timestamp = int(time.time())
                        name_without_ext = os.path.splitext(filename)[0]
                        ext = os.path.splitext(filename)[1]
                        unique_filename = f"{name_without_ext}_{timestamp}{ext}"
                        
                        file_path = os.path.join('static', 'images', unique_filename)
                        file.save(file_path)
                        laptop.image_url = f'/static/images/{unique_filename}'
                
                db.session.commit()
                flash(f'Đã cập nhật laptop "{laptop.name}" thành công!', 'success')
                return redirect(url_for('admin_dashboard'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi khi cập nhật laptop: {str(e)}', 'danger')
        
        return render_template('admin/laptop_form.html', laptop=laptop)

    @app.route("/admin/laptop/<int:laptop_id>/delete", methods=["POST"])
    @admin_required
    def admin_delete_laptop(laptop_id):
        """Xóa laptop (yêu cầu xác nhận)"""
        laptop = Laptop.query.get_or_404(laptop_id)
        laptop_name = laptop.name
        
        # Kiểm tra xác nhận từ form
        confirm = request.form.get('confirm')
        if not confirm:
            flash('Bạn chưa xác nhận xóa. Thao tác đã bị hủy.', 'warning')
            return redirect(url_for('admin_dashboard'))
        
        try:
            db.session.delete(laptop)
            db.session.commit()
            flash(f'Đã xóa laptop "{laptop_name}" thành công!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi xóa laptop: {str(e)}', 'danger')
        
        return redirect(url_for('admin_dashboard'))

    def calculate_performance_score(laptop):
        """Tính điểm hiệu năng cho laptop"""
        score = 0
        
        # Điểm cho CPU
        if 'H' in laptop.cpu or 'HX' in laptop.cpu or 'HK' in laptop.cpu:
            score += 30
        elif 'P' in laptop.cpu:
            score += 20
        else:
            score += 10
        
        # Điểm cho RAM
        if laptop.ram_gb >= 16:
            score += 25
        elif laptop.ram_gb >= 8:
            score += 15
        else:
            score += 5
        
        # Điểm cho GPU
        if laptop.gpu:
            if 'rtx' in laptop.gpu.lower() or 'gtx' in laptop.gpu.lower():
                score += 30
            elif 'mx' in laptop.gpu.lower() or 'iris' in laptop.gpu.lower():
                score += 15
        
        # Điểm cho storage
        if 'ssd' in laptop.storage.lower():
            score += 15
        
        return score

    @app.route("/register", methods=["GET","POST"])
    def register():
        # Use WTForms for validation and CSRF
        form = RegisterForm()
        if form.validate_on_submit():
            username = form.username.data.strip()
            email = form.email.data.strip()
            password = form.password.data.strip()
            
            # Check duplicates
            if User.query.filter_by(username=username).first():
                flash("Tên đăng nhập đã tồn tại", "danger")
                return redirect(url_for("register"))
            if User.query.filter_by(email=email).first():
                flash("Email đã được sử dụng", "danger")
                return redirect(url_for("register"))
            
            # Create user
            try:
                u = User(username=username, email=email)
                u.set_password(password)
                db.session.add(u)
                db.session.commit()
                flash("Đăng ký thành công! Vui lòng đăng nhập.", "success")
                return redirect(url_for("login"))
            except Exception:
                db.session.rollback()
                flash("Có lỗi xảy ra khi đăng ký. Vui lòng thử lại.", "danger")
                return redirect(url_for("register"))
        
        # Render form with CSRF token
        return render_template("register.html", form=form)

    @app.route("/login", methods=["GET","POST"])
    @limiter.limit("5 per minute")
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            username = form.username.data.strip()
            password = form.password.data.strip()
            
            # Tìm user
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                login_user(user)
                app.logger.info(f'User {username} logged in successfully')
                flash(f"Chào mừng {user.username} quay trở lại!", "success")
                
                # Redirect về trang trước đó nếu có
                next_page = request.args.get('next')
                if next_page and next_page.startswith('/'):
                    return redirect(next_page)
                return redirect(url_for("index"))
            else:
                app.logger.warning(f'Failed login attempt for username: {username}')
                flash("Tên đăng nhập hoặc mật khẩu không đúng", "danger")
        
        return render_template("login.html", form=form)

    @app.route("/profile")
    @login_required
    def profile():
        favorites = Favorite.query.filter_by(user_id=current_user.id).all()
        favorites_count = len(favorites)
        compare_count = 0  # Có thể thêm logic đếm số lần so sánh sau
        
        return render_template("profile.html", 
                             favorites=favorites,
                             favorites_count=favorites_count,
                             compare_count=compare_count)

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Đã đăng xuất.", "info")
        return redirect(url_for("index"))

    @app.route("/favorites")
    @login_required
    def favorites():
        favs = Favorite.query.filter_by(user_id=current_user.id).all()
        items = [f.laptop for f in favs]
        return render_template("favorites.html", items=items)

    @app.route("/favorite/<int:laptop_id>", methods=["POST"])
    @login_required
    def add_favorite(laptop_id):
        try:
            # Check if laptop exists
            laptop = Laptop.query.get(laptop_id)
            if not laptop:
                flash("Laptop không tồn tại.", "error")
                return redirect(url_for("index"))
            
            # Check if already in favorites
            existing_favorite = Favorite.query.filter_by(user_id=current_user.id, laptop_id=laptop_id).first()
            if existing_favorite:
                flash("Laptop đã có trong danh sách yêu thích.", "info")
                return redirect(url_for("laptop_detail", laptop_id=laptop_id))
            
            # Add to favorites
            new_favorite = Favorite(user_id=current_user.id, laptop_id=laptop_id)
            db.session.add(new_favorite)
            db.session.commit()
            flash("Đã thêm vào yêu thích.", "success")
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error adding favorite: {e}")
            flash("Có lỗi xảy ra khi thêm vào yêu thích.", "error")
        
        return redirect(url_for("laptop_detail", laptop_id=laptop_id))

    @app.route("/favorite/<int:laptop_id>/remove", methods=["POST"])
    @login_required
    def remove_favorite(laptop_id):
        try:
            fav = Favorite.query.filter_by(user_id=current_user.id, laptop_id=laptop_id).first()
            if fav:
                db.session.delete(fav)
                db.session.commit()
                flash("Đã bỏ yêu thích.", "info")
            else:
                flash("Laptop không có trong danh sách yêu thích.", "warning")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error removing favorite: {e}")
            flash("Có lỗi xảy ra khi bỏ yêu thích.", "error")
        
        return redirect(url_for("favorites"))

    # Thuật toán gợi ý chi tiết theo profile nhu cầu
    @app.route("/recommend")
    def recommend():
        need = request.args.get("need")  # office, student, gaming, design, dev
        budget = request.args.get("budget", type=int)  # VND
        priority = request.args.get("priority", "balanced")  # performance, budget, balanced
        
        query = Laptop.query
        
        # Định nghĩa tiêu chí cho từng loại nhu cầu
        criteria = {
            "gaming": {
                "min_ram": 16,
                "cpu_series": ["H", "HX", "HK"],  # CPU hiệu năng cao
                "gpu_required": True,  # Yêu cầu GPU rời
                "min_price": 15000000,  # Tối thiểu 15 triệu
                "weight": {
                    "gpu": 0.3,
                    "cpu": 0.25,
                    "ram": 0.2,
                    "price": 0.15,
                    "storage": 0.1
                }
            },
            "design": {
                "min_ram": 16,
                "cpu_series": ["H", "HX", "HK", "P"],  # CPU hiệu năng cao hoặc P-series
                "gpu_required": True,
                "min_price": 20000000,  # Tối thiểu 20 triệu
                "weight": {
                    "gpu": 0.25,
                    "cpu": 0.25,
                    "ram": 0.2,
                    "screen": 0.2,
                    "price": 0.1
                }
            },
            "dev": {
                "min_ram": 16,
                "cpu_series": ["H", "HX", "HK", "P", "U"],  # Linh hoạt hơn
                "gpu_required": False,
                "min_price": 12000000,  # Tối thiểu 12 triệu
                "weight": {
                    "cpu": 0.3,
                    "ram": 0.25,
                    "storage": 0.2,
                    "price": 0.15,
                    "gpu": 0.1
                }
            },
            "student": {
                "min_ram": 8,
                "cpu_series": ["U", "P", "H"],  # Linh hoạt
                "gpu_required": False,
                "min_price": 8000000,  # Tối thiểu 8 triệu
                "weight": {
                    "price": 0.4,
                    "cpu": 0.25,
                    "ram": 0.2,
                    "storage": 0.15
                }
            },
            "office": {
                "min_ram": 8,
                "cpu_series": ["U", "P"],  # CPU tiết kiệm điện
                "gpu_required": False,
                "min_price": 6000000,  # Tối thiểu 6 triệu
                "weight": {
                    "price": 0.5,
                    "cpu": 0.2,
                    "ram": 0.2,
                    "storage": 0.1
                }
            }
        }
        
        if need and need in criteria:
            crit = criteria[need]
            
            # Áp dụng các bộ lọc cơ bản
            if crit["min_ram"]:
                query = query.filter(Laptop.ram_gb >= crit["min_ram"])
            
            if crit["gpu_required"]:
                # Lọc laptop có GPU rời (không phải Intel UHD, AMD Radeon Graphics)
                query = query.filter(
                    ~Laptop.gpu.like('%Intel UHD%'),
                    ~Laptop.gpu.like('%AMD Radeon Graphics%'),
                    ~Laptop.gpu.like('%Intel Graphics%')
                )
            
            if budget:
                query = query.filter(Laptop.price <= budget)
            elif crit["min_price"]:
                query = query.filter(Laptop.price >= crit["min_price"])
            
            # Lấy tất cả laptop phù hợp
            candidates = query.all()
            
            # Tính điểm cho từng laptop
            scored_laptops = []
            for laptop in candidates:
                score = calculate_laptop_score(laptop, crit, priority)
                scored_laptops.append((laptop, score))
            
            # Sắp xếp theo điểm số
            scored_laptops.sort(key=lambda x: x[1], reverse=True)
            
            # Trả về top 10 laptop tốt nhất
            items = [laptop for laptop, score in scored_laptops[:10]]
            
        else:
            # Nếu không có nhu cầu cụ thể, trả về tất cả laptop
            if budget:
                query = query.filter(Laptop.price <= budget)
            items = query.order_by(Laptop.price.asc()).all()
        
        return render_template("laptops.html", items=items, recommendation_type=need)

    @app.route("/api/search_suggest")
    def api_search_suggest():
        q = request.args.get("q", "").strip()
        # Allow up to 10, default 5
        raw_limit = request.args.get("limit", 5, type=int)
        limit = max(1, min(raw_limit, 10))
        suggestions = []
        if len(q) >= 2:
            like = f"%{q.lower()}%"
            results = (Laptop.query
                       .filter(db.or_(
                           db.func.lower(Laptop.name).like(like),
                           db.func.lower(Laptop.brand).like(like)
                       ))
                       .order_by(Laptop.price.asc())
                       .limit(limit)
                       .all())
            for it in results:
                suggestions.append({
                    "id": it.id,
                    "name": it.name,
                    "brand": it.brand,
                    "cpu": it.cpu,
                    "image_url": it.image_url,
                    "price": it.price
                })
        return jsonify({"items": suggestions})

    @app.route("/api/products_legacy")
    def api_products_legacy():
        """API cũ để lấy danh sách sản phẩm cho trang chủ (đã deprecated)"""
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 9, type=int)
        
        # Lấy sản phẩm với phân trang
        pagination = Laptop.query.order_by(Laptop.price.asc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        products = []
        for laptop in pagination.items:
            products.append({
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
                "image_url": laptop.image_url
            })
        
        return jsonify({
            "products": products,
            "has_next": pagination.has_next,
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": page
        })

    # ========== API ENDPOINTS CHO UPLOAD VÀ QUẢN LÝ SẢN PHẨM ==========
    
    @app.route("/api/upload-image", methods=["POST"])
    @admin_required
    @limiter.limit("10 per minute")
    def api_upload_image():
        """API endpoint để upload hình ảnh"""
        try:
            if 'image' not in request.files:
                return jsonify({
                    "success": False,
                    "error": "Không tìm thấy file hình ảnh"
                }), 400
            
            file = request.files['image']
            if file.filename == '':
                return jsonify({
                    "success": False,
                    "error": "Chưa chọn file"
                }), 400
            
            # Sử dụng utils để xử lý upload
            image_url = save_uploaded_image(file)
            if not image_url:
                return jsonify({
                    "success": False,
                    "error": "Không thể xử lý file hình ảnh"
                }), 400
            
            # Trả về kết quả thành công
            return jsonify({
                "success": True,
                "image_url": image_url,
                "message": "Upload hình ảnh thành công"
            })
                
        except Exception as e:
            app.logger.error(f"Error in upload image: {e}")
            return jsonify({
                "success": False,
                "error": f"Lỗi server: {str(e)}"
            }), 500

    @app.route("/api/products", methods=["GET", "POST"])
    def api_products_crud():
        """API endpoint cho CRUD operations của sản phẩm"""
        if request.method == "GET":
            # Lấy danh sách sản phẩm với filter
            page = request.args.get("page", 1, type=int)
            per_page = min(request.args.get("per_page", 20, type=int), 100)
            brand = request.args.get("brand")
            category = request.args.get("category")
            min_price = request.args.get("min_price", type=int)
            max_price = request.args.get("max_price", type=int)
            search = request.args.get("search")
            
            query = Laptop.query
            
            # Áp dụng filters
            if brand:
                query = query.filter(Laptop.brand == brand)
            if category:
                query = query.filter(Laptop.category == category)
            if min_price:
                query = query.filter(Laptop.price >= min_price)
            if max_price:
                query = query.filter(Laptop.price <= max_price)
            if search:
                like = f"%{search.lower()}%"
                query = query.filter(db.func.lower(Laptop.name).like(like))
            
            # Phân trang
            pagination = query.order_by(Laptop.price.asc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            products = []
            for laptop in pagination.items:
                products.append({
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
                    "battery_capacity": laptop.battery_capacity,
                    "battery_life_office": laptop.battery_life_office,
                    "battery_life_gaming": laptop.battery_life_gaming,
                    "cpu_single_core_plugged": laptop.cpu_single_core_plugged,
                    "cpu_multi_core_plugged": laptop.cpu_multi_core_plugged,
                    "cpu_single_core_battery": laptop.cpu_single_core_battery,
                    "cpu_multi_core_battery": laptop.cpu_multi_core_battery,
                    "gpu_score_plugged": laptop.gpu_score_plugged,
                    "gpu_score_battery": laptop.gpu_score_battery
                })
            
            return jsonify({
                "success": True,
                "products": products,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": pagination.total,
                    "pages": pagination.pages,
                    "has_next": pagination.has_next,
                    "has_prev": pagination.has_prev
                }
            })
        
        elif request.method == "POST":
            # Tạo sản phẩm mới (chỉ admin)
            if not current_user.is_authenticated or current_user.role != 'admin':
                return jsonify({
                    "success": False,
                    "error": "Không có quyền truy cập"
                }), 403
            
            try:
                data = request.get_json()
                
                # Validation dữ liệu bắt buộc
                required_fields = ['name', 'brand', 'cpu', 'ram_gb', 'storage', 'screen', 'price', 'category']
                for field in required_fields:
                    if field not in data or not data[field]:
                        return jsonify({
                            "success": False,
                            "error": f"Thiếu thông tin bắt buộc: {field}"
                        }), 400
                
                # Tạo laptop mới
                laptop = Laptop(
                    name=data['name'],
                    brand=data['brand'],
                    cpu=data['cpu'],
                    ram_gb=int(data['ram_gb']),
                    gpu=data.get('gpu'),
                    storage=data['storage'],
                    screen=data['screen'],
                    price=int(data['price']),
                    category=data['category'],
                    image_url=data.get('image_url'),
                    battery_capacity=int(data['battery_capacity']) if data.get('battery_capacity') else None,
                    battery_life_office=int(data['battery_life_office']) if data.get('battery_life_office') else None,
                    battery_life_gaming=int(data['battery_life_gaming']) if data.get('battery_life_gaming') else None,
                    cpu_single_core_plugged=int(data['cpu_single_core_plugged']) if data.get('cpu_single_core_plugged') else None,
                    cpu_multi_core_plugged=int(data['cpu_multi_core_plugged']) if data.get('cpu_multi_core_plugged') else None,
                    cpu_single_core_battery=int(data['cpu_single_core_battery']) if data.get('cpu_single_core_battery') else None,
                    cpu_multi_core_battery=int(data['cpu_multi_core_battery']) if data.get('cpu_multi_core_battery') else None,
                    gpu_score_plugged=int(data['gpu_score_plugged']) if data.get('gpu_score_plugged') else None,
                    gpu_score_battery=int(data['gpu_score_battery']) if data.get('gpu_score_battery') else None
                )
                
                db.session.add(laptop)
                db.session.commit()
                
                return jsonify({
                    "success": True,
                    "message": "Tạo sản phẩm thành công",
                    "product": {
                        "id": laptop.id,
                        "name": laptop.name,
                        "brand": laptop.brand,
                        "price": laptop.price
                    }
                }), 201
                
            except Exception as e:
                db.session.rollback()
                return jsonify({
                    "success": False,
                    "error": f"Lỗi khi tạo sản phẩm: {str(e)}"
                }), 500

    @app.route("/api/products/<int:product_id>", methods=["GET", "PUT", "DELETE"])
    def api_product_detail(product_id):
        """API endpoint cho chi tiết sản phẩm"""
        laptop = Laptop.query.get_or_404(product_id)
        
        if request.method == "GET":
            return jsonify({
                "success": True,
                "product": {
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
                    "battery_capacity": laptop.battery_capacity,
                    "battery_life_office": laptop.battery_life_office,
                    "battery_life_gaming": laptop.battery_life_gaming,
                    "cpu_single_core_plugged": laptop.cpu_single_core_plugged,
                    "cpu_multi_core_plugged": laptop.cpu_multi_core_plugged,
                    "cpu_single_core_battery": laptop.cpu_single_core_battery,
                    "cpu_multi_core_battery": laptop.cpu_multi_core_battery,
                    "gpu_score_plugged": laptop.gpu_score_plugged,
                    "gpu_score_battery": laptop.gpu_score_battery
                }
            })
        
        elif request.method == "PUT":
            # Cập nhật sản phẩm (chỉ admin)
            if not current_user.is_authenticated or current_user.role != 'admin':
                return jsonify({
                    "success": False,
                    "error": "Không có quyền truy cập"
                }), 403
            
            try:
                data = request.get_json()
                
                # Cập nhật các trường
                if 'name' in data:
                    laptop.name = data['name']
                if 'brand' in data:
                    laptop.brand = data['brand']
                if 'cpu' in data:
                    laptop.cpu = data['cpu']
                if 'ram_gb' in data:
                    laptop.ram_gb = int(data['ram_gb'])
                if 'gpu' in data:
                    laptop.gpu = data['gpu']
                if 'storage' in data:
                    laptop.storage = data['storage']
                if 'screen' in data:
                    laptop.screen = data['screen']
                if 'price' in data:
                    laptop.price = int(data['price'])
                if 'category' in data:
                    laptop.category = data['category']
                if 'image_url' in data:
                    laptop.image_url = data['image_url']
                if 'battery_capacity' in data:
                    laptop.battery_capacity = int(data['battery_capacity']) if data['battery_capacity'] else None
                if 'battery_life_office' in data:
                    laptop.battery_life_office = int(data['battery_life_office']) if data['battery_life_office'] else None
                if 'battery_life_gaming' in data:
                    laptop.battery_life_gaming = int(data['battery_life_gaming']) if data['battery_life_gaming'] else None
                if 'cpu_single_core_plugged' in data:
                    laptop.cpu_single_core_plugged = int(data['cpu_single_core_plugged']) if data['cpu_single_core_plugged'] else None
                if 'cpu_multi_core_plugged' in data:
                    laptop.cpu_multi_core_plugged = int(data['cpu_multi_core_plugged']) if data['cpu_multi_core_plugged'] else None
                if 'cpu_single_core_battery' in data:
                    laptop.cpu_single_core_battery = int(data['cpu_single_core_battery']) if data['cpu_single_core_battery'] else None
                if 'cpu_multi_core_battery' in data:
                    laptop.cpu_multi_core_battery = int(data['cpu_multi_core_battery']) if data['cpu_multi_core_battery'] else None
                if 'gpu_score_plugged' in data:
                    laptop.gpu_score_plugged = int(data['gpu_score_plugged']) if data['gpu_score_plugged'] else None
                if 'gpu_score_battery' in data:
                    laptop.gpu_score_battery = int(data['gpu_score_battery']) if data['gpu_score_battery'] else None
                
                db.session.commit()
                
                return jsonify({
                    "success": True,
                    "message": "Cập nhật sản phẩm thành công",
                    "product": {
                        "id": laptop.id,
                        "name": laptop.name,
                        "brand": laptop.brand,
                        "price": laptop.price
                    }
                })
                
            except Exception as e:
                db.session.rollback()
                return jsonify({
                    "success": False,
                    "error": f"Lỗi khi cập nhật sản phẩm: {str(e)}"
                }), 500
        
        elif request.method == "DELETE":
            # Xóa sản phẩm (chỉ admin)
            if not current_user.is_authenticated or current_user.role != 'admin':
                return jsonify({
                    "success": False,
                    "error": "Không có quyền truy cập"
                }), 403
            
            try:
                laptop_name = laptop.name
                db.session.delete(laptop)
                db.session.commit()
                
                return jsonify({
                    "success": True,
                    "message": f"Đã xóa sản phẩm '{laptop_name}' thành công"
                })
                
            except Exception as e:
                db.session.rollback()
                return jsonify({
                    "success": False,
                    "error": f"Lỗi khi xóa sản phẩm: {str(e)}"
                }), 500

    @app.route("/api/brands")
    def api_brands():
        """API endpoint để lấy danh sách thương hiệu"""
        brands = [brand[0] for brand in db.session.query(Laptop.brand).distinct().all()]
        return jsonify({
            "success": True,
            "brands": brands
        })

    @app.route("/api/categories")
    def api_categories():
        """API endpoint để lấy danh sách danh mục"""
        categories = [cat[0] for cat in db.session.query(Laptop.category).distinct().all()]
        return jsonify({
            "success": True,
            "categories": categories
        })

    # ========== AI CHATBOT ENDPOINTS ==========
    
    @app.route("/api/chat", methods=["POST"])
    @limiter.limit("10 per minute")
    @csrf.exempt
    def api_chat():
        """Enhanced AI chatbot with conversation memory and smart context"""
        try:
            data = request.get_json()
            user_message = data.get('message', '').strip()
            
            if not user_message:
                return jsonify({
                    "success": False,
                    "error": "Tin nhắn không được để trống"
                }), 400
            
            # Initialize chatbot service
            chatbot = ChatbotService(app.config['ANTHROPIC_API_KEY'])
            
            # Get conversation history from session
            conversation_history = session.get('chat_history', [])
            
            # Generate response with enhanced context
            result = chatbot.generate_response(user_message, conversation_history)
            
            if result['success']:
                # Update conversation history
                conversation_history.append({"role": "user", "content": user_message})
                conversation_history.append({"role": "assistant", "content": result['response']})
                
                # Keep only last 10 messages to prevent session bloat
                if len(conversation_history) > 10:
                    conversation_history = conversation_history[-10:]
                
                session['chat_history'] = conversation_history
                
                # Log analytics
                app.logger.info(f"Chatbot Analytics - Intent: {result.get('intent', 'general')}, "
                              f"Laptops found: {result.get('relevant_laptops_count', 0)}, "
                              f"Message length: {len(user_message)}")
                
                # Validate laptops in response
                if result.get('relevant_laptops'):
                    for laptop in result['relevant_laptops']:
                        if not laptop.get('id') or not laptop.get('name'):
                            app.logger.warning(f"Invalid laptop in response: {laptop}")
                
                return jsonify({
                    "success": True,
                    "response": result['response'],
                    "intent": result.get('intent', 'general'),
                    "relevant_laptops_count": result.get('relevant_laptops_count', 0),
                    "model": result.get('model', 'claude-3-haiku')
                })
            else:
                return jsonify({
                    "success": False,
                    "error": result.get('error', 'Có lỗi xảy ra. Vui lòng thử lại.')
                }), 500
            
        except Exception as e:
            app.logger.error(f"Chatbot Error: {e}")
            return jsonify({
                "success": False,
                "error": "Có lỗi xảy ra. Vui lòng thử lại."
            }), 500

    @app.route("/api/chat/search", methods=["POST"])
    @limiter.limit("10 per minute")
    @csrf.exempt
    def api_chat_search():
        """Enhanced AI search with better matching"""
        try:
            data = request.get_json()
            search_query = data.get('query', '').strip()
            
            if not search_query:
                return jsonify({
                    "success": False,
                    "error": "Truy vấn tìm kiếm không được để trống"
                }), 400
            
            # Initialize chatbot service for enhanced search
            chatbot = ChatbotService(app.config['ANTHROPIC_API_KEY'])
            
            # Use enhanced search
            search_results = chatbot.search_laptops(search_query, limit=10)
            
            return jsonify({
                "success": True,
                "results": search_results,
                "count": len(search_results)
            })
            
        except Exception as e:
            app.logger.error(f"Search Error: {e}")
            return jsonify({
                "success": False,
                "error": "Có lỗi xảy ra khi tìm kiếm."
            }), 500

    @app.route("/api/chat/clear", methods=["POST"])
    @csrf.exempt
    def api_chat_clear():
        """Clear conversation history"""
        try:
            session.pop('chat_history', None)
            return jsonify({
                "success": True,
                "message": "Đã xóa lịch sử trò chuyện"
            })
        except Exception as e:
            app.logger.error(f"Clear chat error: {e}")
            return jsonify({
                "success": False,
                "error": "Có lỗi xảy ra khi xóa lịch sử"
            }), 500

    @app.route("/api/chat/recommend", methods=["POST"])
    @limiter.limit("10 per minute")
    @csrf.exempt
    def api_chat_recommend():
        """Get AI-powered laptop recommendations"""
        try:
            data = request.get_json()
            user_message = data.get('message', '').strip()
            
            if not user_message:
                return jsonify({
                    "success": False,
                    "error": "Tin nhắn không được để trống"
                }), 400
            
            # Initialize chatbot service
            chatbot = ChatbotService(app.config['ANTHROPIC_API_KEY'])
            
            # Extract preferences from message
            preferences = chatbot.extract_user_preferences(user_message, [])
            
            # Get relevant laptops
            relevant_laptops = chatbot.get_relevant_laptops(preferences, limit=5)
            
            # Generate AI recommendation
            result = chatbot.generate_response(user_message, [])
            
            if result['success']:
                return jsonify({
                    "success": True,
                    "recommendation": result['response'],
                    "laptops": relevant_laptops,
                    "intent": result.get('intent', 'recommend'),
                    "preferences": preferences
                })
            else:
                return jsonify({
                    "success": False,
                    "error": result.get('error', 'Có lỗi xảy ra khi tạo gợi ý')
                }), 500
            
        except Exception as e:
            app.logger.error(f"Recommendation Error: {e}")
            return jsonify({
                "success": False,
                "error": "Có lỗi xảy ra khi tạo gợi ý"
            }), 500

    @app.route("/api/chat/analytics")
    @admin_required
    def api_chat_analytics():
        """Get chatbot analytics (Admin only)"""
        try:
            # Get basic stats
            total_laptops = Laptop.query.count()
            total_brands = db.session.query(Laptop.brand).distinct().count()
            total_categories = db.session.query(Laptop.category).distinct().count()
            
            # Get price range
            price_stats = db.session.query(
                db.func.min(Laptop.price).label('min_price'),
                db.func.max(Laptop.price).label('max_price'),
                db.func.avg(Laptop.price).label('avg_price')
            ).first()
            
            # Get category distribution
            category_dist = db.session.query(
                Laptop.category, 
                db.func.count(Laptop.id).label('count')
            ).group_by(Laptop.category).all()
            
            # Get brand distribution
            brand_dist = db.session.query(
                Laptop.brand, 
                db.func.count(Laptop.id).label('count')
            ).group_by(Laptop.brand).all()
            
            analytics = {
                "total_laptops": total_laptops,
                "total_brands": total_brands,
                "total_categories": total_categories,
                "price_stats": {
                    "min": int(price_stats.min_price) if price_stats.min_price else 0,
                    "max": int(price_stats.max_price) if price_stats.max_price else 0,
                    "avg": int(price_stats.avg_price) if price_stats.avg_price else 0
                },
                "category_distribution": [
                    {"category": cat, "count": count} for cat, count in category_dist
                ],
                "brand_distribution": [
                    {"brand": brand, "count": count} for brand, count in brand_dist
                ]
            }
            
            return jsonify({
                "success": True,
                "analytics": analytics
            })
            
        except Exception as e:
            app.logger.error(f"Analytics Error: {e}")
            return jsonify({
                "success": False,
                "error": "Có lỗi xảy ra khi lấy analytics"
            }), 500

    return app

def calculate_laptop_score(laptop, criteria, priority):
    """
    Tính điểm cho laptop dựa trên tiêu chí và ưu tiên
    """
    score = 0
    weights = criteria["weight"]
    
    # Điểm cho CPU
    cpu_score = 0
    cpu_series = criteria.get("cpu_series", [])
    for series in cpu_series:
        if series in laptop.cpu.upper():
            cpu_score = 1.0
            break
    if not cpu_score and "U" in laptop.cpu.upper():
        cpu_score = 0.5  # CPU U-series cơ bản
    
    # Điểm cho RAM
    ram_score = min(laptop.ram_gb / 32.0, 1.0)  # Chuẩn hóa theo 32GB
    
    # Điểm cho GPU
    gpu_score = 0
    if laptop.gpu:
        gpu_lower = laptop.gpu.lower()
        if any(gpu in gpu_lower for gpu in ['rtx', 'gtx', 'rx', 'radeon']):
            gpu_score = 1.0
        elif any(gpu in gpu_lower for gpu in ['mx', 'iris xe']):
            gpu_score = 0.6
        else:
            gpu_score = 0.3
    
    # Điểm cho giá (càng thấp càng tốt)
    price_score = 1.0 - (laptop.price / 50000000.0)  # Chuẩn hóa theo 50 triệu
    price_score = max(0, price_score)
    
    # Điểm cho storage
    storage_score = 0.5  # Mặc định
    if "ssd" in laptop.storage.lower():
        storage_score = 1.0
    elif "hdd" in laptop.storage.lower():
        storage_score = 0.3
    
    # Tính điểm tổng hợp
    score = (
        cpu_score * weights.get("cpu", 0.2) +
        ram_score * weights.get("ram", 0.2) +
        gpu_score * weights.get("gpu", 0.1) +
        price_score * weights.get("price", 0.3) +
        storage_score * weights.get("storage", 0.1)
    )
    
    # Điều chỉnh theo ưu tiên
    if priority == "performance":
        score *= 1.2  # Tăng 20% cho laptop hiệu năng cao
    elif priority == "budget":
        score *= 0.8  # Giảm 20% cho laptop giá rẻ
    
    return score

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        from models import db
        db.create_all()
    app.run(debug=True)
