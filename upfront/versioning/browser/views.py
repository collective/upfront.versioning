from Acquisition import aq_inner
from zope.component import getUtility

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
from plone.app.contentmenu.menu import WorkflowMenu as BaseWorkflowMenu

from upfront.versioning.interfaces import IVersioner, ICheckedOut
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

class WorkflowMenu(BaseWorkflowMenu):
    """Override to return an empty workflow menu for items that are
    checked out."""

    def getMenuItems(self, context, request):
        if ICheckedOut.providedBy(context):
            return []
        return BaseWorkflowMenu.getMenuItems(self, context, request)    
