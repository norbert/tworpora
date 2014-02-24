#!/usr/bin/env python


from __future__ import print_function


import sys
import re
import argparse


from . import datasets


parser = argparse.ArgumentParser(prog='tworpora')
parser.add_argument('-q', '--quiet', action='store_true')
parser.add_argument('NAME')
args = parser.parse_args()


function = getattr(datasets, 'load_' + args.NAME)
data = function()


if args.quiet:
    sys.exit(0)


FIELDS = ('id', 'collected_at', 'user_id', 'screen_name')


keys = data.data[0].keys()
headers = (['label'] +
           [f for f in FIELDS if f in keys] +
           [k for k in keys if not k in FIELDS])
headers.remove('text')
tokenizer = re.compile(r'\s+')


print(u'\t'.join(headers + ['text']).encode('utf-8'))
for record, label in zip(data.data, data.target):
    text = record.get('text')
    if isinstance(text, basestring) and not isinstance(text, unicode):
        text = unicode(text, 'utf-8', 'replace')
    if text:
        text = tokenizer.sub(' ', text)
    record['label'] = label
    row = []
    for key in headers:
        value = record.get(key) or ''
        if not isinstance(value, basestring):
            value = str(value)
        row.append(value)
    row.append(text or '')
    print(u'\t'.join(row).encode('utf-8'))
