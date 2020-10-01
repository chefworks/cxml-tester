import os
from typing import List

import pytest
from lxml import etree
from werkzeug import Request, Response

from p6t import app as flask_app
from p6t.cxml import CxmlOrderRequest, CxmlSetupRequest

setup_request_data_store: List[str] = ['']


@pytest.fixture
def app():
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def htmlparser():
    return etree.HTMLParser()


@pytest.fixture
def html_builder(htmlparser):
    def parse(data):
        return etree.fromstring(data, htmlparser)

    return parse


@pytest.fixture
def xml_builder():
    def parse(data):
        return etree.fromstring(data)

    return parse


@pytest.fixture
def get_template_vars_setup(app):
    with app.test_request_context('/'):
        inst = CxmlSetupRequest()
        template_vars = inst.template_vars.values()
        return template_vars


@pytest.fixture
def get_template_vars_order(app):
    with app.test_request_context('/'):
        inst = CxmlOrderRequest()
        template_vars = inst.template_vars.values()
        return template_vars


@pytest.fixture
def cart_cxml():
    return open('%s/data/cart.xml' % os.path.dirname(__file__)).read()


@pytest.fixture
def setup_response_cxml():
    return """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE cXML SYSTEM "http://xml.cxml.org/schemas/cXML/1.2.032/cXML.dtd">
<cXML xml:lang="en-US" version="1.2.032" payloadID="22695@cxml.chefworks.com" timestamp="2020-10-01T04:12:10">
<Response>
<Status code="200" text="OK"></Status>
<PunchOutSetupResponse>
  <StartPage>
    <URL>https://staging.chefworks.com/punchout/?buyer_cookie=x-yz-2016-16-34-19-286-BABABUBAM&amp;buyer_from=hilton1&amp;gil_sid=a2a9e762b0a1d756508895c62c79a2ea&amp;punchout=Y&amp;po_type=create&amp;pp_name=hilton&amp;custID=&amp;form_post=http%3A%2F%2Fcxml-tester-zxw7sldvra-uc.a.run.app%2Fcart&amp;page=homepage%2Fhilton&amp;page_version=42</URL>
  </StartPage>
</PunchOutSetupResponse>
</Response>
</cXML>"""


@pytest.fixture
def setup_request_data():
    return setup_request_data_store


@pytest.fixture
def setup_response_handler(setup_response_cxml, setup_request_data):
    def handler(request: Request):
        setup_request_data[0] = request.get_data()
        return Response(setup_response_cxml)

    return handler
