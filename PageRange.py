from defs import *
from Page import *

class PageRange:
    def __init__(self, config):
        self.data = []
        self.config = config
        print config

        # Initialize Mapnik (with an arbitrary size)
        self.map = mapnik.Map(10000, 10000)
        mapnik.load_map(self.map, config['map_file'])

        # ensure the target map projection is mercator
        self.map.srs = merc.params()

        # set up projection
        self.map.transform = mapnik.ProjTransform(longlat, merc)

        # Mapnik: set up bbox on correct projection and scale
        self.bbox = mapnik.Box2d(*self.config['bounds'])
        self.bbox = self.map.transform.forward(self.bbox)
        self.map.zoom_to_box(self.bbox)

        # Force scale denominator
        scale_change = self.config['scale'] / self.map.scale_denominator()
        # Resize image size
        self.map.resize(int(10000 / scale_change + 1), int(10000 / scale_change + 1))
        self.map.zoom(self.config['scale'] / self.map.scale_denominator())

        # total map size without overlap
        self.map_size = (self.map.width, self.map.height)
