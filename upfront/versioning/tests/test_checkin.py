import transaction, unittest
from AccessControl.PermissionRole import rolesForPermissionOn
from zope.component import getUtility

from Products.CMFPlone.utils import _createObjectByType
from Products.PloneTestCase.setup import _createHomeFolder

from upfront.versioning.interfaces import IVersioner, ICheckedOut, ICheckedIn, \
    IVersionMetadata
from upfront.versioning.tests.VersioningTestCase import VersioningTestCase

class TestCheckin(VersioningTestCase):

    def afterSetUp(self):
        VersioningTestCase.afterSetUp(self) 

    def test_can_checkin(self):
        """Can content be checked in?"""
        utility = getUtility(IVersioner)

        # Item has not been checked out
        self.failIf(utility.can_checkin(self.portal.repository.document['00000002']['repo-member']))

        # Item has been checked out
        copy = utility.checkout(self.portal.repository.document['00000002']['repo-member'])
        self.failUnless(utility.can_checkin(copy))

    def test_second_checkin(self):
        """Content is already in repo, ie. there exists a
        /repository/document/00000002. Do another checkout and check it back
        in.
        
        test_add_to_repository.test_add_to_repository already checks what we 
        would want to check here."""

        utility = getUtility(IVersioner)
        copy = utility.checkout(self.portal.repository.document['00000002']['repo-member'])
        checkedin = utility.checkin(copy)

        # Parent folder of checkedin must have id 00000003
        self.assertEquals(checkedin.aq_parent.id, '00000003')

        # Is it not expired?
        self.failIf(self.portal.isExpired(checkedin))

    def test_references(self):
        """Inspect references on an item after it has been checked in"""
        ddoc = self.portal.repository.ddocument['00000001']['repo-ddocument']
        utility = getUtility(IVersioner)
        copy = utility.checkout(ddoc)
        checkedin = utility.checkin(copy)
        self.assertEquals(checkedin.getRelated(), ddoc.getRelated())

def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    suite.addTest(makeSuite(TestCheckin))
    return suite
