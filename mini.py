import subprocess
import re
import time
import platform
import os
import random
import socket
import threading
from collections import deque

# Globale Variablen
AP_NAME = f"Mini{random.randint(0, 99999):05d}"  # Initialer zufälliger Name
HOST = '127.0.0.1'  # Lokale IP-Adresse (nur für einfache Tests)
PORT = 12345  # Port für die Kommunikation
friends = {}

def scan_networks():
    """
    Scans the nearby Wi-Fi networks using the 'netsh wlan show networks' command.
    
    Returns:
        tuple: Number of networks and a list of SSIDs found.
    """
    try:
        result = subprocess.run("netsh wlan show networks", shell=True, capture_output=True, text=True, encoding="latin1")
        
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, result.args)
        
        ssid_pattern = re.compile(r"SSID\s*\d*\s*:\s*(.*)")
        ssids = ssid_pattern.findall(result.stdout)
        
        return len(ssids), ssids
    except subprocess.CalledProcessError as e:
        print(f"error while executing command: {e}")
        return 0, []
    except Exception as e:
        print(f"Unknown error: {e}")
        return 0, []

def get_face(num_aps, dynamic_thresholds):
    """
    Returns a face and message based on the number of detected Wi-Fi networks.
    
    Args:
        num_aps (int): The number of access points found.
        dynamic_thresholds (tuple): Dynamically adjusted thresholds for face and message.
        
    Returns:
        tuple: A face (str) and a message (str).
    """
    low_threshold, medium_threshold, high_threshold = dynamic_thresholds

    if num_aps == 0:
        return "(:|", "Nothing.."
    elif num_aps < low_threshold:
        return "(o_o)", "Oh come on"
    elif num_aps < medium_threshold:
        return "(o_O)", "Normal Day Huh"
    elif num_aps < high_threshold:
        return "(¬_¬)", "oh cool a bit more than normal"
    else:
        return "(o_o)", "Many APS Today YAY"

def clear_screen():
    """
    Clears the terminal screen based on the operating system.
    """
    os_type = platform.system().lower()
    
    if os_type == "windows":
        os.system("cls")  
    else:
        os.system("clear")  

def update_dynamic_thresholds(aps_history):
    """
    Dynamically adjust thresholds based on the historical data of AP counts.
    
    Args:
        aps_history (deque): A deque containing recent AP counts.
        
    Returns:
        tuple: A tuple with adjusted low, medium, and high thresholds.
    """
    average_aps = sum(aps_history) / len(aps_history) if aps_history else 0
    low_threshold = max(1, average_aps - 2)
    medium_threshold = average_aps + 2
    high_threshold = average_aps + 5
    return low_threshold, medium_threshold, high_threshold

def handle_connection(conn, addr):
    """
    Handles incoming connections and updates the friend list based on the received data.
    """
    global AP_NAME
    try:
        data = conn.recv(1024).decode('utf-8')
        if data:
            print(f"Empfangen von {addr}: {data}")
            parts = data.split(',')
            friend_id = parts[0]
            friend_face = parts[1]
            signal_strength = parts[2]
            if friend_id == AP_NAME:
                print(f"I ignore myself: {AP_NAME}")
                return 

            friends[friend_id] = {'face': friend_face, 'signal_strength': signal_strength}
            print(f"Freunde: {friends}")
            
            if friend_id in friends and friend_id != AP_NAME:
                print(f"{AP_NAME} and {friend_id} have the same id!")
                new_id = f"Mini{random.randint(0, 99999):05d}"
                print(f"{AP_NAME} changes id to {new_id}")
                AP_NAME = new_id 
                conn.sendall(f"ID changed to {new_id}".encode('utf-8'))
    except Exception as e:
        print(f"error connecting: {e}")
    finally:
        conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"server runs at {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_connection, args=(conn, addr)).start()

def connect_to_friend():
    try:
        if AP_NAME == AP_NAME: 
            print(f"I ignore myself: {AP_NAME}")
            return

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((HOST, PORT))

        face, message = get_face(len(friends), (5.0, 9.0, 12.0))
        data = f"{AP_NAME},{face},{random.randint(0, 100)}"
        client.sendall(data.encode('utf-8'))
        print(f"sendet: {data}")
        client.close()
    except Exception as e:
        print(f"error while connecting: {e}")


def main():
    aps_history = deque(maxlen=10)
    threading.Thread(target=start_server, daemon=True).start()

    while True:
        clear_screen()
        num_aps, ssids = scan_networks()
        dynamic_thresholds = update_dynamic_thresholds(aps_history)
        aps_history.append(num_aps)
        face, message = get_face(num_aps, dynamic_thresholds)
        friend_info = "found no friends..yet"
        if AP_NAME in friends:
            friend = friends[AP_NAME]
            friend_info = f"Friend: ({friend['face']}) {AP_NAME} {friend['signal_strength']}%"

        print(f"APS: {num_aps} {friend_info}")
        print(face)
        print(message)
        print(f"Thresholds: {dynamic_thresholds}")
        print("-" * 20)
        connect_to_friend()

        time.sleep(5)

if __name__ == "__main__":
    main()
