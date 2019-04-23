from maediprojects import models
from maediprojects.extensions import db
from maediprojects.lib import util
import unicodecsv


def convert_from_currency(currency, _date, value):
    if currency == u"USD": return value
    source, rate, value_date = closest_exchange_rate(_date, currency)
    return float(value)*rate


def convert_to_currency(currency, _date, value):
    if currency == u"USD": return value
    source, rate, value_date = closest_exchange_rate(_date, currency)
    return float(value)/rate


def get_currencies():
    c = models.Currency()
    c.code = U"USD"
    c.name = u"USD"
    currencies = [c]
    currencies+=models.Currency.query.order_by(models.Currency.code.asc()).all()
    return currencies


def get_exchange_rate(transaction_date, currency):
    if currency == u"USD":
        return u"USD", 1, transaction_date
    return closest_exchange_rate(transaction_date, currency)


def automatic_currency_conversion(finances_id, force_update=False):
    aF = models.ActivityFinances.query.filter_by(
        id=finances_id).first()
    if not aF: return False
    if (not force_update) and (not aF.currency_automatic): return aF
    aF.currency_automatic = True
    if aF.currency == u"USD":
        aF.currency_source, aF.currency_rate, aF.currency_value_date = u"USD", 1, aF.transaction_date
    else:
        aF.currency_source, aF.currency_rate, aF.currency_value_date = closest_exchange_rate(aF.transaction_date, aF.currency)
    db.session.add(aF)
    db.session.commit()
    return aF


def add_names_to_currencies():
    _currencynamesf = open("maediprojects/lib/data/Currency.csv", "r")
    _currencynamescsv = unicodecsv.DictReader(_currencynamesf)
    _currencies_names = dict(map(lambda c: (c["code"], c["name_en"]), _currencynamescsv))
    for currency in models.Currency.query.all():
        currency.name = unicode(_currencies_names.get(currency.code, ""))
        db.session.add(currency)
    db.session.commit()


def import_exchange_rates():
    _erf = open("consolidated-exchangerates.csv", "r")
    _ercsv = unicodecsv.DictReader(_erf)
    currencies = dict(map(lambda c: (c.code, c.code), models.Currency.query.all()))
    sources = dict(map(lambda s: (s.name, s.id), models.ExchangeRateSource.query.all()))
    for row in _ercsv:
        exchangerate = models.ExchangeRate()
        sourcename = u"{} ({})".format(row["Source"], {u"D": u"Daily", u"M": u"Monthly"}[row["Frequency"]])
        if sourcename not in sources:
            source = models.ExchangeRateSource()
            source.name = sourcename
            db.session.add(source)
            db.session.commit()
            sources[sourcename] = source.id
        exchangerate.exchangeratesource_id = sources[sourcename]

        if row["Currency"] not in currencies:
            currency = models.Currency()
            currency.code = row["Currency"]
            currency.name = row["Currency"]
            db.session.add(currency)
            currencies[row["Currency"]] = currency.code
        exchangerate.currency_code = currencies[row["Currency"]]

        exchangerate.rate_date = util.isostring_date(row["Date"])
        exchangerate.rate = 1/float(row["Rate"])
        db.session.add(exchangerate)
    db.session.commit()

    oecd = models.ExchangeRateSource.query.filter_by(name=u"OECD (Monthly)").first()
    oecd.weight = 33
    db.session.add(oecd)
    db.session.commit()
    add_names_to_currencies()


def closest_exchange_rate(_date, currency):
    exchangerate = models.get_closest_date(_date, currency)
    return exchangerate[0].exchangeratesource.name, exchangerate[0].rate, exchangerate[0].rate_date
