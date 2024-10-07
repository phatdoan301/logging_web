import asyncio
import websockets

# This set will hold all connected clients
connected_clients = set()

# Broadcast function that sends a message to all connected clients
async def broadcast(message):
    if connected_clients:  # Only send if there are clients connected
        tasks = [asyncio.create_task(client.send(message)) for client in connected_clients]
        await asyncio.gather(*tasks)

# Handler for each WebSocket connection
async def handler(websocket, path):
    # Add the new client to the connected_clients set
    connected_clients.add(websocket)
    try:
        # Wait for messages from the client
        async for message in websocket:
            print(message)
            # Broadcast the message to all clients
            await broadcast(message)
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Client disconnected: {e}")
    finally:
        # Remove the client from the set when it disconnects
        connected_clients.remove(websocket)

# Start the WebSocket server
async def main():
    # Serve the WebSocket handler on localhost at port 8765
    async with websockets.serve(handler, "0.0.0.0", 8000):
        print("WebSocket server started")
        await asyncio.Future()  # Keep the server running

# Run the WebSocket server
asyncio.run(main())

