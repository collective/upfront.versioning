import unittest
from zope.interface import alsoProvides
from zope.component import getUtility

from Products.CMFPlone.utils import _createObjectByType
from Products.PloneTestCase.setup import _createHomeFolder

from upfront.versioning.interfaces import IVersioner, ICheckedOut, ICheckedIn, \
    IVersionMetadata
from upfront.versioning.tests.VersioningTestCase import VersioningTestCase

class TestStartNewVersion(VersioningTestCase):

    def afterSetUp(self):
        VersioningTestCase.afterSetUp(self) 

    def test_can_checkout(self):
        """Can item be checked out?"""
        utility = getUtility(IVersioner)
        workspace = self.getWorkspace()

        # We do not have Modify Portal Content permission
        self.failIf(utility.can_start_new_version(self.portal.news))

        # Unversioned and we have Modify Portal Content permission
        self.failUnless(utility.can_start_new_version(workspace['a-document-unversioned']))

        # Versioned and we have Modify Portal Content permission
        self.failUnless(utility.can_start_new_version(workspace['a-document']['00000001']))

        # Versioned and we have Modify Portal Content permission, but already 
        # checked out.
        self.failIf(utility.can_start_new_version(workspace['a-document']['00000002']))

    def test_unversioned(self):
        """Item is not yet versioned. Make it so."""
        utility = getUtility(IVersioner)
        workspace = self.getWorkspace()

        version2 = utility.start_new_version(workspace['a-document-unversioned'])

        # Was version1 created?
        self.failUnless('00000001' in version2.aq_parent.objectIds('ATDocument'))

        version1 = version2.aq_parent['00000001']

        # Version1 tests

        # Is there a VersionFolder with id a-document-unversioned in workspace?
        self.failUnless('a-document-unversioned' in workspace.objectIds('VersionFolder'))

        # Is it a child of the VersionFolder?
        self.assertEquals(workspace['a-document-unversioned']['00000001'], version1)

        # Is interface provided?
        self.failUnless(ICheckedIn.providedBy(version1))

        # Is interface not provided?
        self.failIf(ICheckedOut.providedBy(version1))
       
        # Check metadata
        adapted = IVersionMetadata(version1)
        self.assertEquals(adapted.token, version1.UID())
        self.assertEquals(adapted.state, 'checked_in')
        self.assertEquals(adapted.version, 1)

        # Is it in versioning catalog?
        vc = self.portal.upfront_versioning_catalog
        brains = vc(
            path='/'.join(version1.getPhysicalPath()), 
            token=version1.UID(),
            state='checked_in'
        )
        self.failUnless(brains)      

        # Is it in portal catalog?
        pc = self.portal.portal_catalog
        brains = pc(
            path='/'.join(version1.getPhysicalPath()), 
        )
        self.failUnless(brains)      

        # Is it published?
        wf = self.portal.portal_workflow
        self.assertEquals(wf.getInfoFor(version1, 'review_state'), 'published')

        # Version2 tests

        # Is interface provided?
        self.failUnless(ICheckedOut.providedBy(version2))

        # Is interface not provided?
        self.failIf(ICheckedIn.providedBy(version2))
       
        # Check metadata
        adapted = IVersionMetadata(version2)
        self.assertEquals(adapted.token, version1.UID())
        self.assertEquals(adapted.state, 'checked_out')
        self.assertEquals(adapted.version, 2)

        # Is it in version catalog?
        vc = self.portal.upfront_versioning_catalog
        brains = vc(
            path='/'.join(version2.getPhysicalPath()), 
            token=version1.UID(),
            state='checked_out'
        )
        self.failUnless(brains)      

        # Is it published?
        wf = self.portal.portal_workflow
        self.assertEquals(wf.getInfoFor(version2, 'review_state'), 'published')

    def test_versioned(self):
        """Item is versioned. Start a new version. test_unversioned already 
        does most of the tests."""
        utility = getUtility(IVersioner)
        workspace = self.getWorkspace()
        
        copy = utility.start_new_version(workspace['a-document']['00000001'])
            
        # Check metadata
        adapted = IVersionMetadata(copy)
        self.assertEquals(adapted.version, 3)
   
    def test_delete(self):
        """Item is versioned and deleted"""
        utility = getUtility(IVersioner)
        workspace = self.getWorkspace()

        copy = workspace['a-document']['00000001']
        copy_path = '/'.join(copy.getPhysicalPath())
        copy.aq_parent.manage_delObjects([copy.id])

        # Item may not be in catalog anymore
        brains = self.portal.upfront_versioning_catalog(path=copy_path)
        self.failIf(brains)

    def test_checkout_move(self):
        """Item is versioned and moved"""
        utility = getUtility(IVersioner)
        workspace = self.getWorkspace()

        copy = workspace['a-document']['00000001']
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
        """Version a folderish item that contains another item"""
        utility = getUtility(IVersioner)
        workspace = self.getWorkspace()

        copy = workspace['folder-containing-item']['00000001']

        # Is contained item still published?
        wf = self.portal.portal_workflow
        self.assertEquals(wf.getInfoFor(copy.contained, 'review_state'), 'published')

    def test_references(self):
        """Inspect references on a new version"""
        utility = getUtility(IVersioner)
        workspace = self.getWorkspace()

        # keepReferencesOnCopy is set for DDocument.related so Archetypes
        # handles the reference preservation.
        original = workspace['a-ddocument-unversioned']
        original_related = original.getRelated()

        version2 = utility.start_new_version(original)
        version1 = version2.aq_parent['00000001']

        self.assertEquals(original_related, version1.getRelated())
        self.assertEquals(original_related, version2.getRelated())

        # keepReferencesOnCopy is not set for Document.relatedItems so we
        # handle the reference preservation.
        original = workspace['a-document-unversioned']
        original_related = original.getRelatedItems()

        version2 = utility.start_new_version(original)
        version1 = version2.aq_parent['00000001']

        self.assertEquals(original_related, version1.getRelatedItems())
        self.assertEquals(original_related, version2.getRelatedItems())

def test_suite():
    from unittest import TestSuite, makeSuite

    suite = TestSuite()
    suite.addTest(makeSuite(TestStartNewVersion))
    return suite
