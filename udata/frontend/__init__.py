# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from importlib import import_module
from os.path import join, dirname, isdir, exists
from pkg_resources import resource_stream

from flask import current_app
from webassets.filter import get_filter

from flask.ext.assets import Environment, YAMLLoader, Bundle
from flask.ext.gravatar import Gravatar
from flask.ext.markdown import Markdown
from flask.ext.themes2 import Themes, Theme, render_theme_template, get_theme, packaged_themes_loader
from flask.ext.wtf.csrf import CsrfProtect

from udata.app import ROOT_DIR
from udata.core import MODULES
from udata.i18n import I18nBlueprint


log = logging.getLogger(__name__)

assets = Environment()
csrf = CsrfProtect()
themes = Themes()
gravatar = Gravatar(size=100,
                    rating='g',
                    default='retro',
                    force_default=True,
                    use_ssl=False,
                    base_url=None)
front = I18nBlueprint('front', __name__)


class ThemeYAMLLoader(YAMLLoader):
    '''
    YAML theme assets loaders

    Loads assets from theme assets.yaml file if present
    and handle path rewriting
    '''
    def __init__(self, theme):
        super(ThemeYAMLLoader, self).__init__(join(theme.path, 'assets.yaml'))
        self.theme = theme

    def _yield_bundle_contents(self, data):
        for content in super(ThemeYAMLLoader, self)._yield_bundle_contents(data):
            if isinstance(content, basestring):
                theme_content = join(self.theme.static_path, content)
                if exists(theme_content):
                    yield theme_content
                    continue
            yield content

    def _dependencies_from_theme(self, dependencies):
        if not dependencies:
            return None

        deps = []
        for dependency in dependencies:
            deps.append(dependency)
            deps.append(join(self.theme.static_path, dependency))
        return deps

    def _get_bundle(self, data):
        """Return a bundle initialised by the given dict."""
        filters = data.get('filters', None)
        if filters and 'cssrewrite' in filters:
            filters = [self.cssrewrite() if f == 'cssrewrite' else f for f in filters.split(',')]

        kwargs = dict(
            filters=filters,
            output=data.get('output', None),
            debug=data.get('debug', None),
            extra=data.get('extra', {}),
            depends=self._dependencies_from_theme(data.get('depends', None))
        )
        return Bundle(*list(self._yield_bundle_contents(data)), **kwargs)

    def cssrewrite(self):
        return get_filter('cssrewrite', replace={
            # self.theme.path: '',
            self.theme.static_path: '_themes/{0}'.format(self.theme.name),
        })


def plugin_theme_loader(app):
    for plugin in app.config['PLUGINS']:
        module = import_module('udata.ext.{0}'.format(plugin))
        path = join(dirname(module.__file__), 'theme')
        if isdir(path):
            yield Theme(path)


def render(template, **context):
    '''
    Render a template with uData frontend specifics

        * Theme
    '''
    theme = current_app.config['THEME']
    return render_theme_template(get_theme(theme), template, **context)


def _load_views(app, module):
    try:
        views = import_module(module)
        blueprint = getattr(views, 'blueprint', None)
        if blueprint:
            app.register_blueprint(blueprint)
    except ImportError as e:
        print e
        pass
    except Exception as e:
        log.error('Error importing %s views: %s', module, e)


def init_app(app):
    assets.init_app(app)
    gravatar.init_app(app)
    themes.init_themes(app, app_identifier='udata', loaders=[packaged_themes_loader, plugin_theme_loader])

    Markdown(app)
    csrf.init_app(app)

    app.config['STATIC_DIRS'] = app.config.get('STATIC_DIRS', []) + [
        ('fonts', join(ROOT_DIR, 'static', 'bower', 'bootstrap', 'dist', 'fonts')),
        ('fonts', join(ROOT_DIR, 'static', 'bower', 'font-awesome', 'fonts')),
    ]

    app.config['LESS_PATHS'] = app.config.get('LESS_PATHS', []) + [
        'less',
        'bower/bootstrap/less',
        'bower/font-awesome/less',
        'bower/bootstrap-markdown/less',
        'bower/selectize/dist/less',
    ]

    # Hook into flask security to user themed auth pages
    app.config.setdefault('SECURITY_RENDER', 'udata.frontend:render')

    # Load bundle from yaml file
    assets.from_yaml(resource_stream(__name__, '../static/assets.yaml'))
    # if app.debug:
    app.config['REQUIREJS_CONFIG'] = join(ROOT_DIR, 'static', 'js', 'app.build.js')
    if app.config['ASSETS_DEBUG']:
        app.config['REQUIREJS_OPTIMIZE'] = False
        assets['require-js'].contents += ('js/config.js', 'js/debug.js')

    from . import explore, home, helpers, catalog, error_handlers

    # Load all core modules frontend
    for module in MODULES:
        _load_views(app, 'udata.core.{0}.views'.format(module))

    # Load all plugins views and blueprints
    for plugin in app.config['PLUGINS']:
        module = 'udata.ext.{0}.views'.format(plugin)
        _load_views(app, module)

    # Load all theme assets
    theme = app.theme_manager.themes[app.config['THEME']]
    app.config['STATIC_DIRS'].append(('', theme.static_path))
    if isdir(join(theme.static_path, 'less')):
        app.config['LESS_PATHS'].append(join(theme.static_path, 'less'))
    if exists(join(theme.path, 'assets.yaml')):
        bundles = ThemeYAMLLoader(theme).load_bundles()
        for name in bundles:
            assets.register(name, bundles[name])

    # Load front only views and helpers
    app.register_blueprint(front)

    # Load debug toolbar if enabled
    if app.config.get('DEBUG_TOOLBAR'):
        from flask.ext.debugtoolbar import DebugToolbarExtension
        DebugToolbarExtension(app)
