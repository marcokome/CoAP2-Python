import sys, os
sys.path.append('../')

from coap2 import Coap2
import json

c = Coap2()

@c.resource('/root')
def test(kwargs):
	response = "Data not available :("

	if kwargs:
		# Get arguments
		if 'soil' in kwargs:
			req = kwargs['soil']
			n = 18.0 if 'N' in req else 0.0
			p = 50.0 if 'P' in req else 0.0
			k = 32.0 if 'K' in req else 0.0

			response = {'N':n, 'P':p, 'K':k}
			#print(response)

	return json.dumps(response)

@c.resource('/root/child', methods=['POST'], separate=False)
def test2(kwargs):
	print('Data posted : {}'.format(', '.join(kwargs)))
	response = "temperature is missing !"

	if 'temp' in kwargs:
		response = "It's getting cold !" if float(kwargs['temp']) < 10.0 else "The temperature is perfect"
		print(response)

	return response

@c.resource('/root/child/private', methods=['GET','POST'], discoverable=False)
def test3():
	return "Hello child private"

@c.resource('/random', observable=True)
def test3():
	return str(int.from_bytes(os.urandom(1), 'big'))


c.run()
