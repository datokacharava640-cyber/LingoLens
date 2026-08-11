import os
import asyncio
import websockets

# Render ავტომატურად აწვდის PORT ცვლადს
PORT = int(os.environ.get("PORT", 10000))
HOST = "0.0.0.0"

async def handler(websocket):
    # აქ არის თქვენი სერვერის ლოგიკა / Gemini-სთან გადაგზავნა
    async for message in websocket:
        await websocket.send(message)

async def main():
    print(f"სერვერი გაეშვა პორტზე: {PORT}")
    async with websockets.serve(handler, HOST, PORT):
        await asyncio.Future()  # სერვერის მუდმივად გაშვება

if __name__ == "__main__":
    asyncio.run(main())
