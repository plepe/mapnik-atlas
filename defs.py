import sys

try:
    import mapnik
except:
    try:
        import mapnik2 as mapnik
    except:
        print('Error: Need to have Mapnik installed, with python bindings enabled.')
        sys.exit()

# Set up projections
# spherical mercator (most common target map projection of osm data imported with osm2pgsql)
merc = mapnik.Projection('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over')

# long/lat in degrees, aka ESPG:4326 and "WGS 84" 
longlat = mapnik.Projection('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
# can also be constructed as:
#longlat = mapnik.Projection('+init=epsg:4326')

# Constants
pixel_size = 0.28 # 1 Pixel = 0.28 mm
pdf_unit = 2.83464567 # 1 mm = 2.83464567 pt
