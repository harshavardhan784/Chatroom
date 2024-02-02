import socket
import threading
import tkinter as tk
from tkinter import filedialog
import os
import pickle
import cv2
import struct
import sys 


host = '127.0.0.1'  # local host
port = 55556

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

clients = []
nicknames = []


def broadcast(message,client1,command):
    
    for client in clients:
        if(client!=client1):
            # print(message," ")
            if(command=='M'):
                client.send(message.encode('utf-8'))
            # elif(command=='V'):
            #     client.send(message)
            else:
                client.send(message)
                
def broadcastc(command,client1):
    for client in clients:
        if(client!=client1):
            if command=='V':
                # print(command)
                client.send(command.encode('utf-8'))

def handle(client):
    while True:
        try:
            command=client.recv(1).decode('utf-8')
            # print(command)
            # command='V'
            broadcastc(command,client)
            if command == 'V':
                print('The client is listening to the frame')
                data = b""
                payload_size = struct.calcsize("L")
                # cv2.namedWindow("Receiving video Server", cv2.WINDOW_NORMAL)
                
                while True:
                    while len(data) < payload_size:
                        packet = client.recv(4 * 1024)
                        
                        if not packet:
                            break
                        data += packet
                    
                    packed_msg_size = data[:payload_size]
                    data = data[payload_size:]
                    
                    try:
                        msg_size = struct.unpack("L", packed_msg_size)[0]
                    except:
                        print("Done!")
                        cv2.destroyAllWindows()
                        break
                    broadcast(packed_msg_size,client,command)
                    while len(data) < msg_size:
                        data += client.recv(4 * 1024)
                    
                    frame_data = data[:msg_size]
                    data = data[msg_size:]
                    broadcast(frame_data,client,command)
                    status, frame = pickle.loads(frame_data)
                    # print(type(status))
                    if status==b'1':
                        cv2.destroyAllWindows()
                        break
                        # sys.exit(0)
                    cv2.imshow("Receiving video at server", frame)
                    key = cv2.waitKey(1) & 0xFF
                    
                    if key == ord('q'):
                        last_frame_data = pickle.dumps((status, frame))
                        client.send(struct.pack("L", len(last_frame_data)))
                        client.send(last_frame_data)
                        cv2.destroyAllWindows()
                        client.send(b'q')
                        # sys.exit(0)
                        break
                        


        except Exception as e:
            print("An error occurred:\\", str(e))
            break


def receive():
    while True:
        client, address = server.accept()
        print(f"Connected with {str(address)}")

        client.send('NICK'.encode())
        nickname = client.recv(1024).decode()
        nicknames.append(nickname)
        clients.append(client)

        print(f"Nickname of the client is {nickname}!")
        broadcastc('M',client)
        broadcast(f'{nickname} joined the chat!',client,'M')
        client.send('connected to the server!'.encode())

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()


print("Server is listening...")
receive()
