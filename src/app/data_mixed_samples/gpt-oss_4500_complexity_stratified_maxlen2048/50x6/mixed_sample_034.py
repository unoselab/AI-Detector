# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line3854_lm, name=face_index) ===
def face_index(vertices):
    """Takes an MxNx3 array and returns a 2D vertices and MxN face_indices arrays"""
    import numpy as np

    arr = np.asarray(vertices)
    if arr.ndim != 3 or arr.shape[2] != 3:
        raise ValueError("Input must be an MxNx3 array")
    M, N, _ = arr.shape
    vertices_2d = arr.reshape(-1, 3)
    face_indices = np.arange(M * N, dtype=int).reshape(M, N)
    return vertices_2d, face_indices

# === BLOCK 2 (label=human, source_idx=line329_human, name=add_route) ===
def add_route(config, name, pattern, *args, **kwargs):
    """
    Adds a pyramid route to the config. All args and kwargs will be
    passed on to config.add_route.

    This exists so the default behaviour of including crabpy will still be to
    cache all crabpy routes.
    """
    config.add_route(name, pattern, *args, **kwargs)
    GENERATE_ETAG_ROUTE_NAMES.add(name)

# === BLOCK 3 (label=lm, source_idx=line5080_lm, name=assertFileSizeNotEqual) ===
def assertFileSizeNotEqual(self, filename, size, msg=None):
        """Fail if ``filename`` has the given ``size`` as determined
        by the '!=' operator.

        Parameters
        ----------
        filename : str, bytes, file-like
        size : int, float
        msg : str
            If not provided, the :mod:`marbles.mixins` or
            :mod:`unittest` standard message will be used.

        Raises
        ------
        TypeError
            If ``filename`` is not a str or bytes object and is not
            file-like.
        """

# === BLOCK 4 (label=human, source_idx=line1742_human, name=set_attachments_order) ===
def set_attachments_order(self, order):
        """Remember the attachments order
        """
        # append single uids to the order
        if isinstance(order, basestring):
            new_order = self.storage.get("order", [])
            new_order.append(order)
            order = new_order
        self.storage.update({"order": order})

# === BLOCK 5 (label=human, source_idx=line4512_human, name=parse_geo_box) ===
def parse_geo_box(geo_box_str):
    """
    parses [-90,-180 TO 90,180] to a shapely.geometry.box
    :param geo_box_str:
    :return:
    """

    from_point_str, to_point_str = parse_solr_geo_range_as_pair(geo_box_str)
    from_point = parse_lat_lon(from_point_str)
    to_point = parse_lat_lon(to_point_str)
    rectangle = box(from_point[0], from_point[1], to_point[0], to_point[1])
    return rectangle

# === BLOCK 6 (label=lm, source_idx=line2548_lm, name=add_listener) ===
def add_listener(self, event, callback, once=False):
    """
    Register a *callback* for the specified *event*. The function will be
    called with the #Job as its first argument. If *once* is #True, the
    listener will be removed after it has been invoked once or when the
    job is re-started.

    Note that if the event already ocurred, *callback* will be called
    immediately!

    # Arguments
    event (str, list of str): The name or multiple names of an event, or None
      to register the callback to be called for any event.
    callback (callable): A function.
    once (bool): Whether the callback is valid only once.
    """
