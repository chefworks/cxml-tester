from lxml import etree


def xslt(xml, xsl_file: str, **params):
    xt = etree.parse(xsl_file)
    dom = etree.XML(xml)
    transform = etree.XSLT(xt)

    # below, filter out empty params - xslt seems to have a problem with empty
    # params passed to template
    new_params = {}
    for i in params:
        new_params[i] = etree.XSLT.strparam(params[i])
        pass

    new_params['python'] = "1"
    newdom = transform(dom, **new_params)

    return str(newdom)
