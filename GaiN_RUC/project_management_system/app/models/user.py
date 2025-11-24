from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from . import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(50))
    organization = db.Column(db.String(120))
    password_hash = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    projects = db.relationship("Project", back_populates="applicant", lazy="dynamic")
    reviews = db.relationship("Review", back_populates="expert", lazy="dynamic")
    service_requests = db.relationship(
        "ServiceRequest",
        back_populates="applicant",
        lazy="dynamic",
        foreign_keys="ServiceRequest.applicant_id",
    )
    assigned_services = db.relationship(
        "ServiceRequest",
        back_populates="assigned_staff",
        lazy="dynamic",
        foreign_keys="ServiceRequest.assigned_staff_id",
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def is_active(self):
        return self.status == "active"

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"

