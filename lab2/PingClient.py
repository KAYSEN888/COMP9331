# COMP9331 Lab 2 PingClient
# python3
# Luo Kaisen
# z5185842
from socket import *
import time
import sys

# get input
serverName = sys.argv[1]
serverPort = sys.argv[2]
clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.settimeout(1)

# time info
time_list = []
total_time = 0


for i in range(10):
    # get current time
    start_time = time.time()
    local_time = time.localtime()
    time_format = time.strftime("%Y-%m-%d %H:%M:%S", local_time)

    # message
    message = ('PING' + ' ' + str(i) + ' ' + str(time_format))
    clientSocket.sendto(message.encode(), (serverName, int(serverPort)))

    try:
        modifedMessage, serverAddress = clientSocket.recvfrom(1024)
        print('ping to %s , seq = %d , rtt = %.0f ms' % (serverName, i, (time.time() - start_time) * 1000))

        # rtt
        time_list.append((time.time() - start_time) * 1000)
        total_time += (time.time() - start_time) * 1000

    except Exception as t:
        print('ping to %s , seq = %d , rtt = Time out' % (serverName, i))

print('MAX RTT: {:.2f} ms'.format(max(time_list)))
print('MIN RTT: {:.2f} ms' .format(max(time_list)))
print('AVG RTT: {:.2f} ms' .format(total_time / len(time_list)))
clientSocket.close()

