from datetime import datetime

from . import db


class ProjectMaterial(db.Model):
    __tablename__ = "project_materials"

    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(255), nullable=False, unique=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)

    project = db.relationship("Project", back_populates="materials")

    def __repr__(self) -> str:
        return f"<ProjectMaterial {self.file_name}>"

