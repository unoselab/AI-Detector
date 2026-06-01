# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line2837_lm, name=get_meta) ===
def get_meta(request, pid):
    """MNRead.getSystemMetadata(session, pid) → SystemMetadata."""
    if not request or not pid:
        raise ValueError("Invalid input")
    url = f"https://dataone.org/mn/v2/meta/{pid}"
    response = requests.get(url, headers=request.headers)
    if response.status_code!= 200:
        raise Exception("Failed to retrieve system metadata")
    return response.content

# === BLOCK 2 (label=lm, source_idx=line3320_lm, name=get_resource_type_from_included_serializer) ===
def get_resource_type_from_included_serializer(self):
        """
        Check to see it this resource has a different resource_name when
        included and return that name, or None
        """
        if hasattr(self,'resource_name'):
            return self.resource_name
        return None

# === BLOCK 3 (label=lm, source_idx=line2513_lm, name=run_gevent) ===
def run_gevent(self):
        """Created the server that runs the application supplied a subclass"""
        from gevent.pywsgi import WSGIServer
        http_server = WSGIServer((self.host, self.port), self.app)
        http_server.serve_forever()

# === BLOCK 4 (label=human, source_idx=line886_human, name=get_collection) ===
def get_collection(self, collection, filter=None, fields=None,
            page_size=None):
        """
        Returns a specific collection from the asset service with
        the given collection endpoint.

        Supports passing through parameters such as...
        - filters such as "name=Vesuvius" following GEL spec
        - fields such as "uri,description" comma delimited
        - page_size such as "100" (the default)

        """
        params = {}
        if filter:
            params['filter'] = filter
        if fields:
            params['fields'] = fields
        if page_size:
            params['pageSize'] = page_size

        uri = self.uri + '/v1' + collection
        return self.service._get(uri, params=params)

# === BLOCK 5 (label=human, source_idx=line1259_human, name=inbound_presence_filter) ===
def inbound_presence_filter(f):
    """
    Register the decorated function as a service-level inbound presence filter.

    :raise TypeError: if the decorated object is a coroutine function

    .. seealso::

       :class:`StanzaStream`
          for important remarks regarding the use of stanza filters.

    """

    if asyncio.iscoroutinefunction(f):
        raise TypeError(
            "inbound_presence_filter must not be a coroutine function"
        )

    add_handler_spec(
        f,
        HandlerSpec(
            (_apply_inbound_presence_filter, ())
        ),
    )
    return f

# === BLOCK 6 (label=human, source_idx=line943_human, name=lastPrePrepareSeqNo) ===
def lastPrePrepareSeqNo(self, n):
        """
        This will _lastPrePrepareSeqNo to values greater than its previous
        values else it will not. To forcefully override as in case of `revert`,
        directly set `self._lastPrePrepareSeqNo`
        """
        if n > self._lastPrePrepareSeqNo:
            self._lastPrePrepareSeqNo = n
        else:
            self.logger.debug(
                '{} cannot set lastPrePrepareSeqNo to {} as its '
                'already {}'.format(
                    self, n, self._lastPrePrepareSeqNo))
