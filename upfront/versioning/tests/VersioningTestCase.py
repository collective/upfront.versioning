from zope import event
from Testing import ZopeTestCase

from Products.CMFPlone.tests import PloneTestCase
from Products.PloneTestCase.ptc import setupPloneSite

setupPloneSite(extension_profiles=['upfront.versioning:default'])

class VersioningTestCase(PloneTestCase.PloneTestCase):
    
    def afterSetUp(self):
        PloneTestCase.PloneTestCase.afterSetUp(self)

        # Add a site member
        uf = self.portal.acl_users
        uf._doAddUser('member', 'secret', ['Member'], [])
