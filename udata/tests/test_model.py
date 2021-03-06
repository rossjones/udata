# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import uuid4
from datetime import date, datetime, timedelta

from mongoengine.errors import ValidationError

from udata.models import db
from udata.tests import TestCase, DBTestMixin


class UUIDTester(db.Document):
    uuid = db.AutoUUIDField()


class SlugTester(db.Document):
    title = db.StringField()
    slug = db.SlugField(populate_from='title')
    meta = {
        'allow_inheritance': True,
    }


class SlugUpdateTester(db.Document):
    title = db.StringField()
    slug = db.SlugField(populate_from='title', update=True)


class DateTester(db.Document):
    a_date = db.DateField()


class DateTesterWithDefault(db.Document):
    a_date = db.DateField(default=date.today)


class InheritedSlugTester(SlugTester):
    other = db.StringField()


class DatetimedTester(db.Datetimed, db.Document):
    name = db.StringField()


class AutoUUIDFieldTest(TestCase):
    def test_auto_populate(self):
        '''AutoUUIDField should populate itself if not set'''
        obj = UUIDTester()
        self.assertIsNotNone(obj.uuid)

    def test_do_not_overwrite(self):
        '''AutoUUIDField should not populate itself if a value is already set'''
        uuid = uuid4()
        obj = UUIDTester(uuid=uuid)
        self.assertEqual(obj.uuid, uuid)


class SlugFieldTest(DBTestMixin, TestCase):
    def test_populate(self):
        '''SlugField should populate itself on save if not set'''
        obj = SlugTester(title="A Title")
        self.assertIsNone(obj.slug)
        obj.save()
        self.assertEqual(obj.slug, 'a-title')

    def test_populate_next(self):
        '''SlugField should not keep other fields value'''
        SlugTester.objects.create(title="A Title")
        obj = SlugTester.objects.create(title="Another title")
        self.assertEqual(obj.slug, 'another-title')

    def test_no_populate(self):
        '''SlugField should not populate itself if a value is set'''
        obj = SlugTester(title='A Title', slug='a-slug')
        obj.save()
        self.assertEqual(obj.slug, 'a-slug')

    def test_populate_update(self):
        '''SlugField should populate itself on save and update if update=True'''
        obj = SlugUpdateTester(title="A Title")
        obj.save()
        self.assertEqual(obj.slug, 'a-title')
        obj.title = 'Title'
        obj.save()
        self.assertEqual(obj.slug, 'title')

    def test_no_populate_update(self):
        '''SlugField should not populate itself if update=True and a value is set'''
        obj = SlugUpdateTester(title="A Title")
        obj.save()
        self.assertEqual(obj.slug, 'a-title')
        obj.title = 'Title'
        obj.slug = 'other'
        obj.save()
        self.assertEqual(obj.slug, 'other')

    def test_unchanged(self):
        '''SlugField should not chnage on save if not needed'''
        obj = SlugTester(title="A Title")
        self.assertIsNone(obj.slug)
        obj.save()
        self.assertEqual(obj.slug, 'a-title')
        obj.save()
        self.assertEqual(obj.slug, 'a-title')

    def test_changed_no_update(self):
        '''SlugField should not update slug if update=False'''
        obj = SlugTester(title="A Title")
        obj.save()
        self.assertEqual(obj.slug, 'a-title')
        obj.title = 'Title'
        obj.save()
        self.assertEqual(obj.slug, 'a-title')

    def test_manually_set(self):
        '''SlugField can be manually set'''
        obj = SlugTester(title='A title', slug='a-slug')
        self.assertEqual(obj.slug, 'a-slug')
        obj.save()
        self.assertEqual(obj.slug, 'a-slug')

    def test_work_accross_inheritance(self):
        '''SlugField should ensure uniqueness accross inheritance'''
        obj = SlugTester.objects.create(title='title')
        inherited = InheritedSlugTester.objects.create(title='title')
        self.assertNotEqual(obj.slug, inherited.slug)


class DateFieldTest(DBTestMixin, TestCase):
    def test_none_if_empty_and_not_required(self):
        obj = DateTester()
        self.assertIsNone(obj.a_date)
        obj.save()
        obj.reload()
        self.assertIsNone(obj.a_date)

    def test_default(self):
        today = date.today()
        obj = DateTesterWithDefault()
        self.assertEqual(obj.a_date, today)
        obj.save()
        obj.reload()
        self.assertEqual(obj.a_date, today)

    def test_date(self):
        the_date = date(1984, 6, 6)
        obj = DateTester(a_date=the_date)
        self.assertEqual(obj.a_date, the_date)
        obj.save()
        obj.reload()
        self.assertEqual(obj.a_date, the_date)

    def test_not_valid(self):
        obj = DateTester(a_date='invalid')
        with self.assertRaises(ValidationError):
            obj.save()


class DatetimedTest(DBTestMixin, TestCase):
    def test_class(self):
        self.assertIsInstance(DatetimedTester.created_at, db.DateTimeField)
        self.assertIsInstance(DatetimedTester.last_modified, db.DateTimeField)

    def test_new_instance(self):
        now = datetime.now()
        datetimed = DatetimedTester()

        self.assertGreaterEqual(datetimed.created_at, now)
        self.assertLessEqual(datetimed.created_at, datetime.now())

        self.assertGreaterEqual(datetimed.last_modified, now)
        self.assertLessEqual(datetimed.last_modified, datetime.now())

    def test_save_new_instance(self):
        now = datetime.now()
        datetimed = DatetimedTester.objects.create()

        self.assertGreaterEqual(datetimed.created_at, now)
        self.assertLessEqual(datetimed.created_at, datetime.now())

        self.assertGreaterEqual(datetimed.last_modified, now)
        self.assertLessEqual(datetimed.last_modified, datetime.now())

    def test_save_last_modified_instance(self):
        now = datetime.now()
        earlier = now - timedelta(days=1)
        datetimed = DatetimedTester.objects.create(created_at=earlier, last_modified=earlier)

        datetimed.save()

        self.assertEqual(datetimed.created_at, earlier)

        self.assertGreaterEqual(datetimed.last_modified, now)
        self.assertLessEqual(datetimed.last_modified, datetime.now())
