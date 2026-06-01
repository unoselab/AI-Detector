# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line519_human, name=receive) ===
def receive(self, msg):
        """
        Message dispatching function. This function accepts any PaxosMessage subclass and calls
        the appropriate handler function
        """
        handler = getattr(self, 'receive_' + msg.__class__.__name__.lower(), None)
        if handler is None:
            raise InvalidMessageError('Receiving class does not support messages of type: ' + msg.__class__.__name__)
        return handler(msg)

# === BLOCK 2 (label=lm, source_idx=line2031_lm, name=subontology) ===
def subontology(self, nodes=None, minimal=False, relations=None):
        """
        Return a new ontology that is an extract of this one

        Arguments
        ---------
        - nodes: list
            list of node IDs to include in subontology. If None, all are used
        - relations: list
            list of relation IDs to include in subontology. If None, all are used

        """

# === BLOCK 3 (label=lm, source_idx=line3201_lm, name=add_md) ===
def add_md(text, s, level=0):
    """Adds text to the readme at the given level"""
    if isinstance(text, list):
        lines = text
    else:
        lines = text.splitlines()
    if level > 0:
        heading = f"{'#' * level} {s}"
        lines.append(heading)
    else:
        lines.append(s)
    return lines if isinstance(text, list) else "\n".join(lines)

# === BLOCK 4 (label=lm, source_idx=line3016_lm, name=nuc_v) ===
def nuc_v(msg):
    """Calculate NUCv, Navigation Uncertainty Category - Velocity (ADS-B version 1)

    Args:
        msg (string): 28 bytes hexadecimal message string,

    Returns:
        int or string: 95% Horizontal Velocity Error
        int or string: 95% Vertical Velocity Error
    """

# === BLOCK 5 (label=human, source_idx=line4724_human, name=css) ===
def css(self, mapping=None):
        """Update the css dictionary if ``mapping`` is a dictionary, otherwise
        return the css value at ``mapping``.

        If ``mapping`` is not given, return the whole ``css`` dictionary
        if available.
        """
        css = self._css
        if mapping is None:
            return css
        elif isinstance(mapping, Mapping):
            if css is None:
                self._extra['css'] = css = {}
            css.update(mapping)
            return self
        else:
            return css.get(mapping) if css else None

# === BLOCK 6 (label=human, source_idx=line4646_human, name=search_registered_query_deleted_for_facet) ===
def search_registered_query_deleted_for_facet(self, facet, **kwargs):  # noqa: E501
        """Lists the values of a specific facet over the customer's deleted derived metric definitions  # noqa: E501

          # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.search_registered_query_deleted_for_facet(facet, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str facet: (required)
        :param FacetSearchRequestContainer body:
        :return: ResponseContainerFacetResponse
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        if kwargs.get('async_req'):
            return self.search_registered_query_deleted_for_facet_with_http_info(facet, **kwargs)  # noqa: E501
        else:
            (data) = self.search_registered_query_deleted_for_facet_with_http_info(facet, **kwargs)  # noqa: E501
            return data
