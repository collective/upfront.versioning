import transaction, unittest
from AccessControl.PermissionRole import rolesForPermissionOn
from zope.component import getUtility

from Products.CMFPlone.utils import _createObjectByType
from Products.PloneTestCase.setup import _createHomeFolder

from upfront.versioning.interfaces import IVersioner, ICheckedOut
from upfront.versioning.tests.VersioningTestCase import VersioningTestCase

class TestCheckin(VersioningTestCase):

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

    def test_fresh_checkin(self):
        """Content is not yet in repo, ie. there exists no 
        /repository/document."""
        utility = getUtility(IVersioner)
        workspace = utility.getWorkspace(self.portal)
        working = _createObjectByType('Document', workspace, 'working')
        self.document_fti._finishConstruction(working)
        # We need to commit here so that _p_jar isn't None and move
        # will work
        transaction.savepoint(optimistic=True)
        checkedin = utility.checkin(working)

        # Working copy must be removed from workspace
        self.failIf('working' in workspace.objectIds())

        # Parent folder of checkedin must have id 00000001
        self.assertEquals(checkedin.aq_parent.id, '00000001')

        # Grandparent folder of checkedin must have id 'document'
        self.assertEquals(checkedin.aq_parent.aq_parent.id, 'document')
       
        # Marker interface must be gone
        self.failIf(ICheckedOut.providedBy(checkedin))

    def test_second_checkin(self):
        """Content is already in repo, ie. there exists a 
        /repository/document/00000001."""

        # Create /repository/document/00000001
        document_folder = _createObjectByType(
            'Folder', self.portal.repository, 'document'
        )
        version_folder = _createObjectByType(
            'Folder', document_folder, '00000001'
        )

        utility = getUtility(IVersioner)
        workspace = utility.getWorkspace(self.portal)
        working = _createObjectByType('Document', workspace, 'working')
        # We need to commit here so that _p_jar isn't None and move
        # will work
        transaction.savepoint(optimistic=True)
        checkedin = utility.checkin(working)

        # Parent folder of checkedin must have id 00000002
        self.assertEquals(checkedin.aq_parent.id, '00000002')

def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    suite.addTest(makeSuite(TestCheckin))
    return suite
