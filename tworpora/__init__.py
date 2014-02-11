__all__ = ['Bunch', 'Package',
           'get_data_home', 'get_package_dir',
           'download_package', 'download_package_file']


import os
import itertools
import logging


import urllib2


# FIXME
DEBUG = bool(os.environ.get('TWORPORA_DEBUG', False))
if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig()


logger = logging.getLogger(__name__)


class Bunch(dict):

    def __init__(self, **kwargs):
        dict.__init__(self, kwargs)
        self.__dict__ = self


class Package(Bunch):

    def __init__(self, name, **kwargs):
        kwargs.update(name=name)
        super(Package, self).__init__(**kwargs)

    @property
    def filename(self):
        return self.get('filename', (os.path.basename(self.url) or None))


def get_data_home(data_home=None):
    if data_home is None:
        data_home = os.environ.get('TWORPORA_DATA',
                                   os.path.join(os.getcwd(), 'data'))
    if not os.path.isdir(data_home):
        raise RuntimeError
    return data_home


def get_package_dir(name, data_home=None):
    data_home = get_data_home(data_home)
    return os.path.join(data_home, name)


def download_package(name, filename=None, data_home=None):
    package_dir = get_package_dir(name, data_home)
    if not os.path.isdir(package_dir):
        os.makedirs(package_dir)
    if filename is None:
        return
    download_package_file(name, filename)


def download_package_file(name, filename, url=None, data_home=None):
    package_dir = get_package_dir(name, data_home)
    if not os.path.isdir(package_dir):
        raise RuntimeError
    url = url or package.url
    filename = os.path.join(package_dir, os.path.basename(filename))
    infile = urllib2.urlopen(url)
    with open(filename, 'wb') as outfile:
        for block in itertools.count():
            s = infile.read(1024 * 16)
            outfile.write(s)
            if not s:
                break
    infile.close()


try:
    from . import datasets
    from datasets import *
except ImportError as e:
    logger.debug(e)
