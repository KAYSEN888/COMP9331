
from threading import Thread
import datetime
import socket
import time
import json
import sys


def p2p_thread(global_dict, connection_dict):
    pass
    while True:
        try:
            friend_socket,(friend_ip, friend_port) = global_dict['p2p_socket'].accept()
            recv_data = friend_socket.recv(2048)
        except IOError as e:
            continue
        if not recv_data:
            friend_socket.close()
            continue
        # print(recv_data)
        recv_dict = json.loads(recv_data.decode())
        print(recv_dict['message'])

        if recv_dict['res'] == 'stopprivate':
            username = recv_dict['username']
            if username in connection_dict:
                del connection_dict[username]
            else:
                print('can not remove %s from p2p dict'%username)
        



def main():

    pass
    global_dict = {}
    connection_dict = {}

    global_dict['exit_flag'] = False


    global_dict['server_ip'] = '127.0.0.1'
    global_dict['server_port'] = 9999

    
    # handle input parameter
    if len(sys.argv) == 3:
        global_dict['server_ip'] = sys.argv[1]
        global_dict['server_port'] = int(sys.argv[2])
    else:
        print('Client: invalid command parameter!')

        global_dict['server_ip'] = '127.0.0.1'
        global_dict['server_port'] = 9999
        # return 

    # init p2p socket
    global_dict['p2p_socket'] = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    global_dict['p2p_socket'].bind(('',0))
    global_dict['p2p_socket'].listen(8)
    

    th_p2p = Thread(target = p2p_thread,args = (global_dict,connection_dict))
    th_p2p.start()

    
    # init server socket
    global_dict['server_socket'] = socket.socket()
    global_dict['server_socket'].connect((global_dict['server_ip'], global_dict['server_port']))

    # (1) log in

    while True:
        line = input('Username: ')
        if line:
            username = line
            break
    while True:
        line = input('Password: ')
        if line:
            password = line
            p2p_ip, p2p_port  = global_dict['p2p_socket'].getsockname()
            send_dict = {'cmd':'login', 'username':username, 'password':password, 'p2p_port': p2p_port }
            global_dict['server_socket'].send(json.dumps(send_dict).encode())

            recv_data = global_dict['server_socket'].recv(2048)
            if not recv_data:
                # server close the socket
                print("remove socket close")
                return
            recv_dict = json.loads(recv_data)

            print(recv_dict['message'])
            if recv_dict['res'] == 'loginsuccess':
                break
            
    # (2) communication loop
    def server_listening_thread(conf_dict):
        pass
        while True:
            try:
                recv_data = global_dict['server_socket'].recv(2048)
                if not recv_data:
                    print('Server Close Connection')
                    global_dict['exit_flag'] = True
                    return 
                recv_dict = json.loads(recv_data.decode())
            except IOError as e:
                global_dict['exit_flag'] = True
                print('Server Close Connection')
                return 

            print(recv_dict['message'])
            if recv_dict['res'] == 'logout':
                global_dict['exit_flag'] = True

            elif recv_dict['res'] == 'startprivate':
                pass
                friend = recv_dict['friend']
                p2p_ip = recv_dict['p2p_ip']
                p2p_port = recv_dict['p2p_port']
                connection_dict[friend] = {'p2p_ip':p2p_ip,'p2p_port':p2p_port}


    # create listening thread
    th = Thread(target = server_listening_thread,args = ({},))
    th.start()

    while not global_dict['exit_flag']:
        line = input()
        if global_dict['exit_flag']:
            break
        if not line:
            continue
        words = line.split()
        cmd = words[0]

        # (1) Send <message> to <user> through the server
        if cmd == 'message':
            if len(words) < 3:
                print('Invalid input')
                continue
            send_dict = {'username':username}
            send_dict['cmd'] = cmd
            send_dict['friend'] = words[1]
            send_dict['message'] = ' '.join(words[2:])
            global_dict['server_socket'].send(json.dumps(send_dict).encode())            
            
            continue
        # (2) Send <message> to all online users except A and those users who have blocked A
        if cmd == 'broadcast':
            if len(words) < 2:
                print('Invalid input')
                continue
            send_dict = {'username':username}
            send_dict['cmd'] = cmd
            send_dict['message'] = ' '.join(words[1:])
            global_dict['server_socket'].send(json.dumps(send_dict).encode())     
            continue  

        # (3) This should display the names of all users that are currently online excluding A.
        if cmd == 'whoelse':
            if len(words) != 1:
                print('Invalid input')
                continue
            send_dict = {'username':username}
            send_dict['cmd'] = cmd
            global_dict['server_socket'].send(json.dumps(send_dict).encode())     
            continue  

        # (4) This should display the names of all users who were logged in at any time
        if cmd == 'whoelsesince':
            if len(words) != 2:
                print('Invalid input')
                continue
            send_dict = {'username':username}
            send_dict['cmd'] = cmd
            send_dict['time'] = int(words[1])
            global_dict['server_socket'].send(json.dumps(send_dict).encode())     
            continue  

        # (5) blocks the <user> from sending messages to A.
        if cmd == 'block':
            if len(words) != 2:
                print('Invalid input')
                continue
            send_dict = {'username':username}
            send_dict['cmd'] = cmd
            send_dict['friend'] = words[1]
            global_dict['server_socket'].send(json.dumps(send_dict).encode())   
            continue

        # (6) unblocks the <user> who has been previously blocked by A
        if cmd == 'unblock':
            if len(words) != 2:
                print('Invalid input')
                continue
            send_dict = {'username':username}
            send_dict['cmd'] = cmd
            send_dict['friend'] = words[1]
            global_dict['server_socket'].send(json.dumps(send_dict).encode())   
            continue

        # (7) unblocks the <user> who has been previously blocked by A
        if cmd == 'logout':
            if len(words) != 1:
                print('Invalid input')
                continue
            send_dict = {'username':username}
            send_dict['cmd'] = cmd
            global_dict['server_socket'].send(json.dumps(send_dict).encode())   
            continue

        # (2.1) This command indicates that user A wishes to commence p2p messaging with <user>.
        if cmd == 'startprivate':
            if len(words) != 2:
                print('Invalid input')
                continue
            send_dict = {'username':username}
            send_dict['cmd'] = cmd
            send_dict['friend'] = words[1]
            global_dict['server_socket'].send(json.dumps(send_dict).encode())   
            continue

        # (2.2) Send <message> to <user> directly without routing through the server
        if cmd == 'private':
            if len(words) < 3:
                print('Invalid input')
                continue
            friend = words[1]
            if friend not in connection_dict:
                print('execute startprivate to %s first'%friend)
                continue
            send_dict = {'username':username}
            send_dict['res'] = ''
            send_dict['message'] = 'Private Message From %s:'%username +' '.join(words[2:])
            # send by socket
            try:
                newsocket = socket.socket()
                newsocket.connect((connection_dict[friend]['p2p_ip'],connection_dict[friend]['p2p_port']))
                newsocket.send(json.dumps(send_dict).encode())
                newsocket.close()
                print('OK. Send Success')
            except IOError as e:
                print('Error: Send Failed')
            continue

        if cmd == 'stopprivate':
            if len(words) != 2:
                print('Invalid input')
                continue
            friend = words[1]
            if friend not in connection_dict:
                print('there is not a p2p connection with %s'%friend)
                continue
            send_dict = {'username':username}
            send_dict['res'] = 'stopprivate'
            send_dict['message'] = 'stop private with %s'%username
            # send by socket
            try:
                newsocket = socket.socket()
                newsocket.connect((connection_dict[friend]['p2p_ip'],connection_dict[friend]['p2p_port']))
                newsocket.send(json.dumps(send_dict).encode())
                newsocket.close()
                print('OK. Send Success')
            except IOError as e:
                print('Error: Send Failed')
            del connection_dict[friend]
            continue

        print('Invalid input')
    print('Client End')
        


if __name__ == '__main__':
    time.sleep(0.2)
    main()

