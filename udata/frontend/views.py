# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import request, redirect, abort, g, url_for
from flask.views import MethodView

from udata import search
from udata.auth import login_required
from udata.frontend import render
from udata.utils import multi_to_dict


class Templated(object):
    template_name = None

    def get_context(self):
        return {}

    def render(self, context=None, **kwargs):
        context = context or self.get_context()
        context.update(kwargs)
        return render(self.template_name, **context)


class BaseView(MethodView):
    require = None

    def dispatch_request(self, *args, **kwargs):
        self.kwargs = kwargs
        self.set_identity(g.identity)
        if not self.can(*args, **kwargs):
            return abort(403)
        return super(BaseView, self).dispatch_request(*args, **kwargs)

    def can(self, *args, **kwargs):
        '''Overwrite this method to implement custom contextual permissions'''
        return not self.require or self.require().can()

    def set_identity(self, *args, **kwargs):
        pass


class ListView(Templated, BaseView):
    '''
    Render a Queryset as a list.
    '''
    model = None
    context_name = 'objects'

    def get_queryset(self):
        return self.model.objects

    def get_context(self):
        context = super(ListView, self).get_context()
        context[self.context_name] = self.get_queryset()
        return context

    def get(self, **kwargs):
        return self.render()


class SearchView(Templated, BaseView):
    '''
    Render a Queryset as a list.
    '''
    model = None
    context_name = 'objects'
    search_adapter = None
    search_endpoint = None

    def get_queryset(self):
        return search.query(self.search_adapter, **multi_to_dict(request.args))

    def get_context(self):
        context = super(SearchView, self).get_context()
        context[self.context_name] = self.get_queryset()
        if self.search_endpoint:
            context['search_url'] = url_for(self.search_endpoint)
        return context

    def get(self, **kwargs):
        return self.render()


class SingleObject(object):
    model = None
    object_name = 'object'
    object = None

    def get_object(self):
        if not self.object:
            if self.object_name in self.kwargs:
                self.object = self.kwargs[self.object_name]
            if 'slug' in self.kwargs:
                self.object = self.model.objects.get_or_404(slug=self.kwargs.get('slug'))
            elif 'id' in self.kwargs:
                self.object = self.model.objects.get_or_404(self.kwargs.get('id'))
        return self.object

    def get_context(self):
        context = super(SingleObject, self).get_context()
        context[self.object_name] = self.get_object()
        return context


class DetailView(SingleObject, Templated, BaseView):
    '''
    Render a single object.
    '''
    def get(self, **kwargs):
        return self.render()


class FormView(Templated, BaseView):
    form = None

    def get_context(self):
        context = super(FormView, self).get_context()
        context['form'] = self.form(request.form)
        return context

    def get(self, **kwargs):
        return self.render()

    def on_form_valid(self, form):
        return redirect(self.get_success_url())

    def on_form_error(self, form):
        return self.render(form=form)

    def get_success_url(self, obj):
        raise obj.get_absolute_url()

    def post(self, **kwargs):
        context = self.get_context()
        form = context['form']

        if form.validate():
            return self.on_form_valid(form)

        return self.on_form_error(form)


class CreateView(FormView):
    decorators = [login_required]

    def on_form_valid(self, form):
        obj = self.model()
        form.populate_obj(obj)
        obj.save()
        self.object = obj
        return redirect(self.get_success_url())

    def get_success_url(self):
        return self.object.get_absolute_url()


class EditView(SingleObject, FormView):
    decorators = [login_required]

    def get_context(self):
        context = super(EditView, self).get_context()
        context['form'] = self.form(request.form, self.object)
        return context

    def on_form_valid(self, form):
        form.populate_obj(self.object)
        self.object.save()
        return redirect(self.get_success_url())

    def get_success_url(self):
        return self.object.get_absolute_url()
