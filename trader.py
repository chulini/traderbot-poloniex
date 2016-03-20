import sys
import poloniex
import stats
import priceinfo
import credentials
import json
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.pyplot import plot, draw, show

import matplotlib.ticker as mticker
import matplotlib.dates as mdates
from requests.exceptions import HTTPError
import time
import urllib2

pol = poloniex.poloniex(credentials.credentials.apikey,credentials.credentials.secret)

# #in minutes
# shortEMALength = 10*5 #20*60
# longEMALength = 200*5 #80*60
# priceinfo.removeIndexFromRedis(7150)



def simulateTrade(market, prices, dataLength, shortEMALength, longEMALength, tradeFreeze, savePlot):

	# print 'market=%s\tlen(prices)=%s\tdataLength=%s\tshortEMALength=%s\tlongEMALength=%s\ttradeFreeze=%s\tsavePlot=%s' % (market, len(prices), dataLength, shortEMALength, longEMALength, tradeFreeze, savePlot)

	shortEMA = stats.ExpMovingAverage(prices,shortEMALength)
	longEMA = stats.ExpMovingAverage(prices,longEMALength)

	#returns True if buy, returns False if sell
	def emaTrade(i):
		return (shortEMA[i] > longEMA[i])




	# print 'API %s' % pol.buy('BTC_ETH',prices[-1],amount_btc/prices[-1])
	# returns  {u'orderNumber': u'20852014261', u'resultingTrades': [{u'tradeID': u'3718537', u'rate': u'0.02382087', u'amount': u'2.09731543', u'date': u'2016-03-09 03:40:07', u'total': u'0.04995987', u'type': u'buy'}]}

	# TODO meter esto dentro de un ciclo y que compre/venda
	buyPoints = []
	buyPoints.append([])
	buyPoints.append([])
	sellPoints = []
	sellPoints.append([])
	sellPoints.append([])
	i = longEMALength
	tradeFreezedCounter = 0;
	bougth = False
	btc = 1
	eth = 0
	# print "price\tsEMA\tlEMA\tbuy"
	while i < dataLength:
		if(tradeFreezedCounter <= 0 and not bougth and emaTrade(i-1) == False and emaTrade(i) == True and i > 0):
			tradeFreezedCounter = tradeFreeze
			buyPoints[0].append(i)
			buyPoints[1].append(prices[i])
			bougth = True
			eth = (btc/prices[i])*0.998 #0.2% fee

			btc = 0

			# print "buy\t%.6f\t%.6f\t%.6f\t%s" % (prices[i],shortEMA[i],longEMA[i],emaTrade(i))
			
		elif(tradeFreezedCounter <= 0 and bougth and emaTrade(i-1) == True and emaTrade(i) == False and i > 0):
			tradeFreezedCounter = tradeFreeze
			sellPoints[0].append(i)
			sellPoints[1].append(prices[i])
			bougth = False
			
			btc = eth*prices[i]*0.998 #0.2% fee
			eth = 0;
			# print "sell\t%.6f\t%.6f\t%.6f\t%s" % (prices[i],shortEMA[i],longEMA[i],emaTrade(i))

		tradeFreezedCounter -= 1;
		i += 1

	if savePlot :
		indexes = []
		i = 0
		while i < dataLength:
			indexes.append(i)
			i += 1


		fig = plt.figure(figsize=(20,8))
		# ax1 = plt.subplot2grid((40,40),(0,0),rowspan=40,colspan=40)
		ax1 = fig.add_subplot(111)
		ax1.plot(indexes[longEMALength:],shortEMA[longEMALength:])
		ax1.plot(indexes[longEMALength:],prices[longEMALength:])
		ax1.plot(indexes[longEMALength:],longEMA[longEMALength:])
		# ax1.plot(buyPoints[0],buyPoints[1],'b^')
		# ax1.plot(sellPoints[0],sellPoints[1],'rv')

		# ax = fig.add_subplot(111)
		# print '(%s,%s)' % (buyPoints[0][0],buyPoints[1][0])
		i = 0
		while i < len(buyPoints[0]):
			annotationText = 'Buy @ %s' % buyPoints[1][i]
			ax1.annotate(annotationText,
	            xy=(buyPoints[0][i],buyPoints[1][i]), xycoords='data',
	            xytext=(buyPoints[0][i],1.1*buyPoints[1][i]), textcoords='data',
	            size=10, va="center", ha="center",
	            arrowprops=dict(arrowstyle="fancy",
	            				color="b",
                            shrinkB=5,
                            connectionstyle="arc3,rad=-0.5"), 
	            )
			i += 1
		i = 0
		while i < len(sellPoints[0]):
			annotationText = 'Sell @ %s' % sellPoints[1][i]
			ax1.annotate(annotationText,
	            xy=(sellPoints[0][i],sellPoints[1][i]), xycoords='data',
	            xytext=(sellPoints[0][i],1.1*sellPoints[1][i]), textcoords='data',
	            size=10, va="center", ha="center",
	            arrowprops=dict(arrowstyle="fancy",
	            				color="r",
                            shrinkB=5,
                            connectionstyle="arc3,rad=-0.5"), 
	            )
			i += 1
			
		

		plt.ioff()
		plt.grid(True)
		plotname = 'plots/%s_%s_%s_%s.png' % (market,shortEMALength,longEMALength,tradeFreeze)
		plt.savefig(plotname, bbox_inches='tight')
		plt.close()
		print 'Plot @ %s saved' % plotname
	return (btc + eth*prices[dataLength-1])




# uses all history data to get best parameters for long/short ema
#'BTC_ETH'	159 	 1156 	 0 		1.53170917098 
def getBestParams(market, shortFrom, shortTo, shortDelta, longTo, longDelta):
	dataLength = priceinfo.dataLength()
	prices = priceinfo.getLastValues(market,dataLength)

	bestResult = 0
	bestShort = 0
	bestLong = 0
	bestFreeze = 0

	longE = 1;
	fr = 0
	bestFr = 0
	

	shortE = shortFrom
	while shortE < shortTo:
		print "short = %s" % shortE
		longE = shortE+300
		while longE < longTo:

			result = simulateTrade(market=market, prices=prices, dataLength = dataLength,shortEMALength=shortE, longEMALength=longE,tradeFreeze=fr,savePlot=False);
			if result > bestResult:
				result = simulateTrade(market=market, prices=prices, dataLength = dataLength,shortEMALength=shortE, longEMALength=longE,tradeFreeze=fr,savePlot=True);
				bestResult = result
				bestShort = shortE
				bestLong = longE
				bestFr = fr
				print '%s \t %s \t %s \t %s ' % (bestShort,bestLong,bestFr,bestResult);

			longE+=longDelta

		shortE+=shortDelta


# print json.dumps(pol.returnOrderBook('BTC_ETH')) 
# purchasers pay the ask price // sellers receive the bid price
def buy(market,totalAmount): #totalAmount in ETH
	
	boughtAmount = 0
	while boughtAmount < totalAmount:
		askPrice,askAmount = getLowestAsk(market)
		remainingToBuy = totalAmount - boughtAmount
		if remainingToBuy <= askAmount:
			rBuy = pol.buy(currencyPair=market,rate=float(askPrice),amount=remainingToBuy)
			print rBuy
			if not (rBuy is None) and not ('error' in rBuy.keys()):
				boughtAmount += remainingToBuy
				print "\tbought %.8f at %.8f (%.8f remaining)" % (remainingToBuy,float(askPrice),(totalAmount - boughtAmount))
			else:
				print "buy ended"
				return False
				
		else:
			rBuy = pol.buy(currencyPair=market,rate=float(askPrice),amount=askAmount)
			print rBuy
			if not (rBuy is None) and not ('error' in rBuy.keys()):
				boughtAmount += askAmount
				print "\tbought %.8f at %.8f (%.8f remaining)" % (askAmount,float(askPrice),(totalAmount - boughtAmount))
			else:
				print "buy ended"
				return False
	return True


# TODO test
def sell(market,totalAmount): #totalAmount in ETH
	
	soldAmount = 0
	while soldAmount < totalAmount:
		bidPrice,bidAmount = getHighestBid(market)
		remainingToSell = totalAmount - soldAmount
		if remainingToSell <= bidAmount:
			rSell = pol.sell(currencyPair=market,rate=float(bidPrice),amount=remainingToSell)
			print rSell
			if not (rSell is None) and not ('error' in rSell.keys()):
				soldAmount += remainingToSell
				print "\tsold %.8f at %.8f (%.8f remaining)" % (remainingToSell,float(bidPrice),(totalAmount - soldAmount))
			else:
				print 'Sell ended'
				return False
		else:
			rSell = pol.sell(currencyPair=market,rate=float(bidPrice),amount=bidAmount)
			print rSell
			if not (rSell is None) and not ('error' in rSell.keys()):
				soldAmount += bidAmount
				print "\tsold %.8f at %.8f (%.8f remaining)" % (bidAmount,float(bidPrice),(totalAmount - soldAmount))
			else:
				print 'Sell ended'
				return False
	return True



		

def getLowestAsk(market):
	try:
		orderBook = pol.returnOrderBook(market)
		if not (orderBook is None):
			if orderBook.get('isFrozen') == '0':
				asks = orderBook.get('asks')
				sortedAsks = sorted(asks, key=lambda asks: float(asks[0])) #sort asks from lowest to highest price
				askPrice,askAmount = sortedAsks[0]
				return sortedAsks[0]
			else:
				print "ERROR: %s order book is frozen" % market
	except urllib2.URLError, err:
			print "urllib2.URLError, error code %s" % err


def getHighestBid(market):
	try:
		orderBook = pol.returnOrderBook(market)
		if not (orderBook is None):
			if orderBook.get('isFrozen') == '0':
				bids = orderBook.get('bids')
				sortedBids = sorted(bids, key=lambda bids: float(bids[0])) #sort bids from lowest to highest price
				bidPrice,bidAmount = sortedBids[0]
				return sortedBids[len(sortedBids)-1]
			else:
				print "ERROR: %s order book is frozen" % market
	except urllib2.URLError, err:
			print "urllib2.URLError, error code %s" % err



# spends all balance to buy currency
def buyAll(market):
	currencyToSell,currencyToBuy = market.split('_')
	
	print '--------------------- BUY ALL ----------------------'
	balances = pol.returnBalances()
	if not (balances is None):
		while balances.get(currencyToSell) > 0.0001:
			print 'BUY ALL Spending %.8f %s' % (float(balances.get(currencyToSell)),currencyToSell)
			askPrice,askAmount = getLowestAsk(market)
			totalToSpendInEth = float(balances.get(currencyToSell))/float(askPrice)
			print 'Lowest ask is %.8f\tTotal %s to buy %.8f' % (float(askPrice),currencyToBuy, float(totalToSpendInEth))
			if(totalToSpendInEth <= 0.0001):
				print 'can\'t buy less than 0.0001 eth'
				break
			else:
				if buy(market,totalToSpendInEth) == False:
					return

		printBalance(balances)



# spends all balance to sell currency
def sellAll(market):
	currencyToBuy,currencyToSell = market.split('_')
	print '--------------------- SELL ALL ----------------------'
	balances = pol.returnBalances()
	if not (balances is None):
		while balances.get(currencyToSell) > 0.0001:
			print 'SELL ALL Spending %.8f %s' % (float(balances.get(currencyToSell)),currencyToSell)
			try:
				bidPrice,bidAmount = getHighestBid(market)
			except urllib2.URLError, err:
				print "urllib2.URLError, error code %s" % err
			
			totalToSpendInEth = float(balances.get(currencyToSell))
			print 'Highest bid is %.8f\tTotal %s to sell %.8f' % (float(bidPrice),currencyToSell, float(totalToSpendInEth))
			if(totalToSpendInEth <= 0.0001):
				print 'can\'t buy less than 0.0001 eth'
				break
			else:
				if sell(market,totalToSpendInEth) == False:
					return


		printBalance(balances)


# prints balance
def printBalance(balances):
	print '------------- BALANCE ---------------'
	for key, value in balances.iteritems():
		try:
			if float(value) > 0:
				print '%s\t%s' % (key,value)
		except ValueError,e:
			print "Can't parse balance. Error: %s" % e


def trade(market, shortEMALength, longEMALength, tradeFreeze):
	# dataLength = priceinfo.dataLength() # Plot alldata
	dataLength = 4*24*60 # Plot last 5 days data
	priceinfo.deleteInvalidData(market,dataLength)
	prices = priceinfo.getLastValues(market,dataLength)
	shortEMA = stats.ExpMovingAverage(prices,shortEMALength)
	longEMA = stats.ExpMovingAverage(prices,longEMALength)
	print 'shortEMA %s' % len(shortEMA)
	#returns True if buy, returns False if sell
	def emaTrade(i):
		return (shortEMA[i] > longEMA[i])

	btcName,ethName = market.split('_')

	balances = pol.returnBalances()
	if not (balances is None):
		printBalance(balances)
		lastEmaTrade = emaTrade(dataLength-1)
		if lastEmaTrade == True:
			print 'Time to buy.\t (short)%.8f > (long)%.8f \t (price)%.8f' % (shortEMA[dataLength-1],longEMA[dataLength-1],prices[dataLength-1])
			if float(balances.get(btcName)) > 0.0001:
				print 'buyAll'
				buyAll(market)
			else:
				print 'not enought %s to buy %s' % (btcName,ethName)


		if lastEmaTrade == False:
			print 'Time to sell.\t (short)%.8f < (long)%.8f \t (price)%.8f' % (shortEMA[dataLength-1],longEMA[dataLength-1],prices[dataLength-1])
			
			if float(balances.get(ethName)) > 0.0001:
				print 'sellAll'
				sellAll(market)
			else:
				print 'not enought %s to sell %s' % (ethName,ethName)


		simulateTrade(market=market, prices=prices, dataLength = dataLength,shortEMALength=shortEMALength, longEMALength=longEMALength,tradeFreeze=tradeFreeze,savePlot=True);




def tradeLoop(market, shortEMALength,longEMALength):
	while True:
		print 'Trading'
		starttime=time.time()
		try:
			trade(market,shortEMALength,longEMALength,0)

		except urllib2.URLError, err:
			print "urllib2.URLError, error code %s" % err

			
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



# getBestParams('BTC_ETH')
# getBestParams(market='BTC_MAID', shortFrom=50, shortTo=280, shortDelta=5, longTo=2000, longDelta=8)

market = 'BTC_ETH'
shortEMALength = 159
longEMALength = 1156
tradeLoop(market, shortEMALength, longEMALength)


