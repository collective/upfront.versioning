import unittest
from AccessControl.PermissionRole import rolesForPermissionOn
from zope.component import getUtility

from Products.CMFPlone.utils import _createObjectByType
from Products.PloneTestCase.setup import _createHomeFolder

from upfront.versioning.interfaces import IVersioner, ICheckedOut
from upfront.versioning.tests.VersioningTestCase import VersioningTestCase

class TestCheckout(VersioningTestCase):

    def afterSetUp(self):
        VersioningTestCase.afterSetUp(self) 

        self.document_fti = self.portal.portal_types.getTypeInfo('Document')

        # Create a few items
        self.loginAsPortalOwner()
        apple = _createObjectByType('Document', self.portal.repository, 'apple')
        self.document_fti._finishConstruction(apple)
        self.portal.portal_workflow.doActionFor(apple, 'publish')

        # These tests must be run while logged in as a member since we 
        # need a workspace.
        self.login('member')
        _createHomeFolder(self.portal, 'member', take_ownership=0)

    def test_can_checkout(self):
        """Can content be checked out?"""
        utility = getUtility(IVersioner)

        # Item has not been checked out
        self.failUnless(utility.can_checkout(self.portal.repository.apple))

        # Item has been checked out
        copy = utility.checkout(self.portal.repository.apple)
        self.failIf(utility.can_checkout(copy))

    def test_fresh_checkout(self):
        """Content is not yet in workspace. Check it out."""
        utility = getUtility(IVersioner)
        workspace = utility.getWorkspace(self.portal)
        copy = utility.checkout(self.portal.repository.apple)
        # Is it there?
        self.failUnless(copy in workspace.objectValues())
        # Is interface provided
        self.failUnless(ICheckedOut.providedBy(copy))
        # Only Manager and Owner may have View permission. No acquire.
        roles = rolesForPermissionOn('View', copy)
        self.assertEquals(len(roles), 2)
        self.failUnless('Manager' in roles)
        self.failUnless('Owner' in roles)

    def test_already_checkedout(self):
        """Content is already checked out. Check it out again."""
        utility = getUtility(IVersioner)
        workspace = utility.getWorkspace(self.portal)
        copy_one = utility.checkout(self.portal.repository.apple)
        copy_two = utility.checkout(self.portal.repository.apple)
        self.assertEquals(copy_one, copy_two)

def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    suite.addTest(makeSuite(TestCheckout))
    return suite
