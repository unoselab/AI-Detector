# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line4233_human, name=_read_models) ===
def _read_models(self, graph):
        """
        Read graph and add models to document
        """
        for e in self._get_elements(graph, SBOL.Model):
            identity = e[0]
            m = self._get_rdf_identified(graph, identity)
            m['source'] = self._get_triplet_value(graph, identity, SBOL.source)
            m['language'] = self._get_triplet_value(graph, identity, SBOL.language)
            m['framework'] = self._get_triplet_value(graph, identity, SBOL.framework)
            obj = Model(**m)
            self._models[identity.toPython()] = obj
            self._collection_store[identity.toPython()] = obj

# === BLOCK 2 (label=human, source_idx=line3945_human, name=_set_defaults) ===
def _set_defaults(self):
        """
        Set configuration parameters for drawing guide
        """
        valid_locations = {'top', 'bottom', 'left', 'right'}
        horizontal_locations = {'left', 'right'}
        get_property = self.theme.themeables.property
        margin_location_lookup = {'t': 'b', 'b': 't',
                                  'l': 'r', 'r': 'l'}

        # label position
        self.label_position = self.label_position or 'right'
        if self.label_position not in valid_locations:
            msg = "label position '{}' is invalid"
            raise PlotnineError(msg.format(self.label_position))

        # label margin
        # legend_text_legend or legend_text_colorbar
        name = 'legend_text_{}'.format(
            self.__class__.__name__.split('_')[-1])
        loc = margin_location_lookup[self.label_position[0]]
        try:
            margin = get_property(name, 'margin')
        except KeyError:
            self._label_margin = 3
        else:
            self._label_margin = margin.get_as(loc, 'pt')

        # direction of guide
        if self.direction is None:
            if self.label_position in horizontal_locations:
                self.direction = 'vertical'
            else:
                self.direction = 'horizontal'

        # title position
        if self.title_position is None:
            if self.direction == 'vertical':
                self.title_position = 'top'
            elif self.direction == 'horizontal':
                self.title_position = 'left'
        if self.title_position not in valid_locations:
            msg = "title position '{}' is invalid"
            raise PlotnineError(msg.format(self.title_position))

        # title alignment
        tmp = 'left' if self.direction == 'vertical' else 'center'
        self._title_align = self._default('legend_title_align', tmp)

        # by default, direction of each guide depends on
        # the position all the guides
        try:
            position = get_property('legend_position')
        except KeyError:
            position = 'right'

        if position in {'top', 'bottom'}:
            tmp = 'horizontal'
        else:  # left, right, (default)
            tmp = 'vertical'
        self.direction = self._default('legend_direction', tmp)

        # title margin
        loc = margin_location_lookup[self.title_position[0]]
        try:
            margin = get_property('legend_title', 'margin')
        except KeyError:
            self._title_margin = 8
        else:
            self._title_margin = margin.get_as(loc, 'pt')

        # legend_margin
        try:
            self._legend_margin = get_property('legend_margin')
        except KeyError:
            self._legend_margin = 10

        # legend_entry_spacing
        try:
            self._legend_entry_spacing_x = get_property(
                'legend_entry_spacing_x')
        except KeyError:
            self._legend_entry_spacing_x = 5

        try:
            self._legend_entry_spacing_y = get_property(
                'legend_entry_spacing_y')
        except KeyError:
            self._legend_entry_spacing_y = 2

# === BLOCK 3 (label=lm, source_idx=line5025_lm, name=Process) ===
def Process(self, parser_mediator, zip_file, archive_members):
    """Determines if this is the correct plugin; if so proceed with processing.

    This method checks if the zip file being contains the paths specified in
    REQUIRED_PATHS. If all paths are present, the plugin logic processing
    continues in InspectZipFile.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      zip_file (zipfile.ZipFile): the zip file. It should not be closed in
          this method, but will be closed by the parser logic in czip.py.
      archive_members (list[str]): file paths in the archive.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
      ValueError: if a subclass has not specified REQUIRED_PATHS.
    """
    # Ensure the subclass defines REQUIRED_PATHS
    if not hasattr(self, 'REQUIRED_PATHS'):
        raise ValueError('Subclass must define REQUIRED_PATHS')
    required = getattr(self, 'REQUIRED_PATHS')
    if not required:
        raise ValueError('REQUIRED_PATHS must not be empty')

    # Verify all required paths are present in the archive
    missing = [path for path in required if path not in archive_members]
    if missing:
        raise UnableToParseFile(f'Missing required paths in zip archive: {missing}')

    # All required paths are present; proceed with plugin-specific processing
    return self.InspectZipFile(parser_mediator, zip_file)

# === BLOCK 4 (label=lm, source_idx=line2071_lm, name=set_child_value) ===
def set_child_value(
            self, sensor_id, child_id, value_type, value, **kwargs):
        """Add a command to set a sensor value, to the queue.

        A queued command will be sent to the sensor when the gateway
        thread has sent all previously queued commands.

        If the sensor attribute new_state returns True, the command will be
        buffered in a queue on the sensor, and only the internal sensor state
        will be updated. When a smartsleep message is received, the internal
        state will be pushed to the sensor, via _handle_smartsleep method.
        """

# === BLOCK 5 (label=human, source_idx=line5435_human, name=vec_angle) ===
def vec_angle(vec1, vec2):
    """ Angle between two R-dimensional vectors.

    Angle calculated as:

    .. math::

        \\arccos\\left[
        \\frac{\\mathsf{vec1}\cdot\\mathsf{vec2}}
        {\\left\\|\\mathsf{vec1}\\right\\|
            \\left\\|\\mathsf{vec2}\\right\\|}
        \\right]

    Parameters
    ----------
    vec1
        length-R |npfloat_| --
        First vector

    vec2
        length-R |npfloat_| --
        Second vector

    Returns
    -------
    angle
        |npfloat_| --
        Angle between the two vectors in degrees

    """

    # Imports
    import numpy as np
    from scipy import linalg as spla
    from ..const import PRM

    # Check shape and equal length
    if len(vec1.shape) != 1:
        raise ValueError("'vec1' is not a vector")
    ## end if
    if len(vec2.shape) != 1:
        raise ValueError("'vec2' is not a vector")
    ## end if
    if vec1.shape[0] != vec2.shape[0]:
        raise ValueError("Vector lengths are not equal")
    ## end if

    # Check magnitudes
    if spla.norm(vec1) < PRM.ZERO_VEC_TOL:
        raise ValueError("'vec1' norm is too small")
    ## end if
    if spla.norm(vec2) < PRM.ZERO_VEC_TOL:
        raise ValueError("'vec2' norm is too small")
    ## end if

    # Calculate the angle and return. Do in multiple steps to test for
    #  possible >1 or <-1 values from numerical precision errors.
    dotp = np.dot(vec1, vec2) / spla.norm(vec1) / spla.norm(vec2)

    if dotp > 1:
        angle = 0. # pragma: no cover
    elif dotp < -1:
        angle = 180. # pragma: no cover
    else:
        angle = np.degrees(np.arccos(dotp))
    ## end if

    return angle

# === BLOCK 6 (label=lm, source_idx=line2812_lm, name=find_dimension_by_name) ===
def find_dimension_by_name(self, dim_name):
        """the method searching dimension with a given name"""
        # Attempt to locate a container of dimensions on the instance
        for _attr in ("dimensions", "_dimensions", "dims", "_dims"):
            if hasattr(self, _attr):
                _dims = getattr(self, _attr)
                break
        else:
            raise AttributeError(
                f"{self.__class__.__name__!s} object has no attribute containing dimensions"
            )

        # Support both iterable of objects with a ``name`` attribute and dict‑like entries
        for _dim in _dims:
            # Direct attribute access
            if hasattr(_dim, "name") and _dim.name == dim_name:
                return _dim
            # Mapping style
            if isinstance(_dim, dict) and _dim.get("name") == dim_name:
                return _dim
        # Not found
        return None
