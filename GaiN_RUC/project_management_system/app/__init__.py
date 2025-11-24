import os

from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user

from .config import Config
from .models import db
from .models.user import User

login_manager = LoginManager()
login_manager.login_view = "auth.login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_app():
    """Application factory."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        db.create_all()
        bootstrap_accounts()

    from .routes.auth import auth_bp
    from .routes.applicant import applicant_bp
    from .routes.expert import expert_bp
    from .routes.admin import admin_bp
    from .routes.service_staff import service_staff_bp
    from .routes.files import files_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(applicant_bp)
    app.register_blueprint(expert_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(service_staff_bp)
    app.register_blueprint(files_bp)

    @app.context_processor
    def inject_globals():
        role_routes = {
            "applicant": "applicant.dashboard",
            "expert": "expert.dashboard",
            "admin": "admin.dashboard",
            "service_staff": "service.dashboard",
        }
        return {
            "roles": {
                "applicant": "申报人",
                "expert": "专家",
                "admin": "管理员",
                "service_staff": "服务专员",
            },
            "role_dashboards": role_routes,
        }

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            mapping = {
                "applicant": "applicant.dashboard",
                "expert": "expert.dashboard",
                "admin": "admin.dashboard",
                "service_staff": "service.dashboard",
            }
            endpoint = mapping.get(current_user.role, "auth.login")
            return redirect(url_for(endpoint))
        return redirect(url_for("auth.login"))

    return app


def bootstrap_accounts():
    """Create default demo accounts for quick start."""
    if not User.query.filter_by(email="admin@gainruc.local").first():
        admin = User(
            role="admin",
            name="平台管理员",
            email="admin@gainruc.local",
            organization="人大数智中心",
        )
        admin.set_password("Admin#123")
        db.session.add(admin)

    if not User.query.filter_by(email="service@gainruc.local").first():
        staff = User(
            role="service_staff",
            name="服务专员",
            email="service@gainruc.local",
            organization="创新服务部",
        )
        staff.set_password("Service#123")
        db.session.add(staff)

    db.session.commit()

