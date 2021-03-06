# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import UUID

from flask import request, abort, url_for

from udata.api import api, ModelAPI, ModelListAPI, SingleObjectAPI, API, marshal, fields
from udata.core.organization.api import OrganizationField
from udata.utils import get_by

from .models import Dataset, Resource
from .forms import DatasetForm, ResourceForm
from .search import DatasetSearch

resource_fields = {
    'id': fields.String,
    'title': fields.String,
    'description': fields.String,
    'url': fields.String,
    'checksum': fields.String,
    'created_at': fields.DateTime,
}


dataset_fields = {
    'id': fields.String,
    'title': fields.String,
    'slug': fields.String,
    'description': fields.String,
    'created_at': fields.DateTime,
    'last_modified': fields.DateTime,
    'featured': fields.Boolean,
    'tags': fields.List(fields.String),
    'resources': fields.Nested(resource_fields),
    'community_resources': fields.Nested(resource_fields),
    'frequency': fields.String,
    'extras': fields.Raw,
    'metrics': fields.Raw,
    'organization': OrganizationField,
}


class DatasetField(fields.Raw):
    def format(self, dataset):
        return {
            'id': str(dataset.id),
            'uri': url_for('api.dataset', id=dataset.id, _external=True),
            'page': url_for('datasets.show', dataset=dataset, _external=True),
        }


class DatasetListAPI(ModelListAPI):
    model = Dataset
    form = DatasetForm
    fields = dataset_fields
    search_adapter = DatasetSearch


class DatasetAPI(ModelAPI):
    model = Dataset
    form = DatasetForm
    fields = dataset_fields


class DatasetFeaturedAPI(SingleObjectAPI, API):
    model = Dataset

    def post(self, slug):
        dataset = self.get_or_404(slug=slug)
        dataset.featured = True
        dataset.save()
        return marshal(dataset, dataset_fields)

    def delete(self, slug):
        dataset = self.get_or_404(slug=slug)
        dataset.featured = False
        dataset.save()
        return marshal(dataset, dataset_fields)


class ResourcesAPI(API):
    def post(self, slug):
        dataset = Dataset.objects.get_or_404(slug=slug)
        form = ResourceForm(request.form, csrf_enabled=False)
        if not form.validate():
            return {'errors': form.errors}, 400
        resource = Resource()
        form.populate_obj(resource)
        dataset.resources.append(resource)
        dataset.save()
        return marshal(resource, resource_fields), 201


class ResourceAPI(API):
    def put(self, slug, rid):
        dataset = Dataset.objects.get_or_404(slug=slug)
        resource = get_by(dataset.resources, 'id', UUID(rid))
        if not resource:
            abort(404)
        form = ResourceForm(request.form, instance=resource, csrf_enabled=False)
        if not form.validate():
            return {'errors': form.errors}, 400
        form.populate_obj(resource)
        dataset.save()
        return marshal(resource, resource_fields)

    def delete(self, slug, rid):
        dataset = Dataset.objects.get_or_404(slug=slug)
        resource = get_by(dataset.resources, 'id', UUID(rid))
        if not resource:
            abort(404)
        dataset.resources.remove(resource)
        dataset.save()
        return '', 204


api.add_resource(DatasetListAPI, '/datasets/', endpoint=b'api.datasets')
api.add_resource(DatasetAPI, '/datasets/<string:slug>', endpoint=b'api.dataset')
api.add_resource(DatasetFeaturedAPI, '/datasets/<string:slug>/featured', endpoint=b'api.dataset_featured')
api.add_resource(ResourcesAPI, '/datasets/<string:slug>/resources', endpoint=b'api.resources')
api.add_resource(ResourceAPI, '/datasets/<string:slug>/resources/<string:rid>', endpoint=b'api.resource')
