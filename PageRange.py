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

        # size of map per page
        map_size_per_page = page_map_size(self.config)
        print self.map_size, map_size_per_page

        # center bbox on pages
        count_pages = self.map_size[0] / map_size_per_page[0] + 1,\
                      self.map_size[1] / map_size_per_page[1] + 1
        map_offset = (count_pages[0] * map_size_per_page[0] - self.map_size[0]) / 2,\
                     (count_pages[1] * map_size_per_page[1] - self.map_size[1]) / 2

        # calculate upper left boundary for all pages
        page_boundaries = range(-map_offset[0], self.map_size[0], map_size_per_page[0]),\
                          range(-map_offset[1], self.map_size[1], map_size_per_page[1])

        # coord ... a mapnik ViewTransform to project positions in the local
        # coordinate system
        self.coord = mapnik.ViewTransform(self.map.width, self.map.height, self.map.envelope())

        # update bbox to page_boundaries
        self.bbox = mapnik.Box2d(
            self.coord.backward(mapnik.Coord(
                page_boundaries[0][0],
                page_boundaries[1][0])),
            self.coord.backward(mapnik.Coord(
                page_boundaries[0][-1] + map_size_per_page[0],
                page_boundaries[1][-1] + map_size_per_page[1]))
        )

        # Create Pages
        self.pages = []
        for y, y_boundary in enumerate(page_boundaries[1]):
            for x, x_boundary in enumerate(page_boundaries[0]):
                page_config = self.config
                page_config['page_map_size'] = map_size_per_page
                page_config['page_number'] = len(self.pages) + 1

                self.pages.append(Page(self, (x_boundary, y_boundary), page_config))

    def embed_to_final_pdf(self, final_pdf):
        for page in self.pages:
            page.embed_to_final_pdf(final_pdf)
