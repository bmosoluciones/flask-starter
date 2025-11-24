"""Data model for the app package."""

from __future__ import annotations

from datetime import date, datetime, timezone

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from ulid import ULID


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
database = db


def generador_de_codigos_unicos() -> str:
    codigo_aleatorio = ULID()
    id_unico = str(codigo_aleatorio)
    return id_unico


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BaseTabla:
    id = database.Column(database.String(26), primary_key=True, nullable=False, index=True, default=generador_de_codigos_unicos)
    timestamp = database.Column(database.DateTime, default=utc_now, nullable=False)
    creado = database.Column(database.Date, default=date.today, nullable=False)
    creado_por = database.Column(database.String(150), nullable=True)
    modificado = database.Column(database.DateTime, onupdate=utc_now, nullable=True)
    modificado_por = database.Column(database.String(150), nullable=True)


class Usuario(UserMixin, database.Model, BaseTabla):
    __table_args__ = (database.UniqueConstraint("usuario", name="id_usuario_unico"),)
    __table_args__ = (database.UniqueConstraint("correo_electronico", name="correo_usuario_unico"),)

    usuario = database.Column(database.String(150), nullable=False, index=True, unique=True)
    acceso = database.Column(database.LargeBinary(), nullable=False)
    nombre = database.Column(database.String(100))
    apellido = database.Column(database.String(100))
    correo_electronico = database.Column(database.String(150))
    correo_electronico_verificado = database.Column(database.Boolean(), default=False)
    tipo = database.Column(database.String(20))
    activo = database.Column(database.Boolean())
