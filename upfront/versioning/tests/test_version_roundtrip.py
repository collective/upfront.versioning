import transaction, unittest
from AccessControl.PermissionRole import rolesForPermissionOn
from zope.component import getUtility

from Products.CMFPlone.utils import _createObjectByType
from Products.PloneTestCase.setup import _createHomeFolder

from upfront.versioning.interfaces import IVersioner, ICheckedOut, \
    IVersionMetadata, IVersioningSettings
from upfront.versioning.tests.VersioningTestCase import VersioningTestCase

class TestVersionRoundtrip(VersioningTestCase):

    def afterSetUp(self):
        VersioningTestCase.afterSetUp(self) 
                     
        utility = getUtility(IVersioner)
        workspace = utility.getWorkspace(self.portal)

        # Create a folder with id repo-member. We want its id to collide 
        # with the document repo-member.
        ob = _createObjectByType('Folder', workspace, 'repo-member')
        fti = self.portal.portal_types.getTypeInfo('Folder')
        fti._finishConstruction(ob)

        # Portal owner publishes ob
        self.loginAsPortalOwner()
        self.portal.portal_workflow.doActionFor(ob, 'publish')

        self.login('member')

        transaction.savepoint(optimistic=True)

        # Add folder to repository
        utility.add_to_repository(workspace['repo-member'])

        # Checkout items
        copy = utility.checkout(self.portal.repository.document['00000002']['repo-member'])
        copy_collide = utility.checkout(self.portal.repository.folder['00000002']['repo-member'])

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
        self.assertEquals(self.checkedin.id, 'repo-member')
        self.assertEquals(self.checkedin_collide.id, 'repo-member')

    def test_expired(self):
        """Verify old version is expired"""
        self.failUnless(self.portal.isExpired(self.portal.repository.document['00000002']['repo-member']))

    def test_token_chain(self):
        """Checkout an item and check it in, then checkout the latest version 
        and confirm that original, the checkin and the checkout has the same
        token."""
        utility = getUtility(IVersioner)
        copy = utility.checkout(self.checkedin)

        self.assertEquals(
            IVersionMetadata(self.portal.repository.document['00000002']['repo-member']).token,
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
