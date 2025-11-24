from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models so SQLAlchemy can configure relationships before create_all
from .user import User  # noqa: E402,F401
from .project import Project  # noqa: E402,F401
from .review import Review  # noqa: E402,F401
from .service import ServiceRequest  # noqa: E402,F401
from .material import ProjectMaterial  # noqa: E402,F401

__all__ = ["db", "User", "Project", "Review", "ServiceRequest", "ProjectMaterial"]

