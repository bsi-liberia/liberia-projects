from flask import url_for
import datetime

class TestExchangeRates:
    def test_import_exchange_rates(self, client):
        from maediprojects.query import exchangerates
        from maediprojects import models
        several_days_ago = datetime.datetime.utcnow().date() - datetime.timedelta(days=5)
        since_date = several_days_ago.isoformat()
        exchangerates.import_exchange_rates_from_url(False, since_date)
        assert(type(models.ExchangeRate.query.first()) == models.ExchangeRate)
