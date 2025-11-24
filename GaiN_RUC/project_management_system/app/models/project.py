from datetime import datetime

from . import db


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    application_no = db.Column(db.String(40), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    ip_info = db.Column(db.Text)
    material_notes = db.Column(db.Text)
    status = db.Column(db.String(40), default="申报中")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    applicant_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    applicant = db.relationship("User", back_populates="projects")
    reviews = db.relationship("Review", back_populates="project", lazy="dynamic")
    services = db.relationship("ServiceRequest", back_populates="project", lazy="dynamic")
    materials = db.relationship(
        "ProjectMaterial",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<Project {self.application_no} {self.name}>"

