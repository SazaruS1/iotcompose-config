import datetime

from flask import Blueprint, render_template

def create_webapp(pid):

    webapp = Blueprint(pid, __name__, template_folder="views")

    @webapp.route('/')
    def index():
        return render_template('about/index.html')

    return webapp