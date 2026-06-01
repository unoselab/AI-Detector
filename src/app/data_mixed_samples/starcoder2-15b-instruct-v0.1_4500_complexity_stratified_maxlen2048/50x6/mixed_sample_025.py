# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1749_human, name=_handle_terminate) ===
def _handle_terminate(self, signal_number, _):
        """Handle a signal to terminate."""
        signal_names = {
            signal.SIGINT: 'SIGINT',
            signal.SIGQUIT: 'SIGQUIT',
            signal.SIGTERM: 'SIGTERM',
        }
        message = 'Terminated by {name} ({number})'.format(
            name=signal_names[signal_number], number=signal_number)
        self._shutdown(message, code=128+signal_number)

# === BLOCK 2 (label=human, source_idx=line2128_human, name=mongodb_ensure_index) ===
def mongodb_ensure_index(database_name, collection_name, key):
    """Ensure Index"""

    try:
        mongodb_client_url = getattr(settings, 'MONGODB_CLIENT',
                                 'mongodb://localhost:27017/')
        mc = MongoClient(mongodb_client_url,document_class=OrderedDict)
        dbs = mc[database_name]
        dbc = dbs[collection_name]

        dbc.ensure_index(key)
        # print "success"
        return key

    except:
        # error connecting to mongodb
        # print str(sys.exc_info())
        return str(sys.exc_info())

# === BLOCK 3 (label=lm, source_idx=line4349_lm, name=_extract_proxies) ===
def _extract_proxies(self, ajax_endpoint):

        """ request the xml object """
        response = self._request_xml(ajax_endpoint)
        if response is None:
            return None
        proxies = []
        for proxy in response.findall('proxy'):
            ip = proxy.find('ip').text
            port = proxy.find('port').text
            scheme = proxy.find('scheme').text
            anonymity = proxy.find('anonymity').text
            country = proxy.find('country').text
            proxies.append({
                'ip': ip,
                'port': port,
               'scheme': scheme,
                'anonymity': anonymity,
                'country': country,
            })
        return proxies

# === BLOCK 4 (label=lm, source_idx=line3835_lm, name=Glyph) ===
def Glyph(actor, glyphObj, orientationArray="", 
          scaleByVectorSize=False, c=None, alpha=1):
    """
    At each vertex of a mesh, another mesh - a `'glyph'` - is shown with
    various orientation options and coloring.

    Color can be specfied as a colormap which maps the size of the orientation
    vectors in `orientationArray`.

    :param orientationArray: list of vectors, ``vtkAbstractArray``
        or the name of an already existing points array.
    :type orientationArray: list, str, vtkAbstractArray
    :param bool scaleByVectorSize: glyph mesh is scaled by the size of
        the vectors.

    .. hint:: |glyphs| |glyphs.py|_

        |glyphs_arrow| |glyphs_arrow.py|_
    """
    if not orientationArray:
        return
    if scaleByVectorSize:
        glyphObj.SetScaleModeToScaleByVector()
    else:
        glyphObj.SetScaleModeToDataScalingOff()
    if c is not None:
        glyphObj.SetColorModeToColorByScalar()
        glyphObj.GetGlyphTransform().SetScale(c)
    glyphObj.SetOpacity(alpha)
    glyphObj.Update()

# === BLOCK 5 (label=lm, source_idx=line2216_lm, name=debug_layer) ===
def debug_layer(self, layer, check_fields=True, add_to_datastore=None):
        """Write the layer produced to the datastore if debug mode is on.

        :param layer: The QGIS layer to check and save.
        :type layer: QgsMapLayer

        :param check_fields: Boolean to check or not inasafe_fields.
            By default, it's true.
        :type check_fields: bool

        :param add_to_datastore: Boolean if we need to store the layer. This
            parameter will overwrite the debug mode behaviour. Default to None,
            we usually let debug mode choose for us.
        :param add_to_datastore: bool

        :return: The name of the layer added in the datastore.
        :rtype: basestring
        """
        if add_to_datastore is None:
            add_to_datastore = self.debug_mode
        if add_to_datastore:
            if check_fields:
                inasafe_fields = ['uid', 'geometry', 'name', 'description']
                layer_fields = [field.name() for field in layer.fields()]
                missing_fields = set(inasafe_fields) - set(layer_fields)
                if missing_fields:
                    raise RuntimeError(
                        'Missing fields: {0}'.format(missing_fields))
            layer_name = layer.name()
            self.datastore.add_layer(layer)
            return layer_name
        else:
            return None

# === BLOCK 6 (label=human, source_idx=line2493_human, name=monitor) ===
def monitor(self, name, cb, request=None, notify_disconnect=False, queue=None):
        """Create a subscription.

        :param str name: PV name string
        :param callable cb: Processing callback
        :param request: A :py:class:`p4p.Value` or string to qualify this request, or None to use a default.
        :param bool notify_disconnect: In additional to Values, the callback may also be call with instances of Exception.
                                       Specifically: Disconnected , RemoteError, or Cancelled
        :param WorkQueue queue: A work queue through which monitor callbacks are dispatched.
        :returns: a :py:class:`Subscription` instance

        The callable will be invoked with one argument which is either.

        * A p4p.Value (Subject to :py:ref:`unwrap`)
        * A sub-class of Exception (Disconnected , RemoteError, or Cancelled)
        """
        R = Subscription(self, name, cb, notify_disconnect=notify_disconnect, queue=queue)

        R._S = super(Context, self).monitor(name, R._event, request)
        return R
