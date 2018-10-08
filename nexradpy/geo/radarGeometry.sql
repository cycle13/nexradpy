------------------------------------------------------------------------
--  Connected to nyc_transit_db querying table nyct2010 (nyc tracts)  --
------------------------------------------------------------------------

-- Get NYC bounding box in EPSG 2263
SELECT ST_AsText(ST_Envelope(ST_Transform(ST_Union(nyct2010.geom), 2263))) 
	FROM nyct2010;

-- Get radar point in EPSG 2263
SELECT ST_AsText(
	ST_Transform(ST_SetSRID(ST_MakePoint(-72.868308,40.863255),4326),2263)
	);

-- Get Azimuth from radar to upper right of bb in degrees
SELECT degrees(ST_Azimuth(
	ST_Point(1297269.35727894,255806.712114764),
	ST_Point(1067382.50842285,272844.294006292)
	));

-- Get Azimuth from radar to lower right of bb in degrees
SELECT degrees(ST_Azimuth(
	ST_Point(1297269.35727894,255806.712114764),
	ST_Point(1067382.50842285,120121.881254272)
	));

-- Get distance from radar to bb's right edge 
-- NOTE: ST_Distance defaults to min dist
SELECT ST_Distance(
	ST_GeomFromText('point(1297269.35727894 255806.712114764)',2263),
	ST_GeomFromText('linestring(1067382.50842285 120121.881254272,1067382.50842285 272844.294006292)',2263)
	);

-- Get distance (max) from radar to bb's left edge
SELECT ST_MaxDistance(
	ST_GeomFromText('point(1297269.35727894 255806.712114764)',2263),
	ST_GeomFromText('linestring(913175.109008789 120121.881254272,913175.109008789 272844.294006292)',2263)
	);