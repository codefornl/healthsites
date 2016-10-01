import json
import dicttoxml

from django.views.generic import View
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponseRedirect

__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '10/06/16'
__license__ = "GPL"
__copyright__ = 'kartoza.com'


class ApiView(View):
    limit = 100
    formats = ['json', 'xml', 'geojson']
    format = 'json'

    def get(self, request, *args, **kwargs):
        if request.method == 'GET':
            if 'format' in request.GET:
                self.format = request.GET['format']
                if self.format not in self.formats:
                    self.format = 'json'

    def formating_response(self, response):
        if self.format == 'xml':
            output = dicttoxml.dicttoxml(response)
        elif self.format == 'geojson':
            output = json.dumps({"type": "FeatureCollection", "features": response}, cls=DjangoJSONEncoder)
        else:
            output = json.dumps(response, cls=DjangoJSONEncoder)
        output.replace("|", ",")
        return output


class Docs(View):
    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect('https://github.com/healthsites/healthsites/wiki/API')
