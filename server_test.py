import asyncio

async def echo_server(reader, writer):
    while True:
        data = await reader.read(100)
        if not data:
            break
        writer.write(data)
        await writer.drain()
    writer.close()

async def main(host, port):
    server = await asyncio.start_server(echo_server,host,port)
    await server.serve_forever()

asyncio.run(main('127.0.0.1', 5000))
