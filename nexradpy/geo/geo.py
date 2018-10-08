import shapely.geometry
import geopandas as gpd
import fiona

class BoundingBox(object):
    def __init__(self, ul=(0,0), ur=(0,0), lr=(0,0), ll=(0,0)):
        self.ul = ul
        self.ur = ur
        self.lr = lr
        self.ll = ll

    def coord_transform(self, proj_string):
        pass
