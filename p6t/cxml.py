from flask import Blueprint
from flask import flash
from flask import render_template
from flask import request

bp = Blueprint("cxml", __name__)

ENDPOINT = 'https://magdev23.nargila.org/m2po/cxml'


@bp.route("/", methods=("GET", "POST"))
def cxml_request():
    """Submit cXML to endpoint URL."""
    result = ''
    endpoint = ''

    if request.method == "POST":
        cxml = request.form["cxml"]
        endpoint = request.form["endpoint"]
        result = cxml
        error = None
        # flash(error)

    return render_template('cxml/request.html', result=result, endpoint=(endpoint or ENDPOINT))
