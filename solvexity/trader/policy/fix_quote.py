class FixQuote:
    def __init__(self, quote: float):
        self.quote = quote

    def get_quote(self, _):
        return self.quote

    def __str__(self):
        return f'FixQuote({self.quote})'

    def __repr__(self):
        return str(self)