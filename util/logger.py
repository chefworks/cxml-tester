import logging
import logging.config
from os import path

import yaml

with open('%s/../logging.yaml' % path.dirname(__file__)) as f:
    D = yaml.load(f)
    D.setdefault('version', 1)
    logging.config.dictConfig(D)


def get_logger(name):
    return logging.getLogger(name)
