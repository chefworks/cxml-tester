from lxml import etree


def xslt(xml, xsl_file: str, **params):
    xt = etree.parse(xsl_file)
    dom = etree.XML(xml)
    transform = etree.XSLT(xt)
    params['python'] = "1"
    newdom = transform(dom)

    return str(newdom)
