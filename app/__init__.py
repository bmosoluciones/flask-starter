"""
App
===

Minimal app package for template projects.
"""

from __future__ import annotations

from os import environ

from flask import Flask, flash, redirect, url_for
from flask_babel import Babel
from flask_login import LoginManager
from flask_session import Session

from app.app import app as app_blueprint
from app.auth import auth
from app.config import DIRECTORIO_ARCHIVOS_BASE, DIRECTORIO_PLANTILLAS_BASE
from app.i18n import _
from app.model import Usuario, db
from app.log import log

session_manager = Session()
login_manager = LoginManager()
babel = Babel()


@login_manager.user_loader
def cargar_sesion(identidad):
    if identidad is not None:
        return db.session.get(Usuario, identidad)
    return None


@login_manager.unauthorized_handler
def no_autorizado():
    flash(_("Favor iniciar sesión para acceder al sistema."), "warning")
    return redirect(url_for("auth.login"))


def create_app(config) -> Flask:
    from app.config import configuration as default_conf

    app = Flask(
        __name__, static_folder=DIRECTORIO_ARCHIVOS_BASE, template_folder=DIRECTORIO_PLANTILLAS_BASE
    )

    if config:
        app.config.from_mapping(config)
    else:
        app.config.from_object(default_conf)

    log.trace("create_app: initializing app")
    db.init_app(app)

    try:
        log.trace(f"create_app: SQLALCHEMY_DATABASE_URI = {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    except Exception:
        log.trace("create_app: could not read SQLALCHEMY_DATABASE_URI from app.config")

    try:
        log.trace("create_app: calling ensure_database_initialized")
        ensure_database_initialized(app)
        log.trace("create_app: ensure_database_initialized completed")
    except Exception as exc:
        log.trace(f"create_app: ensure_database_initialized raised: {exc}")
        try:
            log.exception("create_app: ensure_database_initialized exception")
        except Exception:
            pass

    if session_redis_url := environ.get("SESSION_REDIS_URL", None):
        from redis import Redis

        app.config["SESSION_TYPE"] = "redis"
        app.config["SESSION_REDIS"] = Redis.from_url(session_redis_url)
    else:
        app.config["SESSION_TYPE"] = "sqlalchemy"
        app.config["SESSION_SQLALCHEMY"] = db
        app.config["SESSION_SQLALCHEMY_TABLE"] = "sessions"
        app.config["SESSION_PERMANENT"] = False
        app.config["SESSION_USE_SIGNER"] = True

    babel.init_app(app)
    session_manager.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(app_blueprint, url_prefix="/")

    return app


def ensure_database_initialized(app: Flask | None = None) -> None:
    from os import environ as _environ
    from app.model import Usuario, db as _db
    from app.auth import proteger_passwd as _proteger_passwd

    ctx = app
    if ctx is None:
        from flask import current_app

        ctx = current_app

    with ctx.app_context():
        try:
            try:
                log.trace(f"ensure_database_initialized: engine.url = {_db.engine.url}")
            except Exception:
                log.trace("ensure_database_initialized: could not read _db.engine.url")

            try:
                db_uri = ctx.config.get("SQLALCHEMY_DATABASE_URI")
                log.trace(f"ensure_database_initialized: Flask SQLALCHEMY_DATABASE_URI = {db_uri}")
            except Exception:
                log.trace("ensure_database_initialized: could not read SQLALCHEMY_DATABASE_URI from ctx.config")

            log.trace("ensure_database_initialized: calling create_all()")
            _db.create_all()
            log.trace("ensure_database_initialized: create_all() completed")
        except Exception as exc:
            log.trace(f"ensure_database_initialized: create_all() raised: {exc}")
            try:
                log.exception("ensure_database_initialized: create_all() exception")
            except Exception:
                pass

        registro_admin = _db.session.execute(_db.select(Usuario).filter_by(tipo="admin")).scalar_one_or_none()

        if registro_admin is None:
            admin_user = _environ.get("ADMIN_USER", "app-admin")
            admin_pass = _environ.get("ADMIN_PASSWORD", "app-admin")

            nuevo = Usuario()
            nuevo.usuario = admin_user
            nuevo.acceso = _proteger_passwd(admin_pass)
            nuevo.nombre = "Administrador"
            nuevo.apellido = ""
            nuevo.correo_electronico = None
            nuevo.tipo = "admin"
            nuevo.activo = True

            _db.session.add(nuevo)
            _db.session.commit()
