from projectdashboard import models
from projectdashboard.extensions import db
from projectdashboard.lib import util
import csv
import requests
from flask import current_app
from hashlib import md5


EXCHANGE_RATES_API_FULL = "https://codeforiati.org/imf-exchangerates/imf_exchangerates.csv"

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
    c.name = u"U.S. Dollars"
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
    _currencynamesf = open("projectdashboard/lib/data/Currency.csv", "r")
    _currencynamescsv = csv.DictReader(_currencynamesf)
    _currencies_names = dict(map(lambda c: (c["code"], c["name_en"]), _currencynamescsv))
    for currency in models.Currency.query.all():
        currency.name = _currencies_names.get(currency.code, "")
        db.session.add(currency)
    db.session.commit()


def import_exchange_rates_from_file():
    _erf = open("consolidated-exchangerates.csv", "r")
    _ercsv = csv.DictReader(_erf)
    import_exchange_rates_file(_ercsv)


def import_exchange_rates_from_url():
    MORPHIO_API_KEY = current_app.config["MORPHIO_API_KEY"]
    print("Downloading full set of exchange rate data...")
    f = requests.get(EXCHANGE_RATES_API_FULL, stream=True)
    _ercsv = csv.DictReader([line.decode('utf-8') for line in f.iter_lines()])
    required_fieldnames = ['Date', 'Rate', 'Currency', 'Frequency', 'Source']
    for required_fieldname in required_fieldnames: assert required_fieldname in _ercsv.fieldnames
    print("Download begun, beginning import...")
    import_exchange_rates_file(_ercsv)


def import_exchange_rates_file(_ercsv):
    get_exchange_rates = db.session.query(
        models.ExchangeRate.rate_date,
        models.ExchangeRate.currency_code,
        models.ExchangeRateSource.name,
        ).join(
        models.ExchangeRateSource
        ).all()
    seen = list(map(lambda rate: (rate[0].isoformat(), rate[1], rate[2]), get_exchange_rates))
    currencies = dict(map(lambda c: (c.code, c.code), models.Currency.query.all()))
    sources = dict(map(lambda s: (s.name, s.id), models.ExchangeRateSource.query.all()))
    for i, row in enumerate(_ercsv):
        if i % 10000 == 0:
            db.session.commit()
            print("Processed {} rows".format(i))
        if row["Currency"] == '': continue
        sourcename = u"{} ({})".format(row["Source"], {u"D": u"Daily", u"M": u"Monthly"}[row["Frequency"]])
        _unique = (row['Date'], row['Currency'], sourcename)
        if _unique in seen: continue
        seen.append(_unique)
        exchangerate = models.ExchangeRate()
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
    print("Processed all {} rows".format(i))
    db.session.commit()

    oecd = models.ExchangeRateSource.query.filter_by(name=u"OECD (Monthly)").first()
    oecd.weight = 33
    db.session.add(oecd)
    db.session.commit()
    add_names_to_currencies()


def delete_existing_exchange_rates():
    models.ExchangeRate.query.delete()
    db.session.commit()


def closest_exchange_rate(_date, currency):
    exchangerate = models.get_closest_date(_date, currency)
    return exchangerate[0].exchangeratesource.name, exchangerate[0].rate, exchangerate[0].rate_date
