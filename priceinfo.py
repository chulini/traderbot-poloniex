import json
import redis
r = redis.StrictRedis(host='localhost', port=6379, db=0)

# returns a list of last n values
def removeIndexFromRedis(index):
	print 'removing index %s' % index
	r.lset('ticker-data',index,'_REMOVE_')
	r.lrem('ticker-data',0,'_REMOVE_')

def getLastValues(market,n):
	
	length = r.llen('ticker-data')
	ntickers = r.lrange('ticker-data',length-n,-1)
	values = []
	invalidIndex = -1
	i = 0
	while i < len(ntickers):
		tickerData = json.loads(ntickers[i])
		# print tickerData
		if market in tickerData:
			if 'last' in tickerData[market].keys():
				val = tickerData[market]['last']
				values.append(float(val))
			else:
				invalidIndex = length-n+i
				print '%s es none. tickerData[%s][last] does not exists' % (length-n+i,market)
				break
				 
		else:
			invalidIndex = length-n+i
			print '%s es none. tickerData[%s] does not exists' % (length-n+i,market) 
			print 'tickerData = %s' % json.dumps(tickerData)
			break
		i+=1
	if invalidIndex == -1:
		return values
	else:
		removeIndexFromRedis(invalidIndex)
		return

def dataLength():
	return r.llen('ticker-data')
	
def allDataIsValid(market,n):
	length = r.llen('ticker-data')
	ntickers = r.lrange('ticker-data',length-n,-1)
	invalidIndex = -1
	i = 0
	while i < len(ntickers):
		tickerData = json.loads(ntickers[i])
		if market in tickerData:
			if not 'last' in tickerData[market].keys():
				invalidIndex = length-n+i
				print '%s es none. tickerData[%s][last] does not exists' % (length-n+i,market)
				break
		else:
			invalidIndex = length-n+i
			print '%s es none. tickerData[%s] does not exists' % (length-n+i,market) 
			print 'tickerData = %s' % json.dumps(tickerData)
			break
		i+=1
		
	if invalidIndex == -1:
		return True
	else:
		return False

def deleteInvalidData(market,n):
	while not allDataIsValid(market,n):
		print 'Invalid data detected'
		length = r.llen('ticker-data')
		ntickers = r.lrange('ticker-data',length-n,-1)
		invalidIndex = -1
		i = 0
		while i < len(ntickers):
			tickerData = json.loads(ntickers[i])
			if market in tickerData:
				if not 'last' in tickerData[market].keys():
					invalidIndex = length-n+i
					print '%s es none. tickerData[%s][last] does not exists' % (length-n+i,market)
					break
					 
			else:
				invalidIndex = length-n+i
				print '%s es none. tickerData[%s] does not exists' % (length-n+i,market) 
				print 'tickerData = %s' % json.dumps(tickerData)
				break
			i+=1
		if invalidIndex == -1:
			print 'Deleted all invalid data'
		else:
			removeIndexFromRedis(invalidIndex)
