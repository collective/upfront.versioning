from Acquisition import aq_inner
from zope.component import getUtility

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName

from upfront.versioning.interfaces import IVersioner
from upfront.versioning import _

class VersioningView(BrowserView):
    """
    """

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
