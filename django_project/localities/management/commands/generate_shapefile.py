# coding=utf-8
from django.core.management.base import BaseCommand
import os
import shapefile
import zipfile
from django.conf import settings
from localities.models import Domain, Specification, Country
from localities.utils import get_heathsites_master

__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '15/07/16'
__license__ = "GPL"
__copyright__ = 'kartoza.com'


directory_cache = settings.CLUSTER_CACHE_DIR + "/shapefiles"
directory_media = settings.MEDIA_ROOT + "/shapefiles"
fields = [u'uuid', u'upstream', u'source', u'name', u'version', u'date_modified', u'completeness', u'source_url',
          u'raw-source']


def zipdir(path, ziph):
    # ziph is zipfile handle
    abs_src = os.path.abspath(path)
    for root, dirs, files in os.walk(path):
        for file in files:
            absname = os.path.abspath(os.path.join(root, file))
            arcname = absname[len(abs_src) + 1:]
            ziph.write(absname, arcname)


# funtion to generate a .prj file
def getWKT_PRJ(epsg_code):
    import urllib
    wkt = urllib.urlopen("http://spatialreference.org/ref/epsg/{0}/prettywkt/".format(epsg_code))
    remove_spaces = wkt.read().replace(" ", "")
    output = remove_spaces.replace("\n", "")
    return output


def get_cache(shp_filename):
    dir_cache = directory_cache + "/" + shp_filename
    if not os.path.exists(dir_cache):
        os.makedirs(dir_cache)
    return dir_cache


def create_shapefile(shp_filename):
    shp = None
    shp = shapefile.Writer(shapefile.POINT)
    for field in fields:
        shp.field(str(field), 'C', 100)
    return shp


def write_shapefile(shp_filename):
    # write world cache
    dir_cache = get_cache(shp_filename)
    filename = os.path.join(dir_cache, shp_filename)
    if not os.path.exists(dir_cache):
        os.makedirs(dir_cache)
    return filename


def write_shapefile_extras(shp_filename):
    dir_cache = get_cache(shp_filename)
    # create .cpg
    file = open(dir_cache + "/" + shp_filename + ".cpg", 'w+')
    file.write("UTF-8")
    file.close()

    # create .prj
    prj = open(dir_cache + "/" + shp_filename + ".prj", "w")
    epsg = getWKT_PRJ("4326")
    prj.write(epsg)
    prj.close()


def zip_shapefile(shp_filename):
    # zip this output
    print "zipping"
    dir_cache = get_cache(shp_filename)
    if not os.path.exists(directory_media):
        os.makedirs(directory_media)
    filename = os.path.join(directory_media, shp_filename + "_shapefile.zip")
    zipf = zipfile.ZipFile(filename, 'w', allowZip64=True)
    zipdir(dir_cache, zipf)
    zipf.close()
    print "done"


def insert_to_shapefile(healthsites, shp_filename):
    try:
        shp = create_shapefile()
        filename = write_shapefile(shp_filename)

        # get from healthsites
        total = healthsites.count()
        print "generating shape object for " + shp_filename
        if total > 0:
            now = 1
            for healthsite in healthsites:
                values = []
                dict = healthsite.repr_dict(clean=True)
                for field in fields:
                    value = ""
                    if field in dict:
                        value = dict[field]
                    elif field in dict['values']:
                        value = dict['values'][field]
                    try:
                        value = str(value.encode('utf8'))
                    except AttributeError:
                        pass
                    values.append(value)
                print "converted %d / %d" % (now, total)
                shp.point(dict['geom'][0], dict['geom'][1])
                shp.record(*values)
                now += 1
            shp.save(filename)

            write_shapefile_extras(shp_filename)
            zip_shapefile(shp_filename)
    except:
        pass


class Command(BaseCommand):
    help = 'generate shapefile for data in bulk'

    def handle(self, *args, **options):
        domain = Domain.objects.get(name="Health")
        specifications = Specification.objects.filter(domain=domain)

        for specification in specifications:
            fields.append(specification.attribute.key)

        countries = Country.objects.all().order_by('name')
        for country in countries:
            polygons = country.polygon_geometry
            # query for each of ATTRIBUTE
            healthsites = get_heathsites_master().in_polygon(
                polygons)
            insert_to_shapefile(healthsites, country.name)  # generate shapefiles for country

        insert_to_shapefile(get_heathsites_master(), 'facilities')  # generate shapefiles for all country
