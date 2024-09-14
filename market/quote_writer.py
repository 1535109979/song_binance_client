class QuoteWriter():
    def __init__(self,writer):
        self.writer = writer
        self.subscribe_symbol = set()

    def add_symbol(self,symbol):
        self.subscribe_symbol.update(symbol)

    def subtract_symbol(self,symbol):
        self.subscribe_symbol.difference_update(symbol)