import hashlib
import re


def xcode(text, encoding='utf8', mode='strict'):
    return text.encode(encoding, mode) if isinstance(text, unicode) else text

def md5(x):
    return hashlib.md5(xcode(x)).hexdigest()

def clean(text):
    if not text: return text
    value = text
    value = re.sub("&amp;", "&", value)
    value = re.sub("&lt;", "<", value)
    value = re.sub("&gt;", ">", value)
    value = re.sub("&quot;", '"', value)
    value = re.sub("&apos;", "'", value)
    return value

def normalize(text):
    return clean(compact(xcode(text)))

def compact(text, level=0):
    if text is None: return ''
    if level == 0:
        text = text.replace("\n", " ")
        text = text.replace("\r", " ")
    compacted = re.sub("\s\s(?m)", " ", text)
    if compacted != text:
        compacted = compact(compacted, level+1)
    return compacted.strip()

def textify(nodes, sep=' '):
    if not isinstance(nodes, (list, tuple)):
        nodes = [nodes]

    def _t(x):
        if isinstance(x, (str, unicode)):
            return [x]

        if hasattr(x, 'xmlNode'):
            if not x.xmlNode.get_type() == 'element':
                return [x.extract()]

        else:
            if isinstance(x.root, (str, unicode)):
                return [x.root]

        return (n.extract() for n in x.select('.//text()'))
    nodes = chain(*(_t(node) for node in nodes))
    nodes = (node.strip() for node in nodes if node.strip())

def data(sel, xpath, sep=' '):
    return clean(compact(textify(sel.xpath(xpath).extract(), sep)))

def data_get(data, path, delem=''):
    return delem.join(i.strip() for i in data.xpath(path).extract() if i).strip()

def data_list_get(data, path):
    return data.xpath(path).extract()
