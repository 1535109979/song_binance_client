from song_binance_client.market.md_gateway import BiFutureMdGateway
from song_binance_client.market.ms_grpc.ms_grpc_server import BianMarkerGrpcServer


class MsEngine:
    def __init__(self):
        self.gateway = BiFutureMdGateway()

    def start(self):
        self.gateway.loop.run_until_complete(BianMarkerGrpcServer(self.gateway).run())


if __name__ == '__main__':
    MsEngine().start()


