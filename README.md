# Liberia Projects Database

Simple project database to collect information about aid projects in Liberia and publish it in IATI format (both v1.03 and v2.01).

## License: AGPL v3.0

Copyright (c) 2016-2018 Mark Brough, Ministère des Affaires étrangères et du Développement international, Overseas Development Institute Liberia

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

## Screenshots

### Projects
![Projects](/img/projects.png "Projects")

Landing page shows list of projects that have been added so far. Most users can see only their own projects; administrators can see all projects.

### Activity editor
![Activity editor](/img/basic-data.png "Activity editor")

Simple form to edit basic activity data. Data is automatically saved as you move through the form.

### Simple geocoder
![Simple geocoder](/img/geocoder.png "Simple geocoder")

The geocoder retrieves locations automatically from [Geonames.org](http://geonames.org) and providers a list of locations that can be selected by clicking on them on the left hand side. They appear as markers on the map and are instantly saved to the database.

### Financial data
![Financial data](/img/financial-data.png "Financial data")

New financial data (commiments and disbursements) can easily be added. The data is saved as you move through the form.

## Features

1. Internationalisation has been added using [Flask-Babel](https://pythonhosted.org/Flask-Babel/) - you can specify the country in config.py and then add new translations as outlined in Flask-Babel's documentation. Translation strings are stored in `maediprojects/translations`
2. Editing projects is fast and fields are saved as the user moves through the form to avoid loss of data. Fields are constrained as much as possible to ensure the correct format of data - for example, [bootstraper-datetimepicker](https://github.com/smalot/bootstrap-datetimepicker) is used to constrain dates and provide a nice UI.
3. Locations are retrieved from [Geonames.org](http://download.geonames.org/export/dump/) upon request, to populate a simple geocoder. The user can click on regions (ADM1) or choose to see locations within a particular region (ADM2).
4. Financial data can either be provided as a single total amount (as it is currently stored in the original source spreadsheets) or as individual financial transactions (as IATI encourages). If individual financial transactions are specified then these will be published in the IATI data; otherwise the total figures will be.
5. The data is generated in IATI v1.03 and v2.01 formats, with activities grouped by country. In time / if needed, this could potentially be cached, but it is fast at the moment.
6. Fields unlikely to change are filled out by default and hidden, with the option of showing them. Each user has a default country, which means the user doesn't have to specify this each time.

## Limitations

The current software has a few limitations which could be improved upon:

* it does not generate organisation files at all. You can use something like [AidStream.org](http://aidstream.org/) for this
* it does not generate results data for activities.  [Sage2IATI](https://github.com/markbrough/sage-iati) has some relevant code for this, but the user interface could be simplified and it was not currently necessary for this project database.
* project documents cannot be attached to activities.

## Deployment and getting up and running

1. Clone the repository:
  ```
  git clone git@github.com:markbrough/maedi-projects.git
  ```

2. Set up a virtualenv:
   ```
   virtualenv ./pyenv
   ```

3. Activate the virtualenv:
   ```
   source ./pyenv/bin/activate
   ```

4. Install the requirements:
   ```
   pip install -r requirements.txt
   ```

5. Copy and edit the config.py.tmpl:
   ```
   cp config.py.tmpl config.py
   ```

6. Create an environment variable for the app:
   ```
   export FLASK_APP=maediprojects/__init__.py
   ```

7. Run database migrations:
   ```
   flask db upgrade
   ```

8. Run initial setup:
   ```
   flask setup
   ```

9. Run the server:
   ```
   python manage.py runserver
   ```

10. You can log in using the admin username and password defined in your `config.py`

11. Before using the geocoding feature, you need to import locations from Geonames. When logged in as an administrator, you can click on the username in the top right, then "Manage codelists" / "Gérer les listes de codes". Click on the "Locations" / "Localisations" tab, then choose a country to import.
