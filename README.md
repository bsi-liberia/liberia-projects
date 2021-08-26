# Liberia Projects Dashboard

Simple project database to collect information about aid projects in Liberia and publish it in IATI format (both v1.03 and v2.01). View it at https://liberiaprojects.org

Requires Python v3

[![Build Status](https://travis-ci.com/bsi-liberia/liberia-projects.svg?branch=master&status=passed)](https://travis-ci.com/github/bsi-liberia/liberia-projects)
[![License: AGPL v3](https://img.shields.io/badge/license-AGPLv3-blue.svg)](https://github.com/bsi-liberia/liberia-projects/blob/main/LICENSE.txt)

## License: AGPL v3.0

Copyright (c) 2016-2021 Mark Brough, Overseas Development Institute

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

### Front Page
![Projects](/img/liberia-project-dashboard.png "Front page of Project Dashboard")

The landing page of the Liberia Project Dashboard contains a map of project locations.

### Front Page - visualisations of spend over time
![Projects](/img/liberia-project-dashboard-2.png "Visualisations of spend over time")

On the front page, there are also simple visualisations of spend over time

### Project profiles
![Project profiles](/img/liberia-project-dashboard-3.png "Project profiles")

Project profiles contain a simple summary of data

### Project profiles - financial data
![Project profiles](/img/liberia-project-dashboard-4.png "Summary of financial data on project profile")

Project profiles contain a simple summary of project financial data

### Project profiles - results data
![Project profiles](/img/liberia-project-dashboard-6.png "Summary of results data on project profile")

Results data is also displayed on the Dashboard, where available.

### Export data
![Project profiles](/img/liberia-project-dashboard-5.png "Export data")

Data can be exported into Excel and imported again using Excel templates.


## Features

**NB this section is very out of date and will be updated soon.**

1. Internationalisation has been added using [Flask-Babel](https://pythonhosted.org/Flask-Babel/) - you can specify the country in config.py and then add new translations as outlined in Flask-Babel's documentation. Translation strings are stored in `projectdashboard/translations`
2. Editing projects is fast and fields are saved as the user moves through the form to avoid loss of data. Fields are constrained as much as possible to ensure the correct format of data - for example, [bootstraper-datetimepicker](https://github.com/smalot/bootstrap-datetimepicker) is used to constrain dates and provide a nice UI.
3. Locations are retrieved from [Geonames.org](http://download.geonames.org/export/dump/) upon request, to populate a simple geocoder. The user can click on regions (ADM1) or choose to see locations within a particular region (ADM2).
4. Financial data can either be provided as a single total amount (as it is currently stored in the original source spreadsheets) or as individual financial transactions (as IATI encourages). If individual financial transactions are specified then these will be published in the IATI data; otherwise the total figures will be.
5. The data is generated in IATI v1.03 and v2.01 formats, with activities grouped by country. In time / if needed, this could potentially be cached, but it is fast at the moment.
6. Fields unlikely to change are filled out by default and hidden, with the option of showing them. Each user has a default country, which means the user doesn't have to specify this each time.

## Limitations

**NB this section is very out of date and will be updated soon.**

The current software has a few limitations which could be improved upon:

* it does not generate organisation files at all. You can use something like [AidStream.org](http://aidstream.org/) for this
* it does not generate results data for activities.  [Sage2IATI](https://github.com/markbrough/sage-iati) has some relevant code for this, but the user interface could be simplified and it was not currently necessary for this project database.
* project documents cannot be attached to activities.

## Installation (back-end)

Install required packages, if these are not already installed:

```
apt-get install python python3-pip python3-dev libxml2-dev libxslt-dev build-essential libssl-dev zlib1g-dev git
```

1. Clone the repository:
   ```
   git clone git@github.com:bsi-liberia/liberia-projects.git
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

6. Run database migrations:
   ```
   flask db upgrade
   ```

7. Run initial setup:
   ```
   flask setup
   ```

8. Run the development server:
   ```
   flask run
   ```

9. You can log in using the admin username and password defined in your `config.py`

10. Before using the geocoding feature, you need to import locations from Geonames. When logged in as an administrator, you can click on the username in the top right, then "Manage codelists". Click on the "Locations" tab, then choose a country to import.

## Installation (front-end)

1. Switch to the `client` directory and install dependencies.
   ```
   cd client
   npm i
   ```

3. Copy and edit as required nuxt configuration:
   ```
   cp nuxt.config.tmpl.js nuxt.config.js
   ```

4. Run in development mode:
   ```
   npm run dev
   ```

## Running with Apache

1. Install Apache and `mod_wsgi`:

   ```
   apt-get install apache2 libapache2-mod-wsgi
   ```

2. Create a _.wsgi_ file. Assuming you used a `virtualenv`, you need to provide the path to the virtualenv and then the application. It should look something like this:
   ```
   import logging, sys
   logging.basicConfig(stream=sys.stderr)
   sys.path.insert(0, '/path-to-liberia-projects/pyenv/lib/python2.7/site-packages')
   sys.path.insert(0, '/path-to-liberia-projects')
   from wsgi import create_app
   application=create_app()
   ```

3. Edit the Apache config file (in `/etc/apache2/sites-available/liberiaprojects.conf`) to point to the new .wsgi file. In this example,
   ```
    <VirtualHost *:80>
            #ServerName www.example.com
            ServerAdmin webmaster@localhost
            WSGIDaemonProcess liberiaprojects user=www-data group=www-data threads=5
            WSGIScriptAlias / /var/www/liberiaprojects/liberiaprojects.wsgi

            <Directory /var/wwww/liberiaprojects>
                    WSGIProcessGroup liberiaprojects
                    WSGIApplicationGroup %{GLOBAL}
                    Order deny,allow
                    Allow from all
            </Directory>

            #LogLevel info ssl:warn

            ErrorLog ${APACHE_LOG_DIR}/error.log
            CustomLog ${APACHE_LOG_DIR}/access.log combined
    </VirtualHost>
   ```

4. Give the Apache user group `www-data` group ownership of the database, and the database's parent folder:
   ```
   chown :www-data /path-to-liberia-projects/db/merged.db
   chown :www-data /path-to-liberia-projects/db/
   ```

5. Enable the new site and restart Apache, e.g. if it's called `liberiaprojects.conf`:
   ```
   a2ensite liberiaprojects
   systemctl reload apache2
   ```

## Setup `certbot` to allow for HTTPS

1. Setup certbot following [these instructions](https://certbot.eff.org/).
2. Opt to redirect all requests to HTTPS when prompted.
