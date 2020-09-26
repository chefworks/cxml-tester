import os

from flask import Blueprint, flash, render_template, request, session
from lxml import etree
from .settings import settings
from util import cxml, xslt

bp = Blueprint("cxml", __name__)


def preprocess_cxml(
        xml: str,
        identity=None,
        secret=None,
        form_post=None,
        auxiliary_id=None
):
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

    except Exception:
        return xml
    pass


@bp.route("/cart", methods=["POST"])
def cxml_cart():
    cxml_base64 = request.form['cxml-base64']
    xml = cxml.decode_cxml(cxml_base64)
    cxml_decoded = etree.tostring(xml, pretty_print=True)

    if type(cxml_decoded) == bytes:
        cxml_text = cxml_decoded.decode()
    else:
        cxml_text = cxml_decoded
        pass

    return render_template(
        'cxml/cart.html',
        cxml=cxml_text
    )


def cart2order(cart_cxml: str, identity: str, secret: str) -> str:
    return xslt(
        cart_cxml,
        os.path.join(os.path.dirname(__file__), 'xsl', 'cart2order.xsl'),
        identity=identity,
        secret=secret
    )


@bp.route("/order", methods=["POST"])
def cxml_order():
    new_cart = request.form.get('new_cart')
    # init secret, endpoint, identity from session if new cart
    var_src = session if new_cart else request.form

    secret = var_src.get('secret', settings.SECRET)
    endpoint = var_src.get('endpoint', settings.ENDPOINT)
    identity = var_src.get('identity', settings.IDENTITY)
    cxml_response = ''
    cart_cxml = request.form['cart_cxml']

    if new_cart:
        order_cxml = cart2order(request.form['cart_cxml'], identity, secret)
    else:
        order_cxml = request.form['order_cxml']
        auxiliary_id = request.form.get('auxiliary_id')
        xdebug = request.form.get('xdebug', '')
        data = preprocess_cxml(
            order_cxml or None,
            identity or None,
            secret or None,
            None,
            auxiliary_id or None
        )
        session['endpoint'] = endpoint
        session['secret'] = secret
        session['identity'] = identity

        xml, cxml_response = post_cxml(endpoint, data, xdebug)

    return render_template(
        'cxml/order.html',
        cart_cxml=cart_cxml,
        order_cxml=order_cxml,
        endpoint=endpoint,
        identity=identity,
        secret=secret,
        cxml_response=cxml_response
    )


def post_cxml(url, data, xdebug=False):
    headers = {}
    if xdebug:
        headers['Cookie'] = 'XDEBUG_SESSION=%s' % settings.XDEBUG_SESSION_NAME
        pass

    result = cxml.post(url, data, headers=headers)
    xml = None
    content = ''

    if result.ok:

        content = result.text
        try:
            xml = cxml.load_cxml(content.encode())
        except Exception:
            flash('corrupt response cXML')
        pass
    else:
        result_text = (': ' + result.text if result.text else '')
        flash("%d %s%s" % (result.status_code, result.reason, result_text))
        pass

    return xml, content


@bp.route("/", methods=["GET", "POST"])
def cxml_request():
    """Submit cXML to endpoint URL."""
    endpoint = session.get('endpoint', '')
    secret = session.get('secret', '')
    identity = session.get('identity', '')
    content = ''
    start_url = ''
    form_post = request.url + 'cart'
    auxiliary_id = ''

    if request.method == "POST":
        cxml_data = request.form["cxml"]
        endpoint = request.form["endpoint"]
        identity = request.form["identity"]
        secret = request.form["secret"]
        form_post = request.form["form_post"]
        xdebug = request.form.get('xdebug', '')
        auxiliary_id = request.form['auxiliary_id']

        session['endpoint'] = endpoint
        session['secret'] = secret
        session['identity'] = identity
        session['cxml_data'] = cxml_data
    else:
        cxml_path = os.path.join(
            os.path.dirname(__file__),
            'cxml',
            'create.xml'
        )
        cxml_data = session.get('cxml_data', '') or open(cxml_path).read()
        pass

    try:
        data = preprocess_cxml(
            cxml_data or None,
            identity or None,
            secret or None,
            form_post or None,
            auxiliary_id or None
        )

        if request.method == "POST":
            xml, content = post_cxml(endpoint, data, xdebug)
            if xml:
                start_url = cxml.cxml_extract(xml, cxml.XPATH_START_URL)
                pass
            pass

    except Exception as e:
        flash(e)
        pass

    return render_template(
        'cxml/request.html',
        content=content,
        endpoint=endpoint,
        secret=secret,
        identity=identity,
        start_url=start_url,
        form_post=form_post,
        cxml=cxml_data
    )
