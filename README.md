![Contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)
[![License](https://img.shields.io/badge/license-MIT%20License-brightgreen.svg)](https://opensource.org/licenses/MIT)


# GerryPy v2
### Let the machines do the gerrymandering
GerryPy is a geospatial algorithm for building congressional districts.

GerryPy takes census tracts for the state of Colorado and builds the required number of congressional districts.  The algorithm attempts to make districts compact and close to the required population of 711,000.  Each algorithm attempt produces a different result.

# Website
gerrypy.herokuapp.com (not deployed anymore/yet)

# Major Components
GerryPy is built in Python and uses a [PostgresSQL](https://www.postgresql.org/)+[PostGIS](http://postgis.net/) database.

Backend: [Flask-SocketIO](https://github.com/miguelgrinberg/Flask-SocketIO)

Frontend was bootstrapped with [Create React App](https://github.com/facebookincubator/create-react-app).

GoogleMap React component from [google-map-react](https://github.com/istarkov/google-map-react).


# License
MIT License

# Team
[Ford Fowler](https://github.com/fordf)

[Avery Pratt](https://github.com/averyprett)

[Patrick Saunders](https://github.com/pasaunders)

[Jordan Schatzman](https://github.com/julienawilson)

[Julien Wilson](https://github.com/julienawilson)
