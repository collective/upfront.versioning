import transaction, unittest
from AccessControl.PermissionRole import rolesForPermissionOn
from zope.component import getUtility

from Products.CMFPlone.utils import _createObjectByType
from Products.PloneTestCase.setup import _createHomeFolder

from upfront.versioning.interfaces import IVersioner, ICheckedOut, \
    IVersionMetadata
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

        # Create a different item with the same id. It must live in another
        # container. We use portal.
        apple_collide = _createObjectByType('Document', self.portal, 'apple')

        # These tests must be run while logged in as a member since we 
        # need a workspace.
        self.login('member')
        _createHomeFolder(self.portal, 'member', take_ownership=0)

        # Checkout apple and the second apple
        utility = getUtility(IVersioner)
        copy = utility.checkout(self.portal.repository.apple)
        copy_collide = utility.checkout(self.portal.apple)

        transaction.savepoint(optimistic=True)

        # Check both back in
        self.checkedin = utility.checkin(copy)
        self.checkedin_collide = utility.checkin(copy_collide)

    def test_permissions(self):
        """Verify View permission roles after a roundtrip"""        
        roles = rolesForPermissionOn('View', self.checkedin)
        self.assertEquals(len(roles), 1)
        self.failUnless('Anonymous' in roles)

    def test_id(self):
        """Verify checked in item's id matches original item's id"""
        self.failUnless(self.checkedin.id == self.portal.repository.apple.id)
        self.failUnless(self.checkedin_collide.id == self.portal.apple.id)

    def test_expired(self):
        """Verify old version is expired"""
        self.failUnless(self.portal.isExpired(self.portal.repository.apple))

    def test_token_chain(self):
        """Checkout an item and check it in, then checkout the latest version 
        and confirm that original, the checkin and the checkout has the same
        token."""
        utility = getUtility(IVersioner)
        copy = utility.checkout(self.checkedin)

        self.assertEquals(
            IVersionMetadata(self.portal.repository.apple).token,
            IVersionMetadata(self.checkedin).token
        )            
        self.assertEquals(
            IVersionMetadata(self.checkedin).token,
            IVersionMetadata(copy).token
        )            

def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    suite.addTest(makeSuite(TestVersionRoundtrip))
    return suite
