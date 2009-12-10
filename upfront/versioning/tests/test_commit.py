import transaction, unittest
from AccessControl.PermissionRole import rolesForPermissionOn
from zope.component import getUtility

from Products.CMFPlone.utils import _createObjectByType
from Products.PloneTestCase.setup import _createHomeFolder

from upfront.versioning.interfaces import IVersioner, ICheckedOut, ICheckedIn, \
    IVersionMetadata
from upfront.versioning.tests.VersioningTestCase import VersioningTestCase

class TestCommit(VersioningTestCase):

    def afterSetUp(self):
        VersioningTestCase.afterSetUp(self) 

    def test_can_commit(self):
        """Can content be committed?"""
        utility = getUtility(IVersioner)
        workspace = self.getWorkspace()

        # Unversioned and we have Modify Portal Content permission
        self.failIf(utility.can_commit(workspace['a-document-unversioned']))

        # Unversioned and we do not have Modify Portal Content permission
        self.failIf(utility.can_commit(self.portal.news))

        # Versioned but not checked out and we have Modify Portal Content permission
        self.failIf(utility.can_commit(workspace['a-document']['00000001']))

        # Versioned and checked out and we have Modify Portal Content permission
        self.failUnless(utility.can_commit(workspace['a-document']['00000002']))
 
    def test_references(self):
        """Inspect references on an item after it has been committed"""
        utility = getUtility(IVersioner)
        workspace = self.getWorkspace()

        ddoc = workspace['a-ddocument']['00000002']
        committed = utility.commit(ddoc)

        self.assertEquals(committed.getRelated(), ddoc.getRelated())

    def test_token_chain(self):
        """Confirm that all versions of an item have the sametoken."""
        utility = getUtility(IVersioner)
        workspace = self.getWorkspace()

        version1 = workspace['a-document']['00000001']
        version2 = workspace['a-document']['00000002']
        version2 = utility.commit(version2)
        version3 = utility.start_new_version(version2)

        self.assertEquals(
            IVersionMetadata(version1).token,
            IVersionMetadata(version2).token
        )            
        self.assertEquals(
            IVersionMetadata(version2).token,
            IVersionMetadata(version3).token
        )            

def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    suite.addTest(makeSuite(TestCommit))
    return suite
