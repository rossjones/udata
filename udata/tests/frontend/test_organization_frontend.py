# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import url_for

from udata.models import Organization, Member

from . import FrontTestCase
from ..factories import OrganizationFactory


class OrganizationBlueprintTest(FrontTestCase):
    def test_render_list(self):
        '''It should render the organization list page'''
        with self.autoindex():
            organizations = [OrganizationFactory() for i in range(3)]

        response = self.get(url_for('organizations.list'))

        self.assert200(response)
        rendered_organizations = self.get_context_variable('organizations')
        self.assertEqual(len(rendered_organizations), len(organizations))

    def test_render_list_empty(self):
        '''It should render the organization list page event if empty'''
        response = self.get(url_for('organizations.list'))
        self.assert200(response)

    def test_render_create(self):
        '''It should render the organization create form'''
        response = self.get(url_for('organizations.new'))
        self.assert200(response)

    def test_create(self):
        '''It should create a organization and redirect to organization page'''
        data = OrganizationFactory.attributes()
        self.login()
        response = self.post(url_for('organizations.new'), data)

        organization = Organization.objects.first()
        self.assertRedirects(response, organization.get_absolute_url())

    def test_render_display(self):
        '''It should render the organization page'''
        organization = OrganizationFactory()
        response = self.get(url_for('organizations.show', org=organization))
        self.assert200(response)

    def test_render_edit(self):
        '''It should render the organization edit form'''
        user = self.login()
        organization = OrganizationFactory(members=[Member(user=user, role='admin')])

        response = self.get(url_for('organizations.edit', org=organization))
        self.assert200(response)

    def test_edit(self):
        '''It should handle edit form submit and redirect on organization page'''
        user = self.login()

        organization = OrganizationFactory(members=[Member(user=user, role='admin')])
        data = organization.to_dict()
        del data['members']
        data['description'] = 'new description'
        response = self.post(url_for('organizations.edit', org=organization), data)

        organization.reload()
        self.assertRedirects(response, organization.get_absolute_url())
        self.assertEqual(organization.description, 'new description')

    def test_render_edit_members(self):
        '''It should render the organization member edit page'''
        user = self.login()
        organization = OrganizationFactory(members=[Member(user=user, role='admin')])
        response = self.get(url_for('organizations.edit_members', org=organization))
        self.assert200(response)

    def test_render_edit_teams(self):
        '''It should render the organization team edit form'''
        user = self.login()
        organization = OrganizationFactory(members=[Member(user=user, role='admin')])

        response = self.get(url_for('organizations.edit_teams', org=organization))
        self.assert200(response)

    def test_not_found(self):
        '''It should render the organization page'''
        response = self.get(url_for('organizations.show', org='not-found'))
        self.assert404(response)

