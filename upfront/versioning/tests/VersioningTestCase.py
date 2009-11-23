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

ptc.setupPloneSite()

class VersioningTestCase(ptc.PloneTestCase):
    
    def afterSetUp(self):
        ptc.PloneTestCase.afterSetUp(self)

        # I am ready to kill... from Zope 2.10.4 I have to do this here
        from OFS.Application import install_package
        app = ztc.app()
        install_package(app, upfront.versioning, upfront.versioning.initialize)
        self.addProfile('upfront.versioning:default')

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
        created = []
        for id in ('repo-member',):
            ob = _createObjectByType('Document', workspace, id)
            fti._finishConstruction(ob)
            created.append(ob)

        # Portal owner must publish the item before it can be added to the repo
        self.loginAsPortalOwner()
        for ob in created:
            self.portal.portal_workflow.doActionFor(ob, transition)

        transaction.savepoint(optimistic=True)

        # Add items to repo while logged in as member
        self.login('member')
        for ob in created:
            utility.add_to_repository(ob)
