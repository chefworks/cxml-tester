import os
from enum import Enum, auto
from typing import Dict, List

from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)
from lxml import etree

from util import cxml, get_logger, xslt

from .settings import settings

logger = get_logger(__name__)


class VarResolvedSource(Enum):
    NONE = auto()
    SETTINGS = auto()
    SESSION = auto()
    FORM = auto()
    pass


class TemplateVarSpec:
    def __init__(
            self,
            name: str,
            sync_session=True,
            from_settings=True,
            subst_xpath='',
            help=''
    ):
        self.name = name
        self.sync_session = sync_session
        self.subst_xpath = subst_xpath
        self.from_settings = from_settings
        self.session_var_prefix = ''
        self.val = None
        self.resolved_from = VarResolvedSource.NONE
        self.help = help
        pass

    def __str__(self):
        if self.val:
            if type(self.val) is bytes:
                return self.val.decode()
            return str(self.val)

        return ''

    def __resolve_var(self, src: dict, resolved_from: VarResolvedSource):
        no_exist = object()
        name = self.name
        if resolved_from == VarResolvedSource.SETTINGS:
            name = name.upper()
        elif resolved_from == VarResolvedSource.SESSION:
            name = self.session_var_prefix + name
        pass

        val = src.get(name, no_exist)
        if val != no_exist:
            self.val = val
            self.resolved_from = resolved_from
            pass

        return val != no_exist

    def resolve(self):
        # search:
        # 1. form
        # 2. prefixed session var
        # 3. non-prefixed session var
        # 4. settings

        for var_src, src_from in [
            (request.form, VarResolvedSource.FORM),
            (session, VarResolvedSource.SESSION),
            (settings, VarResolvedSource.SETTINGS)
        ]:
            if self.__resolve_var(var_src, src_from):
                return
            pass

        if self.from_settings:  # settings var must exist
            raise KeyError(
                '%s is missing in .env or environment' % self.name.upper()
            )
    pass


VariableSpecMap = Dict[str, TemplateVarSpec]
VariableSpecList = List[TemplateVarSpec]

bp = Blueprint("cxml", __name__)


class CxmlBase:

    def __init__(self):
        self.cxml = TemplateVarSpec('cxml', from_settings=False)
        self.identity = TemplateVarSpec(
            'identity',
            subst_xpath=cxml.XPATH_PUNCHOUT_IDENTITY
        )
        self.secret = TemplateVarSpec(
            'secret',
            subst_xpath=cxml.XPATH_SHARED_SECRET
        )
        self.endpoint = TemplateVarSpec('endpoint')
        self.xdebug = TemplateVarSpec('xdebug')
        self.cxml_status_code = TemplateVarSpec(
            'cxml_status_code',
            sync_session=False,
            from_settings=False
        )
        self.cxml_response = TemplateVarSpec(
            'cxml_response',
            sync_session=False,
            from_settings=False
        )
        self.auxiliary_id = TemplateVarSpec(
            'auxiliary_id',
            subst_xpath=cxml.XPATH_AUXILIARY_ID
        )
        self.deployment_mode = TemplateVarSpec(
            'deployment_mode',
            subst_xpath=cxml.XPATH_DEPLOYMENT_MODE
        )

        # convert cart submit button in order.html was pressed
        self.cart_cxml = TemplateVarSpec(
            'cart_cxml',
            sync_session=False,
            from_settings=False
        )

        self.template_vars: VariableSpecMap = {}

        pass

    def execute(self) -> str:
        for i in self.template_vars:
            spec = self.template_vars[i]
            if spec.sync_session:
                session[spec.session_var_prefix + i] = spec.val
                pass
            pass

        return self.execute_impl()

    def execute_impl(self) -> str:
        ...

    def init_vars(self, *template_vars):
        tmp_list: VariableSpecList = [
            self.cxml,
            self.identity,
            self.secret,
            self.endpoint,
            self.xdebug,
            self.cxml_status_code,
            self.cxml_response,
            self.auxiliary_id,
            self.deployment_mode,
            self.cart_cxml
        ]

        tmp_list.extend(template_vars)

        for spec in tmp_list:
            self.template_vars[spec.name] = spec
            spec.resolve()
            pass
        pass

    @staticmethod
    def load_sample_cxml(filename: str):
        cxml_path = os.path.join(
            os.path.dirname(__file__),
            'static',
            'cxml',
            filename
        )

        return open(cxml_path).read()

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
    def get_form_cxml_param(name: str, base64_encoded: bool):
        cxml_val = request.form[name]
        xml = cxml.decode_cxml(cxml_val, base64_encoded)
        cxml_decoded = etree.tostring(xml, pretty_print=True)
        if type(cxml_decoded) is bytes:
            cxml_text = cxml_decoded.decode()
        else:
            cxml_text = cxml_decoded
            pass
        return cxml_text

    def convert_cart(self, xsl: str):
        xslt_params = {}
        for i in self.template_vars:
            spec = self.template_vars[i]
            xslt_params[i] = spec.val or ''
            pass

        try:
            res = xslt(
                self.cart_cxml.val,
                os.path.join(os.path.dirname(__file__), 'xsl', xsl),
                **xslt_params
            )

            self.cxml.val = self.preprocess_cxml(res)

        except Exception as e:
            flash(e)
            self.cxml_status_code.val = '500'
        pass

    def post_cxml(self) -> etree.ElementBase:
        self.cxml.val = self.preprocess_cxml(self.cxml.val)
        xml = None
        content = ''
        self.cxml_status_code.val = '500'

        headers = {}
        if self.xdebug.val:
            headers['Cookie'] = (
                'XDEBUG_SESSION=%s' % settings.XDEBUG_SESSION_NAME
            )
            pass

        try:
            result = cxml.post(
                self.endpoint.val,
                self.cxml.val,
                headers=headers
            )

            if result.ok:

                content = result.text
                try:
                    xml = cxml.load_cxml(content.encode())
                    self.cxml_status_code.val = cxml.cxml_extract(
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

        self.cxml_response.val = content

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

        self.cxml.session_var_prefix = 'order_'
        self.endpoint.session_var_prefix = 'order_'

        self.init_vars()

        if not self.cxml.val:
            self.cxml.val = self.load_sample_cxml('order.xml')
            pass

        pass

    def execute_impl(self) -> str:
        if request.method == 'POST':

            if request.form.get('convert_cart2order'):
                if self.cart_cxml.val:
                    self.convert_cart('cart2order.xsl')
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
        self.buyer_cookie = TemplateVarSpec(
            'buyer_cookie',
            subst_xpath=cxml.XPATH_BUYER_COOKIE
        )
        self.browser_post_url = TemplateVarSpec(
            'browser_post_url',
            subst_xpath=cxml.XPATH_POST_URL
        )
        self.operation = TemplateVarSpec(
            'operation',
            subst_xpath=cxml.XPATH_OPERATION
        )
        self.start_url = TemplateVarSpec(
            'start_url',
            sync_session=False,
            from_settings=False
        )

        self.cxml.session_var_prefix = 'request_'
        self.endpoint.session_var_prefix = 'request_'

        self.init_vars(
            self.buyer_cookie,
            self.browser_post_url,
            self.start_url,
            self.operation
        )

        if not self.browser_post_url.val:
            # set default if unmodified is empty
            self.browser_post_url.val = request.url + 'cart'
            pass

        if not self.cxml.val:
            self.cxml.val = self.load_sample_cxml('create.xml')
            pass
        pass

    def execute_impl(self) -> str:
        if request.method == 'POST':
            if request.form.get('convert_cart2request'):
                if self.cart_cxml.val:
                    self.convert_cart('cart2setup.xsl')
                    pass
            else:
                xml = self.post_cxml()

                if xml is not None:
                    self.start_url.val = cxml.cxml_extract(
                        xml, cxml.XPATH_START_URL
                    )
                    pass
                pass
            pass

        return self.render_template('cxml/request.html')
    pass


@bp.route("/", methods=["GET", "POST"])
def cxml_request():

    controller = CxmlSetupRequest()
    return controller.execute()


@bp.route("/cart", methods=["POST", "GET"])
def cxml_cart():

    def get_cxml(name: str, base64_encoding: bool):
        if request.form.get(name):
            return CxmlBase.get_form_cxml_param(name, base64_encoding)
        else:
            return session.get(name) or ''
        pass

    cxml_text = get_cxml('cxml-base64', True)
    cxml_urlencoded = get_cxml('cxml-urlencoded', False)
    session['cxml-base64'] = cxml_text
    session['cxml-urlencoded'] = cxml_urlencoded

    return render_template(
        'cxml/cart.html',
        cxml=cxml_text,
        cxml_urlencoded=cxml_urlencoded
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

    for i in ['cxml-base64', 'cxml-urlencoded']:
        if session.get(i):
            del session[i]
            pass
        pass

    return redirect(url_for('cxml.cxml_request'))


@bp.errorhandler(Exception)
def handle_exception(e):
    logger.critical(
        'exception handler: %s' % str(e),
        exc_info=e,
        stack_info=True
    )
    return {
               'error': str(e),
               'type': e.__class__.__name__
           }, 400
