import flask
from pytest_httpserver import HTTPServer

import util.cxml
from p6t.cxml import CxmlSetupRequest


def test_cart2request(app, cart_cxml, xml_builder):
    with app.test_request_context(
            '/',
            method='POST',
            data=dict(
                convert_cart2request='1',
                cart_cxml=cart_cxml
            )
    ):
        cxml_setup = CxmlSetupRequest()
        assert cxml_setup.operation.val == ''  # no initial operation mode

        def execute(operation_mode):
            cxml_setup.operation.val = operation_mode
            cxml_setup.execute()
            xml = xml_builder(cxml_setup.cxml.val)
            attr, = xml.xpath(util.cxml.XPATH_OPERATION)
            assert attr == operation_mode
            pass

        for operation_mode in ['create', 'edit', 'inspect']:
            execute(operation_mode)
            pass
    pass


def test_cxml_xpath_processing(app, xml_builder):
    with app.test_request_context('/'):
        flask.session['identity'] = 'baba'
        cxml_setup = CxmlSetupRequest()
        cxmls = cxml_setup.preprocess_cxml(cxml_setup.cxml.val)
        xml = xml_builder(cxmls)
        el, = xml.xpath(util.cxml.XPATH_PUNCHOUT_IDENTITY)
        assert el.text == 'baba'
        attr, = xml.xpath(util.cxml.XPATH_OPERATION)
        assert attr == 'create'

    with app.test_request_context('/'):
        flask.session['operation'] = 'edit'
        cxml_setup = CxmlSetupRequest()
        cxmls = cxml_setup.preprocess_cxml(cxml_setup.cxml.val)
        xml = xml_builder(cxmls)
        attr, = xml.xpath(util.cxml.XPATH_OPERATION)
        assert attr == 'edit'


def test_var_resolution(app, get_template_vars_setup):

    template_vars = get_template_vars_setup
    for method in ['GET', 'POST']:
        def mkdata():
            data = {}
            for spec in template_vars:
                data[spec.name] = 'form-' + spec.name
                pass
            return data

        data = mkdata() if method == 'POST' else None

        with app.test_request_context('/', method=method, data=data):
            for var in template_vars:
                if var.sync_session:
                    flask.session[var.name] = 'session-' + var.name
                    pass
                pass

            cxml_setup = CxmlSetupRequest()
            for var in cxml_setup.template_vars.values():
                if flask.request.method == 'GET':
                    if var.sync_session:
                        assert var.val == 'session-' + var.name
                    else:
                        assert var.val == ''
                        pass
                else:
                    assert var.val == 'form-' + var.name
                pass
            pass


def test_setup_request(
        app, httpserver: HTTPServer,
        xml_builder,
        setup_response_handler,
        setup_response_cxml,
        setup_request_data
):

    httpserver.expect_request(
        '/m2po/cxml/pr'
    ).respond_with_handler(
        setup_response_handler
    )

    with app.test_request_context('/'):
        flask.session['endpoint'] = httpserver.url_for('/m2po/cxml/pr')
        cxml_setup = CxmlSetupRequest()
        cxml_setup.post_cxml()
        assert setup_request_data[0] == cxml_setup.cxml.val
        xml = xml_builder(cxml_setup.cxml.val)
        el, = xml.xpath(util.cxml.XPATH_POST_URL)
        assert el.text == 'http://localhost/cart'
        assert cxml_setup.cxml_response.val == setup_response_cxml
        pass
    pass
