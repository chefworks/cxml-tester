import os
from typing import Dict

from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)
from lxml import etree

from util import cxml, xslt

from .settings import settings


class TemplateVarSpec:
    def __init__(self, sync_session=True, from_settings=True, subst_xpath=''):
        self.sync_session = sync_session
        self.subst_xpath = subst_xpath
        self.from_settings = from_settings
        self.session_var_prefix = ''
        self.val = None
        pass

    def __str__(self):
        if self.val:
            if type(self.val) == bytes:
                return self.val.decode()
            return str(self.val)

        return ''
    pass


VariableSpecMap = Dict[str, TemplateVarSpec]

bp = Blueprint("cxml", __name__)


class CxmlBase:

    def __init__(self):
        self.template_vars: VariableSpecMap = dict(
            cxml=TemplateVarSpec(from_settings=False),
            identity=TemplateVarSpec(subst_xpath=cxml.XPATH_PUNCHOUT_IDENTITY),
            secret=TemplateVarSpec(subst_xpath=cxml.XPATH_SHARED_SECRET),
            endpoint=TemplateVarSpec(),
            browser_post_url=TemplateVarSpec(subst_xpath=cxml.XPATH_POST_URL),
            xdebug=TemplateVarSpec(),
            cxml_status_code=TemplateVarSpec(
                sync_session=False,
                from_settings=False
            ),
            cxml_response=TemplateVarSpec(
                sync_session=False,
                from_settings=False
            ),
            auxiliary_id=TemplateVarSpec(subst_xpath=cxml.XPATH_AUXILIARY_ID),
            deployment_mode=TemplateVarSpec(
                subst_xpath=cxml.XPATH_DEPLOYMENT_MODE
            )
        )

        self.status_code_var = self.template_vars['cxml_status_code']
        self.cxml_var = self.template_vars['cxml']
        self.endpoint_var = self.template_vars['endpoint']

        pass

    def execute(self) -> str:
        for i in self.template_vars:
            spec = self.template_vars[i]
            if spec.sync_session:
                session[i] = spec.val
                pass
            pass

        return self.execute_impl()

    def execute_impl(self):
        ...

    def init_vars(self):
        for i in self.template_vars:
            spec = self.template_vars[i]
            # search:
            # 1. form
            # 2. prefixed session var
            # 3. non-prefixed session var
            # 4. settings
            spec.val = (
                request.form.get(i) or
                session.get(spec.session_var_prefix + i) or
                session.get(i)
            )
            if not spec.val and spec.from_settings:
                spec.val = settings[i.upper()]
            pass
        pass

    def preprocess_cxml(self, xml: str) -> str:
        subst_vars = self.make_xpath_subst_map()

        try:
            xml_el = cxml.load_cxml(
                xml.encode(),
                subst_vars=subst_vars
            )
            return etree.tostring(xml_el, pretty_print=True)

        except Exception:
            return xml
        pass

    def make_xpath_subst_map(self):
        subst_vars = {}
        for i in self.template_vars:
            spec = self.template_vars[i]
            if spec.subst_xpath:
                subst_vars[spec.subst_xpath] = spec.val
                pass
            pass
        return subst_vars

    def make_template_subst_map(self):
        subst_vars = {}
        for i in self.template_vars:
            spec = self.template_vars[i]
            subst_vars[i] = spec.val
            pass
        # return subst_vars
        return self.template_vars

    @staticmethod
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

    def cart2order(self, cart_cxml: str) -> str:
        xslt_params = {}
        for i in self.template_vars:
            spec = self.template_vars[i]
            xslt_params[i] = spec.val or ''
            pass

        res = xslt(
            cart_cxml,
            os.path.join(os.path.dirname(__file__), 'xsl', 'cart2order.xsl'),
            **xslt_params
        )

        return self.preprocess_cxml(res)

    def post_cxml(self) -> etree.ElementBase:
        self.cxml_var.val = self.preprocess_cxml(self.cxml_var.val)
        xml = None
        content = ''
        self.status_code_var.val = '500'

        headers = {}
        if self.template_vars['xdebug'].val:
            headers['Cookie'] = (
                'XDEBUG_SESSION=%s' % settings.XDEBUG_SESSION_NAME
            )
            pass

        try:
            result = cxml.post(
                self.template_vars['endpoint'].val,
                self.cxml_var.val,
                headers=headers
            )

            if result.ok:

                content = result.text
                try:
                    xml = cxml.load_cxml(content.encode())
                    self.status_code_var.val = cxml.cxml_extract(
                        xml,
                        cxml.XPATH_STATUS_CODE
                    )
                except Exception as e:
                    flash('corrupt response cXML: %s' % e)
                pass
            else:
                result_text = (': ' + result.text if result.text else '')
                flash(
                    "%d %s%s" % (
                        result.status_code,
                        result.reason,
                        result_text
                    )
                )
                pass

        except Exception as e:
            flash('Error submitting form: %s' % e)
            pass

        cxml_response = self.template_vars['cxml_response']
        cxml_response.val = content

        return xml

    def render_template(self, template: str):
        template_vars = self.make_template_subst_map()

        return render_template(template, **template_vars)

    def reset(self):
        for i in self.template_vars:
            spec = self.template_vars[i]
            if not spec.sync_session:
                continue

            for sess_var_name in [spec.session_var_prefix + i, i]:
                if sess_var_name in session:
                    del session[sess_var_name]
                    pass
                pass
            pass
        pass
    pass


class CxmlOrderRequest(CxmlBase):
    def __init__(self):
        super().__init__()
        self.template_vars.update(
            dict(
                # form was submitted from cart.html
                convert_cart=TemplateVarSpec(
                    sync_session=False,
                    from_settings=False
                ),
                cart_cxml=TemplateVarSpec(
                    sync_session=False,
                    from_settings=False
                ),
                # convert cart submit button in order.html was pressed
                new_cart=TemplateVarSpec(
                    sync_session=False,
                    from_settings=False
                ),
            )
        )

        self.cxml_var.session_var_prefix = 'order_'
        self.endpoint_var.session_var_prefix = 'order_'

        self.init_vars()

        pass

    def execute_impl(self):
        if request.method == 'POST':
            convert_cart = self.template_vars['convert_cart'].val
            cart_cxml_var = self.template_vars['cart_cxml']

            if convert_cart:
                if cart_cxml_var.val:
                    try:
                        self.cxml_var.val = self.cart2order(cart_cxml_var.val)
                    except Exception as e:
                        flash(e)
                        self.status_code_var.val = '500'
                        pass
                    pass
            else:
                self.post_cxml()
                pass
            pass

        return self.render_template('cxml/order.html')
    pass


class CxmlSetupRequest(CxmlBase):
    def __init__(self):
        super().__init__()
        self.template_vars.update(
            dict(
                browser_post_url=TemplateVarSpec(
                    subst_xpath=cxml.XPATH_POST_URL
                ),
                start_url=TemplateVarSpec(
                    sync_session=False,
                    from_settings=False
                )
            )
        )

        self.cxml_var.session_var_prefix = 'request_'

        self.init_vars()

        browser_post_url_var = self.template_vars['browser_post_url']

        if not browser_post_url_var.val:
            browser_post_url_var.val = request.url + 'cart'
            pass

        if not self.cxml_var.val:
            self.cxml_var.val = self.load_sample_cxml()
            pass
        pass

    @staticmethod
    def load_sample_cxml():
        cxml_path = os.path.join(
            os.path.dirname(__file__),
            'static',
            'cxml',
            'create.xml'
        )

        return open(cxml_path).read()

    def execute_impl(self) -> str:
        if request.method == 'POST':
            xml = self.post_cxml()

            if xml is not None:
                start_url_var = self.template_vars['start_url']
                start_url_var.val = cxml.cxml_extract(
                    xml, cxml.XPATH_START_URL
                )
                pass
            pass
        return self.render_template('cxml/request.html')
    pass


@bp.route("/", methods=["GET", "POST"])
def cxml_request():

    controller = CxmlSetupRequest()
    return controller.execute()


@bp.route("/cart", methods=["POST"])
def cxml_cart():
    cxml_text = CxmlBase.get_cxml_base64()

    return render_template(
        'cxml/cart.html',
        cxml=cxml_text
    )


@bp.route("/order", methods=["POST", "GET"])
def cxml_order():
    controller = CxmlOrderRequest()
    return controller.execute()


@bp.route("/reset")
def cxml_reset():
    for controller in [CxmlSetupRequest(), CxmlOrderRequest()]:
        controller.reset()
        pass

    return redirect(url_for('cxml.cxml_request'))
