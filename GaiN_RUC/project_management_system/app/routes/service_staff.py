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
from ..models.service import ServiceRequest

service_staff_bp = Blueprint("service", __name__, url_prefix="/service")

RESOURCE_STATE = {
    "办公场地": {"总量": 20, "已使用": 12},
    "算力服务": {"总量": 1000, "已使用": 760},
    "投融资资源": {"总量": 50, "已使用": 32},
}


def ensure_service_staff():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    if current_user.role != "service_staff":
        abort(403)


@service_staff_bp.before_request
def service_guard():
    if request.endpoint and request.endpoint.startswith("service."):
        return ensure_service_staff()


@service_staff_bp.route("/dashboard")
@login_required
def dashboard():
    pending = ServiceRequest.query.filter_by(status="待审核").count()
    active = ServiceRequest.query.filter_by(status="执行中").count()
    completed = ServiceRequest.query.filter_by(status="已完成").count()
    notices = [
        "请关注近期新增的算力资源申请。",
        "资源紧张提示：投融资资源可用额度不足 40%。",
    ]
    return render_template(
        "service_staff/dashboard.html",
        pending=pending,
        active=active,
        completed=completed,
        notices=notices,
    )


@service_staff_bp.route("/review", methods=["GET", "POST"])
@login_required
def review():
    if request.method == "POST":
        request_id = request.form.get("request_id")
        action = request.form.get("action")
        reason = request.form.get("reason")
        service_request = ServiceRequest.query.get_or_404(request_id)
        if action == "approve":
            service_request.status = "待制定方案"
        elif action == "reject":
            service_request.status = "已驳回"
            service_request.progress = f"驳回原因：{reason}"
        db.session.commit()
        flash("审核结果已更新。", "success")
        return redirect(url_for("service.review"))

    requests = ServiceRequest.query.order_by(ServiceRequest.created_at.desc()).all()
    return render_template("service_staff/review.html", requests=requests)


@service_staff_bp.route("/plan/<int:request_id>", methods=["GET", "POST"])
@login_required
def plan(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)
    if request.method == "POST":
        service_request.progress = request.form.get("plan")
        service_request.status = "执行中"
        service_request.assigned_staff = current_user
        db.session.commit()
        flash("方案已提交。", "success")
        return redirect(url_for("service.tracking"))
    return render_template("service_staff/plan.html", service_request=service_request)


@service_staff_bp.route("/tracking", methods=["GET", "POST"])
@login_required
def tracking():
    if request.method == "POST":
        request_id = request.form.get("request_id")
        progress = request.form.get("progress")
        action = request.form.get("action")
        service_request = ServiceRequest.query.get_or_404(request_id)
        service_request.progress = progress
        if action == "complete":
            service_request.status = "已完成"
        else:
            service_request.status = "执行中"
        db.session.commit()
        flash("进度已更新。", "success")
        return redirect(url_for("service.tracking"))

    services = ServiceRequest.query.order_by(ServiceRequest.updated_at.desc()).all()
    return render_template("service_staff/tracking.html", services=services)


@service_staff_bp.route("/resources", methods=["GET", "POST"])
@login_required
def resources():
    if request.method == "POST":
        resource_name = request.form.get("resource_name")
        used = int(request.form.get("used", 0))
        if resource_name in RESOURCE_STATE:
            RESOURCE_STATE[resource_name]["已使用"] = used
            flash("资源状态已更新。", "success")
        return redirect(url_for("service.resources"))

    resource_data = []
    for name, data in RESOURCE_STATE.items():
        resource_data.append(
            {
                "name": name,
                "total": data["总量"],
                "used": data["已使用"],
                "free": max(0, data["总量"] - data["已使用"]),
            }
        )
    return render_template("service_staff/resources.html", resources=resource_data)

