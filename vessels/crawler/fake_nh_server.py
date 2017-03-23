import asyncio

from pathlib import Path

xml_path = Path(__file__).absolute().parent / 'fixture.xml'


class EchoServerClientProtocol(asyncio.Protocol):

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport
        self.run = True

        async def send_xml():
            while self.run:
                print('Send new xml')
                with xml_path.open() as f:
                    data = f.read(50)

                    while self.run:

                        if not data:
                            break
                        transport.write(data.encode('utf8'))
                        data = f.read(50)

                await asyncio.sleep(1)

        asyncio.ensure_future(send_xml())

    def data_received(self, data):
        message = data.decode()
        print('Data received: {!r}'.format(message))

    def connection_lost(self, exc):
        self.run = False
        self.transport.close()
