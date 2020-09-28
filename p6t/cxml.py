import os

from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)
from lxml import etree

from util import cxml, xslt

from .settings import settings

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
    cxml_text = get_cxml_base64()

    return render_template(
        'cxml/cart.html',
        cxml=cxml_text
    )


def get_cxml_base64():
    cxml_base64 = request.form['cxml-base64']
    xml = cxml.decode_cxml(cxml_base64)
    cxml_decoded = etree.tostring(xml, pretty_print=True)
    if type(cxml_decoded) == bytes:
        cxml_text = cxml_decoded.decode()
    else:
        cxml_text = cxml_decoded
        pass
    return cxml_text


def cart2order(
        cart_cxml: str,
        identity: str,
        secret: str,
        deployment_mode: str
) -> str:

    return xslt(
        cart_cxml,
        os.path.join(os.path.dirname(__file__), 'xsl', 'cart2order.xsl'),
        identity=identity,
        secret=secret,
        deployment_mode=deployment_mode
    )


@bp.route("/order", methods=["POST", "GET"])
def cxml_order():
    # form was submitted from cart.html
    new_cart_external = request.form.get('new_cart_external')
    # convert cart submit button in order.html was pressed
    new_cart = new_cart_external or request.form.get('new_cart')

    # init secret, endpoint, identity from session if new cart
    if new_cart_external or request.method == 'GET':
        var_src = session
    else:
        var_src = request.form
        pass

    secret = var_src.get('secret', settings.SECRET)
    endpoint = var_src.get('endpoint', settings.ENDPOINT)
    identity = var_src.get('identity', settings.IDENTITY)
    deployment_mode = (
            var_src.get('deployment_mode') or settings.DEPLOYMENT_MODE
    )
    auxiliary_id = var_src.get('auxiliary_id')

    cart_cxml = ''
    cxml_status_code = None
    cxml_response = ''
    order_cxml = ''

    if request.method == 'POST':
        cart_cxml = request.form['cart_cxml']

        session['endpoint'] = endpoint
        session['secret'] = secret
        session['identity'] = identity
        session['deployment_mode'] = deployment_mode
        session['auxiliary_id'] = auxiliary_id

        if new_cart:
            order_cxml = cart2order(
                cart_cxml,
                identity,
                secret,
                deployment_mode
            )
        else:
            order_cxml = request.form['cxml']
            xdebug = request.form.get('xdebug', '')
            data = preprocess_cxml(
                order_cxml or None,
                identity or None,
                secret or None,
                None,
                auxiliary_id or None
            )

            xml, cxml_response, cxml_status_code = post_cxml(
                endpoint,
                data,
                xdebug
            )
            pass
        pass

    return render_template(
        'cxml/order.html',
        cart_cxml=cart_cxml,
        cxml=order_cxml,
        endpoint=endpoint,
        identity=identity,
        secret=secret,
        cxml_response=cxml_response,
        cxml_status_code=cxml_status_code,
        deployment_mode=deployment_mode
    )


def post_cxml(url, data, xdebug=False):
    headers = {}
    if xdebug:
        headers['Cookie'] = 'XDEBUG_SESSION=%s' % settings.XDEBUG_SESSION_NAME
        pass

    result = cxml.post(url, data, headers=headers)
    xml = None
    content = ''
    cxml_status_code = '500'

    if result.ok:

        content = result.text
        try:
            xml = cxml.load_cxml(content.encode())
            cxml_status_code = cxml.cxml_extract(xml, cxml.XPATH_STATUS_CODE)
        except Exception:
            flash('corrupt response cXML')
        pass
    else:
        result_text = (': ' + result.text if result.text else '')
        flash("%d %s%s" % (result.status_code, result.reason, result_text))
        pass

    return xml, content, cxml_status_code


@bp.route("/reset")
def cxml_reset():
    for i in [
            'endpoint',
            'secret',
            'identity',
            'cxml_data',
            'deployment_mode'
    ]:
        if i in session:
            del session[i]
            pass
        pass

    return redirect(url_for('cxml.cxml_request'))


@bp.route("/", methods=["GET", "POST"])
def cxml_request():
    """Submit cXML to endpoint URL."""
    secret = session.get('secret', settings.SECRET)
    endpoint = session.get('endpoint', settings.ENDPOINT)
    identity = session.get('identity', settings.IDENTITY)
    deployment_mode = (
        session.get('deployment_mode') or settings.DEPLOYMENT_MODE
    )

    cxml_response = ''
    cxml_status_code = None
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
        deployment_mode = request.form['deployment_mode']

        session['endpoint'] = endpoint
        session['secret'] = secret
        session['identity'] = identity
        session['cxml_data'] = cxml_data
        session['deployment_mode'] = deployment_mode

    else:
        cxml_path = os.path.join(
            os.path.dirname(__file__),
            'static',
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
            xml, cxml_response, cxml_status_code = post_cxml(
                endpoint,
                data,
                xdebug
            )
            if xml:
                start_url = cxml.cxml_extract(xml, cxml.XPATH_START_URL)
                pass
            pass

    except Exception as e:
        flash(e)
        pass

    return render_template(
        'cxml/request.html',
        cxml_response=cxml_response,
        endpoint=endpoint,
        secret=secret,
        identity=identity,
        start_url=start_url,
        form_post=form_post,
        cxml=cxml_data,
        cxml_status_code=cxml_status_code,
        deployment_mode=deployment_mode
    )
