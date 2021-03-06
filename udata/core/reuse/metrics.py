# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from udata.core.metrics import Metric
from udata.i18n import lazy_gettext as _
from udata.models import Reuse, User


__all__ = ('DatasetsMetric', 'StarsMetric')


class DatasetsMetric(Metric):
    model = Reuse
    name = 'datasets'
    display_name = _('Datasets')

    def get_value(self):
        return len(self.target.datasets)


DatasetsMetric.connect(Reuse.on_create, Reuse.on_update)


class StarsMetric(Metric):
    model = Reuse
    name = 'stars'
    display_name = _('Stars')

    def get_value(self):
        return User.objects(starred_reuses=self.target).count()


StarsMetric.connect(Reuse.on_star, Reuse.on_unstar)
