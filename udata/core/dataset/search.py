# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from udata.models import Dataset, Organization, License
from udata.search import ModelSearchAdapter, i18n_analyzer
from udata.search.fields import Sort
from udata.search.fields import RangeFilter, DateRangeFilter, BoolFilter
from udata.search.fields import TermFacet, ModelTermFacet
from udata.search.fields import BoolBooster, FunctionBooster

__all__ = ('DatasetSearch', )


class DatasetSearch(ModelSearchAdapter):
    model = Dataset
    mapping = {
        'properties': {
            'title': {
                'type': 'string',
                'analyzer': i18n_analyzer,
                'fields': {
                    'raw': {'type': 'string', 'index': 'not_analyzed'}
                }
            },
            'description': {'type': 'string', 'analyzer': i18n_analyzer},
            'license': {'type': 'string', 'index': 'not_analyzed'},
            'frequency': {'type': 'string'},
            'organization': {'type': 'string'},
            'supplier': {'type': 'string'},
            'tags': {'type': 'string', 'index_name': 'tag', 'index': 'not_analyzed'},
            'tag_suggest': {
                'type': 'completion',
                'index_analyzer': 'simple',
                'search_analyzer': 'simple',
                'payloads': False,
            },
            'resources': {
                'type': 'object',
                'index_name': 'resource',
                'properties': {
                    'title': {'type': 'string'},
                    'description': {'type': 'string'},
                    'license': {'type': 'string'},
                }
            },
            'format_suggest': {
                'type': 'completion',
                'index_analyzer': 'simple',
                'search_analyzer': 'simple',
                'payloads': False,
            },
            'dataset_suggest': {
                'type': 'completion',
                'index_analyzer': 'simple',
                'search_analyzer': 'simple',
                'payloads': True,
            },
            'created': {'type': 'date', 'format': 'date_hour_minute_second'},
            'last_modified': {'type': 'date', 'format': 'date_hour_minute_second'},
            'nb_reuses': {'type': 'integer'},
            'featured': {'type': 'boolean'},
            'temporal_coverage_start': {'type': 'date', 'format': 'date'},
            'temporal_coverage_end': {'type': 'date', 'format': 'date'},
        }
    }
    fields = (
        'title^3',
        'description',
        'tags',
    )
    sorts = {
        'title': Sort('title.raw'),
        'created': Sort('created'),
        'last_modified': Sort('last_modified'),
        'reuses': Sort('nb_reuses'),
        'stars': Sort('nb_stars'),
    }
    facets = {
        'tag': TermFacet('tags'),
        'organization': ModelTermFacet('organization', Organization),
        'supplier': ModelTermFacet('supplier', Organization),
        'license': ModelTermFacet('license', License),
        'format': TermFacet('resources.format'),
    }
    filters = {
        'reuses': RangeFilter('nb_reuses'),
        'temporal_coverage': DateRangeFilter('temporal_coverage_start', 'temporal_coverage_end'),
        'featured': BoolFilter('featured'),
    }
    boosters = [
        BoolBooster('featured', 1.1),
        BoolBooster('from_public_service', 1.1),
        FunctionBooster('_score * (1 + sqrt(0.01 * doc["nb_reuses"].value))'),
    ]

    @classmethod
    def serialize(cls, dataset):
        image_url = dataset.organization.image_url if dataset.organization and dataset.organization.image_url else None
        document = {
            'title': dataset.title,
            'description': dataset.description,
            'license': dataset.license.id if dataset.license else None,
            'tags': dataset.tags,
            'tag_suggest': dataset.tags,
            'resources': [
                {
                    'title': r.title,
                    'description': r.description,
                    'format': r.format,
                }
                for r in dataset.resources],
            'format_suggest': [r.format.lower() for r in dataset.resources],
            'frequency': dataset.frequency,
            'organization': str(dataset.organization.id) if dataset.organization else None,
            'supplier': str(dataset.supplier.id) if dataset.supplier else None,
            'dataset_suggest': {
                'input': [dataset.title],
                'payload': {
                    'id': str(dataset.id),
                    'slug': dataset.slug,
                    'image_url': image_url,
                },
            },
            'created': dataset.created_at.strftime('%Y-%m-%dT%H:%M:%S'),
            'last_modified': dataset.last_modified.strftime('%Y-%m-%dT%H:%M:%S'),
            'nb_reuses': dataset.metrics.get('reuses', 0),
            'nb_stars': dataset.metrics.get('stars', 0),
            'featured': dataset.featured,
            'from_public_service': dataset.organization.public_service if dataset.organization else False,  # TODO: extract tis into plugin
        }
        if dataset.temporal_coverage and dataset.temporal_coverage.start and dataset.temporal_coverage.end:
            document.update({
                'temporal_coverage_start': dataset.temporal_coverage.start.isoformat(),
                'temporal_coverage_end': dataset.temporal_coverage.end.isoformat(),
            })
        return document
