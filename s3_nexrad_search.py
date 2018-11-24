#!/usr/bin/env python3

import datetime
import math
import multiprocessing
import os
import time

import boto
import matplotlib
import numpy
import trianglesolver
import utm

from nexrad_metadata import *


# From https://en.wikipedia.org/wiki/NEXRAD
# "The deployment of the dual polarization capability (Build 12) to NEXRAD sites began in 2010 and was completed by the summer of 2013."
# Would love to have specifics on deployment for this, for now just assume August 2013
DUAL_POLE_DEPLOYMENT_COMPLETION=datetime.datetime(month=8, year=2013, day=1)

# From https://en.wikipedia.org/wiki/NEXRAD
# The first installation of a WSR-88D for operational use in everyday forecasting was in Sterling, Virginia on June 12, 1992. The last system deployed as part of this installation campaign was installed in North Webster, Indiana on August 30, 1997. In 2011
WSR88D_DEPLOYMENT_COMPLETION=datetime.datetime(month=8, year=1997, day=30)

# https://aws.amazon.com/public-datasets/nexrad/
# "The full historical archive from NOAA from June 1991 to present is available"
S3_NEXRAD_START_DATE=datetime.datetime(month=6, year=1991, day=1)

DATASET_START_DATE=DUAL_POLE_DEPLOYMENT_COMPLETION

# beam distance from: https://www.roc.noaa.gov/WSR88D/Engineering/NEXRADTechInfo.aspx
WSR88D_BEAM_DISTANCE=230

# Lowest angle of WSR88D
WSR88D_LOW_ANGLE=math.radians(0.5)

# Highest angle of WSR88D
WSR88D_HIGH_ANGLE=math.radians(19.5)

# Earth radius in km
EARTH_RADIUS_KM=6371.0

# Coefficent for the distance of the radius of a radar station that would be relevant
RELEVANT_DISTANCE_COEFFICENT=0.5


STATION_IDS = [station["station_id"] for station in STATION_INDEX]
STATION_LATLONS = [(station["latitude"], station["longitude"]) for station in STATION_INDEX]


class S3NEXRADHelper:

    def __init__(self, verbose=True, threads=1):
        """Initalizes variables for this class

        verbose: Boolean of if we should print non-error information
        threads: The amount of threads to use for downloading from S3
        """
        self.s3conn = boto.connect_s3(anon=True)
        self.bucket = self.s3conn.get_bucket("noaa-nexrad-level2")
        self.verbose = verbose
        self.thread_max = threads
        self.threads = []
        self.thread_count = 0

    def findNEXRADKeysByTimeAndDomain(self, start_datetime, end_datetime, maxlat, maxlon, minlat, minlon, height):
        """Get list of keys to nexrad files on s3 from a time range and lat/lon domain.

        start_datetime: start of time range in a datetime.datetime object
        end_datetime: end of time range in a datetime.datetime object
        maxlat: maximum latitude of domain
        maxlon: maximum longitude of domain
        minlat: minimum lattitude of domain
        minlon: minimum longitude of domain
        height: height above sealevel in meters for domain

        returns: List of keys in nexrad s3 bucket corespopnding to the parameters
        """
        station_list = self.getStationsFromDomain(maxlat, maxlon, minlat, minlon, height)
        if not station_list:
            print("No stations found for specified domain")
            return

        if self.verbose:
           print(f"Found stations: {','.join(station_list)} for domain {maxlat}, {maxlon} to {minlat}, {minlon}")
        files = self.searchNEXRADS3(start_datetime, end_datetime, station_list)

        if self.verbose:
            print("Found files for time range: %s to %s" % (
                    start_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                    end_datetime.strftime("%Y-%m-%d %H:%M:%S")))
            for filekey in files:
                print(filekey)

        return files

    def downloadNEXRADFiles(self, download_dir, s3keys):
        """Download files from S3 NEXRAD bucket

        download_dir: The directory to download the file to
        s3keys: list of keys in the nexrad bucket to download

        returns: list of downloaded file paths
        """
        if not os.path.exists(download_dir):
            print("Unable to find download directory, skipping downloads")
            return
        file_paths = []
        for key in s3keys:
            file_path = os.path.join(download_dir, key.split('/')[-1])
            file_paths.append(file_path)

            self._addToThreadPool(_downloadFile, (key, file_path, self.verbose))
            self._waitForThreadPool()

        self._waitForThreadPool(thread_max=0)

        return file_paths

    def getStationsFromWRFDomain(self, dx, dy, e_sn, e_we, ref_lat, ref_lon, height):
        """Searches station list for radar stations that would be relevant
        to the domain provided.

        WARNING: This may not be accurate for very large domains

        dx, dy, e_sn, e_we, ref_lat, ref_lon are equivalent to the namelist.wps variables
        from the WRF Preprocessing System (WPS)

        height: height above sealevel in meters for domain (not from WPS namelist)

        returns: list of station ids ex. ['KIND', 'KLVX']
        """
        center_east, center_north, zone_number, zone_letter = utm.from_latlon(ref_lat, ref_lon)
        maxlat, maxlon = utm.to_latlon(center_east + (e_we/2.0*dx), center_north + (e_sn/2.0*dy),
                                       zone_number, zone_letter, strict=False)
        minlat, minlon = utm.to_latlon(center_east - (e_we/2.0*dx), center_north - (e_sn/2.0*dy),
                                       zone_number, zone_letter, strict=False)

        station_list = self.getStationsFromDomain(maxlat, maxlon, minlat, minlon, height)
        return station_list
            
    def getStationsFromDomain(self, maxlat, maxlon, minlat, minlon, height):
        """Searches station list for radar stations that would be relevant
        to the domain provided.

        maxlat: maximum latitude of domain
        maxlon: maximum longitude of domain
        minlat: minimum lattitude of domain
        minlon: minimum longitude of domain
        height: height above sealevel in meters for domain

        returns: list of station ids ex. ['KIND', 'KLVX']
        """

        # http://geokov.com/education/utm.aspx
        # easting values increase towards east
        # max lon is east side
        # max lat is north 

        maxeast_domain, maxnorth_domain, max_zone_number, max_zone_letter = utm.from_latlon(maxlat, maxlon)

        mineast_domain, minnorth_domain, min_zone_number, min_zone_letter = utm.from_latlon(minlat, minlon)

        relevant_stations = []
        possibly_relevant_stations = []
        for i, latlon in enumerate(STATION_LATLONS): 
            lat, lon = latlon

            station_radius = self._calculateRadiusAtHeight(height, 
                    STATION_INDEX[i]['station_elevation'])
            if station_radius is None:
                continue

            relevant_radius = RELEVANT_DISTANCE_COEFFICENT*station_radius

            maxeast = maxeast_domain + relevant_radius
            maxnorth = maxnorth_domain + relevant_radius
            domain_maxlat, domain_maxlon = utm.to_latlon(maxeast, maxnorth, max_zone_number,
                max_zone_letter, strict=False)

            mineast = mineast_domain - relevant_radius
            minnorth = minnorth_domain - relevant_radius
            domain_minlat, domain_minlon = utm.to_latlon(mineast, minnorth, min_zone_number,
                    min_zone_letter, strict=False)

            # Vertical band of relevant domain bounded by user-given domain
            if ((lat <= domain_maxlat and lat >= domain_minlat) and
                    (lon <= maxlon and lon >= minlon)):
                relevant_stations.append(STATION_INDEX[i]['station_id'])

            # Horizontal band of relevant domain bounded by user-given domain
            elif ((lat <= maxlat and lat >= minlat) and
                    (lon <= domain_maxlon and lon >= domain_minlon)):
                relevant_stations.append(STATION_INDEX[i]['station_id'])

            # north east corner of relevant domain
            elif ((lat <= domain_maxlat and lat >= maxlat) and 
                    (lon <= domain_maxlon and lon >= maxlon) and
                    _isStationInDomainCorner(maxlat, maxlon,
                        STATION_INDEX[i]['latitude'], 
                        STATION_INDEX[i]['longitude'],
                        relevant_radius)):

                relevant_stations.append(STATION_INDEX[i]['station_id'])

            # south east corner of relevant domain
            elif ((lat <= domain_minlat and lat >= minlat) and
                    (lon <= domain_maxlon and lon >= maxlon) and
                    _isStationInDomainCorner(minlat, maxlon,
                        STATION_INDEX[i]['latitude'], 
                        STATION_INDEX[i]['longitude'],
                        relevant_radius)):

                relevant_stations.append(STATION_INDEX[i]['station_id'])

            # south west corner of relevant domain
            elif ((lat <= domain_minlat and lat >= minlat) and
                    (lon <= domain_minlon and lon >= minlon) and
                    _isStationInDomainCorner(minlat, minlon,
                        STATION_INDEX[i]['latitude'], 
                        STATION_INDEX[i]['longitude'],
                        relevant_radius)):

                relevant_stations.append(STATION_INDEX[i]['station_id'])

            # north west corner of relevant domain
            elif ((lat <= domain_maxlat and lat >= maxlat) and
                    (lon <= domain_minlon and lon >= minlon) and
                    _isStationInDomainCorner(maxlat, minlon,
                        STATION_INDEX[i]['latitude'], 
                        STATION_INDEX[i]['longitude'],
                        relevant_radius)):

                relevant_stations.append(STATION_INDEX[i]['station_id'])

        return relevant_stations

    def searchNEXRADS3(self, start_datetime, end_datetime, station_list):
        """Find available files from a date range and a station list

        start_datetime: start of time range in a datetime.datetime object
        end_datetime: end of time range in a datetime.datetime object
        station_list: list of station ids as strings ex. ["KIND", "KVBX"]

        returns: list of keys in the nexrad s3 bucket within the time range for the specified stations
        """
        start = start_datetime
        if start_datetime < DATASET_START_DATE:
            if verbose:
                print("Start time is before the dataset start date, will use dataset start time instead")
            start = DATASET_START_DATE

        end = end_datetime
        if end_datetime > datetime.datetime.now():
            if verbose:
                print("End time is in the future, will use today as end time")
            end = datetime.datetime.now()


        dir_key_list = []
        for station_id in station_list:
            if station_id not in STATION_IDS:
                print("Station %s not found, skipping") % station_id
                continue
            current_date = start.replace(hour=0)
            while current_date < end:
                dir_key_list.append("%d/%02d/%02d/%s" % (current_date.year, current_date.month,
                    current_date.day, station_id))
                current_date = current_date + datetime.timedelta(days=1)

        start_dir = "%d/%02d/%02d/" % (start.year, start.month ,start.day)
        end_dir = "%d/%02d/%02d/" % (end.year, end.month, end.day)
        files_list = []

        # 2015/05/06/KSGF/KSGF20150506_224351_V06.gz
        # drop everything except the time the time
        before_time_index = 20
        after_time_index = 35
        for dir_key in dir_key_list:
            for file in self.bucket.list("%s/" % dir_key, "/"):
                file_name = file.name 

                if not file_name.endswith('gz'):
                    continue

                if file_name.startswith(start_dir):
                    file_datetime = datetime.datetime.strptime(
                            file_name[before_time_index:after_time_index],
                            "%Y%m%d_%H%M%S")
                    if file_datetime <= start:
                        continue

                if file_name.startswith(end_dir):
                    file_datetime = datetime.datetime.strptime(
                            file_name[before_time_index:after_time_index],
                            "%Y%m%d_%H%M%S")
                    if file_datetime >= end:
                        continue

                files_list.append(file_name)
        return files_list

    def _calculateRadiusAtHeight(self, height, station_elevation):
        """This function calculates the radius at the specified height above sealevel.
        This function takes into consideration both the height of the radar station 
        and the ange of the radar beam. This is a rough estimate and does not take
        into account refraction or beam width. It also assumes a spherical earth.

        height: height above sea level in meters
        station_elevation: radar site height above sea level in meters

        returns: ground distance radius of radar in meters or None if height is not available
        """
        # anything bigger can throw errors and this is outside of the operational specs of
        # the current and future VCPs - https://en.wikipedia.org/wiki/NEXRAD
        if height > 90000: return None

        # There should probably be a lower bound here but I haven't been able to find it yet
        #if height < ?: return None

        # highest point above sea level
        if station_elevation > 6267: return None

        # radar must be lower than specified height
        if station_elevation >= height: return None

        # based on figure 2 of http://www.radartutorial.eu/01.basics/Calculation%20of%20height.en.html
        # TODO: include refraction in the calculation
        height_km = height/1000.0 - station_elevation/1000

        localized_radius = EARTH_RADIUS_KM + station_elevation/1000

        # Create an triange on a circle (2d earth), the three side are the length of
        # localized radius connected, the radar beam and the height + localized_radius 
        # connecting to the beam end and the earth center

        height_of_beam_end = localized_radius + height_km

        # lowest angle at the radar site
        # 90 degrees + radar beam angle
        radar_site_angle = math.radians(90) + WSR88D_LOW_ANGLE
        #######
        # Calculate max ground distance at 0.5 degrees for WSR88D_MAX_RADIUS constant
        #a, b, beam_distance, beam_point_angle, B, earth_center_angle = trianglesolver.solve(
        #        a = EARTH_RADIUS_KM, c = WSR88D_BEAM_DISTANCE, B = radar_site_angle, ssa_flag='acute')
        #print earth_center_angle * EARTH_RADIUS_KM
        # WSR88D_MAX_RADIUS=229819.074224
        #######

        a, b, beam_distance, beam_point_angle, B, earth_center_angle = trianglesolver.solve(
                a = localized_radius, b = height_of_beam_end, B = radar_site_angle, ssa_flag='acute')

        # if our beam_distance is too high then check the highest beam
        if (beam_distance > WSR88D_BEAM_DISTANCE):
        
            # angle at the radar site
            # 90 degrees + radar beam angle
            radar_site_angle = math.radians(90) + WSR88D_HIGH_ANGLE

            a, b, beam_distance, beam_point_angle, B, earth_center_angle = trianglesolver.solve(
                    a = localized_radius, b = height_of_beam_end, B = radar_site_angle, ssa_flag='acute')

            # if we still don't have a reasonable beam distance, return None
            if (beam_distance > WSR88D_BEAM_DISTANCE):
                return None

            # If beam distance is fine, solve for this height at max beam_distance so we can 
            # get the appropriate ground distance for the radar's radius at this height
            a, b, c, A, radar_site_angle, earth_center_angle = trianglesolver.solve(
                    a = localized_radius, b = height_of_beam_end, c = WSR88D_BEAM_DISTANCE)

        #print math.degrees(radar_site_angle)

        # the ground distance is the circular segment with angle earth_center_angle and r of localized_radius
        # this assumes a smooth earth (and a shperical cow)
        ground_distance_km = earth_center_angle * localized_radius

        ground_distance = ground_distance_km * 1000

        return ground_distance

    def _isStationInDomainCorner(self, corner_lat, corner_lon, station_lat, station_lon,
            radius):
        """Take the relevant domain distance as the radius for a circle around the point
        of the corner of the user-provided domain. Create this shape and check to see if the 
        station lies within it.

        corner_lat: lattitude of a corner point of the user-provided domain
        corner_lon: longitude of the same corner point of the user-provided domain
        station_lat: latitude of the station to be checked
        station_lon: longitude of the station to be checked
        radius: distance from the corner point to check 
            Highly suggested: the radius is the same distance to calculate the relevant domain


        return: Boolean of if the station is within the domain
        """
        easting_points, northing_points, zone_number, zone_letter =_createGeographicCircle(
                corner_lat, corner_lon, radius)
        shape = []
        for i in range(0, len(easting_points)):
            shape.append([easting_points[i], northing_points[i]])

        relevant_domain = matplotlib.path.Path(numpy_array(shape))

        station_easting, station_northing, station_zone_number, station_zone_letter = utm.from_latlon(
            lat, lon, force_zone_number=zone_number)

        return relevant_domain.contains_point(station_easting, station_northing)

    def _createGeographicCircle(self, lat, lon, radius):
        """Create points on circumfrence of circle centered at lat,lon.
        
        lat: lattiude of center of circle
        lon: longitude of center of circle
        radius: radius of circle in meters

        returns: tuple of (easting_points, northing_points, zone_number, zone_letter)
        """
        center_easting, center_northing, zone_number, zone_letter = utm.from_latlon(lat, lon)

        points_in_shape = 45

        easting_points = []
        northing_points = []

        theta = (math.pi*2) / points_in_shape
        for i in range(1, points_in_shape + 1):
            angle = theta * i

            point_easting = radius * math.cos(angle) + center_easting
            point_northing  = radius * math.sin(angle) + center_northing

        easting_points.append(point_easting)
        northing_points.append(point_northing)

        return (easting_points, northing_points, zone_number, zone_letter)

    def _addToThreadPool(self, function, args):
        proc = multiprocessing.Process(target=function, args=args)
        proc.start()
        self.threads.append(proc)
        self.thread_count += 1

    def _waitForThreadPool(self, thread_max=None):
        if thread_max is None:
            thread_limit = self.thread_max - 1
        else:
            thread_limit = thread_max
        count = 0
        while len(self.threads) > thread_limit:
            time.sleep(.1)
            if count > len(self.threads) - 1:
                count = 0
            if self.threads[count].exitcode is not None:
                self.threads[count].join(1)
                self.threads.pop(count)
            else: 
                count += 1


def _downloadFile(key, file_path, verbose):
    s3conn = boto.connect_s3(anon=True)
    bucket = s3conn.get_bucket("noaa-nexrad-level2")
    keyobj = bucket.get_key(key)
    if keyobj is None:
        if self.verbose: print("Unable to find file %s, skipping" % key)
        return

    dfile = open(file_path, 'wb')
    try:
        keyobj.get_file(dfile)
    finally:
        dfile.close()

    if verbose:
        print("%s downloaded" % file_path)


def main():
    ## EXAMPLE USAGE
    nexrad = S3NEXRADHelper(threads=20)
    s3keys = nexrad.findNEXRADKeysByTimeAndDomain(
            datetime.datetime(day=5, month=5, year=2015, hour=5),
            datetime.datetime(day=5, month=5, year=2015, hour=6), 
            40.901954, -73.632802, 40.460969, -74.363177, 20000)
    nexrad.downloadNEXRADFiles('data/raw', s3keys)

if __name__ == "__main__":
    main()
