from defs import *
import PyPDF2 as PDF
from reportlab.pdfgen import canvas
import reportlab.lib.colors as colors
import xhtml2pdf.pisa as pisa
import cStringIO

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

    def crop_map(self, page_final):
        page_overlay_file = cStringIO.StringIO()
        page_overlay = canvas.Canvas(page_overlay_file, pagesize=self.page_size_pdf)
        page_overlay.setFillColor(colors.white)
        if self.config['overlap'] < self.config['page_border']:
            page_overlay.rect(
                0, 0, \
                (self.config['page_border'] - self.config['overlap']) * pdf_unit, \
                self.page_size_pdf[1], \
                stroke=0, fill=1
            )
            page_overlay.rect(
                self.page_size_pdf[0] - (self.config['page_border'] - self.config['overlap']) * pdf_unit, \
                0, \
                self.page_size_pdf[0], \
                self.page_size_pdf[1], \
                stroke=0, fill=1
            )
            page_overlay.rect(
                0, 0, \
                self.page_size_pdf[0], \
                (self.config['page_border'] - self.config['overlap']) * pdf_unit, \
                stroke=0, fill=1
            )
            page_overlay.rect(
                0, \
                self.page_size_pdf[1] - (self.config['page_border'] - self.config['overlap']) * pdf_unit, \
                self.page_size_pdf[0], \
                self.page_size_pdf[1], \
                stroke=0, fill=1
            )

        page_overlay.showPage()
        page_overlay.save()

        page_overlay = PDF.PdfFileReader(page_overlay_file).getPage(0)
        page_final.mergePage(page_overlay)
        page_overlay_file.close()

    def overlay_map(self, page_final):
# Create HTML-page as overlay
        page_overlay_file = cStringIO.StringIO()
        content = file('template-page.html', 'r').read()
        content = content.format(
            page_number=str(self.config['page_number'])
        )
        pdf = pisa.CreatePDF(cStringIO.StringIO(content), page_overlay_file)

        page_overlay = PDF.PdfFileReader(page_overlay_file).getPage(0)
        page_final.mergePage(page_overlay)
        page_overlay_file.close()

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
        self.page_size_pdf = (
            self.config['page_size'][0] * pdf_unit,
            self.config['page_size'][1] * pdf_unit
        )

        print self.config
        map_size_pdf = (
            round(self.config['page_size'][0] - self.config['page_border'] * 2 + self.config['overlap'] * 2) * pdf_unit,
            round(self.config['page_size'][1] - self.config['page_border'] * 2 + self.config['overlap'] * 2) * pdf_unit
        )

        page_background_file = cStringIO.StringIO()
        page_background = canvas.Canvas(page_background_file, pagesize=self.page_size_pdf)
        page_background.showPage()
        page_background.save()

        # page map is the rendered map from above
        page_map = PDF.PdfFileReader(open(self.file_name, 'rb')).getPage(0)
        print 'pdf', map_size_pdf
        page_map.scaleTo(*map_size_pdf)

        page_final = PDF.PdfFileReader(page_background_file).getPage(0)

        page_final.mergeTranslatedPage(page_map,
            (self.config['page_border'] - self.config['overlap']) * pdf_unit,
            (self.config['page_border'] - self.config['overlap']) * pdf_unit
        )

        self.crop_map(page_final)
        page_background_file.close()

        self.overlay_map(page_final)

        final_pdf.addPage(page_final)

    def page_bounds_as_csv(self):
        geom = self.map.transform.backward(self.bbox)
        return ['"POLYGON((' + repr(geom.minx) + ' ' + repr(geom.miny) + ',' + \
                ' ' + repr(geom.maxx) + ' ' + repr(geom.miny) + ',' + \
                ' ' + repr(geom.maxx) + ' ' + repr(geom.maxy) + ',' + \
                ' ' + repr(geom.minx) + ' ' + repr(geom.maxy) + ',' + \
                ' ' + repr(geom.minx) + ' ' + repr(geom.miny) + '))"' + \
                ';' + str(self.config['page_number'])]
