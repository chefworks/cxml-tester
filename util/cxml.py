import argparse
import base64
import os
from urllib.parse import urlparse

import requests
from lxml import etree

XPATH_PUNCHOUT_IDENTITY = '//Header/From/Credential/Identity'
XPATH_POST_URL = '/cXML/Request/PunchOutSetupRequest/BrowserFormPost/URL'
XPATH_SHARED_SECRET = '//Header/Sender/Credential/SharedSecret'
XPATH_START_URL = '//Response/PunchOutSetupResponse/StartPage/URL'
XPATH_AUXILIARY_ID = '//SupplierPartAuxiliaryID'
XPATH_STATUS_CODE = '/cXML/Response/Status/@code'
XPATH_DEPLOYMENT_MODE = '/cXML/Request/@deploymentMode'
XPATH_OPERATION = '/cXML/Request/PunchOutSetupRequest/@operation'


def get_proxy():
    socks = os.environ.get('SOCKS', None)

    if socks:
        prox = 'socks5://%s' % socks

        return dict(http=prox, https=prox)

    return None


def post(url, data, verify=False, headers={}):
    return requests.post(
        url,
        data=data,
        proxies=get_proxy(),
        verify=verify,
        headers=headers
    )


def post_pr(xml: etree.ElementBase, url) -> (str, etree.ElementBase):
    parts = urlparse(url)

    for u in xml.xpath("//Request"):
        u.attrib['deploymentMode'] = 'test'
        pass

    for u in xml.xpath("//BrowserFormPost/URL"):
        u.text = "//%s/m2po/cxml/cartecho" % parts.netloc
        pass

    res = post(url, etree.tostring(xml, pretty_print=True))

    if not res.ok:
        raise Exception("failed with status %s" % res.status_code)

    res_xml: etree.ElementBase = etree.fromstring(res.content)

    punchout_url = str(res_xml.xpath('string(//URL)'))

    return punchout_url, res_xml


def parseargs():
    argparser = argparse.ArgumentParser(
        description='Post CXML Punchout request'
    )

    sample_host = 'https://dev.chefworks.com/adacopr.php'
    argparser.add_argument(
        'url',
        type=str,
        help=f'post CXML to this url - e.g. {sample_host}'
    )

    argparser.add_argument(
        'cxml',
        type=argparse.FileType('r'),
        help='Input CXML file'
    )

    argparser.add_argument(
        '--validate',
        dest='validate',
        action='store_const',
        const=True,
        default=False,
        help='perform DTD validation on input CXML (default: False)'
    )

    args = argparser.parse_args()

    if args.validate:
        parser = etree.XMLParser(no_network=False, dtd_validation=True)
    else:
        parser = etree.XMLParser()
        pass

    xml = etree.parse(args.cxml, parser)

    args.cxml.close()

    return xml, args


def decode_cxml(cxml_base64: str) -> etree.ElementBase:
    cxml = base64.decodebytes(cxml_base64.encode())
    parser = etree.XMLParser()
    return etree.fromstring(cxml, parser)


def load_cxml(cxml: bytes or str, subst_vars: dict = {}) -> etree.ElementBase:
    parser = etree.XMLParser()
    xml: etree.ElementBase = None
    if type(cxml) == bytes:
        xml = etree.fromstring(cxml, parser)
    else:
        xml = etree.parse(cxml, parser)
        pass

    for xpath in subst_vars:
        subst_value = subst_vars[xpath]

        if subst_value:
            # this is an attribute xpath
            # e.g. /cXML/Request/@deploymentMode
            arr = xpath.split('/@')
            attr = None
            if len(arr) > 1:
                el_xpath, attr = arr
            else:
                el_xpath = arr[0]
                pass

            for u in xml.xpath(el_xpath):
                if attr:
                    u.attrib[attr] = subst_value
                else:
                    u.text = subst_value
                    pass
                pass
            pass
        pass

    return xml


def cxml_extract(cxml: str or etree.ElementBase, xpath: str) -> str:
    xml = load_cxml(cxml.encode()) if type(cxml) == str else cxml
    arr = xml.xpath(xpath)
    if not arr:
        return ''

    res = arr[0]

    if hasattr(res, 'text'):
        return res.text  # element result

    return str(res)  # attribute result
