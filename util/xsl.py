from lxml import etree


def xslt(xml, xsl_file: str, **params):
    xt = etree.parse(xsl_file)
    dom = etree.XML(xml)
    transform = etree.XSLT(xt)

    # below, filter out empty params - xslt seems to have a problem with empty params passed to template
    new_params = {}
    for i in params:
        if params[i]:
            new_params[i] = params[i]
            pass
        pass

    new_params['python'] = "1"
    newdom = transform(dom, **new_params)

    return str(newdom)
