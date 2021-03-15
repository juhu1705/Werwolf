import functools
import os

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app
)

bp = Blueprint('game', __name__)


@bp.route('/')
def start():
    return render_template('game.html')


@bp.route('/imprint')
def imprint():
    return render_template('imprint.html')


@bp.route('/privacy')
def privacy():
    return render_template('privacy.html')


@bp.route('/license')
def license():
    return render_template('license.html')
