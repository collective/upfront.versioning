import unittest
from zope.component import getUtility

from upfront.versioning.interfaces import IVersioner, ICheckedIn, \
    IVersionMetadata
from upfront.versioning.versioner import ANNOT_KEY    
from upfront.versioning.tests.VersioningTestCase import VersioningTestCase

class TestDeriveCopy(VersioningTestCase):

    def afterSetUp(self):
        VersioningTestCase.afterSetUp(self) 

    def test_can_derive_copy(self):
        """Can copy be derived?"""
        utility = getUtility(IVersioner)

        # Item has nothing to do with versioning
        self.failUnless(utility.can_derive_copy(self.portal['root-published']))

        # Item has been checked out
        copy = utility.checkout(self.portal.repository.document['00000002']['repo-member'])
        self.failIf(utility.can_derive_copy(copy))

        # Item has been checked in but we do not have Modify Portal Content
        self.failUnless(utility.can_derive_copy(self.portal.repository.document['00000001']['repo-admin']))

        # Item has been checked in and we do have Modify Portal Content
        self.failUnless(utility.can_derive_copy(self.portal.repository.document['00000002']['repo-member']))

        # Attempt to derive the portal
        self.failIf(utility.can_derive_copy(self.portal))

    def test_derive(self):
        """Derive an item that is not in the repository."""
        utility = getUtility(IVersioner)
        workspace = utility.getWorkspace(self.portal)
        copy = utility.derive_copy(self.portal['root-published'])

        # Is it there?
        self.failUnless(copy in workspace.objectValues())

        # IVersionMetadata annotation must be present
        self.failUnless(IVersionMetadata(copy).has_key(ANNOT_KEY))

    def test_derive_from_repo(self):
        """Derive an item that is in the repository"""
        utility = getUtility(IVersioner)
        copy = utility.derive_copy(self.portal.repository.document['00000002']['repo-member'])

        # Marker interface must be gone
        self.failIf(ICheckedIn.providedBy(copy))

    def test_crazy_derive(self):
        """Derive the entire Plone site"""
        utility = getUtility(IVersioner)
        self.assertRaises(RuntimeError, utility.derive_copy, self.portal)

def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    suite.addTest(makeSuite(TestDeriveCopy))
    return suite
