
import parameters, socket, time, yaml
from Message import Message

'''
Utils functions
'''

# Default callback function for the discovery
def default_discovery_callback(**res):
    print("**Default discovery callback:")
    print("---------------------------------")

    print("ip:{},\nhn:{},\nrs:{}".format(res["ip"], res["hn"], res["rs"]))

    print("---------------------------------")

def add_resource(func, path, **options):
    #Check if options are supported...
    for op in options:
        if op not in parameters.RESOURCE_OPTIONS:
            raise Exception("Option '{}' not defined".format(op))

    #Register the resource
    o = dict()
    o['discoverable'] = options['discoverable'] if 'discoverable' in options else True
    o['observable'] = options['observable'] if 'observable' in options else False
    o['separate'] = options['separate'] if 'separate' in options else False
    if 'methods' not in options:
        o['methods'] = ['GET']
    else:
        for x in options['methods']:
            if x not in parameters.METHODS:
                raise Exception("No methods corresponds to the code '{}' ".format(x))

        o['methods'] = options['methods']

    #self.functions[path] = {'rule':func, 'options':o}

    return(path, func, o, True if o['discoverable'] else False)

def getAddressAndPath(uri):
    if uri.find(parameters.COAP_HEADER) == 0:
        address = uri.strip(parameters.COAP_HEADER).split("/")[0]
        path = '/'+'/'.join(uri.strip(parameters.COAP_HEADER).split("/")[1:])
    else:
        raise Exception("The uri must be structure as following :'coap://\{domainame\}/\{resource\}' !")

    return (address, path)

def optionContains(name, options):
    for o in options:
        if name in o :
            return True

    return False

# Default callback function for the discovery
def default_notifcation_callback(**res):
    print("**Default notification callback:")
    print("---------------------------------")

    print("rule_nbre: {},\nmssage: {}".format(res["rule_nbre"], res["message"]))

    print("---------------------------------")

def listen_to_notifications(callback, s, recv_pipe, notif_id):
    print("Listening for notif {}...".format(notif_id))
    while True:
        if recv_pipe.poll(0.1):
            msg = recv_pipe.recv()
            print("Received on the pipe : {}".format(msg))
            if msg == notif_id:
                print("Stop listening for notif {}...\n".format(notif_id))
                break

        try:
            raw_data, client = s.recvfrom(parameters.BUFFERSIZE)
            message = Message(raw_data=raw_data)
            print(message)
            rule_nbre = next((x['Notification'] for x in message.options if 'Notification' in x), 0)

            callback(rule_nbre=rule_nbre, message=message.payload)
        except socket.timeout:
            print("Waiting for notification {}....".format(notif_id))

# Discovery utils methods
def pool(s, message, recv_pipe):
    while True:
        if recv_pipe.poll(0.1):
            print("Closing the discovery server...\n")
            break

        print("New pooling...")
        message.send(socket=s, discovery=True)
        time.sleep(parameters.DEFAULT_DISCOVERY_POOLING)

def getCachedIP(domainame):
    f = open('dns.yaml', 'r')
    data = yaml.load(f)
    f.close()

    return None if data is None else next((data[e] for e in data if e == domainame), None)

def cacheDNS(domainame, ip):
    f = open('dns.yaml', 'r')
    data = yaml.load(f)

    if data is not None:
        if domainame in data:
            print("Updating the ip address for {}".format(domainame))
            data[domainame] = ip
            yaml.dump(data, f, default_flow_style=False)
            f.close()
    else:
        f.close()
        f = open('dns.yaml', 'a+')
        print("Adding a new domainame to the table : {}:{}".format(domainame, ip))
        yaml.dump({domainame:ip}, f, default_flow_style=False)
        f.close()

def sendACK(mid, socket, client):
    t = parameters.TYPES['ACK']
    code = parameters.RESPONSE_CODES['Valid']
    mid = mid
    token = b''
    payload = b''
    options = dict()
    options['Content-Format'] = 'text/plain'

    response_message = Message(type=t, code=code, mid=mid, options=options, token=token, payload=payload)
    response_message.send(socket=socket, client=client)


def listen_to_asynchronous_req(callback, s, message):
    print("Waiting for asynchronous response...")
    c = callback if callback else default_asynchronous_callback

    while True:
        try:
            raw_data, client = s.recvfrom(parameters.BUFFERSIZE)
            response = Message(raw_data=raw_data)
            #print(response)

            c(code=response.code, type=response.type, payload=response.payload)

            code = parameters.RESPONSE_CODES['Valid']
            t = parameters.TYPES['ACK']
            mid = message.mid
            options = dict()
            options['Content-Format'] = 'text/plain'
            token = b''
            payload = ''

            response = Message(type=t, code=code, mid=mid, options=options, token=token, payload=payload)
            response.send(socket=s, client=client)

            break

        except socket.timeout:
            #print("Waiting for incoming response....")
            pass


# Default callback function for the async requests
def default_asynchronous_callback(**res):
    print("**Default asynchronous request callback:")
    print("---------------------------------")

    print("code: {},\ntype: {},\npayload: {}".format(res["code"], res["type"], res["payload"]))

    print("---------------------------------")

'''
def listen(s, client, callback_function, send_pipe):
        devices_found = 0

        while True:

            try:
                response = s.recvfrom(parameters.BUFFERSIZE)
                devices_found += 1
            except socket.timeout:
                info = "{} device found." if devices_found == 1 else "{} devices found."
                print("Timed out...\n"+info.format(devices_found))
                # Kill pooling server
                send_pipe.send(0)
                break
            else:
                client = response[1]

                message = Message(raw_data=response[0])
                print("Received -- \n{}".format(message))
                for o in message.options:
                    if 'Uri-Host' in o :
                        #hn = o['Uri-Host'].decode()
                        hn = o['Uri-Host']
                rs = message.payload.decode()

                Coap2.makeResponse(message=message)

                callback_function(ip=client, hn=hn, rs=rs)
'''
