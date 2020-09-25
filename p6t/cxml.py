from flask import Blueprint
from flask import flash
from flask import render_template
from flask import request
from util import cxml
from lxml import etree
from flask import session

bp = Blueprint("cxml", __name__)

ENDPOINT = 'https://magdev23.nargila.org/m2po/cxml'


def preprocess_cxml(xml: str, identity=None, secret=None, form_post=None, auxiliary_id=None):
    try:
        xml_el = cxml.load_cxml(
            xml.encode(),
            subst_vars={
                cxml.XPATH_PUNCHOUT_IDENTITY: identity,
                cxml.XPATH_SHARED_SECRET: secret,
                cxml.XPATH_POST_URL: form_post,
                cxml.XPATH_AUXILIARY_ID: auxiliary_id
            }
        )
        return etree.tostring(xml_el, pretty_print=True)

    except Exception as e:
        return xml
    pass


@bp.route("/", methods=("GET", "POST"))
def cxml_request():
    """Submit cXML to endpoint URL."""
    content = ''
    endpoint = ''
    start_url = ''
    error = None

    if request.method == "POST":
        cxml_data = request.form["cxml"]
        endpoint = request.form["endpoint"]
        identity = request.form["identity"]
        secret = request.form["secret"]
        form_post = request.form["form_post"]
        xdebug = request.form.get('xdebug', '')
        auxiliary_id = request.form['auxiliary_id']

        headers = {}
        if xdebug:
            headers['Cookie'] = 'XDEBUG_SESSION=PHPSTORM'
            pass

        try:
            data = preprocess_cxml(
                cxml_data or None,
                identity or None,
                secret or None,
                form_post or None,
                auxiliary_id or None
            )

            result = cxml.post(endpoint, data, headers=headers)
            if not result.ok:
                error = "%d %s%s" % (result.status_code, result.reason, (': ' + result.text if result.text else ''))
            else:
                content = result.text
                try:
                    xml = cxml.load_cxml(content.encode())
                    start_url = cxml.cxml_extract(xml, cxml.XPATH_START_URL)
                except:
                    raise Warning('corrupt response cXML')
                pass

        except Exception as e:
            error = e
            pass

        flash(error)

    return render_template('cxml/request.html', content=content, endpoint=(endpoint or ENDPOINT), start_url=start_url)
