import transaction, unittest
from zope.component import getUtility
from Testing import ZopeTestCase as ztc 

from Products.Five import zcml
from Products.CMFPlone.utils import _createObjectByType
from Products.PloneTestCase.setup import _createHomeFolder
from Products.PloneTestCase import PloneTestCase as ptc 
from Products.PloneTestCase.layer import onsetup

import upfront.versioning
from upfront.versioning.interfaces import IVersioner

@onsetup
def setup_product():
    zcml.load_config('configure.zcml', upfront.versioning)
    zcml.load_config('overrides.zcml', upfront.versioning)

setup_product()
ptc.setupPloneSite(extension_profiles=['upfront.versioning:default'])

class VersioningTestCase(ptc.PloneTestCase):
    
    def afterSetUp(self):
        ptc.PloneTestCase.afterSetUp(self)
        utility = getUtility(IVersioner)
        fti = self.portal.portal_types.getTypeInfo('Document')

        # Create documents in site root as admin
        self.loginAsPortalOwner()
        for id, transition in (
            ('root-private', None),
            ('root-published', 'publish'),
            ('repo-admin', 'publish'),
            ):
            ob = _createObjectByType('Document', self.portal, id)
            fti._finishConstruction(ob)
            if transition is not None:
                self.portal.portal_workflow.doActionFor(ob, transition)

        # We need to commit here so that _p_jar isn't None and move will work
        transaction.savepoint(optimistic=True)

        # Add repo-admin to repo while logged in as admin
        utility.add_to_repository(self.portal['repo-admin'])

        # Add a site member
        uf = self.portal.acl_users
        uf._doAddUser('member', 'secret', ['Member'], [])

        # Login as the member
        self.login('member')
        _createHomeFolder(self.portal, 'member', take_ownership=0)
        workspace = utility.getWorkspace(self.portal)

        # Create documents in workspace as member
        for id, transition in (
            ('repo-member', None),
            ):
            ob = _createObjectByType('Document', workspace, id)
            fti._finishConstruction(ob)
            if transition is not None:
                self.portal.portal_workflow.doActionFor(ob, transition)
        transaction.savepoint(optimistic=True)

        # Add repo-member to repo while logged in as member
        utility.add_to_repository(workspace['repo-member'])
