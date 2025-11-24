from datetime import datetime

from . import db


class ServiceRequest(db.Model):
    __tablename__ = "service_requests"

    id = db.Column(db.Integer, primary_key=True)
    request_no = db.Column(db.String(40), unique=True, nullable=False)
    service_type = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text, nullable=False)
    attachment_name = db.Column(db.String(255))
    status = db.Column(db.String(40), default="待审核")
    progress = db.Column(db.Text, default="待处理")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"))
    applicant_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    project = db.relationship("Project", back_populates="services")
    applicant = db.relationship(
        "User", back_populates="service_requests", foreign_keys=[applicant_id]
    )
    assigned_staff = db.relationship(
        "User", back_populates="assigned_services", foreign_keys=[assigned_staff_id]
    )

    def __repr__(self) -> str:
        return f"<ServiceRequest {self.request_no} {self.service_type}>"

