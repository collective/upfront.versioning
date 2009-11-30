import unittest
from AccessControl.PermissionRole import rolesForPermissionOn
from zope.interface import alsoProvides
from zope.component import getUtility

from Products.CMFPlone.utils import _createObjectByType
from Products.PloneTestCase.setup import _createHomeFolder

from upfront.versioning.interfaces import IVersioner, ICheckedOut, ICheckedIn, \
    IVersionMetadata
from upfront.versioning.tests.VersioningTestCase import VersioningTestCase

class TestCheckout(VersioningTestCase):

    def afterSetUp(self):
        VersioningTestCase.afterSetUp(self) 

    def test_can_checkout(self):
        """Can item be checked out?"""
        utility = getUtility(IVersioner)

        # Item has not been checked out and we do not have Modify Portal 
        # Content permission
        self.failIf(utility.can_checkout(self.portal.repository.document['00000001']['repo-admin']))

        # Item has not been checked out and we have Modify Portal Content 
        # permission
        self.failUnless(utility.can_checkout(self.portal.repository.document['00000002']['repo-member']))

        # Attempt to checkout a checked out item
        copy = utility.checkout(self.portal.repository.document['00000002']['repo-member'])
        self.failIf(utility.can_checkout(copy))

    def test_fresh_checkout(self):
        """Item is not yet in workspace. Check it out."""
        utility = getUtility(IVersioner)
        workspace = utility.getWorkspace(self.portal)
        copy = utility.checkout(self.portal.repository.document['00000002']['repo-member'])

        # Is it there?
        self.failUnless(copy in workspace.objectValues())

        # Is interface provided?
        self.failUnless(ICheckedOut.providedBy(copy))

        # Is interface not provided?
        self.failIf(ICheckedIn.providedBy(copy))

        # Only Manager and Owner may have View permission. No acquire.
        roles = rolesForPermissionOn('View', copy)
        self.assertEquals(len(roles), 2)
        self.failUnless('Manager' in roles)
        self.failUnless('Owner' in roles)

        # Check metadata
        adapted = IVersionMetadata(copy)
        self.assertEquals(adapted.token, self.portal.repository.document['00000002']['repo-member'].UID())
        self.assertEquals(adapted.state, 'checked_out')
        self.assertEquals(adapted.version, 2)

        # Is checked out item in catalog?
        vc = self.portal.upfront_versioning_catalog
        brains = vc(
            path='/'.join(copy.getPhysicalPath()), 
            token=self.portal.repository.document['00000002']['repo-member'].UID(),
            state='checked_out'
        )
        self.failUnless(brains)      

        # Is it expired?
        self.failUnless(self.portal.isExpired(copy))

        # Is it published?
        wf = self.portal.portal_workflow
        self.assertEquals(wf.getInfoFor(copy, 'review_state'), 'published')

    def test_already_checkedout(self):
        """Item is already checked out. Check it out again."""
        utility = getUtility(IVersioner)      
        copy_one = utility.checkout(self.portal.repository.document['00000002']['repo-member'])
        copy_two = utility.checkout(self.portal.repository.document['00000002']['repo-member'])
        self.assertEquals(copy_one, copy_two)

    def test_checkout_delete(self):
        """Item is checked out and deleted"""
        utility = getUtility(IVersioner)
        copy = utility.checkout(self.portal.repository.document['00000002']['repo-member'])
        copy_path = '/'.join(copy.getPhysicalPath())
        copy.aq_parent.manage_delObjects([copy.id])

        # Item may not be in catalog anymore
        brains = self.portal.upfront_versioning_catalog(path=copy_path)
        self.failIf(brains)

    def test_checkout_move(self):
        """Item is checked out and moved"""
        utility = getUtility(IVersioner)
        workspace = utility.getWorkspace(self.portal)
        copy = utility.checkout(self.portal.repository.document['00000002']['repo-member'])
        old_copy_path = '/'.join(copy.getPhysicalPath())

        # Create a new folder in workspace and move the copy there
        temp = _createObjectByType('Folder', workspace, 'temp')
        cp = copy.aq_parent.manage_cutObjects(ids=[copy.id])
        res = temp.manage_pasteObjects(cp)
        new_copy = temp._getOb(res[0]['new_id'])
        new_copy_path = '/'.join(new_copy.getPhysicalPath())

        # Original copy path may not be in catalog anymore
        brains = self.portal.upfront_versioning_catalog(path=old_copy_path)
        self.failIf(brains)

        # New copy path must be in catalog
        brains = self.portal.upfront_versioning_catalog(path=new_copy_path)
        self.failUnless(brains)

    def test_checkout_nested(self):
        """Checkout a folderish item that contains another item"""
        utility = getUtility(IVersioner)
        copy = utility.checkout(self.portal.repository.folder['00000001']['folder-containing-item'])

        # Is contained item published?
        wf = self.portal.portal_workflow
        self.assertEquals(wf.getInfoFor(copy.contained, 'review_state'), 'published')

    def test_references(self):
        """Inspect references on an item after it has been checked out"""
        ddoc = self.portal.repository.ddocument['00000001']['repo-ddocument']
        utility = getUtility(IVersioner)
        copy = utility.checkout(ddoc)
        self.assertEquals(copy.getRelated(), ddoc.getRelated())

def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    suite.addTest(makeSuite(TestCheckout))
    return suite
