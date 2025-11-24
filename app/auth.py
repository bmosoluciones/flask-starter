"""Auth module."""

from __future__ import annotations

from datetime import datetime

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user

from app.log import log
from app.model import Usuario, database
from app.forms import LoginForm
from app.i18n import _

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        usuario_id = form.email.data or ""
        clave = form.password.data or ""

        if validar_acceso(usuario_id, clave):
            registro = database.session.execute(database.select(Usuario).filter_by(usuario=usuario_id)).scalar_one_or_none()
            if not registro:
                registro = database.session.execute(database.select(Usuario).filter_by(correo_electronico=usuario_id)).scalar_one_or_none()

            if registro is not None:
                login_user(registro)
                return redirect(url_for("app.index"))

        flash(_("Usuario o contraseña incorrectos."), "error")

    return render_template("auth/login.html", form=form)


@auth.route("/logout")
def logout():
    logout_user()
    flash(_("Sesión cerrada correctamente."), "info")
    return redirect(url_for("auth.login"))


ph = PasswordHasher()


def proteger_passwd(clave: str, /) -> bytes:
    _hash = ph.hash(clave.encode()).encode("utf-8")
    return _hash


def validar_acceso(usuario_id: str, acceso: str, /) -> bool:
    log.trace(f"Verifying access for {usuario_id}")
    registro = database.session.execute(database.select(Usuario).filter_by(usuario=usuario_id)).scalar_one_or_none()

    if not registro:
        registro = database.session.execute(database.select(Usuario).filter_by(correo_electronico=usuario_id)).scalar_one_or_none()

    if registro is not None:
        try:
            ph.verify(registro.acceso, acceso.encode())
            clave_validada = True
        except VerifyMismatchError:
            clave_validada = False
    else:
        log.trace(f"User record not found for {usuario_id}")
        clave_validada = False

    log.trace(f"Access validation result is {clave_validada}")
    if clave_validada:
        registro.ultimo_acceso = datetime.now()
        database.session.commit()

    return clave_validada
