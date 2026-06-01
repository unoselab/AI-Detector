# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line779_human, name=zoom_in) ===
def zoom_in(self):
        """Increase zoom factor and redraw TimeLine"""
        index = self._zoom_factors.index(self._zoom_factor)
        if index + 1 == len(self._zoom_factors):
            # Already zoomed in all the way
            return
        self._zoom_factor = self._zoom_factors[index + 1]
        if self._zoom_factors.index(self.zoom_factor) + 1 == len(self._zoom_factors):
            self._button_zoom_in.config(state=tk.DISABLED)
        self._button_zoom_out.config(state=tk.NORMAL)
        self.draw_timeline()

# === BLOCK 2 (label=lm, source_idx=line1379_lm, name=load_data_file) ===
def load_data_file(fname, directory=None, force_download=False):
    """Get a standard vispy demo data file

    Parameters
    ----------
    fname : str
        The filename on the remote ``demo-data`` repository to download,
        e.g. ``'molecular_viewer/micelle.npy'``. These correspond to paths
        on ``https://github.com/vispy/demo-data/``.
    directory : str | None
        Directory to use to save the file. By default, the vispy
        configuration directory is used.
    force_download : bool | str
        If True, the file will be downloaded even if a local copy exists
        (and this copy will be overwritten). Can also be a YYYY-MM-DD date
        to ensure a file is up-to-date (modified date of a file on disk,
        if present, is checked).

    Returns
    -------
    fname : str
        The path to the file on the local system.
    """
    if directory is None:
        directory = os.path.join(os.path.expanduser('~'), '.vispy')
    if not os.path.exists(directory):
        os.makedirs(directory)
    url = 'https://github.com/vispy/demo-data/raw/main/' + fname
    local_file = os.path.join(directory, os.path.basename(fname))
    if not os.path.exists(local_file) or force_download:
        urllib.request.urlretrieve(url, local_file)
    return local_file

# === BLOCK 3 (label=lm, source_idx=line1025_lm, name=all_documents) ===
def all_documents(index=INDEX_NAME):
    """
    Get all documents from the given index.

    Returns full Elasticsearch objects so you can get metadata too.
    """
    query = {
        "query": {
            "match_all": {}
        }
    }
    response = es.search(index=index, body=query)
    return response['hits']['hits']

# === BLOCK 4 (label=lm, source_idx=line3382_lm, name=_build_file) ===
def _build_file(self, cif_str):
        """Build :class:`~nmrstarlib.nmrstarlib.CIFFile` object.

        :param cif_str: NMR-STAR-formatted string.
        :type cif_str: :py:class:`str` or :py:class:`bytes`
        :return: instance of :class:`~nmrstarlib.nmrstarlib.CIFFile`.
        :rtype: :class:`~nmrstarlib.nmrstarlib.CIFFile`
        """
        if isinstance(cif_str, bytes):
            cif_str = cif_str.decode('utf-8')
        lines = cif_str.splitlines()
        file = CIFFile()
        current_block = None
        for line in lines:
            if line.startswith('data_'):
                block_name = line[5:].strip()
                current_block = CIFBlock(block_name)
                file.add_block(current_block)
            elif line.startswith('#'):
                continue
            elif line.strip():
                tag, value = line.split('=', 1)
                tag = tag.strip()
                value = value.strip()
                current_block.add_item(tag, value)
        return file

# === BLOCK 5 (label=human, source_idx=line2993_human, name=load) ===
def load(self, path=None, fatal=True, logger=None):
        """
        :param str|None path: Load this object from file with 'path' (default: self._path)
        :param bool|None fatal: Abort execution on failure if True
        :param callable|None logger: Logger to use
        """
        self.reset()
        if path:
            self._path = path
            self._source = short(path)

        else:
            path = getattr(self, "_path", None)

        if path:
            self.set_from_dict(read_json(path, default={}, fatal=fatal, logger=logger))

# === BLOCK 6 (label=human, source_idx=line3905_human, name=process_non_api_filters) ===
def process_non_api_filters(search_opts, non_api_filter_info):
    """Process filters by non-API fields

    There are cases where it is useful to provide a filter field
    which does not exist in a resource in a backend service.
    For example, nova server list provides 'image' field with image ID
    but 'image name' is more useful for GUI users.
    This function replaces fake fields into corresponding real fields.

    The format of non_api_filter_info is a tuple/list of
    (fake_field, real_field, resources).

    This returns True if further lookup is required.
    It returns False if there are no matching resources,
    for example, if no corresponding real field exists.
    """
    for fake_field, real_field, resources in non_api_filter_info:
        if not _swap_filter(resources, search_opts, fake_field, real_field):
            return False
    return True
