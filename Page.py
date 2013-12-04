from defs import *

def page_map_size(config):
    page_map_size_mm = config['page_size'][0] - config['page_border'] * 2,\
                       config['page_size'][1] - config['page_border'] * 2
    page_map_size = int(round(page_map_size_mm[0] / pixel_size)), \
                    int(round(page_map_size_mm[1] / pixel_size))
    return page_map_size

class Page:
    def __init__(self, page_range, offset, page_config):
        self.data = []
        self.page_range = page_range
        self.map = self.page_range.map
        self.config = page_config
        self.offset = offset
        print self.config['page_number'], self.offset
        self.bbox = mapnik.Box2d(
            self.page_range.coord.backward(mapnik.Coord(
                self.offset[0],
                self.offset[1])),
            self.page_range.coord.backward(mapnik.Coord(
                self.offset[0] + self.config['page_map_size'][0],
                self.offset[1] + self.config['page_map_size'][1]))
        )
        print self.bbox

        overlap = self.config['overlap'] / pixel_size
        self.bbox_overlap = mapnik.Box2d(
            self.page_range.coord.backward(mapnik.Coord(
                self.offset[0] - overlap,
                self.offset[1] - overlap)),
            self.page_range.coord.backward(mapnik.Coord(
                self.offset[0] + self.config['page_map_size'][0] + overlap,
                self.offset[1] + self.config['page_map_size'][1] + overlap))
        )

        self.map.resize(
            int(round(self.config['page_map_size'][0] + overlap * 2)),
            int(round(self.config['page_map_size'][1] + overlap * 2))
        )

        self.map.zoom_to_box(self.bbox_overlap)

        # Fix zoom
        self.map.zoom(self.config['scale'] / self.map.scale_denominator())

        mapnik.render_to_file(self.map, 'map-' + str(self.config['page_number']) + '.pdf')
