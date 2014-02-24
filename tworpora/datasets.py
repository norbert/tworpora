import os
import time
import re
import csv
import logging


from collections import OrderedDict, Counter
from . import Bunch, Package, Database, HTMLReader, APIReader
from . import get_package_dir
from . import download_package, download_package_file
from . import read_text, read_texts


logger = logging.getLogger(__name__)


STS = Package('sts',
    url=('http://cs.stanford.edu/people/alecmgo/'
         'trainingandtestdata.zip'),
    filename='testdata.manual.2009.06.14.csv',
    mapping=['label', None, 'created_at', 'query', 'screen_name', 'text'],
    labels={'4': 'positive', '0': 'negative', '2': 'neutral'})
STS_GOLD = Package('sts-gold',
    url=('http://tweenator.com/download/'
         'sts_gold_v03.zip'),
    filename='sts_gold_tweet.csv',
    mapping=['id', 'label', 'text'],
    labels={'4': 'positive', '0': 'negative'})
HCR = Package('hcr',
    url=('https://bitbucket.org/speriosu/updown'
         '/raw/1deb8fe45f603a61d723cc9b987ae4f36cbe6b16'
         '/data/hcr/'),
    splits=('train', 'test', 'dev'),
    mapping=['id', 'user_id', 'screen_name', 'text',
             'label', None, 'annotator', None, None])
OMD = Package('omd',
    url=('https://bitbucket.org/speriosu/updown'
         '/raw/1deb8fe45f603a61d723cc9b987ae4f36cbe6b16'
         '/data/shamma/orig/'
         'debate08_sentiment_tweets.tsv'),
    mapping=(['id', None, 'text', 'screen_name', None] +
             ['rating%d' % i for i in range(1, 9)]),
    labels={'2': 'positive', '1': 'negative', '3': 'mixed', '4': 'other'})
SENTISTRENGTH = Package('sentistrength',
    url=('http://sentistrength.wlv.ac.uk/documentation/'
         '6humanCodedDataSets.zip'),
    filename='twitter4242.txt',
    mapping=['mean_positive', 'mean_negative', 'text'])
SANDERS = Package('sanders',
    url=('http://www.sananalytics.com/lab/twitter-sentiment'
         '/sanders-twitter-0.2.zip'),
    filename='corpus.csv',
    mapping=['query', 'label', 'id'])
SEMEVAL2013 = Package('semeval2013',
    url=('http://www.cs.york.ac.uk/semeval-2013/task2/'
         '/data/uploads/datasets/'),
    filenames={
        'a': {None: 'tweeti-a.dist.tsv', 'dev': 'tweeti-a.dev.dist.tsv'},
        'b': {None: 'tweeti-b.dist.tsv', 'dev': 'tweeti-b.dev.dist.tsv'}
    },
    mapping={
        'a':['id', 'user_id', 'phrase_start', 'phrase_end', 'label'],
        'b':['id', 'user_id', 'label']
    },
    labels={'positive': 'positive', 'negative': 'negative',
            'neutral': 'neutral',
            'objective': 'neutral', 'objective-OR-neutral': 'neutral'})


def parse_row(row, mapping, labels=None, encoding='utf-8'):
    record, label = OrderedDict(), None
    for idx, key in enumerate(mapping):
        if not key:
            continue
        value = unicode(row[idx], encoding) if len(row) > idx else None
        value = value.strip() if value else None
        if key == 'label':
            if labels:
                label = labels.get(value)
            else:
                label = value
        else:
            record[key] = value
    return record, label


def load_sts_test(data_home=None):
    package_dir = get_package_dir(STS.name, data_home)
    filename = os.path.join(package_dir, STS.filename)
    if not os.path.exists(filename):
        raise RuntimeError
    records = []
    labels = []
    with open(filename, 'rb') as infile:
        reader = csv.reader(infile, dialect=csv.excel)
        for row in reader:
            record, label = parse_row(row, STS.mapping, STS.labels)
            created_at = time.strptime(record['created_at'],
                                       '%a %b %d %H:%M:%S UTC %Y')
            record['created_at'] = int(time.mktime(created_at))
            records.append(record)
            labels.append(label)
    return Bunch(name='sts-test', data=records, target=labels)


def load_sts_gold(data_home=None):
    package_dir = get_package_dir(STS_GOLD.name, data_home)
    filename = os.path.join(package_dir, STS_GOLD.filename)
    if not os.path.exists(filename):
        raise RuntimeError
    records = []
    labels = []
    with open(filename, 'rb') as infile:
        infile.readline()
        reader = csv.reader(infile, dialect=csv.excel,
                            delimiter=';')
        for row in reader:
            record, label = parse_row(row, STS_GOLD.mapping, STS_GOLD.labels)
            records.append(record)
            labels.append(label)
    return Bunch(name=STS_GOLD.name, data=records, target=labels)


def load_hcr(data_home=None):
    package_dir = get_package_dir(HCR.name, data_home)
    download_package(HCR.name, data_home)
    records = []
    labels = []
    id_filter = re.compile(r'^\d+$')
    for idx, split in enumerate(HCR.splits):
        source_path = '%s/orig/hcr-%s.csv' % (split, split)
        url = os.path.join(HCR.url, source_path)
        filename = os.path.join(package_dir, os.path.basename(source_path))
        if not os.path.exists(filename):
            download_package_file(HCR.name, source_path, url, data_home)
        with open(filename, 'rb') as infile:
            reader = csv.reader(infile)
            next(reader)
            for row in reader:
                record, label = parse_row(row, HCR.mapping)
                if not id_filter.match(record['id']):
                    record['id'] = None
                record['split'] = split
                records.append(record)
                labels.append(label)
    return Bunch(name=HCR.name, data=records, target=labels)


def load_omd(data_home=None):
    package_dir = get_package_dir(OMD.name, data_home)
    filename = os.path.join(package_dir, OMD.filename)
    if not os.path.exists(filename):
        download_package(OMD.name)
    records = []
    labels = []

    def score(ratings):
        if len(ratings) < 3:
            return
        counter = Counter(ratings)
        frac_pos = float(counter['positive']) / len(ratings)
        frac_neg = float(counter['negative']) / len(ratings)
        if frac_pos > 0.5 and frac_pos > frac_neg:
            return 'positive'
        elif frac_neg > 0.5 and frac_neg > frac_pos:
            return 'negative'
    with open(filename, 'rb') as infile:
        for _ in range(30):
            infile.readline()
        reader = csv.reader(infile, dialect=csv.excel_tab)
        for row in reader:
            record = OrderedDict()
            ratings = []
            for idx, key in enumerate(OMD.mapping):
                value = row[idx] if len(row) > idx else None
                if not key:
                    continue
                elif 'rating' in key:
                    rating = OMD.labels.get(value)
                    record[key] = rating
                    if rating:
                        ratings.append(rating)
                else:
                    record[key] = value
            records.append(record)
            label = score(ratings)
            labels.append(label)
    return Bunch(name=OMD.name, data=records, target=labels)


def load_sentistrength(data_home=None):
    package_dir = get_package_dir(SENTISTRENGTH.name, data_home)
    filename = os.path.join(package_dir, SENTISTRENGTH.filename)
    if not os.path.exists(filename):
        raise RuntimeError
    records = []
    labels = []

    def score(mean_positive, mean_negative):
        if mean_positive == mean_negative:
            return 'neutral'
        elif mean_positive > mean_negative * 1.5:
            return 'positive'
        else:
            return 'negative'
    with open(filename, 'rb') as infile:
        infile.readline()
        reader = csv.reader(infile, dialect=None,
                            delimiter='\t', quoting=csv.QUOTE_NONE)
        for row in reader:
            record, label = parse_row(row, SENTISTRENGTH.mapping,
                                      encoding='iso-8859-1')
            records.append(record)
            label = score(float(record['mean_positive']),
                          float(record['mean_negative']))
            labels.append(label)
    return Bunch(data=records, target=labels)


def load_sanders(data_home=None):
    package_dir = get_package_dir(SANDERS.name, data_home)
    filename = os.path.join(package_dir, SANDERS.filename)
    if not os.path.exists(filename):
        raise RuntimeError
    records = []
    labels = []
    database = Database(package_dir + '.db')
    with open(filename, 'rb') as infile:
        reader = csv.reader(infile, dialect=csv.excel)
        for row in reader:
            record, label = parse_row(row, SANDERS.mapping)
            text = read_text(database, record['id'],
                             reader=APIReader, sleep=6)
            record['text'] = text
            records.append(record)
            labels.append(label)
    return Bunch(name=SANDERS.name, data=records, target=labels)


def load_semeval2013(data_home=None):
    package_dir = get_package_dir(SEMEVAL2013.name, data_home)
    records = []
    labels = []
    database = Database(package_dir + '.db')

    def merge_texts(records):
        status_ids = [r['id'] for r in records]
        user_ids = [r.get('user_id') for r in records]
        texts = read_texts(database, status_ids, user_ids)
        for idx, record in enumerate(records):
            record['text'] = texts[idx]
    def extract_phrases(records):
        tokenizer = re.compile(r'\s')
        for record in records:
            if record['partition'] != 'a':
                continue
            text = record['text']
            if text is None:
                continue
            phrase_start = int(record['phrase_start'])
            phrase_end = int(record['phrase_end'])
            words = tokenizer.split(text)
            if phrase_start > len(words) or phrase_end > len(words):
                continue
            phrase = ' '.join(words[phrase_start:(phrase_end + 1)])
            record['phrase'] = phrase
    for partition in SEMEVAL2013.filenames:
        mapping = SEMEVAL2013.mapping[partition]
        filenames = SEMEVAL2013.filenames[partition]
        for split in filenames:
            filename = os.path.join(package_dir, filenames[split])
            if not os.path.exists(filename):
                raise RuntimeError
            with open(filename, 'rb') as infile:
                reader = csv.reader(infile, dialect=None,
                                    delimiter='\t')
                for row in reader:
                    record, label = parse_row(row, mapping, SEMEVAL2013.labels)
                    record['split'] = split
                    record['partition'] = partition
                    records.append(record)
                    labels.append(label)
    merge_texts(records)
    extract_phrases(records)
    return Bunch(name=SEMEVAL2013.name, data=records, target=labels)


sentiment = ['load_sts_test',
             'load_sts_gold',
             'load_hcr',
             'load_omd',
             'load_sentistrength',
             'load_sanders',
             'load_semeval2013']
__all__ = ['sentiment'] + sentiment
