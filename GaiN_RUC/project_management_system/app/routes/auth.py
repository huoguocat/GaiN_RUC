from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..models import db
from ..models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(role_dashboard(current_user.role))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role")
        email = request.form.get("email")
        password = request.form.get("password")
        captcha = request.form.get("captcha")

        if captcha != "1234":
            flash("验证码错误（提示：请输入 1234）", "danger")
            return redirect(url_for("auth.login"))

        user = User.query.filter_by(email=email, role=role).first()
        if user and user.check_password(password):
            if user.status != "active":
                flash("账号已被禁用，请联系管理员。", "warning")
                return redirect(url_for("auth.login"))
            login_user(user)
            flash("登录成功。", "success")
            return redirect(role_dashboard(role))
        flash("账号或密码错误。", "danger")
    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    allowed_roles = {"applicant", "expert"}
    if request.method == "POST":
        role = request.form.get("role")
        if role not in allowed_roles:
            flash("仅申报人或专家可自助注册。", "warning")
            return redirect(url_for("auth.register"))

        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        organization = request.form.get("organization")
        phone = request.form.get("phone")

        if User.query.filter_by(email=email).first():
            flash("该邮箱已注册。", "danger")
            return redirect(url_for("auth.register"))

        user = User(role=role, name=name, email=email, organization=organization, phone=phone)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("注册成功，请登录。", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("已退出登录。", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        contact = request.form.get("contact")
        code = request.form.get("code")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if code != "000000":
            flash("验证码错误（提示：输入 000000）", "danger")
            return redirect(url_for("auth.reset_password"))

        if new_password != confirm_password:
            flash("两次输入的密码不一致。", "warning")
            return redirect(url_for("auth.reset_password"))

        user = User.query.filter((User.email == contact) | (User.phone == contact)).first()
        if not user:
            flash("未找到匹配的账号。", "danger")
            return redirect(url_for("auth.reset_password"))

        user.set_password(new_password)
        db.session.commit()
        flash("密码重置成功，请使用新密码登录。", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/reset_password.html")


def role_dashboard(role: str):
    mapping = {
        "applicant": "applicant.dashboard",
        "expert": "expert.dashboard",
        "admin": "admin.dashboard",
        "service_staff": "service.dashboard",
    }
    endpoint = mapping.get(role, "auth.login")
    return url_for(endpoint)

