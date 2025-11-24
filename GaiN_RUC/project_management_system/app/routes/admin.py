from collections import Counter
from datetime import datetime

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from ..models import db
from ..models.project import Project
from ..models.review import Review
from ..models.service import ServiceRequest
from ..models.user import User

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def ensure_admin():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    if current_user.role != "admin":
        abort(403)


@admin_bp.before_request
def admin_guard():
    if request.endpoint and request.endpoint.startswith("admin."):
        return ensure_admin()


@admin_bp.route("/dashboard")
@login_required
def dashboard():
    stats = {
        "projects": Project.query.count(),
        "reviews": Review.query.count(),
        "services": ServiceRequest.query.count(),
    }
    pending_tasks = Project.query.filter_by(status="申报中").limit(5).all()
    return render_template("admin/dashboard.html", stats=stats, pending_tasks=pending_tasks)


@admin_bp.route("/projects/initial-review", methods=["GET", "POST"])
@login_required
def initial_review():
    if request.method == "POST":
        project_id = request.form.get("project_id")
        action = request.form.get("action")
        feedback = request.form.get("feedback")
        project = Project.query.get_or_404(project_id)
        if action == "approve":
            project.status = "初审通过"
        elif action == "reject":
            project.status = "驳回"
            project.material_notes = (project.material_notes or "") + f"\n驳回理由：{feedback}"
        db.session.commit()
        flash("初审结果已更新。", "success")
        return redirect(url_for("admin.initial_review"))

    projects = Project.query.filter(Project.status.in_(["申报中", "草稿", "驳回"])).all()
    return render_template("admin/initial_review.html", projects=projects)


@admin_bp.route("/projects/assign", methods=["GET", "POST"])
@login_required
def assign_experts():
    projects = Project.query.filter_by(status="初审通过").all()
    experts = User.query.filter_by(role="expert", status="active").all()
    if request.method == "POST":
        project_id = int(request.form.get("project_id"))
        expert_ids = [int(eid) for eid in request.form.getlist("expert_ids")]
        project = Project.query.get_or_404(project_id)
        for expert_id in expert_ids:
            review = Review.query.filter_by(project_id=project.id, expert_id=expert_id).first()
            if not review:
                db.session.add(
                    Review(
                        project_id=project.id,
                        expert_id=expert_id,
                        status="待确认",
                    )
                )
        project.status = "待评审"
        db.session.commit()
        flash("专家分配完成。", "success")
        return redirect(url_for("admin.assign_experts"))

    return render_template(
        "admin/assign_experts.html", projects=projects, experts=experts
    )


@admin_bp.route("/projects/publication", methods=["GET", "POST"])
@login_required
def publication():
    if request.method == "POST":
        project_id = request.form.get("project_id")
        action = request.form.get("action")
        project = Project.query.get_or_404(project_id)
        if action == "publish":
            project.status = "公示中"
        elif action == "finalize":
            project.status = "已入库"
        db.session.commit()
        flash("公示状态已更新。", "success")
        return redirect(url_for("admin.publication"))

    projects = Project.query.filter(Project.status.in_(["答辩通过", "公示中"])).all()
    return render_template("admin/publication.html", projects=projects)


@admin_bp.route("/users", methods=["GET", "POST"])
@login_required
def user_management():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "create":
            user = User(
                role=request.form.get("role"),
                name=request.form.get("name"),
                email=request.form.get("email"),
                organization=request.form.get("organization"),
                phone=request.form.get("phone"),
            )
            user.set_password(request.form.get("password"))
            db.session.add(user)
            flash("用户已创建。", "success")
        elif action in {"disable", "reset"}:
            user = User.query.get(request.form.get("user_id"))
            if user:
                if action == "disable":
                    user.status = "disabled"
                    flash("账号已禁用。", "warning")
                else:
                    user.set_password("Temp#123456")
                    flash("密码已重置为 Temp#123456。", "info")
        db.session.commit()
        return redirect(url_for("admin.user_management"))

    role = request.args.get("role")
    query = User.query
    if role:
        query = query.filter_by(role=role)
    users = query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users, role=role)


@admin_bp.route("/reports")
@login_required
def reports():
    projects = Project.query.all()
    counts = Counter([p.category for p in projects])
    status_counts = Counter([p.status for p in projects])
    return render_template(
        "admin/reports.html",
        category_counts=counts,
        status_counts=status_counts,
        generated_at=datetime.utcnow(),
    )

