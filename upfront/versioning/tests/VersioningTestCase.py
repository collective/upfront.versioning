import transaction
from zope import event
from zope.component import getUtility
from Testing import ZopeTestCase

from Products.CMFPlone.utils import _createObjectByType
from Products.CMFPlone.tests import PloneTestCase
from Products.PloneTestCase.ptc import setupPloneSite
from Products.PloneTestCase.setup import _createHomeFolder

from upfront.versioning.interfaces import IVersioner

PloneTestCase.installProduct('upfront.versioning')
setupPloneSite(extension_profiles=['upfront.versioning:default'])

class VersioningTestCase(PloneTestCase.PloneTestCase):
    
    def afterSetUp(self):
        PloneTestCase.PloneTestCase.afterSetUp(self)
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
