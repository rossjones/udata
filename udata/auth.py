# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from flask import render_template, current_app
from flask.ext.principal import Permission as BasePermission, identity_loaded, RoleNeed
from flask.ext.security import Security, current_user, login_required
from werkzeug.utils import import_string


log = logging.getLogger(__name__)


class UDataSecurity(Security):
    def render_template(self, *args, **kwargs):
        try:
            render = import_string(current_app.config.get('SECURITY_RENDER'))
        except:
            render = render_template
        return render(*args, **kwargs)


security = UDataSecurity()


class Permission(BasePermission):
    def __init__(self, *needs):
        '''Let administrator bypass all permissions'''
        super(Permission, self).__init__(RoleNeed('admin'), *needs)


def init_app(app):
    from udata.models import datastore
    security.init_app(app, datastore)
