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

    def can_checkout(self):
        return not ICheckedOut.providedBy(aq_inner(self.context))

    def can_checkin(self):
        return ICheckedOut.providedBy(aq_inner(self.context))

    def checkout(self):
        utility = getUtility(IVersioner)
        obj = utility.checkout(aq_inner(self.context))
        msg = _("The item has been checked out")
        getToolByName(self.context, 'plone_utils').addPortalMessage(
            msg, type='info'
        )
        self.request.response.redirect(obj.absolute_url())

    def checkin(self):
        utility = getUtility(IVersioner)
        obj = utility.checkin(aq_inner(self.context))
        msg = _("The item has been checked in")
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
