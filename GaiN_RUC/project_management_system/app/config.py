import os


class Config:
    """Application configuration."""

    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    INSTANCE_DIR = os.path.join(BASE_DIR, "instance")

    SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(INSTANCE_DIR, 'project_management.db')}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get(
        "UPLOAD_FOLDER", os.path.join(INSTANCE_DIR, "uploads")
    )
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB


os.makedirs(Config.INSTANCE_DIR, exist_ok=True)
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

