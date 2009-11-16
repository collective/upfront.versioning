from zope.interface import Interface
from zope import schema
from zope.component import adapts
from zope.interface import implements
from zope.schema.vocabulary import SimpleVocabulary
from zope.formlib.form import FormFields, action

from Products.CMFCore.utils import getToolByName
from Products.CMFDefault.formlib.schema import SchemaAdapterBase
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFPlone.interfaces import IPloneSiteRoot
from plone.app.controlpanel.form import ControlPanelForm
from plone.app.controlpanel.widgets import MultiCheckBoxVocabularyWidget

from upfront.versioning import _
from upfront.versioning.interfaces import IVersioningSettings

def portal_types(context):
    items = (('Page','Page'), ('Folder','Folder'))
    return SimpleVocabulary.fromItems(items)

class IVersioningSettingsSchema(Interface):
    versionable_types = schema.Tuple(
        title=_(u'Versionable types'),        
        description=_(u'Specify content types that can be versioned.'),
        required=False,
        missing_value=tuple(),
        value_type=schema.Choice(
            vocabulary='upfront.versioning-portal_types'
        )
    )

class VersioningSettingsConfigletAdapter(SchemaAdapterBase):

    adapts(IPloneSiteRoot)
    implements(IVersioningSettingsSchema)

    def _getUtility(self):
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        sm = portal.getSiteManager()
        return sm.getUtility(IVersioningSettings, 'upfront.versioning-settings')

    def get_versionable_types(self):
        utility = self._getUtility()
        return utility.versionable_types

    def set_versionable_types(self, value):
        utility = self._getUtility()
        utility.versionable_types = value

    versionable_types = property(get_versionable_types, set_versionable_types)

class VersioningSettingsConfiglet(ControlPanelForm):
    """The formlib class for the versioning settings page"""

    form_fields = FormFields(IVersioningSettingsSchema)
    form_fields['versionable_types'].custom_widget = MultiCheckBoxVocabularyWidget

    label = _("Upfront Versioning Settings")
    description = _("")
    form_name = _("Upfront Versioning Settings")

    '''
    def _getUtility(self):
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        sm = portal.getSiteManager()
        return sm.getUtility(IVersioningSettings, 'upfront.versioning-settings')

    @action("submit")
    def action_submit(self, action, data):
        utility = self._getUtility()
        utility.versionable_types = data['versionable_types']

    def getVersionableTypes(self):
        utility = self._getUtility()
        return utility.versionable_types

    form_fields['versionable_types'].get_rendered = getVersionableTypes
    '''
