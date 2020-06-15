#!/usr/bin/python3

import os, socket, struct, asyncio, time, json
import parameters, utils
from Subscription import Subscription
from Message import Message

from pprint import pprint

from multiprocessing import Process, Pipe

class Coap2():

    def __init__(self, domainame=None, port=None):
        #self.domainame = domainame[:9] +'.local' if domainame is not None else os.popen('hostname').read().split('\n')[0]+'.local'
        self.domainame = ''.join([domainame[:9],'.local']) if domainame else ''.join([os.popen('hostname').read().split('\n')[0], '.local'])

        self.port = port if port is not None else parameters.DEFAULT_PORT
        ip = os.popen('hostname -I').read().split('\n')[0].split(' ')[0]
        self.ip = ip if ip is not '' else parameters.LOCALHOST

        self.functions = {}
        self.discovery_response = {}

        self.message_blacklisted = []

        self.s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.s.settimeout(parameters.DEFAULT_TIMOUT)

        self.client = None

        self.subscriptions = Subscription(self.s)

    '''
    ----------------------------------------
    SERVER METHODS:
        - RUN: Start server
        - RESOURCE: Declare a new resource
        - DISCOVERY: equivalent to MDNS
        - MAKERESPONSE: respond according to a Received Message
    ----------------------------------------
    '''
    def run(self):
        print("CoAp2 server is running on {}:{}".format(self.domainame, self.port))
        print("Listening on localhost,...\nCheck your connection status !" if self.ip is parameters.LOCALHOST
        else "Listening on {}...".format(self.ip))
        print("Available resources (DEBUG):")
        #pprint(self.discovery_response)
        pprint(self.functions)

        self.s.bind(('', self.port))
        group = socket.inet_aton(parameters.MULTICAST_V4)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        self.s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        while True:
            try:
                raw_data, self.client = self.s.recvfrom(parameters.BUFFERSIZE)
                print("Raw data: {}".format(raw_data))

                message = Message(raw_data=raw_data)
                print(message)
                print('.\n.')
                self.makeResponse(message=message)
            except socket.timeout:
                pass

    def resource(self, path, **options):
        def decorator(f):
            p, func, o, d = utils.add_resource(f, path, **options)
            self.functions[p] = {'rule':func, 'options':o}

            if d:
                self.discovery_response[p] = {'options':o}

            return f
        return decorator

    def discover(self, *param, callback=None, sync=False):
        self.s.settimeout(parameters.DEFAULT_TIMOUT)
        ttl = struct.pack('b', 1)
        self.s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

        c = callback if callback is not None else utils.default_discovery_callback

        self.devices_found = 0

        t = parameters.TYPES['NON']
        code = parameters.METHODS['GET']
        mid = int.from_bytes(os.urandom(2), 'big')
        options = dict()
        options['Content-Format'] = 'json'

        if not param:
            print("Looking for everybody on the network...")
            options['Discovery'] = ''
        elif len(param) > 1:
            raise Exception("Only one domainame at the time !")
        else:
            if type(param[0]) is list:
                print("Looking for devices with the following resources: {}".format(param[0]))
                options['Discovery'] = ','.join(param[0])+',' #Resources or functionalities we are looking for

            elif type(param[0]) is str:
                print("Looking for device with domain name: {}".format(param[0]))
                options['Discovery'] = param[0] # the device we are looking for

        message = Message(type=t, code=code, mid=mid, options=options)

        if not sync:
            #Start discovery server
            (receiver, sender) = Pipe(False) # Open unidirectionnal pipe
            self.listening_server = Process(target=self._listen, args=(c, sender))
            #self.listening_server = Process(target=utils.listen, args=(self.s, self.client, c, sender))
            #self.pooling_server = Process(target=self._pool, args=(message, receiver))
            self.pooling_server = Process(target=utils.pool, args=(self.s, message, receiver))

            self.listening_server.start()
            self.pooling_server.start()
        else:
            #Wait for the resolution to complete
            message.send(socket=self.s, discovery=True)
            try:
                recv = self.s.recvfrom(parameters.BUFFERSIZE)
            except socket.timeout:
                print("Timed out...No device found")
            else:
                response = Message(raw_data=recv[0])
                if response.mid == message.mid:
                    for o in response.options:
                        if 'Uri-Host' in o :
                            if o['Uri-Host'] != self.domainame:
                                print("Wrong Domain name, device {} shouldn't be responding to our request !!!".format(o['Uri-Host']))
                                break
                            else:
                                #print("Response from {}".format(recv[1][0]))
                                return recv[1]

    def _listen(self, callback_function, send_pipe):
        while True:

            try:
                response = self.s.recvfrom(parameters.BUFFERSIZE)
                self.devices_found += 1
            except socket.timeout:
                info = "{} device found." if self.devices_found == 1 else "{} devices found."
                print("Timed out...\n"+info.format(self.devices_found))
                # Kill pooling server
                send_pipe.send(0)
                break
            else:
                self.client = response[1]

                message = Message(raw_data=response[0])
                print("Received -- \n{}".format(message))
                for o in message.options:
                    if 'Uri-Host' in o :
                        #hn = o['Uri-Host'].decode()
                        hn = o['Uri-Host']
                rs = message.payload.decode()

                self.makeResponse(message=message)

                callback_function(ip=self.client, hn=hn, rs=rs)

    def makeResponse(self, **data):
        # Called for a default response...
        if 'payload' in data and len(data) is 1:

            t = parameters.TYPES['ACK']
            code = parameters.RESPONSE_CODES['Content']
            mid = int.from_bytes(os.urandom(2), 'big')
            options = dict()
            options['Content-Format'] = 'text/plain'

            payload = data['payload']

            message = Message(type=t, code=code, mid=mid, options=options, payload=payload)
            message.send(socket=self.s, client=self.client)

        # Called when the server receives a resquest...
        elif 'message' in data:
            message = data['message']
            response_message = None
            # MDNS role
            if message.type == parameters.TYPES['NON']:
                print("Received a NON message !!")
                # Responding to Discovery requests if and only if concerned
                # by Domainame or functionalities filters
                if self._shouldIRespond(message.options, message.payload, message.mid):
                    v = parameters.VERSION
                    t = parameters.TYPES['CON']
                    code = parameters.RESPONSE_CODES['Content']
                    mid = message.mid
                    token = b''

                    options = dict()
                    options['Uri-Host'] = self.domainame
                    options['Content-Format'] = 'json'
                    '''
                    for o in message.options:
                        if 'Content-Format' in o :
                            options['Content-Format'] = o['Content-Format']
                            print('content-format: {}'.format(o['Content-Format']))
                    '''

                    # blacklist the message
                    self.message_blacklisted.append(mid)

                    response_message = Message(version=v, type=t, code=code, mid=mid, token=token, options=options, payload=self.discovery_response)
                    response_message.send(socket=self.s, client=self.client)

                    #self.waiting_thread = Process(target=self._waiting_for_confirmation, args=(response_message, ))
                    #self._waiting_for_confirmation()

                else:
                    print("I'm not concerned !")

            elif message.type == parameters.TYPES['ACK']:
                # Sending acknowledgement message
                print("Received a ACK message !!")
            elif message.type == parameters.TYPES['CON']:
                # Responding to a Confirmable message
                print("Received a CON message !!")

                v = parameters.VERSION
                t = parameters.TYPES['ACK']
                code = parameters.RESPONSE_CODES['Valid']
                mid = message.mid
                token = b''
                payload = b''
                options = dict()
                options['Content-Format'] = 'text/plain'
                # ----------------------------------------
                # HANDLING Notifications
                # if message.options contains 'Notification'
                # then get the rule and subscribe the user...
                # ----------------------------------------
                if next((True for x in message.options if 'Notification' in x), False):
                    notif_id = next((x['Notification'] for x in message.options if 'Notification' in x), None)

                    # Susbcription
                    if notif_id == 0:
                        rule = next((x['Rule'] for x in message.options if 'Rule' in x), None)
                        resource = '/'+next((x['Uri-Path'] for x in message.options if 'Uri-Path' in x), None)

                        if next((True for x in self.functions if resource == x), False):
                            rule_nbr = int.from_bytes(os.urandom(1), 'big')
                            options['Notification'] = rule_nbr
                            payload = self.functions[resource]['rule']()

                            #***TO DO open a thread dedicaded to this rule...
                            self.subscriptions.addClient(rule_nbr, self.client[0], resource, rule, parameters.QOS_1)

                        else:
                            print("Error: The resource '{}' doesnt exist".format(resource))
                            code = parameters.RESPONSE_CODES['Bad Request']
                            payload = "The resource '{}' doesnt exist".format(resource)

                        if not rule:
                            print("Be updated with no restriction".format(rule))

                    # Unsubscription
                    else:
                        if not self.subscriptions.removeClient(notif_id):
                            code = parameters.RESPONSE_CODES['Not Found']
                            payload = 'The registration nbre doesnt exist'
                # ----------------------------------------
                # HANDLING Requests
                # if message.options contains 'Uri-Path'
                # then get the rule and subscribe the user...
                # ----------------------------------------
                elif next((True for x in message.options if 'Uri-Path' in x), False):
                    uri = '/'+next((x['Uri-Path'] for x in message.options if 'Uri-Path' in x), None)
                    print('Requesting {}'.format(uri))

                    v = parameters.VERSION
                    code = parameters.RESPONSE_CODES['Valid']
                    t = parameters.TYPES['ACK']
                    mid = message.mid
                    options = dict()
                    options['Content-Format'] = 'text/plain'
                    token = b''
                    payload = ''

                    if next((True for x in self.functions if uri == x), False):
                        c = next((x for x,y in parameters.METHODS.items() if y == message.code), None)
                        if c in self.functions[uri]['options']['methods']:
                            params = next((x['Uri-Query'] for x in message.options if 'Uri-Query' in x),None)
                            #print('params: {}'.format(params))
                            if params :
                                payload = self.functions[uri]['rule'](json.loads(params))
                            else:
                                payload = self.functions[uri]['rule'](params)
                        else:
                            code = parameters.RESPONSE_CODES['Method Not Allowed']
                    else:
                        code = parameters.RESPONSE_CODES['Not Found']


                response_message = Message(type=t, code=code, mid=mid, options=options, token=token, payload=payload)
                response_message.send(socket=self.s, client=self.client)


            elif message.type == parameters.TYPES['RST']:
                # Responding to a Reset message
                print("Received a RST message !!")
            #elif message.type is parameters.TYPES['CON']:

    def _shouldIRespond(self, options, payload, mid):
        # Don't answer to blacklisted messages
        print("Should I respond ?...")
        if mid in self.message_blacklisted:
            print("Already answered to message {}".format(mid))
            return False

        # No filters
        print(options)
        if not options:
            return True
        else:
            for o in options:
                print(o)
                if 'Discovery' in o:
                    if ',' in o['Discovery']:
                        resources = o['Discovery'].split(',')
                        for r in resources:
                            if r in self.functions.keys():
                                return True
                    elif o['Discovery'] == self.domainame:
                        return True

        # In any other cases, don't answer
        print("No filters ...")
        return False

    '''
    ----------------------------------------
     CLIENT Methods:
     - Subscribe: equivalent to MQTT
     - Unsubscribe: equivalent to MQTT
     - CRUD Methods:
        - get
        - put
        - post
        - delete
    ----------------------------------------
    '''
    def subscribe(self, uri, payload=None, rule=None, qos=0, callback=None):
        address, resource = utils.getAddressAndPath(uri)
        print("Address: {}\nResource: {}\nRule: {}\nQoS {}".format(address, resource, rule, qos))

        ip = utils.getCachedIP(address)

        if ip is not None:
            self.client = (ip, parameters.DEFAULT_PORT)
        else:
            response = self.discover(address, sync=True)
            print(response)
            if response is not None:
                self.client = response
                utils.cacheDNS(address, self.client[0])
            else:
                raise Exception("'{}' doesnt exist on the network or is not responding !".format(address))

        t = parameters.TYPES['CON']
        code = parameters.METHODS['GET']
        mid = int.from_bytes(os.urandom(2), 'big')
        token = b''
        options = dict()
        options['Uri-Path'] = resource
        options['Notification'] = ''
        options['Rule'] = '' if rule is None else rule

        message = Message(type=t, code=code, mid=mid, options=options, token=token)
        message.send(socket=self.s, client=self.client)

        print("Waiting for incoming messages")
        # TO DO: Notification server: Receive message through the callback function
        rule_nbre = 0

        try:
            raw_data, self.client = self.s.recvfrom(parameters.BUFFERSIZE)
            message = Message(raw_data=raw_data)
            print(message)
            print("\n")

            rule_nbre = next((x['Notification'] for x in message.options if 'Notification' in x), 0)

            if rule_nbre == 0 or message.code == parameters.RESPONSE_CODES['Bad Request']:
                print("Bad request: {}".format(message.payload.decode('utf-8')))
                #break
            else:
                # TO DO: Cache the rule (rule_nbr, resource)!!!!!
                print("To cache : ")
                print("Rule Nbre : {}".format(rule_nbre))
                print("client: {}".format(self.client))
                print("resource: {}".format(resource))
                print("rule: {}".format(rule))


                print("1st Message: {}".format(message.payload.decode('utf-8')))

                utils.sendACK(message.mid, self.s, self.client)

                print("Start notificaton server...")
                self.subscriptions.addServer(rule_nbre, self.client[0], resource, rule, parameters.QOS_1)

        except socket.timeout:
            print("Stop listening to incoming notifications...\n***TO DO***Devrait renvoyer le message un certain nbre de fois jusqu'à recevoir un ACK")
            #break
        #while True:
            # Get rule nbre, break then start notification server
            # give the rule nbre in params


    def unsubscribe(self, uri):
        address, resource = utils.getAddressAndPath(uri)
        ip = utils.getCachedIP(address)

        if ip is not None:
            self.client = (ip, parameters.DEFAULT_PORT)
        else:
            response = self.discover(address, sync=True)
            if response is not None:
                self.client = response
                utils.cacheDNS(address, self.client[0])
            else:
                raise Exception("'{}' doesnt exist on the network or is not responding !".format(address))

        print("The client is {}".format(self.client))

        id = self.subscriptions.getResourceId(resource)
        if id is None:
            print("The resource {} doesnt exist".format(resource))
        else:
            self.subscriptions.removeServer(id)

            t = parameters.TYPES['CON']
            code = parameters.METHODS['GET']
            mid = int.from_bytes(os.urandom(2), 'big')
            token = b''
            options = dict()
            options['Notification'] = id

            message = Message(type=t, code=code, mid=mid, options=options, token=token)
            message.send(socket=self.s, client=self.client)

            while True:
                try:
                    raw_data, self.client = self.s.recvfrom(parameters.BUFFERSIZE)
                    message = Message(raw_data=raw_data)
                    print(message)
                    print("\n")

                    if message.code == parameters.RESPONSE_CODES['Valid']:
                        utils.sendACK(message.mid, self.s, self.client)

                    else:
                        print("ERROR: {}".format(message.payload.decode('utf-8')))

                    break

                except socket.timeout:
                    print("Stop listening...socket Timeout")
                    break

            #self.sender.send(0)


    def _getIP(self, address):
        ip = utils.getCachedIP(address)

        if ip is not None:
            return (ip, parameters.DEFAULT_PORT)
        else:
            response = self.discover(address, sync=True)
            print(response)
            if response is not None:
                utils.cacheDNS(address, response[0])
                return response
            else:
                return None

    def _request(self, uri, type, data=None, header=None):
        address, resource = utils.getAddressAndPath(uri)

        self.client = self._getIP(address)
        if self.client is None:
            raise Exception("'{}' doesnt exist on the network or is not available !".format(address))


        t = parameters.TYPES['CON']
        mid = int.from_bytes(os.urandom(2), 'big')
        token = b''
        code = 0

        if type == 1:
            code = parameters.METHODS['GET']
        elif type == 2:
            code = parameters.METHODS['PUT']
        elif type == 3:
            code = parameters.METHODS['POST']
        elif type == 4:
            code = parameters.METHODS['DELETE']

        options = dict()
        options['Uri-Path'] = resource

        if data:
            options['Uri-Query'] = json.dumps(data)

        message = Message(type=t, code=code, mid=mid, options=options, token=token)
        message.send(socket=self.s, client=self.client)

        try:
            raw_data, self.client = self.s.recvfrom(parameters.BUFFERSIZE)
            message = Message(raw_data=raw_data)
            #print(message)
            return (message.code, next((x['Content-Format'] for x in message.options if 'Content-Format' in x), None), message.payload.decode())

        except socket.timeout:
            print("Stop listening to incoming response...\n")
            return (parameters.RESPONSE_CODES['Gateway Timeout'], None, None)

    def get(self, uri, data=None, header=None):
        return self._request(uri, 1, data=data, header=header)

    def put(self, uri, data=None, header=None):
        return self._request(uri, 2, data=data, header=header)

    def post(self, uri, data=None, header=None):
        return self._request(uri, 3, data=data, header=header)

    def delete(self, uri, data=None, header=None):
        return self._request(uri, 4, data=data, header=header)
