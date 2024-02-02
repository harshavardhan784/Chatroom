import socket
import threading
import tkinter as tk
import os
from tkinter import filedialog
import pickle
import sys
import struct
import cv2

global flag
flag=1
import hashlib

# Function for user registration
def signup():
    username = input("Enter username: ")
    password = input("Enter password: ")

    # Create a hash of the password for security
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # Store the username and hashed password in a file or database
    with open("user_credentials.txt", "a") as file:
        file.write(f"{username}:{hashed_password}\n")

# Function for user login
def login():
    username = input("Enter username: ")
    password = input("Enter password: ")

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # Verify if the username and password exist in the file or database
    with open("user_credentials.txt", "r") as file:
        for line in file:
            stored_username, stored_password = line.strip().split(":")
            if stored_username == username and stored_password == hashed_password:
                return True
    
    return False

# Ask the user if they want to login or signup

client1_lock = threading.Lock()
root = tk.Tk()
root.withdraw()
status = b'0'  # Example initial status byte



def receive():
    # flag=0
    message = client1.recv(1024).decode('utf-8')
    if message == 'NICK':
        client1.send(nickname.encode('utf-8'))
        message = client1.recv(1024).decode('utf-8')
        print(message)
    while True:
        try:
            command = client1.recv(1).decode('utf-8')
            if command == 'M':  # Message transfer
                message = client1.recv(1024).decode('utf-8')
                print(message)
            elif command == 'F':  # File transfer 
                header = client1.recv(100).decode('utf-8')
                file_name, file_size_str = header.strip().split('|')
                file_size = int(file_size_str)
                
                file_path = filedialog.asksaveasfilename()
                                
                with open(file_path, "wb") as file:
                    bytes_received = 0
                    while bytes_received < file_size:
                        file_data = client1.recv(1024)
                        if not file_data:  
                            break
                        file.write(file_data)
                        bytes_received += len(file_data)
                    print("File received and saved successfully.")

            # if command=='V' or flag==1:
            #     flag=1
            #     receive_video_thread=threading.Thread(target=video_receive,args=())
            #     receive_video_thread.start()
                
                
        except Exception as e:
            print("An error occurred:", str(e))
            client1.close()
            break

def receiveV():
    message = client2.recv(1024).decode('utf-8')
    global flag
    if message == 'NICK':
        client2.send(nickname.encode('utf-8'))
        message = client2.recv(1024).decode('utf-8')
        print(message)
            
    while True:
        if flag==1:
            try:
                command = client2.recv(1).decode('utf-8')
                # print("------",command)
                if command=='V':
                    flag=0
                    # print(command)
                    receive_video_thread=threading.Thread(target=video_receive,args=())
                    receive_video_thread.start()
                    
            except Exception as e:
                print("An error occurred:", str(e))
                client1.close()


def video_receive():
    global flag
    print('The client1 is listening to the frame')
    data = b""
    payload_size = struct.calcsize("L")
    cv2.namedWindow(f"Receiving video{nickname}", cv2.WINDOW_NORMAL)
    # print("command")
    while True:
        # print("command")
        while len(data) < payload_size:
            packet = client2.recv(4 * 1024)
            
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
        
        while len(data) < msg_size:
            data += client2.recv(4 * 1024)
        
        frame_data = data[:msg_size]
        data = data[msg_size:]
        
        status, frame = pickle.loads(frame_data)
        # print(type(status))
        if status==b'1':
            flag=1
            cv2.destroyAllWindows()
            break
            # sys.exit(0)
        cv2.imshow(f"Receiving video{nickname}", frame)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            last_frame_data = pickle.dumps((status, frame))
            client2.send(struct.pack("L", len(last_frame_data)))
            client2.send(last_frame_data)
            cv2.destroyAllWindows()
            client2.send(b'q')
            sys.exit(0)


def send_file():
    file_path = filedialog.askopenfilename()
    print("Selected File:", file_path)
    # client1.send(file_path.encode('utf-8'))
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    header = f"{file_name}|{file_size}".ljust(100).encode('utf-8')
    client1.send(header)
    
    
    if file_path:
        with open(file_path, "rb") as file:
            while True:
                file_data = file.read(1024)
                if not file_data:
                    break
                # with client1_lock:
                client1.send(file_data)  # Send file data to the server
            # with client11_lock:
            #     client11.send(b"#")  # Signal the end of the file
        
def send_message():
    message=f'{nickname}: {input("")}'
    client1.send(message.encode('ascii'))


def send_video():
    global status
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        cv2.imshow('Camera', frame)
        
        data = pickle.dumps((status, frame))
        frame_size = struct.pack("L", len(data))
        
        try:
            client2.send(frame_size)
            client2.send(data)
        except:
            cap.release()
            cv2.destroyAllWindows()
            break
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            status=b'1'
            last_frame_data = pickle.dumps((status, frame))
            client2.send(struct.pack("L", len(last_frame_data)))
            client2.send(last_frame_data)
            print("Streaming stopped")
            status=b'0'
            break
    
    cap.release()
    cv2.destroyAllWindows()


def send_option():
    videoflag=0
    option = input("Enter 'M' for message or 'F' for file transfer: ")
    client1.send(option.encode('ascii'))
    # if(videoflag==0 and option =='V'):
    #     videoflag=1
    #     client2.send(option.encode('ascii'))
    if option == 'M':
        send_message()
    elif option == 'F':
        send_file()
    elif option == 'V':
        client2.send(option.encode('ascii'))
        send_video_thread=threading.Thread(target=send_video,args=())
        # send_video()
        send_video_thread.start()
    else:
        print("Invalid option. Please enter 'M' for message or 'F' for file transfer.")


def write():
    client1.send(nickname.encode('ascii'))
    client2.send(nickname.encode('ascii'))
    while True:
        send_option()
        
while True:
    choice = input("Enter 'L' for login or 'S' for signup: ")
    if choice.upper() == 'S':
        signup()
        print("Signup successful. Please login.")
        
    if choice.upper() == 'L':
        if login():
            print("Login successful.")
            break
            # Place your client code here for connecting to the network after successful login
        else:
            print("Invalid username or password.")
    else:
        print("Invalid choice.")
        
        
nickname = input("Choose a nickname: ")

client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client1.connect(('127.0.0.1', 55555))

client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client2.connect(('127.0.0.1', 55556))

        
receive_thread = threading.Thread(target=receive)
receive_thread.start()

receive_thread = threading.Thread(target=receiveV)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()
root.mainloop()


