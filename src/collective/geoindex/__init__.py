def initialize(context):
    # Products.* initialization code is Automatically called by Zope
    from . import index

    context.registerClass(
        index.GeoIndex,
        permission="Add Pluggable Index",
        constructors=(index.manage_addDRIndexForm, index.manage_addDRIndex),
        icon="www/index.gif",
        visibility=None,
    )
