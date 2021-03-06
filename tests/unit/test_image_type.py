# Copyright (c) 2012 - Rackspace Inc.
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

import unittest

from stacktach import image_type


class ImageTypeTestCase(unittest.TestCase):

    # Abstractions
    def _test_get_numeric_code(self, image, os_type, os_distro, expected,
                               default=0):
        payload = {
            "image_meta": {
                "image_type": image,
                "os_type": os_type,
                "os_distro": os_distro
            }
        }

        result = image_type.get_numeric_code(payload, default)

        self.assertEqual(result, expected)

    def _test_readable_with_os_distro(self, value, image, os_type, os_distro):
        result = image_type.readable(value)

        self.assertEqual(result, [image, os_type, os_distro])

    def _test_readable_without_os_distro(self, value, image, os_type, os_distro):
        result = image_type.readable(value)

        self.assertEqual(result, [image, os_type])

    def _test_isset(self, code):
        value = 0
        value |= code

        self.assertTrue(image_type.isset(value, code))

    def _test_false_isset(self, code, false_code):
        value = 0
        value |= code

        self.assertFalse(image_type.isset(value, false_code))

    # Test get_numeric_code
    def test_empty_payload_in_get_numeric_code(self):
        result = image_type.get_numeric_code({})

        self.assertEqual(result, 0x0)

    def test_empty_meta_in_get_numeric_code(self):
        result = image_type.get_numeric_code({'image_meta': {}})

        self.assertEqual(result, 0x0)

    def test_empty_os_type_in_payload_not_meta(self):
        result = image_type.get_numeric_code({'image_meta': {}, 'os_type': ''})

        self.assertEqual(result, 0x0)

    def test_os_type_in_meta_with_empty_os_type_in_payload(self):
        payload = {
            "image_meta":   {
                "os_type": "windows"
            },
            "os_type": ''
        }

        result = image_type.get_numeric_code(payload)

        self.assertEqual(result, image_type.WINDOWS_IMAGE)

    def test_os_type_in_meta_has_precedent_over_one_in_payload(self):
        payload = {
            "image_meta": {
                "os_type": "linux"
            },
            "os_type": "windows"
        }

        result = image_type.get_numeric_code(payload)

        self.assertEqual(result, image_type.LINUX_IMAGE)

    def test_os_type_in_payload_not_meta(self):
        payload = {
            "image_meta": {},
            "os_type": "linux"
        }

        result = image_type.get_numeric_code(payload)

        self.assertEqual(result, image_type.LINUX_IMAGE)

    def test_get_numeric_code_base_linux_ubuntu(self):
        self._test_get_numeric_code('base', 'linux', 'ubuntu',
                                    expected=0x111)

    def test_get_numeric_code_base_linux_debian(self):
        self._test_get_numeric_code('base', 'linux', 'debian',
                                    expected=0x211)

    def test_get_numeric_code_base_linux_centos(self):
        self._test_get_numeric_code('base', 'linux', 'centos',
                                    expected=0x411)

    def test_get_numeric_code_base_linux_rhel(self):
        self._test_get_numeric_code('base', 'linux', 'rhel',
                                    expected=0x811)

    def test_get_numeric_code_snapshot_linux_ubuntu(self):
        self._test_get_numeric_code('snapshot', 'linux', 'ubuntu',
                                    expected=0x112)

    def test_get_numeric_code_snapshot_linux_debian(self):
        self._test_get_numeric_code('snapshot', 'linux', 'debian',
                                    expected=0x212)

    def test_get_numeric_code_snapshot_linux_centos(self):
        self._test_get_numeric_code('snapshot', 'linux', 'centos',
                                    expected=0x412)

    def test_get_numeric_code_snapshot_linux_rhel(self):
        self._test_get_numeric_code('snapshot', 'linux', 'rhel',
                                    expected=0x812)

    def test_get_numeric_code_base_windows(self):
        self._test_get_numeric_code('base', 'windows', None,
                                    expected=0x21)

    def test_get_numeric_code_snapshot_windows(self):
        self._test_get_numeric_code('snapshot', 'windows', None,
                                    expected=0x22)

    def test_get_numeric_code_base_freebsd(self):
        self._test_get_numeric_code('base', 'freebsd', None,
                                    expected=0x41)

    def test_get_numeric_code_snapshot_freebsd(self):
        self._test_get_numeric_code('snapshot', 'freebsd', None,
                                    expected=0x42)

    # Test readable with os_distro available
    def _test_readable_with_os_distro_base_linux_ubuntu(self):
        self._test_readable_with_os_distro(0x111, 'base', 'linux', 'ubuntu')

    def _test_readable_with_os_distro_base_linux_debian(self):
        self._test_readable_with_os_distro(0x211, 'base', 'linux', 'debian')

    def _test_readable_with_os_distro_base_linux_centos(self):
        self._test_readable_with_os_distro(0x411, 'base', 'linux', 'centos')

    def _test_readable_with_os_distro_base_linux_rhel(self):
        self._test_readable_with_os_distro(0x811, 'base', 'linux', 'rhel')

    def _test_readable_with_os_distro_snapshot_linux_ubuntu(self):
        self._test_readable_with_os_distro(0x112, 'snapshot', 'linux', 'ubuntu')

    def _test_readable_with_os_distro_snapshot_linux_debian(self):
        self._test_readable_with_os_distro(0x212, 'snapshot', 'linux', 'debian')

    def _test_readable_with_os_distro_snapshot_linux_centos(self):
        self._test_readable_with_os_distro(0x412, 'snapshot', 'linux', 'centos')

    def _test_readable_with_os_distro_snapshot_linux_rhel(self):
        self._test_readable_with_os_distro(0x812, 'snapshot', 'linux', 'rhel')

    # Test readable without os_distro available
    def test_readable_without_os_distro_base_windows_(self):
        self._test_readable_without_os_distro(0x21, 'base', 'windows', None)

    def test_readable_without_os_distro_snapshot_windows(self):
        self._test_readable_without_os_distro(0x22, 'snapshot', 'windows', None)

    def test_readable_without_distro_base_freebsd(self):
        self._test_readable_without_os_distro(0x41, 'base', 'freebsd', None)

    def test_readable__without_distro_snapshot_freebsd(self):
        self._test_readable_without_os_distro(0x42, 'snapshot', 'freebsd', None)

    # Test isset
    def test_isset_base_image(self):
        self._test_isset(image_type.BASE_IMAGE)

    def test_isset_snapshot_image(self):
        self._test_isset(image_type.SNAPSHOT_IMAGE)

    def test_isset_linux_image(self):
        self._test_isset(image_type.LINUX_IMAGE)

    def test_isset_windows_image(self):
        self._test_isset(image_type.WINDOWS_IMAGE)

    def test_isset_freebsd_image(self):
        self._test_isset(image_type.FREEBSD_IMAGE)

    def test_isset_os_debian(self):
        self._test_isset(image_type.OS_DEBIAN)

    def test_isset_os_ubuntu(self):
        self._test_isset(image_type.OS_UBUNTU)

    def test_isset_os_centos(self):
        self._test_isset(image_type.OS_CENTOS)

    def test_isset_os_rhel(self):
        self._test_isset(image_type.OS_RHEL)

    # Negative test isset
    def test_false_isset_base_image_from_payload(self):
        self._test_false_isset(image_type.SNAPSHOT_IMAGE, image_type.BASE_IMAGE)

    def test_false_isset_snapshot_image(self):
        self._test_false_isset(image_type.BASE_IMAGE, image_type.SNAPSHOT_IMAGE)

    def test_false_isset_linux_image(self):
        self._test_false_isset(image_type.WINDOWS_IMAGE, image_type.LINUX_IMAGE)

    def test_false_isset_windows_image(self):
        self._test_false_isset(image_type.LINUX_IMAGE, image_type.WINDOWS_IMAGE)

    def test_false_isset_freebsd_image(self):
        self._test_false_isset(image_type.LINUX_IMAGE, image_type.FREEBSD_IMAGE)

    def test_false_isset_os_debian_os_ubuntu(self):
        self._test_false_isset(image_type.OS_DEBIAN, image_type.OS_UBUNTU)

    def test_false_isset_os_centos_os_ubuntu(self):
        self._test_false_isset(image_type.OS_CENTOS, image_type.OS_UBUNTU)

    def test_false_isset_os_rhel_os_ubuntu(self):
        self._test_false_isset(image_type.OS_RHEL, image_type.OS_UBUNTU)

    def test_false_isset_os_ubuntu_os_debian(self):
        self._test_false_isset(image_type.OS_UBUNTU, image_type.OS_DEBIAN)

    def test_false_isset_os_centos_os_debian(self):
        self._test_false_isset(image_type.OS_CENTOS, image_type.OS_DEBIAN)

    def test_false_isset_os_rhel_os_debian(self):
        self._test_false_isset(image_type.OS_RHEL, image_type.OS_DEBIAN)

    def test_false_isset_os_debian_os_centos(self):
        self._test_false_isset(image_type.OS_DEBIAN, image_type.OS_CENTOS)

    def test_false_isset_os_ubuntu_os_centos(self):
        self._test_false_isset(image_type.OS_DEBIAN, image_type.OS_CENTOS)

    def test_false_isset_os_rhel_os_centos(self):
        self._test_false_isset(image_type.OS_RHEL, image_type.OS_CENTOS)

    def test_false_isset_os_debian_os_rhel(self):
        self._test_false_isset(image_type.OS_DEBIAN, image_type.OS_RHEL)

    def test_false_isset_os_centos_os_rhel(self):
        self._test_false_isset(image_type.OS_CENTOS, image_type.OS_RHEL)

    def test_false_isset_os_ubuntu_os_rhel(self):
        self._test_false_isset(image_type.OS_UBUNTU, image_type.OS_RHEL)

    # Test blank argument to isset
    def test_blank_argument_isset(self):
        self.assertFalse(image_type.isset(None, image_type.OS_CENTOS))
