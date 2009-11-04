import unittest
from zope.component import getUtility

from Products.CMFPlone.utils import _createObjectByType
from Products.PloneTestCase.setup import _createHomeFolder

from upfront.versioning.interfaces import IVersioner
from upfront.versioning.tests.VersioningTestCase import VersioningTestCase

class TestCheckout(VersioningTestCase):

    def afterSetUp(self):
        VersioningTestCase.afterSetUp(self) 

        # Create a few items
        apple = _createObjectByType('Document', self.portal.repository, 'apple')

        # These tests must be run while logged in as a member since we 
        # need a workspace.
        self.login('member')
        _createHomeFolder(self.portal, 'member', take_ownership=0)

    def test_checkout(self):
        """Content is not yet in workspace. Check it out.
        """
        utility = getUtility(IVersioner)
        workspace = utility.getWorkspace(self.portal)
        copy = utility.checkout(self.portal.repository.apple)
        self.failIf(copy not in workspace.objectValues())

def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    suite.addTest(makeSuite(TestCheckout))
    return suite
