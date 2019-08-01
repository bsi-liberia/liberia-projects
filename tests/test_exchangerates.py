from flask import url_for
import datetime

class TestExchangeRates:
    def test_import_exchange_rates(self, client):
        from maediprojects.query import exchangerates
        from maediprojects import models
        day_before_yesterday = datetime.datetime.utcnow().date() - datetime.timedelta(days=2)
        since_date = day_before_yesterday.isoformat()
        exchangerates.import_exchange_rates_from_url(False, since_date)
        assert(type(models.ExchangeRate.query.first()) == models.ExchangeRate)
