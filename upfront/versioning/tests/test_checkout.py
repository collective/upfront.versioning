import unittest
from zope.component import getUtility

from Products.CMFPlone.utils import _createObjectByType

from upfront.versioning.tests.VersioningTestCase import VersioningTestCase

class TestCheckout(VersioningTestCase):

    def afterSetUp(self):
        VersioningTestCase.afterSetUp(self) 

    def testCase1(self):
        """
        """
        utility = getUtility(IVersioner)

def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    suite.addTest(makeSuite(TestCheckout))
    return suite
