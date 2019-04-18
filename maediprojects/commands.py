"""Click commands."""
import click
from flask.cli import with_appcontext


@click.command()
@click.argument('language', default='en')
@with_appcontext
def setup(language):
    """Initial setup."""
    from query import setup as qsetup
    qsetup.create_codes_codelists()
    qsetup.import_countries(language)
    qsetup.create_user()


@click.command()
@click.argument('country_code')
@with_appcontext
def setup_country(country_code):
    """Setup a country."""
    from query import setup as qsetup
    qsetup.import_countries(country_code)


@click.command()
@with_appcontext
def import_liberia():
    """Import Liberia data."""
    from query import import_liberia_db as qlibimport
    qlibimport.import_file()


@click.command()
@with_appcontext
def import_psip():
    """Import psip data."""
    from query import import_psip as qpsipimport
    qpsipimport.import_file()


@click.command()
@with_appcontext
def import_currencies():
    """ Import currency data"""
    from query import exchangerates as qexchangerates
    qexchangerates.import_exchange_rates()


@click.command()
@click.argument('date')
@click.argument('currency')
@with_appcontext
def test_closest_date(date, currency):
    """ Import currency data"""
    from query import exchangerates as qexchangerates
    from lib import util
    date = util.isostring_date(date)
    print qexchangerates.closest_exchange_rate(date, currency)
