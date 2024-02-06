import requests  # pip install requests
import json
import base64
import hashlib
import hmac
import os
import time #for nonce
from time import sleep

MAX_RATE = 0.001

ticker_vocabulary = {
	0: "FRR",
	1: "BID",
	2: "BID_PERIOD",
	3: "BID_SIZE",
	4: "ASK",
	5: "ASK_PERIOD",
	6: "ASK_SIZE",
	7: "DAILY_CHANGE",
	8: "DAILY_CHANGE_PERC",
	9: "LAST_PRICE",
	10: "VOLUME",
	11: "HIGH",
	12: "LOW",
	13: "___",
	14: "___",
	15: "FRR_AMOUNT_AVAILABLE"
}

class BitfinexClient(object):
	BASE_URL = "https://api.bitfinex.com/"
	KEY = "" # <- from your account
	SECRET = "" # <- from your account

	def _nonce(self):
		# Returns a nonce
		# Used in authentication
		return str(int(round(time.time() * 10000)))

	def _headers(self, path, nonce, body):
		secbytes = self.SECRET.encode(encoding='UTF-8')
		signature = "/api/" + path + nonce + body
		sigbytes = signature.encode(encoding='UTF-8')
		h = hmac.new(secbytes, sigbytes, hashlib.sha384)
		hexstring = h.hexdigest()
		return {
			"bfx-nonce": nonce,
			"bfx-apikey": self.KEY,
			"bfx-signature": hexstring,
			"content-type": "application/json",
		}

	def req(self, path, params = {}, payloads = {}):
		nonce = self._nonce()
		body = params
		rawBody = json.dumps(body)
		headers = self._headers(path, nonce, rawBody)
		url = self.BASE_URL + path
		while True:
			try:
				resp = requests.post(url, json=payloads, headers=headers, data=rawBody, verify=True)
				break
			except Exception as e:
				print(f"{e.__class__.__name__} - {str(e)}")
				print("I will try it again after one second... HERE")
				sleep(1)

		return resp

	def active_orders(self):
		# Fetch active orders
		response = self.req("v2/auth/r/orders")
		if response.status_code == 200:
			return response.json()
		else:
			print('error, status_code = ', response.status_code)
			return ''

	def get_active_funding_orders(self, symbol):
		while True:
			try:
				response = self.req(f"v2/auth/r/funding/offers/{symbol}")
				break
			except ConnectionError as ce:
				print(f"{ce.__class__.__name__} - {str(ce)}")
				print("I will try send request again after 1 second.")
				sleep(1)

		if response.status_code == 200:
			return response.json()
		else:
			print('error, get_active_funding_orders, status_code = ', response.status_code)
			return ''

	def history_funding_orders(self, symbol):
		payloads = {
				"STATUS": "EXECUTED",
			}
		params = {
					"limit": 50,
				}
		response = self.req(f"v2/auth/r/funding/offers/{symbol}/hist", params=params, payloads=payloads)
		if response.status_code == 200:
			return response.json()
		else:
			print('error, status_code = ', response.status_code)
			return ''

	def get_wallets(self):
		response = self.req("v2/auth/r/wallets")
		if response.status_code == 200:
			return response.json()
		else:
			print('error, status_code = ', response.status_code)
			return ''

	def set_funding_order(self, _type, symbol, amount, rate, period, flags = 0):
		payloads = {
					"type": _type,
					"symbol": symbol,
					"amount": amount,
					"rate": rate,
					"period": period,
					"flags": flags
					}
		
		response = self.req("v2/auth/w/funding/offer/submit", payloads)
		if response.status_code == 200:
			return response.json()
		else:
			print('error, status_code = ', response.status_code)
			print('error, msg = ', response.content)
			return response
		
	def set_cancel_funding_order(self, _id):
		payloads = {"id": _id}

		response = self.req("v2/auth/w/funding/offer/cancel", payloads)
		if response.status_code == 200:
			return response.json()
		else:
			print('error, status_code = ', response.status_code)
			print('error, msg = ', response.content)

			return ''

	def get_funding_statistics(self, symbol):
		url = f"https://api-pub.bitfinex.com/v2/funding/stats/{symbol}/hist"
		response = requests.get(url)
		if response.status_code == 200:
			return response.json()
		else:
			print('error, status_code = ', response.status_code)
			return response

	def get_ticker_statistics(self, symbol):
		url = f"https://api-pub.bitfinex.com/v2/ticker/{symbol}"
		response = requests.get(url)
		if response.status_code == 200:
			return response.json()
		else:
			print('error, status_code = ', response.status_code)
			return response
		
	def get_candles(self, symbol, limit):

		params = {
					"limit": limit,
				}

		url = f"https://api-pub.bitfinex.com/v2/candles/trade:1D:{symbol}:a30:p2:p30/hist"
		response = requests.get(url, params=params)
		if response.status_code == 200:
			return response.json()
		else:
			print('error, status_code = ', response.status_code)
			return response


if __name__ == "__main__":



	# fetch all your orders and print out
	client = BitfinexClient()
	# result = client.active_orders()
	# print(result)

	result = client.set_cancel_funding_order(_id=2505835328) # WTF? what's means?

	# result = client.active_funding_orders()
	# print(result)

	# for r in result:
	# 	print(r)

	# result = client.history_funding_orders()
	# for r in result:
	# 	print(r)

	# result = client.set_funding_order("LIMIT", "fLTC", "2.55", "0.0006", 30, flags = 0 )
	# print(result)

	# result = client.get_funding_statistics("fUSD")
	# print(result)

	# result = client.get_ticker_statistics("fUSD")
	# for i, r in enumerate(result):
	# 	print(f"{ticker_vocabulary[i]}: {r}")

	# while True:

	# 	result = client.get_wallets()
	# 	# print(result)
	# 	for r in result:
	# 		if r[0] == "funding" and r[1] == "USD":
	# 			# print(r[4])
	# 			available_usd_balance = r[4]
	# 			print(f"Dostupný zostatok na účte je: {round(available_usd_balance, 2)} $")

	# 			if available_usd_balance >= 150:
	# 			# if available_usd_balance < 150:
	# 				ticker_stat = client.get_ticker_statistics("fUSD")
	# 				daily_high = ticker_stat[11]
	# 				print(daily_high)

	# 				# my_rate = daily_high - 0.00002 # test, v skutocnosti by to mal byt -
	# 				my_rate = daily_high + 0.00005 # test, v skutocnosti by to mal byt -

	# 				print(my_rate)
	# 				print(round(my_rate, 6))

	# 				_type = "LIMIT"
	# 				symbol = "fUSD"
	# 				amount = available_usd_balance
	# 				rate = round(my_rate, 6)

	# 				if my_rate > 0.00065:
	# 					period = 30
	# 				else:
	# 					period = 2

	# 				if my_rate > MAX_RATE:
	# 					my_rate = MAX_RATE - 0.00002

	# 				resp = client.set_funding_order(_type, symbol, amount, rate, period, flags = 0)
	# 				print(resp)

	# 	sleep(60)
