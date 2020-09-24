import logging
import logging.config
from os import path
import yaml

with open('%s/../logging.yaml' % path.dirname(__file__)) as f:
    D = yaml.load(f)
    D.setdefault('version', 1)
    logging.config.dictConfig(D)

def url_log_sanitize(txt: str) -> str:
    return re.sub(r'//(.+):(.+)@', r'//\1:xxxx@', txt)

def get_logger(name):
    return logging.getLogger(name)
