import sched
from datetime import datetime
import urllib
import urllib2
import json
import time
import requests
from requests.exceptions import HTTPError
import sys


import redis
r = redis.StrictRedis(host='localhost', port=6379, db=0)

starttime=time.time()
while True:
	try:
		req = requests.post('https://poloniex.com/public?command=returnTicker')
		if(req.reason == 'OK'):
			ticker = req.text
			tickerDict = json.loads(req.text)
			if 'BTC_ETH' in tickerDict:
				if 'last' in tickerDict.get('BTC_ETH').keys():
					r.rpush('ticker-time',time.time())
					r.rpush('ticker-data',ticker)
					s = "%s) %.2f saved" % (r.llen('ticker-time') , time.time())
					r.bgsave()
					sys.stdout.write(s)
				else:
					print 'ticker not valid = %s' % ticker
			else:
				print 'ticker not valid = %s' % ticker

			
		else:
			print('Post failed. Reason:%s Text: %s' % (req.reason,req.text))
	except requests.exceptions.RequestException as e:
		print 'Post failed. Exception %s' % e

	towait = 60.0 - ((time.time() - starttime) % 60.0)
	i = 1
	while i <= 60:
		sys.stdout.write('.')
		if i % 10 == 0:
			sys.stdout.write('|')
		sys.stdout.flush()
		time.sleep(towait/60.0)
		i += 1
	print ''
