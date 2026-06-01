# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line44_lm, name=connect) ===
def connect(self, *args, **kwargs):
        """
        Connect to a server.

        This overrides the function in SimpleIRCClient
        to provide SSL functionality.

        :param args:
        :param kwargs:
        :return:
        """
        if self.ssl:
            kwargs['ssl'] = True
        return super(SimpleIRCClient, self).connect(*args, **kwargs)

# === BLOCK 2 (label=human, source_idx=line3896_human, name=process_lpd) ===
def process_lpd(name, dir_tmp):
    """
    Opens up json file, invokes doi_resolver, closes file, updates changelog, cleans directory, and makes new bag.
    :param str name: Name of current .lpd file
    :param str dir_tmp: Path to tmp directory
    :return none:
    """
    logger_doi_main.info("enter process_lpd")
    dir_root = os.getcwd()
    dir_bag = os.path.join(dir_tmp, name)
    dir_data = os.path.join(dir_bag, 'data')

    # Navigate down to jLD file
    # dir : dir_root -> dir_data
    os.chdir(dir_data)

    # Open jld file and read in the contents. Execute DOI Resolver.
    jld_data = read_json_from_file(os.path.join(dir_data, name + '.jsonld'))

    # Overwrite data with new data
    jld_data = DOIResolver(dir_root, name, jld_data).main()
    # Open the jld file and overwrite the contents with the new data.
    write_json_to_file(jld_data)

    # Open changelog. timestamp it. Prompt user for short description of changes. Close and save
    # update_changelog()

    # Delete old bag files, and move files to bag root for re-bagging
    # dir : dir_data -> dir_bag
    dir_cleanup(dir_bag, dir_data)
    finish_bag(dir_bag)

    logger_doi_main.info("exit process_lpd")
    return

# === BLOCK 3 (label=lm, source_idx=line6216_lm, name=save_state_regularly) ===
def save_state_regularly(self, fname, frequency=600):
        """
        Save the state of node with a given regularity to the given
        filename.

        Args:
            fname: File name to save retularly to
            frequency: Frequency in seconds that the state should be saved.
                        By default, 10 minutes.
        """
        self.save_state_regularly = True
        self.save_state_fname = fname
        self.save_state_frequency = frequency

# === BLOCK 4 (label=human, source_idx=line1805_human, name=fetch) ===
def fetch(self, _filter=None, ignore_incremental=False):
        """ Fetch the items from raw or enriched index. An optional _filter
        could be provided to filter the data collected """

        logger.debug("Creating a elastic items generator.")

        scroll_id = None
        page = self.get_elastic_items(scroll_id, _filter=_filter, ignore_incremental=ignore_incremental)

        if not page:
            return []

        scroll_id = page["_scroll_id"]
        scroll_size = page['hits']['total']

        if scroll_size == 0:
            logger.warning("No results found from %s", self.elastic.anonymize_url(self.elastic.index_url))
            return

        while scroll_size > 0:

            logger.debug("Fetching from %s: %d received", self.elastic.anonymize_url(self.elastic.index_url),
                         len(page['hits']['hits']))
            for item in page['hits']['hits']:
                eitem = item['_source']
                yield eitem

            page = self.get_elastic_items(scroll_id, _filter=_filter, ignore_incremental=ignore_incremental)

            if not page:
                break

            scroll_size = len(page['hits']['hits'])

        logger.debug("Fetching from %s: done receiving", self.elastic.anonymize_url(self.elastic.index_url))

# === BLOCK 5 (label=human, source_idx=line54_human, name=_post_build) ===
def _post_build(self, module, encoding):
        """Handles encoding and delayed nodes after a module has been built"""
        module.file_encoding = encoding
        self._manager.cache_module(module)
        # post tree building steps after we stored the module in the cache:
        for from_node in module._import_from_nodes:
            if from_node.modname == "__future__":
                for symbol, _ in from_node.names:
                    module.future_imports.add(symbol)
            self.add_from_names_to_locals(from_node)
        # handle delayed assattr nodes
        for delayed in module._delayed_assattr:
            self.delayed_assattr(delayed)

        # Visit the transforms
        if self._apply_transforms:
            module = self._manager.visit_transforms(module)
        return module

# === BLOCK 6 (label=lm, source_idx=line3012_lm, name=list) ===
def list(self, **params):
        """
        Retrieve all stages

        Returns all stages available to the user, according to the parameters provided

        :calls: ``get /stages``
        :param dict params: (optional) Search options.
        :return: List of dictionaries that support attriubte-style access, which represent collection of Stages.
        :rtype: list
        """
        return self._get('stages', params=params)
