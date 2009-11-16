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
    def has_versions(self):
        """Return true if context has versions, false otherwise"""
        vc = getToolByName(self.context, 'upfront_versioning_catalog')
        return len(vc.getVersionsOf(aq_inner(self.context))) > 0

    def jquery(self):
        """The viewlet is potentially slow so load content asynchronously"""
        return '''
        <script type="text/javascript">
        jq(document).ready(
        function()
        {
            jq('#upfront-versioning-versions-viewlet-toggle').click(
                function()
                {
                    var elem = jq('#upfront-versioning-versions-viewlet-content');
                    if (!elem.html())
                    {
                        elem.html('Loading...');
                        jq.get(
                            '%s/@@upfront.versioning-versions-inner', 
                            function(data)
                            {
                                elem.html(data);
                            }
                        );
                    }                        
                }
            );
        }                
        );</script>''' % self.context.absolute_url()

    render = ViewPageTemplateFile("versions.pt")

class VersionsView(BrowserView):
    """A view that is intended to be loaded via ajax. It shows tabled 
    version infomation for the context."""

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
                date=adapted.date,
                url=member.has_permission(View, ob) and brain.getURL() or None,
                title=ob.title,
            )    
            li.append(di)

        # Sort on date, version
        def mysort(a, b):
            if a['date'] == b['date']:
                return cmp(a['version'], b['version'])
            return cmp(a['date'], b['date'])
        li.sort(mysort)            

        return li

    def checkedin_versions(self):
        return [v for v in self.versions() if v['state'] == 'checked_in']

    def checkedout_versions(self):
        return [v for v in self.versions() if v['state'] == 'checked_out']

