"""App module."""

from __future__ import annotations

from flask import Blueprint, render_template
from flask_login import login_required

app = Blueprint("app", __name__)


@app.route("/")
@login_required
def index():
    return render_template("index.html")
