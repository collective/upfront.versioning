from Acquisition import aq_inner
from zope.component import getUtility

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
from plone.app.contentmenu.menu import WorkflowSubMenuItem \
    as BaseWorkflowSubMenuItem
from plone.memoize.instance import memoize

from upfront.versioning.interfaces import IVersioner, ICheckedOut, ICheckedIn
from upfront.versioning import _

class VersioningView(BrowserView):
    """
    """

    def can_start_new_version(self):
        utility = getUtility(IVersioner)
        return utility.can_start_new_version(aq_inner(self.context))

    def can_commit(self):
        utility = getUtility(IVersioner)
        return utility.can_commit(aq_inner(self.context))

    def start_new_version(self):
        utility = getUtility(IVersioner)
        obj = utility.start_new_version(aq_inner(self.context))
        msg = _("You have started a new version")
        getToolByName(self.context, 'plone_utils').addPortalMessage(
            msg, type='info'
        )
        self.request.response.redirect(obj.absolute_url())            

    def commit(self):
        utility = getUtility(IVersioner)
        obj = utility.checkin(aq_inner(self.context))
        msg = _("The item has been committed")
        getToolByName(self.context, 'plone_utils').addPortalMessage(
            msg, type='info'
        )
        self.request.response.redirect(obj.absolute_url())            

class WorkflowSubMenuItem(BaseWorkflowSubMenuItem):
    """Override availability of workflow menu item."""

    @memoize
    def available(self):
        """If ICheckedOut is provided by context then return empty list. 
        If ICheckedIn is provided and context is not the latest version 
        return empty list, else default."""
        if ICheckedOut.providedBy(self.context):
            return []

        if ICheckedIn.providedBy(self.context):
            vc = getToolByName(self.context, 'upfront_versioning_catalog')
            ob = vc.getLatestVersionOf(self.context)
            if ob != self.context:
                return []

        return BaseWorkflowSubMenuItem.available(self)
