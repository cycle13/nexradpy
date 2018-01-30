## NEXRADpy
#### _Work in progress!_

For a project currently in the works, see [Subway-Substitution](https://github.com/clambygrum/substitution), I need very granular precipitation data for New  York City. While NOAA provides hourly precip totals for a [large network of weather stations](https://www.ncdc.noaa.gov/data-access/land-based-station-data) across the U.S., there are only three stations around NYC. However, NOAA also provides access to [archived radar data](https://www.ncdc.noaa.gov/data-access/radar-data), which offers sub-hourly precip estimates at a very granular spatial level. It took some time to familiarize myself with accessing and cleaning the radar files, so I hope this repo may someday prove useful for others looking to use this interesting data source. The end product I have in mind is a small scraper that collects radar readings given two dates, converts them from a radial to a table format, and deposits them into a SQL database. The img below&mdash;showing radar gates, the level at which reflectivity and thus precip is measured&mdash;shows the level of detail provided by the radar files. Level II gates are in blue, and Level III gates are in red.

![Radar Level Comparison](https://github.com/clambygrum/NEXRADpy/blob/master/l2_l3_comparison.PNG)

#### Status
I'm currently scraping the radar files directly from NOAA's site, though may soon switch over to [using S3](https://eng.climate.com/2015/10/27/how-to-read-and-display-nexrad-on-aws-using-python/). To read and clean the radar files, I'm using [Pyart](https://arm-doe.github.io/pyart/dev/index.html), which is fairly complete and well documented. I'm storing the formatted precip data in a (PostgreSQL)[https://www.enterprisedb.com/downloads/postgres-postgresql-downloads] database for use with PostGIS, but the `db.py` script could be easily ported over to SQLite.  

#### Set up
Here's how I set up the project on OS Sierra and Ubuntu 16.04 using Python2.7:

```bash
git clone https://github.com/clambygrum/nexradpy.git
virtualenv <your virtualenv>
pip install -r requirements.txt
```

Next install pyart:

```bash
touch <yourvirtualenv>/lib/python2.7/site-packages/matplotlib/matplotlibrc
echo "backend:TkAgg" > <yourvirtualenv>/lib/python2.7/site-packages/matplotlib/matplotlibrc
git clone https://github.com/ARM-DOE/pyart
python pyart/setup.py build_ext -i
touch <your virtualenv>/lib/python2.7/site-packages/pyart.pth
echo "/Users/<your username>/.../nexradpy/pyart" > <yourvirtualenv>/lib/python2.7/site-packages/pyart.pth
```
