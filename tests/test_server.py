import sys
sys.path.append('../')

from coap2 import Coap2

c = Coap2()

@c.resource('/root', observable=True)
def test():
	return "Hello root"

@c.resource('/root/child', methods=['POST'], observable=True, separate=False)
def test2():
	print("Hello root's child !")

@c.resource('/root/child/private', observable=True, discoverable=False)
def test3():
	print("Hello child private")

@c.resource('/random', observable=True)
def test3():
	return str(int.from_bytes(os.urandom(1), 'big'))


c.run()
