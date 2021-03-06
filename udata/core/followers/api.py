# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime

from flask import abort

from flask.ext.security import current_user

from udata.api import api, API, marshal, fields
from udata.models import FollowOrg, FollowDataset, Follow, FollowReuse


class FollowAPI(API):
    '''
    Base Follow Model API.
    '''
    model = Follow

    def post(self, id):
        if not current_user.is_authenticated():
            abort(401)
        follow, created = self.model.objects.get_or_create(follower=current_user.id, following=id)
        count = self.model.objects.followers(id).count()

        return {'followers': count}, 201 if created else 200

    def delete(self, id):
        if not current_user.is_authenticated():
            abort(401)
        follow = self.model.objects.get_or_404(follower=current_user.id, following=id, until=None)
        follow.until = datetime.now()
        follow.save()
        count = self.model.objects.followers(id).count()
        return {'followers': count}, 200


class FollowUserAPI(FollowAPI):
    model = Follow


class FollowOrgAPI(FollowAPI):
    model = FollowOrg


class FollowDatasetAPI(FollowAPI):
    model = FollowDataset


class FollowReuseAPI(FollowAPI):
    model = FollowReuse


api.add_resource(FollowUserAPI, '/follow/user/<id>/', endpoint=b'api.follow_user')
api.add_resource(FollowOrgAPI, '/follow/organization/<id>/', endpoint=b'api.follow_organization')
api.add_resource(FollowDatasetAPI, '/follow/dataset/<id>/', endpoint=b'api.follow_dataset')
api.add_resource(FollowReuseAPI, '/follow/reuse/<id>/', endpoint=b'api.follow_reuse')
