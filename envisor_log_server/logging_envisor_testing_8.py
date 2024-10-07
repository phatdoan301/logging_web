#!/usr/bin/env python3
import asyncio
import websockets
import socket
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from datetime import datetime, timedelta
import time
import os

# WebSocket clients
CONNECTIONS = set()

# UDP server configuration
UDP_IP = "0.0.0.0"
UDP_PORT = 5008
WS_PORT = 8008
base_log_dir = "logs_envisor_testing_08"
drive_dir = '1727uLleypch9DcZstFlTwCwhb6yHPfag'
os.makedirs(base_log_dir, exist_ok=True)
uploaded_files = []

def get_time():
    try:
        time_string = time.asctime()
        return time_string.replace(" ", "_")
    except Exception as e:
        return f"Failed to get time: {e}"

def upload_to_drive(file_path, folder_id):
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)
    file_drive = drive.CreateFile({"parents": [{"id": folder_id}], "title": os.path.basename(file_path)})
    file_drive.SetContentFile(file_path)
    file_drive.Upload()
    print(f"Uploaded {file_path} to Google Drive.")
    uploaded_files.append(file_path)

def create_drive_folder(folder_name, parent_id = drive_dir):
    folder_id = None
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)
    query = f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false"
    file_list = drive.ListFile({'q': query}).GetList()
    if file_list:
        print(f"Folder {folder_name} already exists on Google Drive.")
        folder_id = file_list[0]['id']
    else:
        folder_metadata = {'title': folder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [{'id': parent_id}]}
        folder = drive.CreateFile(folder_metadata)
        folder.Upload()
        print(f"Created folder {folder_name} on Google Drive.")
        folder_id = folder['id']
    if folder_id:
        local_folder_path = os.path.join(base_log_dir, folder_name)
        os.makedirs(local_folder_path, exist_ok=True)
        print(f"Created local folder {local_folder_path}.")
    return folder_id

def list_drive_files(folder_id):
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)
    query = f"'{folder_id}' in parents and trashed=false"
    file_list = drive.ListFile({'q': query}).GetList()
    return [file['title'] for file in file_list]

def check_and_upload_unuploaded_files(folder_id, local_folder_path):
    drive_files = list_drive_files(folder_id)
    for filename in os.listdir(local_folder_path):
        if filename not in drive_files:
            file_path = os.path.join(local_folder_path, filename)
            upload_to_drive(file_path, folder_id)

async def udp_listener():
    global log_file, log_file_path, current_hour, current_day, folder_id

    current_day = datetime.now().date()
    folder_name = str(current_day)
    folder_id = create_drive_folder(folder_name)
    local_folder_path = os.path.join(base_log_dir, folder_name)
    current_hour = datetime.now().hour
    log_file_path = os.path.join(local_folder_path, f"log_{current_day}_{current_hour}.txt")
    log_file = open(log_file_path, "a")
    # Create UDP socket
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setblocking(False)  # Set socket to non-blocking mode
    udp_sock.bind((UDP_IP, UDP_PORT))
    print(f"Listening for UDP packets on {UDP_IP}:{UDP_PORT}")

    loop = asyncio.get_event_loop()
    while True:
        try:
            # Directly use loop.sock_recv_from to receive both data and address
            data, addr = await loop.sock_recvfrom(udp_sock, 1024)  # Buffer size is 1024 bytes
            if not data:
                continue
            # Decode and strip newline characters
            message = "[" + get_time().replace("_", " ") + "] " + data.decode().strip()
            print(f"Received message: {message} from {addr}")
            log_file.writelines(message + "\n")
            log_file.flush()
            # Broadcast received message to all WebSocket clients
            if CONNECTIONS:
                await asyncio.gather(*(client.send(message) for client in CONNECTIONS))
        except BlockingIOError:
            # Non-blocking sockets raise this when no data is available
            await asyncio.sleep(0.001)  # Short delay to prevent busy-waiting
        except Exception as e:
            print(f"Error receiving UDP data: {e}")

        now = datetime.now()
        if now.hour != current_hour:
            log_file.close()
            if folder_id:
                upload_to_drive(log_file_path, folder_id)
            current_hour = now.hour
            log_file_path = os.path.join(local_folder_path, f"log_{now.date()}_{current_hour}.txt")
            log_file = open(log_file_path, "a")
        # Check if the current day has changed
        if datetime.now().date() != current_day:
            check_and_upload_unuploaded_files(folder_id,local_folder_path)
            current_day = datetime.now().date()
            folder_name = str(current_day)
            folder_id = create_drive_folder(folder_name)
            local_folder_path = os.path.join(base_log_dir, folder_name)

async def echo(websocket):
    if websocket not in CONNECTIONS:
        CONNECTIONS.add(websocket)
        notification = f"New client connected. Total clients: {len(CONNECTIONS)}"
        print(notification)
        await asyncio.gather(*(client.send(notification) for client in CONNECTIONS))
    try:
        async for message in websocket:
            await asyncio.gather(*(client.send(message) for client in CONNECTIONS))
    finally:
        CONNECTIONS.remove(websocket)
        notification = f"Client disconnected. Total clients: {len(CONNECTIONS)}"
        print(notification)
        await asyncio.gather(*(client.send(notification) for client in CONNECTIONS))

async def websocket_server():
    async with websockets.serve(echo, "0.0.0.0", WS_PORT, ping_timeout=180, ping_interval=60):
        print("Connected to WebSocket server")
        await asyncio.Future()  # run forever

async def main():
    # Run UDP listener and WebSocket server concurrently
    await asyncio.gather(
        udp_listener(),
        websocket_server()
    )

if __name__ == "__main__":
    asyncio.run(main())
