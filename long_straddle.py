import asyncio
import websockets
import json

# User's API key and secret
client_id = "uIZzUX8n"
client_secret = "8xPa_ut4HKz2yoK6NZBforhxQ3hu4HLpuM1J59f0thc"

# Long Straddle details
instrument_name_call = "BTC-29DEC23-30000-C"  # Example call option instrument
instrument_name_put = "BTC-29DEC23-30000-P"  # Example put option instrument
amount = 1  # Quantity of options to purchase


# Authentication function
async def authenticate(websocket):
    msg = {
        "jsonrpc": "2.0",
        "id": 9929,
        "method": "public/auth",
        "params": {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        }
    }
    await websocket.send(json.dumps(msg))
    response = await websocket.recv()
    return json.loads(response)


# Function to create a Long Straddle trade
async def create_long_straddle():
    async with websockets.connect('wss://test.deribit.com/ws/api/v2') as websocket:
        # Authenticate
        auth_response = await authenticate(websocket)
        if not auth_response.get('result'):
            print("Authentication failed", auth_response)
            return

        # Buy call option
        buy_call_msg = {
            "jsonrpc": "2.0",
            "id": 5275,
            "method": "private/buy",
            "params": {
                "instrument_name": instrument_name_call,
                "amount": amount,
                "type": "market",
                "label": "straddle_buy_call"
            }
        }
        await websocket.send(json.dumps(buy_call_msg))
        buy_call_response = await websocket.recv()
        print("Buy call option result:", buy_call_response)

        # Buy put option
        buy_put_msg = {
            "jsonrpc": "2.0",
            "id": 5276,
            "method": "private/buy",
            "params": {
                "instrument_name": instrument_name_put,
                "amount": amount,
                "type": "market",
                "label": "straddle_buy_put"
            }
        }
        await websocket.send(json.dumps(buy_put_msg))
        buy_put_response = await websocket.recv()
        print("Buy put option result:", buy_put_response)


# Execute the program
asyncio.get_event_loop().run_until_complete(create_long_straddle())
