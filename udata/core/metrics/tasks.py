# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import date, timedelta

from celery.utils.log import get_task_logger

from udata.tasks import celery

from .models import Metrics

log = get_task_logger(__name__)


@celery.task
def update_metric(metric):
    log.debug('Update metric %s for %s', metric.name, metric.target)
    metric.compute()


@celery.task
def archive_metric(metric):
    log.debug('Store metric %s for %s', metric.name, metric.target)
    metric.store()


@celery.task(name='bump-metrics')
def bump_metrics():
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(1)).isoformat()
    log.info('Bumping metrics from to %s to %s', yesterday, today)
    script = '''
    function() {
        var processed = 0;
        db[collection].find(query).forEach(function(doc) {
            delete doc._id;
            doc.date = options.today;
            db[collection].save(doc);
            processed += 1;
        });
        return processed;
    }
    '''
    processed = Metrics.objects(date=yesterday).exec_js(script, today=today)
    log.info('Processed %s document(s)', processed)


@celery.task
def update_metrics_for(obj):
    from udata.core.metrics import Metric
    metrics = Metric.get_for(obj.__class__)
    for metric in metrics.values():
        metric(obj).compute()


@celery.task
def update_site_metrics():
    from udata.core.metrics import Metric
    metrics = Metric.get_for('site')
    for metric in metrics.values():
        metric.update()
