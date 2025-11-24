import os

from flask import Blueprint, abort, current_app, send_from_directory
from flask_login import current_user, login_required

from ..models.material import ProjectMaterial

files_bp = Blueprint("files", __name__, url_prefix="/files")


@files_bp.route("/project/<int:material_id>")
@login_required
def download_project_material(material_id):
    material = ProjectMaterial.query.get_or_404(material_id)
    project = material.project

    if not can_access_material(project.applicant_id):
        abort(403)

    directory = os.path.join(
        current_app.config["UPLOAD_FOLDER"], "projects", str(project.id)
    )
    return send_from_directory(
        directory,
        material.stored_name,
        download_name=material.file_name,
        mimetype="application/pdf",
        as_attachment=True,
    )


def can_access_material(applicant_id: int) -> bool:
    if not current_user.is_authenticated:
        return False
    if current_user.id == applicant_id:
        return True
    return current_user.role in {"admin", "expert"}

