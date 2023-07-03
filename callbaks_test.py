import asyncio

class EchoProtocol(asyncio.Protocol):
    def connection_made(self, transport) -> None:
        self.transport = transport

    def data_received(self, data) -> None:
        print(f'{ data = }')
        message  =data.decode()
        print(f'{ message = }')
        self.transport.write(data)

async def main(host,port):
    loop = asyncio.get_running_loop()
    server = await loop.create_server(EchoProtocol,host,port)
    await server.serve_forever()

asyncio.run(main('127.0.0.1',5000))
