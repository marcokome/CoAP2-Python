import yaml, utils, parameters, time, os
from multiprocessing import Process, Pipe

class Subscription():
    def __init__(self, socket):
        (self.receiver, self.sender) = Pipe(False) # Open unidirectionnal pipe
        self.callback = utils.default_notifcation_callback
        self.s = socket


    def setCallback(self, callback):
        self.callback = callback

    #Used by the server
    def addClient(self, nbre, client, resource, rule, qos):
        f = open('server_subscriptions.yaml', 'a+')
        data = {nbre: {"client": client, "resource": resource, "rule": rule, "qos": qos }}
        yaml.dump(data, f, default_flow_style=False)
        f.close()
        print(">>Subs class: The client '{}' subscribed to resource '{}', with the rule '{}' and QoS {}".format(client, resource, rule, qos))

    '''
    -------------------------------------------
    Methods used by the client: the subscriber:
        -addServer
        -removeServer
    --------------------------------------------
    '''
    def addServer(self, nbre, client, resource, rule, qos):
        notificaton_server = Process(target=utils.listen_to_notifications, args=(self.callback, self.s, self.receiver, nbre))
        notificaton_server.start()

        f = open('client_subscriptions.yaml', 'a+')
        data = {nbre: {"client": client, "resource": resource, "rule": rule, "qos": qos, "pid": notificaton_server.pid}}
        yaml.dump(data, f, default_flow_style=False)
        f.close()

        print(">>{} subscriber: Just subscribed to resource '{}', with the rule '{}' and QoS {}.".format(client, resource, rule, qos))

    def removeServer(self, notif_id):
        f = open('client_subscriptions.yaml', 'r')
        data = yaml.load(f)
        f.close()

        pid = None if data is None else next((data[e]['pid'] for e in data if notif_id in data),None)

        if pid is None:
            print(">>Subs class: The registration nbre doesnt exist")
            return False

        data.pop(notif_id)
        os.system('kill -9 {}'.format(pid))

        f = open('client_subscriptions.yaml', 'w')
        yaml.dump(data, f, default_flow_style=False) if  data != {} else None
        f.close()

        print(">>Subs class: Unsubscription to the notification {}".format(notif_id))
        return True

    def getResourceId(self, resource):
        f = open('client_subscriptions.yaml', 'r')
        data = yaml.load(f)
        f.close()

        return None if data is None else next((e for e in data if resource in data[e]['resource']), None)

    #Used by the server
    def removeClient(self, notif_id):
        f = open('server_subscriptions.yaml', 'r')
        data = yaml.load(f)
        f.close()

        try:
            data.pop(notif_id)
        except:
            print(">>Subs class: The registration nbre doesnt exist")
            return False

        f = open('server_subscriptions.yaml', 'w')
        yaml.dump(data, f, default_flow_style=False) if  data != {} else None
        f.close()

        print(">>Subs class: Unsubscription to the notification {}".format(notif_id))
        return True

    #Used by the client

def _listen_to_notifications(self, callback, s, recv_pipe):
    while True:
        print("Listening...")
        if recv_pipe.poll(0.1):
            print("Closing the notification server...\n")
            break

        try:
            #raw_data, self.client = self.s.recvfrom(parameters.BUFFERSIZE)
            raw_data, client = s.recvfrom(parameters.BUFFERSIZE)
            message = Message(raw_data=raw_data)
            print(message)
            rule_nbre = next((x['Notification'] for x in message.options if 'Notification' in x), 0)

            callback(rule_nbre=rule_nbre, message=message.message)
        except socket.timeout:
            print("Still listening until unsubscription....")
