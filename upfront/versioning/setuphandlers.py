from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import _createObjectByType

import logging
logger = logging.getLogger('upfront.versioning')

def postInstall(context):
    site = context.getSite()

    # Create repository
    if 'repository' not in site.objectIds():
        folder = _createObjectByType(
            'Large Plone Folder', site, 'repository', title='Repository'
        )
        # Publish it
        site.portal_workflow.doActionFor(folder, 'publish')
