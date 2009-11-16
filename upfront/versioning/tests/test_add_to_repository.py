import transaction, unittest
from AccessControl.PermissionRole import rolesForPermissionOn
from zope.component import getUtility

from Products.CMFPlone.utils import _createObjectByType
from Products.PloneTestCase.setup import _createHomeFolder

from upfront.versioning.interfaces import IVersioner, ICheckedOut, ICheckedIn, \
    IVersionMetadata
from upfront.versioning.tests.VersioningTestCase import VersioningTestCase

class TestAddToRepository(VersioningTestCase):

    def afterSetUp(self):
        VersioningTestCase.afterSetUp(self) 
     
        # Create orange owned by member
        utility = getUtility(IVersioner)
        workspace = utility.getWorkspace(self.portal)
        orange = _createObjectByType('Document', workspace, 'orange')
        fti = self.portal.portal_types.getTypeInfo('Document')
        fti._finishConstruction(orange)
        transaction.savepoint(optimistic=True)

    def test_can_add_to_repository(self):
        """Can item be added to the repository?"""
        utility = getUtility(IVersioner)
        workspace = utility.getWorkspace(self.portal)

        # Member does not have permission Modify Portal Content
        self.failIf(utility.can_add_to_repository(self.portal['root-published']))

        # Member does have permission Modify Portal Content
        self.failUnless(utility.can_add_to_repository(workspace.orange))

        # Item has been checked out
        copy = utility.checkout(self.portal.repository.document['00000002']['repo-member'])
        self.failIf(utility.can_add_to_repository(copy))

        # Item has been checked in
        checkedin = utility.checkin(copy)
        self.failIf(utility.can_add_to_repository(checkedin))

        # todo: test constrain portal types, dangerous trees etc.

    def test_add_to_repository(self):
        """Content type is not yet in repo, ie. there exists no 
        /repository/document/00000003."""
        utility = getUtility(IVersioner)
        workspace = utility.getWorkspace(self.portal)
        added = utility.add_to_repository(workspace.orange)

        # Orange copy must be removed from workspace
        self.failIf('orange' in workspace.objectIds())

        # Parent folder of added must have id 00000003
        self.assertEquals(added.aq_parent.id, '00000003')

        # Marker interface must be set
        self.failUnless(ICheckedIn.providedBy(added))

        # Check metadata
        adapted = IVersionMetadata(added)
        self.assertEquals(adapted.token, added.UID())
        self.assertEquals(adapted.state, 'checked_in')
        self.assertEquals(adapted.version, 3)

        # Is checked in item in catalog?
        vc = self.portal.upfront_versioning_catalog
        brains = vc(
            path='/'.join(added.getPhysicalPath()),
            token=added.UID(),
            state='checked_in'
        )
        self.failUnless(brains)

def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    suite.addTest(makeSuite(TestAddToRepository))
    return suite
