import grpc

from song_binance_client.grpc_files import ms_server_pb2_grpc, ms_server_pb2
from song_binance_client.utils.thread import run_in_new_thread


class BianMarketStub():
    def __init__(self):
        channel = grpc.insecure_channel("0.0.0.0:6610")
        self.sub = ms_server_pb2_grpc.AsyncMarketServerStub(channel=channel)
        self.subscribed_instruments = set()
        self.sub_count = 0

    @run_in_new_thread(thread_name="MS")
    def subscribe_stream_in_new_thread(self, on_quote, instruments=None):
        self.subscribe_stream(on_quote=on_quote, instruments=instruments, )

    def subscribe_stream(self, on_quote, instruments=None):
        self.sub_count += len(instruments)
        print(self.sub_count, instruments)
        if instruments:
            self.subscribed_instruments.update(set(instruments))

        quote_reply_stream = self.sub.GetQuoteStream(ms_server_pb2.Symbols(symbols=instruments))

        for i in quote_reply_stream:
            on_quote(i.quote)

    def add_subscribe(self, instruments):
        self.sub_count += len(instruments)
        print(self.sub_count, instruments)
        self.sub.AddSubscribe(ms_server_pb2.Symbols(symbols=instruments))

    def stop_egine(self):
        print('market stub stop')
        self.sub.StopEngine(ms_server_pb2.FlagReply(flag=True))


def on_quote(quote):
    print('get quote:', quote)


if __name__ == '__main__':
    BianMarketStub().subscribe_stream_in_new_thread(instruments=['BTCUSDT'], on_quote=on_quote)

    while 1:
        pass