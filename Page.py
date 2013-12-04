from defs import *
import PyPDF2 as PDF
from reportlab.pdfgen import canvas
import reportlab.lib.colors as colors

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

        self.overlap = self.config['overlap'] / pixel_size
        self.bbox_overlap = mapnik.Box2d(
            self.page_range.coord.backward(mapnik.Coord(
                self.offset[0] - self.overlap,
                self.offset[1] - self.overlap)),
            self.page_range.coord.backward(mapnik.Coord(
                self.offset[0] + self.config['page_map_size'][0] + self.overlap,
                self.offset[1] + self.config['page_map_size'][1] + self.overlap))
        )

        self.file_name = 'map-' + str(self.config['page_number']) + '.pdf'

    def render(self, final_pdf):
        # Important: select correct map region
        self.map.zoom_to_box(self.bbox_overlap)

        # Fix zoom
        self.map.zoom(self.config['scale'] / self.map.scale_denominator())

        # Make sure map is correctly sized
        self.map.resize(
            int(round(self.config['page_map_size'][0] + self.overlap * 2)),
            int(round(self.config['page_map_size'][1] + self.overlap * 2))
        )

        # Fix zoom
        self.map.zoom(self.config['scale'] / self.map.scale_denominator())

        # Finally render map
        mapnik.render_to_file(self.map, self.file_name)

        # page_background is an empty page with the final page size
        page_size_pdf = (
            self.config['page_size'][0] * pdf_unit,
            self.config['page_size'][1] * pdf_unit
        )
        print page_size_pdf

        print self.config
        map_size_pdf = (
            round(self.config['page_size'][0] - self.config['page_border'] * 2 + self.config['overlap'] * 2) * pdf_unit,
            round(self.config['page_size'][1] - self.config['page_border'] * 2 + self.config['overlap'] * 2) * pdf_unit
        )

        page_background = canvas.Canvas("tmp1.pdf", pagesize=page_size_pdf)
        page_background.showPage()
        page_background.save()

        # page map is the rendered map from above
        page_map = PDF.PdfFileReader(open(self.file_name, 'rb')).getPage(0)
        print 'pdf', map_size_pdf
        page_map.scaleTo(*map_size_pdf)

        page_final = PDF.PdfFileReader(open('tmp1.pdf', 'rb')).getPage(0)

        page_final.mergeTranslatedPage(page_map,
            (self.config['page_border'] - self.config['overlap']) * pdf_unit,
            (self.config['page_border'] - self.config['overlap']) * pdf_unit
        )

        page_overlay = canvas.Canvas("tmp2.pdf", pagesize=page_size_pdf)
        page_overlay.setFillColor(colors.white)
        if self.config['overlap'] < self.config['page_border']:
            page_overlay.rect(
                0, 0, \
                (self.config['page_border'] - self.config['overlap']) * pdf_unit, \
                page_size_pdf[1], \
                stroke=0, fill=1
            )
            page_overlay.rect(
                page_size_pdf[0] - (self.config['page_border'] - self.config['overlap']) * pdf_unit, \
                0, \
                page_size_pdf[0], \
                page_size_pdf[1], \
                stroke=0, fill=1
            )
            page_overlay.rect(
                0, 0, \
                page_size_pdf[0], \
                (self.config['page_border'] - self.config['overlap']) * pdf_unit, \
                stroke=0, fill=1
            )
            page_overlay.rect(
                0, \
                page_size_pdf[1] - (self.config['page_border'] - self.config['overlap']) * pdf_unit, \
                page_size_pdf[0], \
                page_size_pdf[1], \
                stroke=0, fill=1
            )

        page_overlay.setFillColor(colors.black)
        page_overlay.drawString(10, 10, str(self.config['page_number']))

        page_overlay.showPage()
        page_overlay.save()

        page_overlay = PDF.PdfFileReader(open('tmp2.pdf', 'rb')).getPage(0)
        page_final.mergePage(page_overlay)

        final_pdf.addPage(page_final)

    def page_bounds_as_csv(self):
        geom = self.map.transform.backward(self.bbox)
        return ['"POLYGON((' + repr(geom.minx) + ' ' + repr(geom.miny) + ',' + \
                ' ' + repr(geom.maxx) + ' ' + repr(geom.miny) + ',' + \
                ' ' + repr(geom.maxx) + ' ' + repr(geom.maxy) + ',' + \
                ' ' + repr(geom.minx) + ' ' + repr(geom.maxy) + ',' + \
                ' ' + repr(geom.minx) + ' ' + repr(geom.miny) + '))"' + \
                ';' + str(self.config['page_number'])]
