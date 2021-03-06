# Copyright (c) 2013 - Rackspace Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import datetime
import decimal
import json
import unittest
import uuid
import multiprocessing

import kombu.common
import kombu.entity
import kombu.pools
import mox

from stacktach import datetime_to_decimal as dt
from stacktach import models
from utils import INSTANCE_ID_1
from utils import RAX_OPTIONS_1
from utils import RAX_OPTIONS_2
from utils import OS_DISTRO_1
from utils import OS_DISTRO_2
from utils import OS_ARCH_1
from utils import OS_ARCH_2
from utils import OS_VERSION_1
from utils import OS_VERSION_2
from utils import TENANT_ID_1
from utils import TENANT_ID_2
from utils import INSTANCE_TYPE_ID_1
from verifier import dbverifier
from verifier import AmbiguousResults
from verifier import FieldMismatch
from verifier import NotFound
from verifier import VerificationException


class VerifierTestCase(unittest.TestCase):
    def setUp(self):
        self.mox = mox.Mox()
        self.mox.StubOutWithMock(models, 'RawData', use_mock_anything=True)
        models.RawData.objects = self.mox.CreateMockAnything()
        self.mox.StubOutWithMock(models, 'Deployment', use_mock_anything=True)
        models.Deployment.objects = self.mox.CreateMockAnything()
        self.mox.StubOutWithMock(models, 'Lifecycle', use_mock_anything=True)
        models.Lifecycle.objects = self.mox.CreateMockAnything()
        self.mox.StubOutWithMock(models, 'Timing', use_mock_anything=True)
        models.Timing.objects = self.mox.CreateMockAnything()
        self.mox.StubOutWithMock(models, 'RequestTracker',
                                 use_mock_anything=True)
        models.RequestTracker.objects = self.mox.CreateMockAnything()
        self.mox.StubOutWithMock(models, 'InstanceUsage',
                                 use_mock_anything=True)
        models.InstanceUsage.objects = self.mox.CreateMockAnything()
        self.mox.StubOutWithMock(models, 'InstanceDeletes',
                                 use_mock_anything=True)
        models.InstanceDeletes.objects = self.mox.CreateMockAnything()
        self.mox.StubOutWithMock(models, 'InstanceReconcile',
                                 use_mock_anything=True)
        models.InstanceReconcile.objects = self.mox.CreateMockAnything()
        self.mox.StubOutWithMock(models, 'InstanceExists',
                                 use_mock_anything=True)
        models.InstanceExists.objects = self.mox.CreateMockAnything()
        self.mox.StubOutWithMock(models, 'JsonReport', use_mock_anything=True)
        models.JsonReport.objects = self.mox.CreateMockAnything()
        self._setup_verifier()

    def _setup_verifier(self):
        self.config = {
            "tick_time": 30,
            "settle_time": 5,
            "settle_units": "minutes",
            "pool_size": 2,
            "enable_notifications": False,
        }
        self.pool = self.mox.CreateMockAnything()
        self.verifier = dbverifier.Verifier(self.config, pool=self.pool)

        self.config_notif = {
            "tick_time": 30,
            "settle_time": 5,
            "settle_units": "minutes",
            "pool_size": 2,
            "enable_notifications": True,
            "rabbit": {
                "durable_queue": False,
                "host": "10.0.0.1",
                "port": 5672,
                "userid": "rabbit",
                "password": "rabbit",
                "virtual_host": "/",
                "exchange_name": "stacktach",
            }
        }
        self.pool_notif = self.mox.CreateMockAnything()
        self.verifier_notif = dbverifier.Verifier(self.config_notif,
                                                  pool=self.pool_notif)

    def tearDown(self):
        self.mox.UnsetStubs()
        self.verifier = None
        self.pool = None
        self.verifier_notif = None
        self.pool_notif = None

    def test_verify_for_launch(self):
        exist = self.mox.CreateMockAnything()
        exist.launched_at = decimal.Decimal('1.1')
        exist.instance_type_id = INSTANCE_TYPE_ID_1
        exist.tenant = TENANT_ID_1

        exist.usage = self.mox.CreateMockAnything()
        exist.usage.launched_at = decimal.Decimal('1.1')
        exist.usage.instance_type_id = INSTANCE_TYPE_ID_1
        exist.usage.tenant = TENANT_ID_1
        self.mox.ReplayAll()

        dbverifier._verify_for_launch(exist)

        self.mox.VerifyAll()

    def test_verify_for_launch_launched_at_in_range(self):
        exist = self.mox.CreateMockAnything()
        exist.usage = self.mox.CreateMockAnything()
        exist.launched_at = decimal.Decimal('1.0')
        exist.instance_type_id = 2
        exist.usage.launched_at = decimal.Decimal('1.4')
        exist.usage.instance_type_id = 2
        self.mox.ReplayAll()

        result = dbverifier._verify_for_launch(exist)
        self.assertIsNone(result)

        self.mox.VerifyAll()

    def test_verify_for_launch_launched_at_missmatch(self):
        exist = self.mox.CreateMockAnything()
        exist.usage = self.mox.CreateMockAnything()
        exist.launched_at = decimal.Decimal('1.1')
        exist.instance_type_id = 2
        exist.usage.launched_at = decimal.Decimal('2.1')
        exist.usage.instance_type_id = 2
        self.mox.ReplayAll()

        try:
            dbverifier._verify_for_launch(exist)
            self.fail()
        except FieldMismatch, fm:
            self.assertEqual(fm.field_name, 'launched_at')
            self.assertEqual(fm.expected, decimal.Decimal('1.1'))
            self.assertEqual(fm.actual, decimal.Decimal('2.1'))

        self.mox.VerifyAll()

    def test_verify_for_launch_instance_type_id_missmatch(self):
        exist = self.mox.CreateMockAnything()
        exist.usage = self.mox.CreateMockAnything()
        exist.launched_at = decimal.Decimal('1.1')
        exist.instance_type_id = 2
        exist.usage.launched_at = decimal.Decimal('1.1')
        exist.usage.instance_type_id = 3
        self.mox.ReplayAll()

        try:
            dbverifier._verify_for_launch(exist)
            self.fail()
        except FieldMismatch, fm:
            self.assertEqual(fm.field_name, 'instance_type_id')
            self.assertEqual(fm.expected, 2)
            self.assertEqual(fm.actual, 3)

        self.mox.VerifyAll()

    def test_verify_for_launch_tenant_id_mismatch(self):
        exist = self.mox.CreateMockAnything()
        exist.tenant = TENANT_ID_1

        exist.usage = self.mox.CreateMockAnything()
        exist.usage.tenant = TENANT_ID_2
        self.mox.ReplayAll()

        with self.assertRaises(FieldMismatch) as cm:
            dbverifier._verify_for_launch(exist)
        exception = cm.exception

        self.assertEqual(exception.field_name, 'tenant')
        self.assertEqual(exception.expected, TENANT_ID_1)
        self.assertEqual(exception.actual, TENANT_ID_2)

        self.mox.VerifyAll()

    def test_verify_for_launch_rax_options_mismatch(self):
        exist = self.mox.CreateMockAnything()
        exist.rax_options = RAX_OPTIONS_1

        exist.usage = self.mox.CreateMockAnything()
        exist.usage.rax_options = RAX_OPTIONS_2
        self.mox.ReplayAll()

        with self.assertRaises(FieldMismatch) as cm:
            dbverifier._verify_for_launch(exist)
        exception = cm.exception

        self.assertEqual(exception.field_name, 'rax_options')
        self.assertEqual(exception.expected, RAX_OPTIONS_1)
        self.assertEqual(exception.actual, RAX_OPTIONS_2)

        self.mox.VerifyAll()

    def test_verify_for_launch_os_distro_mismatch(self):
        exist = self.mox.CreateMockAnything()
        exist.os_distro = OS_DISTRO_1

        exist.usage = self.mox.CreateMockAnything()
        exist.usage.os_distro = OS_DISTRO_2
        self.mox.ReplayAll()

        with self.assertRaises(FieldMismatch) as cm:
            dbverifier._verify_for_launch(exist)
        exception = cm.exception

        self.assertEqual(exception.field_name, 'os_distro')
        self.assertEqual(exception.expected, OS_DISTRO_1)
        self.assertEqual(exception.actual, OS_DISTRO_2)

        self.mox.VerifyAll()

    def test_verify_for_launch_os_architecture_mismatch(self):
        exist = self.mox.CreateMockAnything()
        exist.os_architecture = OS_ARCH_1

        exist.usage = self.mox.CreateMockAnything()
        exist.usage.os_architecture = OS_ARCH_2
        self.mox.ReplayAll()

        with self.assertRaises(FieldMismatch) as cm:
            dbverifier._verify_for_launch(exist)
        exception = cm.exception

        self.assertEqual(exception.field_name, 'os_architecture')
        self.assertEqual(exception.expected, OS_ARCH_1)
        self.assertEqual(exception.actual, OS_ARCH_2)

        self.mox.VerifyAll()

    def test_verify_for_launch_os_version_mismatch(self):
        exist = self.mox.CreateMockAnything()
        exist.os_version = OS_VERSION_1

        exist.usage = self.mox.CreateMockAnything()
        exist.usage.os_version = OS_VERSION_2
        self.mox.ReplayAll()

        with self.assertRaises(FieldMismatch) as cm:
            dbverifier._verify_for_launch(exist)
        exception = cm.exception

        self.assertEqual(exception.field_name, 'os_version')
        self.assertEqual(exception.expected, OS_VERSION_1)
        self.assertEqual(exception.actual, OS_VERSION_2)

        self.mox.VerifyAll()

    def test_verify_for_launch_late_usage(self):
        exist = self.mox.CreateMockAnything()
        exist.usage = None
        exist.instance = INSTANCE_ID_1
        exist.launched_at = decimal.Decimal('1.1')
        exist.instance_type_id = 2
        results = self.mox.CreateMockAnything()
        models.InstanceUsage.objects.filter(instance=INSTANCE_ID_1)\
                                    .AndReturn(results)
        results.count().AndReturn(1)
        filters = {
            'instance': INSTANCE_ID_1,
            'launched_at__gte': decimal.Decimal('1.0'),
            'launched_at__lte': decimal.Decimal('1.999999')
        }
        models.InstanceUsage.objects.filter(**filters).AndReturn(results)
        results.count().AndReturn(1)
        usage = self.mox.CreateMockAnything()
        results.__getitem__(0).AndReturn(usage)
        usage.launched_at = decimal.Decimal('1.1')
        usage.instance_type_id = 2
        self.mox.ReplayAll()

        dbverifier._verify_for_launch(exist)
        self.mox.VerifyAll()

    def test_verify_for_launch_no_usage(self):
        exist = self.mox.CreateMockAnything()
        exist.usage = None
        exist.instance = INSTANCE_ID_1
        exist.launched_at = decimal.Decimal('1.1')
        exist.instance_type_id = 2
        results = self.mox.CreateMockAnything()
        models.InstanceUsage.objects.filter(instance=INSTANCE_ID_1) \
            .AndReturn(results)
        results.count().AndReturn(0)
        self.mox.ReplayAll()

        try:
            dbverifier._verify_for_launch(exist)
            self.fail()
        except NotFound, nf:
            self.assertEqual(nf.object_type, 'InstanceUsage')
            self.assertEqual(nf.search_params, {'instance': INSTANCE_ID_1})

        self.mox.VerifyAll()

    def test_verify_for_launch_late_ambiguous_usage(self):
        exist = self.mox.CreateMockAnything()
        exist.usage = None
        exist.instance = INSTANCE_ID_1
        exist.launched_at = decimal.Decimal('1.1')
        exist.instance_type_id = 2
        results = self.mox.CreateMockAnything()
        models.InstanceUsage.objects.filter(instance=INSTANCE_ID_1) \
            .AndReturn(results)
        results.count().AndReturn(1)
        filters = {
            'instance': INSTANCE_ID_1,
            'launched_at__gte': decimal.Decimal('1.0'),
            'launched_at__lte': decimal.Decimal('1.999999')
        }
        models.InstanceUsage.objects.filter(**filters).AndReturn(results)
        results.count().AndReturn(2)
        self.mox.ReplayAll()

        try:
            dbverifier._verify_for_launch(exist)
            self.fail()
        except AmbiguousResults, nf:
            self.assertEqual(nf.object_type, 'InstanceUsage')
            search_params = {'instance': INSTANCE_ID_1,
                             'launched_at': decimal.Decimal('1.1')}
            self.assertEqual(nf.search_params, search_params)

        self.mox.VerifyAll()

    def test_verify_for_delete(self):
        exist = self.mox.CreateMockAnything()
        exist.delete = self.mox.CreateMockAnything()
        exist.launched_at = decimal.Decimal('1.1')
        exist.deleted_at = decimal.Decimal('5.1')
        exist.delete.launched_at = decimal.Decimal('1.1')
        exist.delete.deleted_at = decimal.Decimal('5.1')
        self.mox.ReplayAll()

        dbverifier._verify_for_delete(exist)
        self.mox.VerifyAll()

    def test_verify_for_delete_found_delete(self):
        exist = self.mox.CreateMockAnything()
        exist.delete = None
        exist.instance = INSTANCE_ID_1
        exist.launched_at = decimal.Decimal('1.1')
        exist.deleted_at = decimal.Decimal('5.1')
        filters = {
            'instance': INSTANCE_ID_1,
            'launched_at__gte': decimal.Decimal('1.0'),
            'launched_at__lte': decimal.Decimal('1.999999'),
        }
        results = self.mox.CreateMockAnything()
        models.InstanceDeletes.objects.filter(**filters).AndReturn(results)
        results.count().AndReturn(1)
        delete = self.mox.CreateMockAnything()
        delete.launched_at = decimal.Decimal('1.1')
        delete.deleted_at = decimal.Decimal('5.1')
        results.__getitem__(0).AndReturn(delete)

        self.mox.ReplayAll()

        dbverifier._verify_for_delete(exist)
        self.mox.VerifyAll()

    def test_verify_for_delete_non_delete(self):
        exist = self.mox.CreateMockAnything()
        exist.delete = None
        exist.instance = INSTANCE_ID_1
        exist.launched_at = decimal.Decimal('1.1')
        exist.deleted_at = None
        exist.audit_period_ending = decimal.Decimal('1.1')
        filters = {
            'instance': INSTANCE_ID_1,
            'launched_at__gte': decimal.Decimal('1.0'),
            'launched_at__lte': decimal.Decimal('1.999999'),
            'deleted_at__lte': decimal.Decimal('1.1')
            }
        results = self.mox.CreateMockAnything()
        models.InstanceDeletes.objects.filter(**filters).AndReturn(results)
        results.count().AndReturn(0)

        self.mox.ReplayAll()

        dbverifier._verify_for_delete(exist)
        self.mox.VerifyAll()

    def test_verify_for_delete_non_delete_found_deletes(self):
        exist = self.mox.CreateMockAnything()
        exist.delete = None
        exist.instance = INSTANCE_ID_1
        exist.launched_at = decimal.Decimal('1.1')
        exist.deleted_at = None
        exist.audit_period_ending = decimal.Decimal('1.3')
        filters = {
            'instance': INSTANCE_ID_1,
            'launched_at__gte': decimal.Decimal('1.0'),
            'launched_at__lte': decimal.Decimal('1.999999'),
            'deleted_at__lte': decimal.Decimal('1.3')
        }
        results = self.mox.CreateMockAnything()
        models.InstanceDeletes.objects.filter(**filters).AndReturn(results)
        results.count().AndReturn(1)

        self.mox.ReplayAll()

        try:
            dbverifier._verify_for_delete(exist)
            self.fail()
        except VerificationException, ve:
            msg = 'Found InstanceDeletes for non-delete exist'
            self.assertEqual(ve.reason, msg)

        self.mox.VerifyAll()

    def test_verify_for_delete_launched_at_mismatch(self):
        exist = self.mox.CreateMockAnything()
        exist.delete = self.mox.CreateMockAnything()
        exist.launched_at = decimal.Decimal('1.1')
        exist.deleted_at = decimal.Decimal('5.1')
        exist.delete.launched_at = decimal.Decimal('2.1')
        exist.delete.deleted_at = decimal.Decimal('5.1')
        self.mox.ReplayAll()

        try:
            dbverifier._verify_for_delete(exist)
            self.fail()
        except FieldMismatch, fm:
            self.assertEqual(fm.field_name, 'launched_at')
            self.assertEqual(fm.expected, decimal.Decimal('1.1'))
            self.assertEqual(fm.actual, decimal.Decimal('2.1'))
        self.mox.VerifyAll()

    def test_verify_for_delete_deleted_at_mismatch(self):
        exist = self.mox.CreateMockAnything()
        exist.delete = self.mox.CreateMockAnything()
        exist.launched_at = decimal.Decimal('1.1')
        exist.deleted_at = decimal.Decimal('5.1')
        exist.delete.launched_at = decimal.Decimal('1.1')
        exist.delete.deleted_at = decimal.Decimal('6.1')
        self.mox.ReplayAll()

        try:
            dbverifier._verify_for_delete(exist)
            self.fail()
        except FieldMismatch, fm:
            self.assertEqual(fm.field_name, 'deleted_at')
            self.assertEqual(fm.expected, decimal.Decimal('5.1'))
            self.assertEqual(fm.actual, decimal.Decimal('6.1'))
        self.mox.VerifyAll()

    def test_verify_pass(self):
        exist = self.mox.CreateMockAnything()
        exist.launched_at = decimal.Decimal('1.1')
        self.mox.StubOutWithMock(dbverifier, '_verify_for_launch')
        self.mox.StubOutWithMock(dbverifier, '_verify_for_delete')
        self.mox.StubOutWithMock(dbverifier, '_mark_exist_failed')
        self.mox.StubOutWithMock(dbverifier, '_mark_exist_verified')
        dbverifier._verify_for_launch(exist)
        dbverifier._verify_for_delete(exist)
        dbverifier._mark_exist_verified(exist)
        self.mox.ReplayAll()
        result, exists = dbverifier._verify(exist)
        self.assertTrue(result)
        self.mox.VerifyAll()

    def test_verify_no_launched_at(self):
        exist = self.mox.CreateMockAnything()
        exist.launched_at = None
        self.mox.StubOutWithMock(dbverifier, '_verify_for_launch')
        self.mox.StubOutWithMock(dbverifier, '_verify_for_delete')
        self.mox.StubOutWithMock(dbverifier, '_mark_exist_failed')
        self.mox.StubOutWithMock(dbverifier, '_mark_exist_verified')
        dbverifier._mark_exist_failed(exist,
                                      reason="Exists without a launched_at")
        self.mox.StubOutWithMock(dbverifier, '_verify_with_reconciled_data')
        dbverifier._verify_with_reconciled_data(exist, mox.IgnoreArg())\
                  .AndRaise(NotFound('InstanceReconcile', {}))
        self.mox.ReplayAll()
        result, exists = dbverifier._verify(exist)
        self.assertFalse(result)
        self.mox.VerifyAll()

    def test_verify_launch_fail(self):
        exist = self.mox.CreateMockAnything()
        exist.launched_at = decimal.Decimal('1.1')
        self.mox.StubOutWithMock(dbverifier, '_verify_for_launch')
        self.mox.StubOutWithMock(dbverifier, '_verify_for_delete')
        self.mox.StubOutWithMock(dbverifier, '_mark_exist_failed')
        self.mox.StubOutWithMock(dbverifier, '_mark_exist_verified')
        verify_exception = VerificationException('test')
        dbverifier._verify_for_launch(exist).AndRaise(verify_exception)
        self.mox.StubOutWithMock(dbverifier, '_verify_with_reconciled_data')
        dbverifier._verify_with_reconciled_data(exist, verify_exception)\
                  .AndRaise(NotFound('InstanceReconcile', {}))
        dbverifier._mark_exist_failed(exist, reason='test')
        self.mox.ReplayAll()
        result, exists = dbverifier._verify(exist)
        self.assertFalse(result)
        self.mox.VerifyAll()

    def test_verify_fail_reconcile_success(self):
        exist = self.mox.CreateMockAnything()
        exist.launched_at = decimal.Decimal('1.1')
        self.mox.StubOutWithMock(dbverifier, '_verify_for_launch')
        self.mox.StubOutWithMock(dbverifier, '_verify_for_delete')
        self.mox.StubOutWithMock(dbverifier, '_mark_exist_failed')
        self.mox.StubOutWithMock(dbverifier, '_mark_exist_verified')
        verify_exception = VerificationException('test')
        dbverifier._verify_for_launch(exist).AndRaise(verify_exception)
        self.mox.StubOutWithMock(dbverifier, '_verify_with_reconciled_data')
        dbverifier._verify_with_reconciled_data(exist, verify_exception)
        dbverifier._mark_exist_verified(exist)
        self.mox.ReplayAll()
        result, exists = dbverifier._verify(exist)
        self.assertTrue(result)
        self.mox.VerifyAll()

    def test_verify_fail_with_reconciled_data_exception(self):
        exist = self.mox.CreateMockAnything()
        exist.launched_at = decimal.Decimal('1.1')
        self.mox.StubOutWithMock(dbverifier, '_verify_for_launch')
        self.mox.StubOutWithMock(dbverifier, '_verify_for_delete')
        self.mox.StubOutWithMock(dbverifier, '_mark_exist_failed')
        self.mox.StubOutWithMock(dbverifier, '_mark_exist_verified')
        verify_exception = VerificationException('test')
        dbverifier._verify_for_launch(exist).AndRaise(verify_exception)
        self.mox.StubOutWithMock(dbverifier, '_verify_with_reconciled_data')
        dbverifier._verify_with_reconciled_data(exist, verify_exception)\
                  .AndRaise(Exception())
        dbverifier._mark_exist_failed(exist, reason='Exception')
        self.mox.ReplayAll()
        result, exists = dbverifier._verify(exist)
        self.assertFalse(result)
        self.mox.VerifyAll()

    def test_verify_delete_fail(self):
        exist = self.mox.CreateMockAnything()
        exist.launched_at = decimal.Decimal('1.1')
        self.mox.StubOutWithMock(dbverifier, '_verify_for_launch')
        self.mox.StubOutWithMock(dbverifier, '_verify_for_delete')
        self.mox.StubOutWithMock(dbverifier, '_mark_exist_failed')
        self.mox.StubOutWithMock(dbverifier, '_mark_exist_verified')
        verify_exception = VerificationException('test')
        dbverifier._verify_for_launch(exist)
        dbverifier._verify_for_delete(exist).AndRaise(verify_exception)
        self.mox.StubOutWithMock(dbverifier, '_verify_with_reconciled_data')
        dbverifier._verify_with_reconciled_data(exist, verify_exception)\
                  .AndRaise(NotFound('InstanceReconcile', {}))
        dbverifier._mark_exist_failed(exist, reason='test')
        self.mox.ReplayAll()
        result, exists = dbverifier._verify(exist)
        self.assertFalse(result)
        self.mox.VerifyAll()

    def test_verify_exception_during_launch(self):
        exist = self.mox.CreateMockAnything()
        exist.launched_at = decimal.Decimal('1.1')
        self.mox.StubOutWithMock(dbverifier, '_verify_for_launch')
        self.mox.StubOutWithMock(dbverifier, '_verify_for_delete')
        self.mox.StubOutWithMock(dbverifier, '_mark_exist_failed')
        self.mox.StubOutWithMock(dbverifier, '_mark_exist_verified')
        dbverifier._verify_for_launch(exist).AndRaise(Exception())
        dbverifier._mark_exist_failed(exist, reason='Exception')
        self.mox.ReplayAll()
        result, exists = dbverifier._verify(exist)
        self.assertFalse(result)
        self.mox.VerifyAll()

    def test_verify_exception_during_delete(self):
        exist = self.mox.CreateMockAnything()
        exist.launched_at = decimal.Decimal('1.1')
        self.mox.StubOutWithMock(dbverifier, '_verify_for_launch')
        self.mox.StubOutWithMock(dbverifier, '_verify_for_delete')
        self.mox.StubOutWithMock(dbverifier, '_mark_exist_failed')
        self.mox.StubOutWithMock(dbverifier, '_mark_exist_verified')
        dbverifier._verify_for_launch(exist)
        dbverifier._verify_for_delete(exist).AndRaise(Exception())
        dbverifier._mark_exist_failed(exist, reason='Exception')
        self.mox.ReplayAll()
        result, exists = dbverifier._verify(exist)
        self.assertFalse(result)
        self.mox.VerifyAll()

    def test_verify_for_range_without_callback(self):
        when_max = datetime.datetime.utcnow()
        results = self.mox.CreateMockAnything()
        models.InstanceExists.objects.select_related().AndReturn(results)
        models.InstanceExists.PENDING = 'pending'
        models.InstanceExists.VERIFYING = 'verifying'
        filters = {
            'audit_period_ending__lte': dt.dt_to_decimal(when_max),
            'status': 'pending'
        }
        results.filter(**filters).AndReturn(results)
        results.order_by('id').AndReturn(results)
        results.count().AndReturn(2)
        exist1 = self.mox.CreateMockAnything()
        exist2 = self.mox.CreateMockAnything()
        results.__getslice__(0, 1000).AndReturn(results)
        results.__iter__().AndReturn([exist1, exist2].__iter__())
        exist1.save()
        exist2.save()
        self.pool.apply_async(dbverifier._verify, args=(exist1,),
                              callback=None)
        self.pool.apply_async(dbverifier._verify, args=(exist2,),
                              callback=None)
        self.mox.ReplayAll()
        self.verifier.verify_for_range(when_max)
        self.assertEqual(exist1.status, 'verifying')
        self.assertEqual(exist2.status, 'verifying')
        self.mox.VerifyAll()

    def test_verify_for_range_with_callback(self):
        callback = self.mox.CreateMockAnything()
        pool = self.mox.CreateMockAnything()
        when_max = datetime.datetime.utcnow()
        results = self.mox.CreateMockAnything()
        models.InstanceExists.objects.select_related().AndReturn(results)
        models.InstanceExists.PENDING = 'pending'
        models.InstanceExists.VERIFYING = 'verifying'
        filters = {
            'audit_period_ending__lte': dt.dt_to_decimal(when_max),
            'status': 'pending'
        }
        results.filter(**filters).AndReturn(results)
        results.order_by('id').AndReturn(results)
        results.count().AndReturn(2)
        exist1 = self.mox.CreateMockAnything()
        exist2 = self.mox.CreateMockAnything()
        results.__getslice__(0, 1000).AndReturn(results)
        results.__iter__().AndReturn([exist1, exist2].__iter__())
        exist1.save()
        exist2.save()
        self.pool.apply_async(dbverifier._verify, args=(exist1,),
                              callback=callback)
        self.pool.apply_async(dbverifier._verify, args=(exist2,),
                              callback=callback)
        self.mox.ReplayAll()
        self.verifier.verify_for_range(when_max, callback=callback)
        self.assertEqual(exist1.status, 'verifying')
        self.assertEqual(exist2.status, 'verifying')
        self.mox.VerifyAll()

    def test_send_verified_notification_default_routing_key(self):
        connection = self.mox.CreateMockAnything()
        exchange = self.mox.CreateMockAnything()
        exist = self.mox.CreateMockAnything()
        exist.raw = self.mox.CreateMockAnything()
        exist_dict = [
            'monitor.info',
            {
                'event_type': 'test',
                'message_id': 'some_uuid'
            }
        ]
        exist_str = json.dumps(exist_dict)
        exist.raw.json = exist_str
        self.mox.StubOutWithMock(kombu.pools, 'producers')
        self.mox.StubOutWithMock(kombu.common, 'maybe_declare')
        producer = self.mox.CreateMockAnything()
        producer.channel = self.mox.CreateMockAnything()
        kombu.pools.producers[connection].AndReturn(producer)
        producer.acquire(block=True).AndReturn(producer)
        producer.__enter__().AndReturn(producer)
        kombu.common.maybe_declare(exchange, producer.channel)
        self.mox.StubOutWithMock(uuid, 'uuid4')
        uuid.uuid4().AndReturn('some_other_uuid')
        message = {'event_type': 'compute.instance.exists.verified.old',
                   'message_id': 'some_other_uuid',
                   'original_message_id': 'some_uuid'}
        producer.publish(message, exist_dict[0])
        producer.__exit__(None, None, None)
        self.mox.ReplayAll()

        dbverifier.send_verified_notification(exist, exchange, connection)
        self.mox.VerifyAll()

    def test_send_verified_notification_routing_keys(self):
        connection = self.mox.CreateMockAnything()
        exchange = self.mox.CreateMockAnything()
        exist = self.mox.CreateMockAnything()
        exist.raw = self.mox.CreateMockAnything()
        exist_dict = [
            'monitor.info',
            {
                'event_type': 'test',
                'message_id': 'some_uuid'
            }
        ]
        exist_str = json.dumps(exist_dict)
        exist.raw.json = exist_str
        self.mox.StubOutWithMock(uuid, 'uuid4')
        uuid.uuid4().AndReturn('some_other_uuid')
        self.mox.StubOutWithMock(kombu.pools, 'producers')
        self.mox.StubOutWithMock(kombu.common, 'maybe_declare')
        routing_keys = ['notifications.info', 'monitor.info']
        for key in routing_keys:
            producer = self.mox.CreateMockAnything()
            producer.channel = self.mox.CreateMockAnything()
            kombu.pools.producers[connection].AndReturn(producer)
            producer.acquire(block=True).AndReturn(producer)
            producer.__enter__().AndReturn(producer)
            kombu.common.maybe_declare(exchange, producer.channel)
            message = {'event_type': 'compute.instance.exists.verified.old',
                       'message_id': 'some_other_uuid',
                       'original_message_id': 'some_uuid'}
            producer.publish(message, key)
            producer.__exit__(None, None, None)
        self.mox.ReplayAll()

        dbverifier.send_verified_notification(exist, exchange, connection,
                                              routing_keys=routing_keys)
        self.mox.VerifyAll()

    def test_run_notifications(self):
        self.mox.StubOutWithMock(dbverifier, '_create_exchange')
        exchange = self.mox.CreateMockAnything()
        dbverifier._create_exchange('stacktach', 'topic', durable=False)\
                  .AndReturn(exchange)
        self.mox.StubOutWithMock(dbverifier, '_create_connection')
        conn = self.mox.CreateMockAnything()
        dbverifier._create_connection(self.config_notif).AndReturn(conn)
        conn.__enter__().AndReturn(conn)
        self.mox.StubOutWithMock(self.verifier_notif, '_run')
        self.verifier_notif._run(callback=mox.IgnoreArg())
        conn.__exit__(None, None, None)
        self.mox.ReplayAll()
        self.verifier_notif.run()
        self.mox.VerifyAll()

    def test_run_notifications_with_routing_keys(self):
        self.mox.StubOutWithMock(dbverifier, '_create_exchange')
        exchange = self.mox.CreateMockAnything()
        dbverifier._create_exchange('stacktach', 'topic', durable=False) \
            .AndReturn(exchange)
        self.mox.StubOutWithMock(dbverifier, '_create_connection')
        conn = self.mox.CreateMockAnything()
        dbverifier._create_connection(self.config_notif).AndReturn(conn)
        conn.__enter__().AndReturn(conn)
        self.mox.StubOutWithMock(self.verifier_notif, '_run')
        self.verifier_notif._run(callback=mox.IgnoreArg())
        conn.__exit__(None, None, None)
        self.mox.ReplayAll()
        self.verifier_notif.run()
        self.mox.VerifyAll()

    def test_run_no_notifications(self):
        self.mox.StubOutWithMock(self.verifier, '_run')
        self.verifier._run()
        self.mox.ReplayAll()
        self.verifier.run()
        self.mox.VerifyAll()

    def test_run_once_notifications(self):
        self.mox.StubOutWithMock(dbverifier, '_create_exchange')
        exchange = self.mox.CreateMockAnything()
        dbverifier._create_exchange('stacktach', 'topic', durable=False) \
            .AndReturn(exchange)
        self.mox.StubOutWithMock(dbverifier, '_create_connection')
        conn = self.mox.CreateMockAnything()
        dbverifier._create_connection(self.config_notif).AndReturn(conn)
        conn.__enter__().AndReturn(conn)
        self.mox.StubOutWithMock(self.verifier_notif, '_run_once')
        self.verifier_notif._run_once(callback=mox.IgnoreArg())
        conn.__exit__(None, None, None)
        self.mox.ReplayAll()
        self.verifier_notif.run_once()
        self.mox.VerifyAll()

    def test_run_once_no_notifications(self):
        self.mox.StubOutWithMock(self.verifier, '_run_once')
        self.verifier._run_once()
        self.mox.ReplayAll()
        self.verifier.run_once()
        self.mox.VerifyAll()
