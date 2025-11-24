import os
import uuid
from datetime import datetime

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from ..models import db
from ..models.material import ProjectMaterial
from ..models.project import Project
from ..models.service import ServiceRequest

applicant_bp = Blueprint("applicant", __name__, url_prefix="/applicant")

ALLOWED_EXTENSIONS = {"pdf"}


def ensure_applicant():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    if current_user.role != "applicant":
        abort(403)


@applicant_bp.before_request
def applicant_guard():
    if request.endpoint and request.endpoint.startswith("applicant."):
        return ensure_applicant()


@applicant_bp.route("/dashboard")
@login_required
def dashboard():
    stats = {
        "pending": current_user.projects.filter_by(status="申报中").count(),
        "completed": current_user.projects.filter(Project.status != "申报中").count(),
    }
    projects = (
        current_user.projects.order_by(Project.updated_at.desc()).limit(5).all()
    )
    notices = [
        "系统通知：初审结果将在 3 个工作日内反馈。",
        "入库项目可在“孵化服务申请”申请资源。",
    ]
    return render_template(
        "applicant/dashboard.html", stats=stats, projects=projects, notices=notices
    )


@applicant_bp.route("/projects")
@login_required
def projects():
    status = request.args.get("status")
    query = current_user.projects.order_by(Project.created_at.desc())
    if status:
        query = query.filter_by(status=status)
    return render_template("applicant/projects.html", projects=query.all(), status=status)


@applicant_bp.route("/projects/new", methods=["GET", "POST"])
@login_required
def new_project():
    if request.method == "POST":
        category = request.form.get("category")
        name = request.form.get("name")
        summary = request.form.get("summary")
        ip_info = request.form.get("ip_info")
        material_notes = request.form.get("material_notes")
        action = request.form.get("action")

        project = Project(
            application_no=generate_application_no(),
            name=name,
            category=category,
            summary=summary,
            ip_info=ip_info,
            material_notes=material_notes,
            status="草稿" if action == "draft" else "申报中",
            applicant=current_user,
        )
        db.session.add(project)
        db.session.commit()
        save_uploaded_materials(project, request.files.getlist("materials"))
        flash("项目已保存。" if action == "draft" else "项目提交成功。", "success")
        return redirect(url_for("applicant.projects"))

    return render_template("applicant/project_form.html", project=None)


@applicant_bp.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
@login_required
def edit_project(project_id):
    project = Project.query.filter_by(id=project_id, applicant=current_user).first_or_404()
    if project.status not in {"申报中", "草稿", "驳回"}:
        flash("当前状态不可修改。", "warning")
        return redirect(url_for("applicant.projects"))

    if request.method == "POST":
        project.name = request.form.get("name")
        project.category = request.form.get("category")
        project.summary = request.form.get("summary")
        project.ip_info = request.form.get("ip_info")
        project.material_notes = request.form.get("material_notes")
        action = request.form.get("action")
        project.status = "草稿" if action == "draft" else "申报中"
        db.session.commit()
        save_uploaded_materials(project, request.files.getlist("materials"))
        flash("项目已更新。", "success")
        return redirect(url_for("applicant.projects"))

    return render_template("applicant/project_form.html", project=project)


@applicant_bp.route("/projects/<int:project_id>")
@login_required
def project_detail(project_id):
    project = Project.query.filter_by(id=project_id, applicant=current_user).first_or_404()
    return render_template("applicant/project_detail.html", project=project)


@applicant_bp.route("/services/apply", methods=["GET", "POST"])
@login_required
def apply_service():
    projects = current_user.projects.all()
    if request.method == "POST":
        service_type = request.form.get("service_type")
        project_id_raw = request.form.get("project_id")
        project_id = int(project_id_raw) if project_id_raw else None
        details = request.form.get("details")

        service = ServiceRequest(
            request_no=generate_service_no(),
            service_type=service_type,
            project_id=project_id or None,
            details=details,
            applicant=current_user,
        )
        db.session.add(service)
        db.session.commit()
        flash("服务申请已提交，服务专员会尽快审核。", "success")
        return redirect(url_for("applicant.service_progress"))

    return render_template("applicant/service_form.html", projects=projects)


@applicant_bp.route("/services/progress")
@login_required
def service_progress():
    services = (
        current_user.service_requests.order_by(ServiceRequest.created_at.desc()).all()
    )
    return render_template("applicant/service_progress.html", services=services)


@applicant_bp.route("/projects/<int:project_id>/materials/<int:material_id>/delete", methods=["POST"])
@login_required
def delete_material(project_id, material_id):
    project = Project.query.filter_by(id=project_id, applicant=current_user).first_or_404()
    material = project.materials.filter_by(id=material_id).first_or_404()
    file_path = get_material_path(project_id, material.stored_name)
    db.session.delete(material)
    db.session.commit()
    if os.path.exists(file_path):
        os.remove(file_path)
    flash("已删除证明材料。", "info")
    return redirect(request.referrer or url_for("applicant.edit_project", project_id=project_id))


def generate_application_no() -> str:
    return f"AP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4]}"


def generate_service_no() -> str:
    return f"SR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4]}"


def save_uploaded_materials(project: Project, files):
    for file in files or []:
        if not file or file.filename == "":
            continue
        filename = secure_filename(file.filename)
        if not allowed_file(filename):
            flash(f"不支持的文件类型：{filename}，仅允许 PDF。", "warning")
            continue
        stored_name = f"{uuid.uuid4().hex}_{filename}"
        storage_dir = os.path.join(
            current_app.config["UPLOAD_FOLDER"], "projects", str(project.id)
        )
        os.makedirs(storage_dir, exist_ok=True)
        file_path = os.path.join(storage_dir, stored_name)
        file.save(file_path)
        material = ProjectMaterial(
            file_name=filename,
            stored_name=stored_name,
            project=project,
        )
        db.session.add(material)
    db.session.commit()


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_material_path(project_id: int, stored_name: str) -> str:
    return os.path.join(
        current_app.config["UPLOAD_FOLDER"], "projects", str(project_id), stored_name
    )

