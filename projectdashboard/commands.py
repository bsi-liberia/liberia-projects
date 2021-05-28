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
    qsetup.import_countries('en', country_code)


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
def update_iati():
    """Update activities linked to IATI"""
    from .query import import_iati as qimport_iati
    qimport_iati.update_imported_data()


@click.command()
@with_appcontext
def import_currencies_from_file():
    """Import currency data"""
    from .query import exchangerates as qexchangerates
    qexchangerates.import_exchange_rates_from_file()


@click.command()
@with_appcontext
def import_currencies_from_url():
    """Import currency data from URL"""
    from .query import exchangerates as qexchangerates
    qexchangerates.import_exchange_rates_from_url()


@click.command()
@with_appcontext
def delete_currencies():
    """Delete currency data"""
    from .query import exchangerates as qexchangerates
    qexchangerates.delete_existing_exchange_rates()
    print("Deleted all existing currencies.")


@click.command()
@click.argument('date')
@click.argument('currency')
@with_appcontext
def test_closest_date(date, currency):
    """ Import currency data"""
    from .query import exchangerates as qexchangerates
    from lib import util
    date = util.isostring_date(date)
    print(qexchangerates.closest_exchange_rate(date, currency))


@click.command()
@with_appcontext
def import_iati():
    """Import Liberia data."""
    from query import import_iati as qiatiimport
    qiatiimport.import_documents()


@click.command()
@with_appcontext
def import_psip_transactions():
    """ Import currency data"""
    from query import import_psip_transactions as qimportpsip
    qimportpsip.import_transactions()


@click.command()
@click.argument('username')
@click.argument('role_slug')
@with_appcontext
def add_user_role(username, role_slug):
    """ Add user roles """
    from query import user as quser
    assert username and role_slug
    if quser.add_user_role(username, role_slug):
        print("User role created successfully.")
    else:
        print("Sorry, user role could not be created. Perhaps it already exists?")


@click.command()
@click.argument('username')
@click.argument('role_slug')
@with_appcontext
def delete_user_role(username, role_slug):
    """ Delete user roles """
    from query import user as quser
    assert username and role_slug
    if quser.delete_user_role(username, role_slug):
        print("User role deleted successfully.")
    else:
        print("Sorry, user role could not be deleted. Perhaps it does not exist?")


@click.command()
@click.argument('username')
@with_appcontext
def list_user_roles(username):
    """ List user roles """
    from query import user as quser
    assert username
    roles = quser.list_user_role_by_username(username)
    if roles:
        print("User {} has the following roles: {}".format(username, ", ".join(roles)))
    else:
        print("Sorry, could not find roles for that user.")


@click.command()
@with_appcontext
def list_users():
    """ List user roles """
    from query import user as quser
    users = list(map(lambda u: u.username, quser.user()))
    if users:
        print("There are the following users:")
        for user in users: print(user)
    else:
        print("Sorry, could not find any users.")


@click.command()
@with_appcontext
def list_roles():
    """ List user roles """
    from query import user as quser
    roles = list(map(lambda r: r.slug, quser.role()))
    if roles:
        print("There are the following roles:")
        for role in roles: print(role)
    else:
        print("Sorry, could not find any roles.")
