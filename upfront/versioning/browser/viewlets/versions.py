from Acquisition import aq_inner
from zope.interface import implements
from zope.viewlet.interfaces import IViewlet

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import View
from plone.memoize.instance import memoize

from upfront.versioning.interfaces import IVersionMetadata

class VersionsViewlet(BrowserView):
    implements(IViewlet)
  
    def __init__(self, context, request, view, manager):
        self.context = context
        self.request = request
        self.__parent__ = view
        self.manager = manager

    def update(self):
        pass

    @memoize
    def versions(self):
        """Return versions info as a list of dictionaries"""
        vc = getToolByName(self.context, 'upfront_versioning_catalog')
        pms = getToolByName(self.context, 'portal_membership')
        member = pms.getAuthenticatedMember()
        li = []
        for brain in vc.getVersionsOf(aq_inner(self.context)):
            ob = brain.getObject()
            adapted = IVersionMetadata(ob)
            di = dict(
                state=adapted.state,
                owner=ob.getOwner(),
                version=adapted.version,
                url=member.has_permission(View, ob) and brain.getURL() or None,
                title=ob.title,
            )    
            li.append(di)
        return li

    render = ViewPageTemplateFile("versions.pt")
