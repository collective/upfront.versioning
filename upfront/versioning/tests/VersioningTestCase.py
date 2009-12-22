import transaction, unittest
from zope.component import getUtility
from Testing import ZopeTestCase as ztc 

from Products.Five import zcml
from Products.CMFPlone.utils import _createObjectByType
from Products.PloneTestCase.setup import _createHomeFolder
from Products.PloneTestCase import PloneTestCase as ptc 
from Products.PloneTestCase.layer import onsetup
from Products.GenericSetup import EXTENSION, profile_registry

import upfront.versioning
from upfront.versioning.interfaces import IVersioner, IVersioningSettings

# Register Archetypes sample types
profile_registry.registerProfile('Archetypes_sampletypes',
    'Archetypes Sample Content Types',
    'Extension profile including Archetypes sample content types',
    'profiles/sample_types',
    'Products.Archetypes',
    EXTENSION)

ptc.setupPloneSite(
    extension_profiles=['Products.Archetypes:Archetypes_sampletypes']
)

class VersioningTestCase(ptc.PloneTestCase):
    
    def afterSetUp(self):
        ptc.PloneTestCase.afterSetUp(self)

        # I am ready to kill... from Zope 2.10.4 I have to do this here
        from OFS.Application import install_package
        app = ztc.app()
        install_package(app, upfront.versioning, upfront.versioning.initialize)
        self.addProfile('upfront.versioning:default')

        # Hack persistent utility since we need Folder to be versionable
        sm = self.portal.getSiteManager()
        utility = sm.getUtility(IVersioningSettings, 'upfront.versioning-settings')
        utility.versionable_types = ['Document', 'Folder', 'DDocument']
        
        utility = getUtility(IVersioner)

        # Add a site member
        uf = self.portal.acl_users
        uf._doAddUser('member', 'secret', ['Member'], [])

        # Login as the member
        self.login('member')
        _createHomeFolder(self.portal, 'member', take_ownership=0)

        workspace = self.getWorkspace()

        # Create items in workspace as member
        created = []
        versioned = []
        for portal_type, id, version in (
            ('Document', 'a-document', 1),
            ('Folder', 'folder-containing-item', 1),
            ('DDocument', 'a-ddocument', 1),
            ('Document', 'a-document-unversioned', 0),
            ('Folder', 'folder-containing-item-unversioned', 0),
            ('DDocument', 'a-ddocument-unversioned', 0),
            ):
            ob = _createObjectByType(portal_type, workspace, id)
            fti = self.portal.portal_types.getTypeInfo(portal_type)
            fti._finishConstruction(ob)
            if portal_type == 'DDocument':
                ob.setRelated(self.portal.news)
            if portal_type == 'Document':
                ob.setRelatedItems([self.portal.news])
            created.append(ob)
            if version:
                versioned.append(ob)

        # Create sub-items
        ob = _createObjectByType('Document', workspace['folder-containing-item'], 'contained')
        fti = self.portal.portal_types.getTypeInfo('Document')
        fti._finishConstruction(ob)
        created.append(ob)

        ob = _createObjectByType('Document', workspace['folder-containing-item-unversioned'], 'contained')
        fti = self.portal.portal_types.getTypeInfo('Document')
        fti._finishConstruction(ob)
        created.append(ob)

        # Portal owner must publish the items
        self.loginAsPortalOwner()
        for ob in created:
            self.portal.portal_workflow.doActionFor(ob, 'publish')

        transaction.savepoint(optimistic=True)

        # Subject some items to versioning. The member still has 
        # Modify Portal Content permission thanks to 
        # simple_publication_workflow.
        self.login('member')
        for ob in versioned:
            utility.start_new_version(ob)


    def getWorkspace(self):
        return self.portal.portal_membership.getAuthenticatedMember().getHomeFolder()
