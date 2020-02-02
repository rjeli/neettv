#!/usr/bin/env python3
import time
import gzip
import json

from web import app, db
from models import Upload, Video

def iter_dicts(d, cb):
	stack = [d]
	while stack:
		el = stack.pop()
		if isinstance(el, dict):
			cb(el)
			stack.extend(el.values())
		elif isinstance(el, list):
			stack.extend(el)

if __name__ == '__main__':
	while True:
		print('starting index.')
		with app.app_context():
			for u in Upload.query.all():
				print('upload', u.id)
				t0 = time.time()
				doc = json.loads(gzip.decompress(u.payload))
				t1 = time.time()
				print('loaded in', (t1-t0)*1000, 'ms')

				def cb(el):
					if 'compactVideoRenderer' in el:
						src_id = el['compactVideoRenderer']['navigationEndpoint']['watchEndpoint']['videoId']
						title = el['compactVideoRenderer']['title']['simpleText']
						print('found vid:', src_id, title)

						v = Video.query.filter_by(src='yt', src_id=src_id).first()
						if v is None:
							v = Video(src='yt', src_id=src_id)
							db.session.add(v)
						v.title = title
						db.session.commit()

				iter_dicts(doc, cb)

		print('sleeping.')
		time.sleep(5)