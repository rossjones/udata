# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from bson import ObjectId

from werkzeug.routing import BaseConverter

from udata import models


class LanguagePrefixConverter(BaseConverter):
    regex = r'\w{2}'


class ListConverter(BaseConverter):
    def to_python(self, value):
        return value.split(',')

    def to_url(self, values):
        return ','.join(super(ListConverter, self).to_url(value) for value in values)


class ModelConverter(BaseConverter):
    '''
    A base class helper for model helper.

    Allow to give model or slug or ObjectId as parameter to url_for().

    When serializing to url using a model parameter
    it use the slug field if possible and then fallback on the id field.

    When serializing to python, ir try in the following order:

    * fetch by slug
    * fetch by id
    * raise 404
    '''

    model = None

    def to_python(self, value):
        obj = self.model.objects(slug=value).first()
        return obj or self.model.objects.get_or_404(id=value)

    def to_url(self, obj):
        if isinstance(obj, (basestring, ObjectId)):
            return obj
        elif getattr(obj, 'slug', None):
            return obj.slug
        elif getattr(obj, 'id', None):
            return str(obj.id)
        else:
            raise ValueError('Unable to serialize "%s" to url' % obj)




class DatasetConverter(ModelConverter):
    model = models.Dataset


class OrganizationConverter(ModelConverter):
    model = models.Organization


class ReuseConverter(ModelConverter):
    model = models.Reuse


class UserConverter(ModelConverter):
    model = models.User


class TopicConverter(ModelConverter):
    model = models.Topic


class PostConverter(ModelConverter):
    model = models.Post


def init_app(app):
    app.url_map.converters['lang'] = LanguagePrefixConverter
    app.url_map.converters['list'] = ListConverter
    app.url_map.converters['dataset'] = DatasetConverter
    app.url_map.converters['org'] = OrganizationConverter
    app.url_map.converters['reuse'] = ReuseConverter
    app.url_map.converters['user'] = UserConverter
    app.url_map.converters['topic'] = TopicConverter
    app.url_map.converters['post'] = PostConverter
