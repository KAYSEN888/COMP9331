
from threading import Thread
import datetime
import socket
import time
import json
import sys


def timeout_thread(global_dict,connection_dict):
    # search which connection is time out
    pass 
    while not global_dict['exit_flag']:
        for k,v in connection_dict.items():
            if v['islogin'] and datetime.datetime.now() - v['last_active_time'] > datetime.timedelta(seconds = global_dict['timeout']):
                v['islogin'] = False
                send_dict = {}
                send_dict['res'] = 'logout'
                send_dict['message'] = 'OK. Logout due to timeout!'
                v['client_socket'].send(json.dumps(send_dict).encode())
                time.sleep(1)
                v['client_socket'].close()

        time.sleep(1)

def client_thread(global_dict,connection_dict,remoteSocket, romoteAddr, remotePort):

    send_dict = {}

    # (1) log in loop
    while True:

        recv_data = remoteSocket.recv(2048)
        if not recv_data:
            # client close the socket
            remoteSocket.close()
            return
        # print(recv_data)
        recv_dict = json.loads(recv_data.decode())
        if recv_dict['cmd'] != 'login':
            remoteSocket.close()
            return

        if 'username' in recv_dict:
            username = recv_dict['username']
        else:
            print('Error in recv_dict')

        if 'password' in recv_dict:
            password = recv_dict['password']
        else:
            print('Error in recv_dict')

        if 'p2p_port' in recv_dict:
            p2p_port = recv_dict['p2p_port']
        else:
            print('Error in recv_dict')


        if username not in connection_dict:
            send_dict = {}
            send_dict['res'] = ''
            send_dict['message'] = 'Error: Invalid User Name'
            remoteSocket.send(json.dumps(send_dict).encode())
            continue

        if connection_dict[username]['islogin'] == True:
            # someone same username or password to log in
            send_dict['res'] = ''
            send_dict['message'] = 'Error: The user %s already log in' % (username)
            remoteSocket.send(json.dumps(send_dict).encode())
            continue


        if connection_dict[username]['wrongtimes'] >= 3 and datetime.datetime.now() - connection_dict[username]['last_login_time'] \
            < datetime.timedelta(seconds = global_dict['block_time']):
            # after 3 failed attempts, the user blocked for duration
            send_dict['res'] = ''
            send_dict['message'] = 'Error: Your account is blocked due to multiple login failures. Please try again later'
            remoteSocket.send(json.dumps(send_dict).encode())
            continue

        # update last login time
        connection_dict[username]['last_login_time'] = datetime.datetime.now()
        
        if connection_dict[username]['password'] != password:
            # wrong pass word

            connection_dict[username]['wrongtimes'] += 1
            send_dict['res'] = ''
            if connection_dict[username]['wrongtimes'] < 3:
                send_dict['message'] = 'Error: Invalid Password. Please try again'
            else:
                send_dict['message'] = 'Error: Invalid Password. Your account has been blocked. Please try again later'


            remoteSocket.send(json.dumps(send_dict).encode())
            continue
        # If the credentials are correct, the client is considered to be logged in

        # broadcast the message
        for k,v in connection_dict.items():
            if v['islogin'] and k != username:
                send_dict['res'] = ''
                send_dict['message'] = 'Login Broadcast: %s login' % (username)
                v['client_socket'].send(json.dumps(send_dict).encode())


        connection_dict[username]['wrongtimes'] = 0
        connection_dict[username]['islogin'] = True
        connection_dict[username]['last_active_time'] = datetime.datetime.now()
        connection_dict[username]['client_socket'] = remoteSocket

        # CAUTION: how to get IP!
        connection_dict[username]['p2p_ip'] = romoteAddr
        connection_dict[username]['p2p_port'] = p2p_port

        send_dict['res'] = 'loginsuccess'
        send_dict['message'] = 'OK: Welcome to the greatest messaging application ever!' + connection_dict[username]['offline_message']
        connection_dict[username]['offline_message'] = ''
        remoteSocket.send(json.dumps(send_dict).encode())
        break
        pass


    # (2) communication loop
    while True:
        try:
            recv_data = remoteSocket.recv(2048)
        except IOError as e:
            return
        if not recv_data:
            # client close the socket            
            remoteSocket.close()
            # print('socket close for recvive no data')
            return
        # print(recv_data)
        recv_dict = json.loads(recv_data.decode())

        if 'username' in recv_dict:
            username = recv_dict['username']
        else:
            print('Error in recv_dict')
        if 'last_active_time' in connection_dict[username]:
            connection_dict[username]['last_active_time'] = datetime.datetime.now()   
        else:
            print('Error in connection_dict')

        # (1) Send <message> to <user> through the server
        if recv_dict['cmd'] == 'message':
            friend = recv_dict['friend']
            message = recv_dict['message']

            if friend not in connection_dict:
                # If the <user> is not present in the credentials file (i.e. invalid user) or is self 
                # then an appropriate error message should be displayed
                send_dict['res'] = ''
                send_dict['message'] = 'Error: %s Not Exist!' % (friend)
            elif friend == username:
                # If the <user> is not present in the credentials file (i.e. invalid user) or is self 
                # then an appropriate error message should be displayed
                send_dict['res'] = ''
                send_dict['message'] = 'Error: %s is yourself!' % (friend)
            elif username in connection_dict[friend]['block_set']:
                # If <user> has blocked A, then a message to that effect should be displayed for A.
                send_dict['res'] = ''
                send_dict['message'] = 'Error: %s block you!' % (friend)

            elif connection_dict[friend]['islogin'] == False:
                # store the message for offline delivery
                send_dict['res'] = ''
                send_dict['message'] = 'Error: %s is Offline!' % (friend)

                if 'offline_message' in connection_dict[friend]:
                    connection_dict[friend]['offline_message'] += '\nOffine Message %s: %s' % (username, message)
                else:
                    print('Error in connection_dict')
            else:
                # If the user is online then deliver the message immediately
                send_dict['res'] = ''
                send_dict['message'] = 'Message from %s: %s' % (username, message)
                connection_dict[friend]['client_socket'].send(json.dumps(send_dict).encode())

                send_dict['res'] = ''
                send_dict['message'] = 'OK: Send to %s Success!' % (friend)
            remoteSocket.send(json.dumps(send_dict).encode())
            continue
        # (2) Send <message> to all online users except A and those users who have blocked A
        if recv_dict['cmd'] == 'broadcast':
            message = recv_dict['message']

            broadcast_list = ''

            send_dict['res'] = ''
            send_dict['message'] = 'Broadcast Message From %s: %s' % (username,message)
            for k,v in connection_dict.items():
                if v['islogin'] and k != username and username not in v['block_set']:
                    broadcast_list += k + ' '
                    v['client_socket'].send(json.dumps(send_dict).encode())
            send_dict['res'] = ''
            send_dict['message'] = 'Broadcast To: %s' % (broadcast_list if broadcast_list else 'nobody')
            remoteSocket.send(json.dumps(send_dict).encode())
            continue

        # (3) This should display the names of all users that are currently online excluding A.
        if recv_dict['cmd'] == 'whoelse':

            online_user_list = ''
            send_dict['res'] = ''
            for k,v in connection_dict.items():
                if v['islogin'] and k != username:
                    online_user_list += k + ' '
            send_dict['res'] = ''
            send_dict['message'] = 'Online User List: %s' % (online_user_list if online_user_list else 'nobody')
            remoteSocket.send(json.dumps(send_dict).encode())
            continue

        # (4) This should display the names of all users who were logged in at any time
        if recv_dict['cmd'] == 'whoelsesince':
            
            online_user_list = ''
            send_dict['res'] = ''
            for k,v in connection_dict.items():
                if k != username and v['last_login_time'] and datetime.datetime.now() - v['last_login_time'] <= datetime.timedelta(seconds = recv_dict['time']):
                    online_user_list += k + ' '
            send_dict['res'] = ''
            send_dict['message'] = 'User List since %d s: %s' % (recv_dict['time'], online_user_list if online_user_list else 'nobody')
            remoteSocket.send(json.dumps(send_dict).encode())
            continue
        
        # (5) blocks the <user> from sending messages to A.
        if recv_dict['cmd'] == 'block':
            if 'friend' in recv_dict:
                friend = recv_dict['friend']
            else:
                print("error in recv_dict")

            if friend not in connection_dict:
                # If the <user> is not present in the credentials file 
                send_dict['res'] = ''
                send_dict['message'] = 'Error: %s Not Exist!' % (friend)
            elif friend == username:
                # If the <user> is not present in the credentials file (i.e. invalid user) or is self 
                # then an appropriate error message should be displayed
                send_dict['res'] = ''
                send_dict['message'] = 'Error: %s is yourself!' % (friend)
            else:
                connection_dict[username]['block_set'].add(friend)
                send_dict['res'] = ''
                send_dict['message'] = 'OK. %s is add to block list!' % (friend)
            remoteSocket.send(json.dumps(send_dict).encode())
            continue

        # (6) unblocks the <user> who has been previously blocked by A
        if recv_dict['cmd'] == 'unblock':
            if 'friend' in recv_dict:
                friend = recv_dict['friend']
            else:
                print("error in recv_dict")
            if friend not in connection_dict:
                # If the <user> is not present in the credentials file 
                send_dict['res'] = ''
                send_dict['message'] = 'Error: %s Not Exist!' % (friend)
            elif friend not in connection_dict[username]['block_set']:
                # If the <user> is not present in the credentials file (i.e. invalid user) or is self 
                # then an appropriate error message should be displayed
                send_dict['res'] = ''
                send_dict['message'] = 'Error: %s is not on your block list!' % (friend)
            else:
                connection_dict[username]['block_set'].remove(friend)
                send_dict['res'] = ''
                send_dict['message'] = 'OK. %s is remove from block list!' % (friend)
            remoteSocket.send(json.dumps(send_dict).encode())
            continue

        # (7) log out user A.
        if recv_dict['cmd'] == 'logout':

            connection_dict[username]['islogin'] = False

            send_dict['res'] = 'logout'
            send_dict['message'] = 'OK. Logout due to command!'
            remoteSocket.send(json.dumps(send_dict).encode())
            time.sleep(1)
            remoteSocket.close()
            continue

        # (2.1) This command indicates that user A wishes to commence p2p messaging with <user>.
        if recv_dict['cmd'] == 'startprivate':
            friend = recv_dict['friend']
            if friend not in connection_dict:
                # If the <user> is not present in the credentials file 
                send_dict['res'] = ''
                send_dict['message'] = 'Error: %s Not Exist!' % (friend)
            elif friend == username:

                send_dict['res'] = ''
                send_dict['message'] = 'Error: %s is yourself!' % (friend)
            elif username in connection_dict[friend]['block_set']:
                # be blocked by target
                send_dict['res'] = ''
                send_dict['message'] = 'Error: %s block you!' % (friend)

            elif connection_dict[friend]['islogin'] == False:
                # store the message for offline delivery
                send_dict['res'] = ''
                send_dict['message'] = 'Error: %s is Offline!' % (friend)
            else:
                # send to current user to friend
                send_dict['res'] = 'startprivate'
                send_dict['friend'] = username
                send_dict['p2p_ip'] = connection_dict[username]['p2p_ip']
                send_dict['p2p_port'] = connection_dict[username]['p2p_port']
                send_dict['message'] = 'OK. P2P with %s. IP: %s Port:%d' % (username, connection_dict[username]['p2p_ip'],connection_dict[username]['p2p_port'])
                connection_dict[friend]['client_socket'].send(json.dumps(send_dict).encode())

                # send the friend info to current user
                send_dict['res'] = 'startprivate'
                send_dict['friend'] = friend
                send_dict['p2p_ip'] = connection_dict[friend]['p2p_ip']
                send_dict['p2p_port'] = connection_dict[friend]['p2p_port']
                send_dict['message'] = 'OK. P2P with %s. IP: %s Port:%d' % (friend, connection_dict[friend]['p2p_ip'],connection_dict[friend]['p2p_port'])
            remoteSocket.send(json.dumps(send_dict).encode())
            continue

        # print('Error: Invaild command: %s'%(recv_dict['cmd']))

def create_user_dict(password):
    d = {}
    d['last_active_time'] = datetime.datetime.now() 
    d['client_socket'] = None
    d['offline_message'] = ''
    d['last_login_time'] = None 
    d['block_set'] = set()
    d['p2p_ip'] = None
    d['password'] = password
    d['wrongtimes'] = 0
    d['islogin'] = False
    d['p2p_port'] = None
    return d

def listening_thread(global_dict,connection_dict):
    # accept connection from client
    global_dict['main_socket'] = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    global_dict['main_socket'].bind(('',global_dict['main_port']))
    global_dict['main_socket'].listen(8)

    n = global_dict['main_socket'].getsockname()

    global_dict['main_socket'].settimeout(1)

    while not global_dict['exit_flag']:
        try:
            remoteSocket,(romoteAddr, remotePort) = global_dict['main_socket'].accept()

            th = Thread(target = client_thread,args = (global_dict,connection_dict,remoteSocket, romoteAddr, remotePort))
            th.start()
            # print('get a connection')

        except Exception as e:
            pass
            # print(e)

    # print()



def read_user_file(connection_dict):
    file = open('credentials.txt','r')
    for line in file:
        words = line.strip().split(' ')
        [name, password] = words
        # create a user record
        connection_dict[name] = create_user_dict(password)
    file.close()

def main():


    global_dict = {}
    connection_dict = {}

    # read user-password file
    read_user_file(connection_dict)

    global_dict['main_port'] = 9999
    global_dict['block_time'] = 30
    global_dict['timeout'] = 500

    if len(sys.argv) == 4:
        global_dict['main_port'] = int(sys.argv[1])
        global_dict['block_time'] = int(sys.argv[2])
        global_dict['timeout'] = int(sys.argv[3])
    else:
        print('Server: invalid command parameter!')

        #return   

    global_dict['exit_flag'] = False
    main_thread = Thread(target = listening_thread,args = (global_dict,connection_dict))
    main_thread.start()

    th_timeout = Thread(target = timeout_thread,args = (global_dict,connection_dict))
    th_timeout.start()

    while True:
        try:
            s = input()
            print(global_dict)
        except KeyboardInterrupt as e:
            print("KeyboardInterrupt")
            global_dict['exit_flag'] = True
            break


    print("Server End")

if __name__ == '__main__':
    main()

