import unittest
from AccessControl.PermissionRole import rolesForPermissionOn
from zope.component import getUtility

from Products.CMFPlone.utils import _createObjectByType
from Products.PloneTestCase.setup import _createHomeFolder

from upfront.versioning.interfaces import IVersioner, ICheckedOut
from upfront.versioning.tests.VersioningTestCase import VersioningTestCase

class TestVersionRoundtrip(VersioningTestCase):

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

        # Checkout apple
        utility = getUtility(IVersioner)
        copy = utility.checkout(self.portal.repository.apple)

        # Check it back in
        self.checkedin = utility.checkin(copy)

    def test_permissions(self):
        """Verify View permission roles after a roundtrip"""        
        roles = rolesForPermissionOn('View', self.checkedin)
        self.assertEquals(len(roles), 1)
        self.failUnless('Anonymous' in roles)

def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    suite.addTest(makeSuite(TestVersionRoundtrip))
    return suite
