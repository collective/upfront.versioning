from zope.interface import implements

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.browser.interfaces import INavigationBreadcrumbs
from Products.CMFPlone.browser.navigation import PhysicalNavigationBreadcrumbs

from upfront.versioning import _
from upfront.versioning.interfaces import IVersionMetadata

class VersionFolderPhysicalNavigationBreadcrumbs(PhysicalNavigationBreadcrumbs):
    implements(INavigationBreadcrumbs)

    def breadcrumbs(self):
        result = PhysicalNavigationBreadcrumbs.breadcrumbs(self)
        if not result:
            return result

        # Override last element
        vc = getToolByName(self.context, 'upfront_versioning_catalog')
        latest = vc.getLatestVersionOf(self.context)
        if self.context == latest:
            result[-1]['Title'] = _('Latest')
        else:
            result[-1]['Title'] = '#%s' % IVersionMetadata(self.context).version
        return result
