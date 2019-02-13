"""Click commands."""
import click


@click.command()
@click.argument('language', default='en')
def setup(language):
    """Initial setup."""
    from query import setup as qsetup
    qsetup.create_codes_codelists()
    qsetup.import_countries(language)
    qsetup.create_user()


@click.command()
@click.argument('country_code')
def setup_country(country_code):
    """Setup a country."""
    from query import setup as qsetup
    qsetup.import_countries(country_code)


@click.command()
def import_liberia():
    """Import Liberia data."""
    from query import import_liberia_db as qlibimport
    qlibimport.import_file()


@click.command()
def import_psip():
    """Import psip data."""
    from query import import_psip as qpsipimport
    qpsipimport.import_file()
