__all__ = ['Bunch', 'Package', 'Database', 'HTMLReader', 'APIReader',
           'get_data_home', 'get_package_dir',
           'download_package', 'download_package_file',
           'read_text', 'read_texts']


import os
import time
import itertools
import zipfile
import json
import sqlite3
import logging


import urllib2
import httplib
import twitter
import joblib


from collections import OrderedDict
from bs4 import BeautifulSoup


# FIXME
DEBUG = bool(os.environ.get('TWORPORA_DEBUG', False))
if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig()


logger = logging.getLogger(__name__)


COLUMNS = OrderedDict((
    ('id', 'INTEGER'),
    ('collected_at', 'INTEGER'),
    ('user_id', 'INTEGER'),
    ('screen_name', 'TEXT'),
    ('text', 'TEXT'),
    ('body', 'BLOB'),
    ('error', 'BLOB')))
API = None


try:
    API = twitter.Api(
        consumer_key=os.environ.get('TWITTER_CONSUMER_KEY'),
        consumer_secret=os.environ.get('TWITTER_CONSUMER_SECRET'),
        access_token_key=os.environ.get('TWITTER_ACCESS_TOKEN'),
        access_token_secret=os.environ.get('TWITTER_ACCESS_TOKEN_SECRET'),
    )
except twitter.TwitterError as e:
    logger.info(e)
except AttributeError:
    pass


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


class Database(object):

    def __init__(self, filename):
        self.filename = filename
        self._create_table()

    def connection(self):
        return sqlite3.connect(self.filename, isolation_level=None)

    def cursor(self):
        return self.connection().cursor()

    def read(self):
        cursor = self.cursor()
        sql = ("SELECT id, text FROM tweets "
               "ORDER BY collected_at")
        rows = cursor.execute(sql).fetchall()
        return dict(rows)

    def get(self, status_id):
        cursor = self.cursor()
        status_id = int(status_id)
        sql = ("SELECT text, collected_at FROM tweets "
               "WHERE id = ? "
               "ORDER BY collected_at DESC LIMIT 1")
        row = cursor.execute(sql, (status_id,)).fetchone()
        return row

    def set(self, status_id, text=None, body=None, error=None):
        cursor = self.cursor()
        status_id = int(status_id)
        collected_at = int(time.time())
        row = self.get(status_id)
        if row:
            return
        if self.get(status_id):
            sql = ("UPDATE tweets "
                   "SET collected_at = ?, text = ?, body = ?, error = ? "
                   "WHERE id = ?")
            cursor.execute(sql, (collected_at, text, body, error, status_id))
        else:
            sql = ("INSERT INTO tweets "
                   "(id, text, body, error, collected_at) "
                   "VALUES (?, ?, ?, ?, ?)")
            cursor.execute(sql, (status_id, text, body, error, collected_at))

    def _create_table(self):
        cursor = self.cursor()
        sql = ("CREATE TABLE IF NOT EXISTS tweets(" +
               ', '.join((k + ' ' + COLUMNS[k] for k in COLUMNS)) +
               ")")
        cursor.execute(sql)


def HTMLReader(status_id, user_id):
    status_id = str(status_id)
    url = 'http://twitter.com/%s/status/%s' % (user_id, status_id)
    infile = urllib2.urlopen(url)
    # Thanks to Arturo!
    html = infile.read().replace('</html>', '') + '</html>'
    soup = BeautifulSoup(html)
    jstts = soup.select('.js-original-tweet .js-tweet-text')
    text = None
    if len(jstts) > 0:
        text = jstts[0].get_text()
    return (text, None)


def APIReader(status_id, user_id=None, client=None, sleep=None):
    if not client:
        client = API  # FIXME
    status_id = str(status_id)
    status, error = None, None
    try:
        status = client.GetStatus(status_id)
    except twitter.TwitterError as e:
        error = e
    finally:
        if sleep is not None:
            time.sleep(sleep)
        if error:
            raise error
    text = status.text
    body = status.AsDict()
    return (text, body)


def get_data_home(data_home=None):
    if data_home is None:
        data_home = os.environ.get('TWORPORA_DATA',
                                   os.path.join(os.getcwd(), 'tworpora_data'))
    if not os.path.isdir(data_home):
        os.makedirs(data_home)
    return data_home


def get_package_dir(name, data_home=None):
    data_home = get_data_home(data_home)
    return os.path.join(data_home, name)


def download_file(url, filename):
    infile = urllib2.urlopen(url)
    with open(filename, 'wb') as outfile:
        for block in itertools.count():
            s = infile.read(1024 * 16)
            if not s:
                break
            outfile.write(s)
    infile.close()


def download_package_file(name, filename, url, data_home=None):
    package_dir = get_package_dir(name, data_home)
    if not os.path.exists(package_dir):
        os.makedirs(package_dir)
    filename = os.path.join(package_dir, os.path.basename(filename))
    download_file(url, filename)


def unzip_package_file(name, filename, url=None, data_home=None):
    package_dir = get_package_dir(name, data_home)
    if not os.path.exists(package_dir):
        os.makedirs(package_dir)
    zip_filename = package_dir + '.zip'
    if not os.path.exists(zip_filename):
        if not url:
            raise ValueError
        download_file(url, zip_filename)
    with zipfile.ZipFile(zip_filename) as zf:
        fn = os.path.join(package_dir, os.path.basename(filename))
        with open(fn, 'wb') as outfile:
            infile = zf.open(filename)
            for block in itertools.count():
                s = infile.read(1024 * 16)
                if not s:
                    break
                outfile.write(s)


def read_text(database, status_id, reader=None, **kwargs):
    if not reader:
        reader = HTMLReader  # FIXME
    row = database.get(status_id)
    if row:
        return row[0]
    text, body, error = None, None, None
    try:
        result = reader(status_id, **kwargs)
        if result:
            text, body = result
    except (urllib2.HTTPError, httplib.BadStatusLine) as e:
        error = e
    except twitter.TwitterError as e:
        error = e
    row = {}
    if text:
        row['text'] = text
        if body:
            row['body'] = json.dumps(body, separators=(',', ':'))
    elif error:
        logger.info(error)
        row['error'] = repr(error)  # FIXME
    database.set(status_id, **row)
    return text


def read_text_process(filename, *args, **kwargs):
    database = Database(filename)
    return read_text(database, *args, **kwargs)


def read_texts(database, status_ids, user_ids=None, **kwargs):
    cache = database.read()
    status_ids = [int(s) for s in status_ids]
    if user_ids:
        assert len(user_ids) == len(status_ids)
    else:
        user_ids = [None for _ in range(len(status_ids))]
    user_status_ids = list(set(((s, int(u) if u else None)
                           for s, u in zip(status_ids, user_ids)
                           if s not in cache)))
    texts = None
    if len(user_status_ids) > 0:
        n_jobs = int(os.environ.get('TWORPORA_JOBS', 1))
        verbose = 0 if logger.level > 0 else 100
        texts = joblib.Parallel(backend="threading",
                                n_jobs=n_jobs, verbose=verbose)(
            joblib.delayed(read_text_process)(database.filename,
                                              s, user_id=u, **kwargs)
            for s, u in user_status_ids)
        for idx, (status_id, _) in enumerate(user_status_ids):
            cache[status_id] = texts[idx]
    return map(lambda x: cache[x], status_ids)


try:
    from . import datasets
except ImportError as e:
    logger.debug(e)
