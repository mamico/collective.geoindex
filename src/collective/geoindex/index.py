# https://github.com/Toblerity/zope.index.rtree

from .datamanager import DataManager
from .storage import Storage
from AccessControl.class_init import InitializeClass
from App.special_dtml import DTMLFile
from BTrees.IIBTree import IISet
from logging import getLogger
from OFS.PropertyManager import PropertyManager
from persistent.dict import PersistentDict
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PluginIndexes.interfaces import IQueryIndex
from Products.PluginIndexes.unindex import UnIndex
from rtree.index import Property
from rtree.index import Rtree
from zope.interface import implementer
from zope.schema import Int

import BTrees
import transaction


# from zope.schema import Bool
# from zope.schema import Text
# from Products.ZCatalog.query import IndexQuery
# from Products.PluginIndexes.interfaces import ISortIndex
# from Products.PluginIndexes.interfaces import IUniqueValueIndex
# from zope.indexer.interfaces import IInjection
# from zope.indexer.interfaces import IStatistics
# from zope.indexer.interfaces import IIndexSearch
# from Products.PluginIndexes.util import safe_callable
# from ZODB.POSException import ConflictError
# from BTrees.IIBTree import difference
# from zope.interface import Interface


LOG = getLogger("collective.geoindex")
_marker = object()


class IGeospatialIndex(IQueryIndex):
    # (IInjection, IStatistics, IIndexSearch):
    # TODO
    # attr_recurdef = Text(
    #     title=u"Attribute- or fieldname of recurrence rule definition."
    #           u"RFC2445 compatible string or timedelta."
    # )
    # attr_until = Text(
    #     title=u"Attribute- or fieldname of until date (optional)."
    # )

    dimension = Int(
        title="Dimension",
        description="Number of dimensions in the spatial index.",
        default=2,
        readonly=True,
    )

    leaf_capacity = Int(
        title="Leaf capacity",
        description="Maximum number of entries in a leaf node.",
        default=20,
    )


@implementer(IGeospatialIndex)
class GeospatialIndex(UnIndex, PropertyManager):
    """Index for dates with recurrence support."""

    meta_type = "GeospatialIndex"
    zmi_icon = "fas fa-info-circle"

    operators = ("intersection", "nearest")
    useOperator = "intersection"
    query_options = ("query", "operator", "limit")

    default_family = BTrees.family32

    manage_main = PageTemplateFile("www/manageDRIndex", globals())
    manage_browse = DTMLFile("www/browseIndex", globals())

    # TODO: for that, this has to be a DTMLFile?
    # manage_main._setName('manage_main')
    manage_options = (
        {"label": "Settings", "action": "manage_main"},
        {"label": "Browse", "action": "manage_browse"},
    ) + PropertyManager.manage_options

    def __init__(self, id, ignore_ex=None, call_methods=None, extra=None, caller=None):
        """Initialize the index
        @ param extra.recurdef:
        @ param extral.until:

            Init. settings provide many means to customize the spatial tree.
            E.g. setting leaf_capacity and near_minimum_overlap_factor to "good"
            values can help to reduce the possibility of write conflict errors.

            Below is a list of the currently available properties. For more info
            about these and other properties see the rtree docs and/or code.

                writethrough
                buffering_capacity
                pagesize
                leaf_capacity
                near_minimum_overlap_factor
                type
                variant
                dimension
                index_capacity
                index_pool_capacity
                point_pool_capacity
                region_pool_capacity
                tight_mbr
                fill_factor
                split_distribution_factor
                tpr_horizon
                reinsert_factor

            If you supply an initialValuesGenerator you can build a spatial index
            from initial values. This is much faster than doing repeated insert()s.
        """
        settings = dict(
            dimension=extra.dimension,
            leaf_capacity=extra.leaf_capacity,
            pagesize=4096,
            near_minimum_overlap_factor=20,
            writethrough=False,
            buffering_capacity=100,
        )
        self.family = self.default_family
        self.settings = PersistentDict(settings)
        self.pageData = self.family.IO.BTree()  # here we save the actual rtree data in
        self.idToCoordinates = (
            self.family.IO.BTree()
        )  # we need to know the coordinates for each objectid to be able to delete it

        # this creates the tree and creates header and root pages
        # self._getTree( initialValuesGenerator )
        self._getTree(None)
        UnIndex.__init__(
            self, id, ignore_ex=None, call_methods=None, extra=None, caller=None
        )

    def is_coordinates(self, value):
        """:param coordinates: This may be an object that satisfies the numpy array
        protocol, providing the index's dimension * 2 coordinate
        pairs representing the `mink` and `maxk` coordinates in
        each dimension defining the bounds of the query window.
        """
        dimension = self.settings["dimension"]
        return (
            isinstance(value, (list, tuple))
            and len(value) == dimension * 2
            and all(isinstance(v, (int, float)) for v in value)
            and all(value[i] <= value[i + dimension] for i in range(0, dimension))
        )

    def query_index(self, record, resultset=None):
        """See IPluggableIndex.

        o Unpacks record from catalog and map onto '_search'.
        """
        operator = record.operator

        if operator == "intersection":
            return IISet(self.intersection(record.keys))
        elif operator == "nearest":
            return IISet(self.nearest(record.keys, num_results=record.get("limit")))
        else:
            raise ValueError("Invalid operator: %s" % operator)

    def _index_object(self, documentId, obj, threshold=None, attr=""):
        """Inserts object with bounds into this index. Returns the added item."""

        returnStatus = 0
        datum = self._get_object_datum(obj, attr)
        oldDatum = self._unindex.get(documentId, _marker)
        if datum != oldDatum:
            # if oldDatum is not _marker:
            #     self.removeForwardIndexEntry(oldDatum, documentId, check=False)
            #     if datum is _marker:
            #         try:
            #             del self._unindex[documentId]
            #             self._length.change(-1)
            #         except ConflictError:
            #             raise
            #         except Exception:
            #             LOG.error('Should not happen: oldDatum was there, now '
            #                       'its not, for document with id %s',
            #                       documentId)

            if datum is not _marker:
                # self.insertForwardIndexEntry(datum, documentId)
                self._registerDataManager()

                if self.is_coordinates(datum):
                    self.tree.add(documentId, datum)
                elif isinstance(datum, (list, tuple)):
                    for d in datum:
                        assert self.is_coordinates(d)
                        self.tree.add(documentId, d)
                else:
                    assert False, "Invalid datum: %s" % datum
                # ???
                self.idToCoordinates[documentId] = datum
                self._length.change(1)

            returnStatus = 1

        return returnStatus

    # def unindex_object(self, documentId):
    #     """ Carefully unindex the object with integer id 'documentId'"""
    #     values = self._unindex.get(documentId, _marker)
    #     if values is _marker:
    #         return None

    #     for value in values:
    #         self.removeForwardIndexEntry(value, documentId)

    #     try:
    #         del self._unindex[documentId]
    #     except ConflictError:
    #         raise
    #     except Exception:
    #         LOG.debug('Attempt to unindex nonexistent document'
    #                   ' with id %s' % documentId, exc_info=True)

    # def _convert(self, value, default=None):
    #     """Convert record keys/datetimes into int representation.
    #     """
    #     return dt2int(value) or default

    def unindex_doc(self, docid):
        """Deletes an item from this index"""
        self._registerDataManager()
        try:
            coordinates = self.idToCoordinates.pop(docid)
        except KeyError:
            # docid was not indexed
            return
        self.tree.delete(docid, coordinates)

    def clear(self):
        self._clearBuffer(True)
        del self._v_tree
        self.pageData.clear()
        self.idToCoordinates.clear()
        self._getTree()  # this creates the tree and creates header and root pages
        UnIndex.clear(self)

    def documentCount(self):
        """See interface IStatistics"""
        return len(
            self.idToCoordinates
        )  # Could use BTree.Len() instead for better performance

    def wordCount(self):
        """See interface IStatistics"""
        return 0  # no meaning really

    def apply(self, queryName, *args, **keys):
        queryFunc = getattr(self, queryName)
        generator = queryFunc(*args, **keys)
        return self.family.IF.Set(generator)

    # query methods
    def count(self, coordinates):
        """Counts the number of objects within coordinates"""
        self._registerDataManager()
        count = self.tree.count(coordinates)
        if self.family == BTrees.family32:
            count = int(count)
        return count

    def intersection(self, coordinates):
        """Returns all docids which are within the given bounds."""
        self._registerDataManager()
        tree = self.tree
        if self.family == BTrees.family32:
            for id in tree.intersection(coordinates, objects=False):
                yield int(id)
        else:
            for id in tree.intersection(coordinates, objects=False):
                yield id

    def nearest(self, coordinates, num_results=1):
        """Returns the num_results docids which are closest to coordinates"""
        self._registerDataManager()
        tree = self.tree
        if self.family == BTrees.family32:
            for id in tree.nearest(coordinates, num_results, objects=False):
                yield int(id)
        else:
            for id in tree.nearest(coordinates, num_results, objects=False):
                yield id

    def leaves(self):
        """Returns all leaves in the tree. A leaf is a tuple (id, child_ids, bounds)"""
        self._registerDataManager()
        for leaf in self.tree.leaves():
            yield leaf

    def get_bounds(self, coordinate_interleaved=None):
        """Returns the bounds of the whole tree"""
        self._registerDataManager()
        return self.tree.get_bounds(coordinate_interleaved)

    bounds = property(get_bounds)

    # implementation helpers

    def _clearBuffer(self, blockWrites):
        tree = getattr(self, "_v_tree", None)
        if not tree:
            return
        if blockWrites:
            tree.customstorage.blockWrites = True
        # log( 'PRE-CLEAR blockWrites:%s tree:%s bounds:%s' % ( blockWrites, self.tree, self.bounds ) )
        # log( 'PRE-CLEAR' )
        tree.clearBuffer()
        # log( 'POST-CLEAR bounds:%s' % self.bounds )
        # log( 'POST-CLEAR' )
        if blockWrites:
            tree.customstorage.blockWrites = False

    def _registerDataManager(self):
        """This registers a custom data manager to flush all the buffers when
        they are dirty."""
        registered = getattr(self, "_v_dataManagerRegistered", False)
        if registered:
            return
        self._v_dataManagerRegistered = True

        # haha, this is really ugly, but zodb's transaction module sorts
        #  data managers only on commit(). That's not good for us, our data
        #  manager's savepoint/rollback/abort calls need to be executed before
        #  the connection's savepoint/rollback/abort.
        t = transaction.get()
        org_join = t.join

        def join(resource):
            org_join(resource)
            t._resources = sorted(t._resources, key=transaction._transaction.rm_key)
            # t._resources = sorted( t._resources, transaction._transaction.rm_cmp )

        t.join = join
        t.join(DataManager(self))

    def _unregisterDataManager(self):
        self._v_dataManagerRegistered = False

    def _getTree(self, initialValuesGenerator=None):
        """Creates the r-tree if it is not already created yet and returns it"""
        tree = getattr(self, "_v_tree", None)
        if not tree:
            # create r-tree property object
            properties = Property()
            settings = getattr(self, "settings", None)
            if not settings:
                raise ValueError("invalid spatial index")
            # check interleaved setting
            interleaved = settings.pop("interleaved", True)
            for name, value in settings.items():
                if not hasattr(properties, name):
                    raise ValueError('Invalid setting "%s"' % name)
                setattr(properties, name, value)
            # create r-tree storage object
            storage = Storage(
                self.pageData, convertToInt=(self.family == BTrees.family32)
            )
            # create r-tree
            if not initialValuesGenerator:
                tree = Rtree(storage, properties=properties, interleaved=interleaved)
            else:
                tree = Rtree(
                    storage,
                    initialValuesGenerator,
                    properties=properties,
                    interleaved=interleaved,
                )
            self._v_tree = tree
        else:
            if initialValuesGenerator:
                raise ValueError(initialValuesGenerator)

        return tree

    tree = property(_getTree)


manage_addIndexForm = DTMLFile("www/addIndex", globals())


def manage_addIndex(self, id, extra=None, REQUEST=None, RESPONSE=None, URL3=None):
    """Add a Index"""
    return self.manage_addIndex(
        id,
        "GeospatialIndex",
        extra=extra,
        REQUEST=REQUEST,
        RESPONSE=RESPONSE,
        URL1=URL3,
    )


InitializeClass(GeospatialIndex)
