import pytest

from app import create_app, ensure_database_initialized
from app.model import Usuario, db


@pytest.fixture
def app():
    cfg = {"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True}
    application = create_app(cfg)
    return application


def test_create_app_instance(app):
    assert app is not None
    assert app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite")


def test_ensure_database_creates_admin(app):
    # Ensure database initialized creates admin user
    with app.app_context():
        ensure_database_initialized(app)
        admin = db.session.execute(db.select(Usuario).filter_by(tipo="admin")).scalar_one_or_none()
        assert admin is not None
        assert admin.tipo == "admin"
