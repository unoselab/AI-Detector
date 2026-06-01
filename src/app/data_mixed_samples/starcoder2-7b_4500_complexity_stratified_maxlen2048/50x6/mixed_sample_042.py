# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line5545_human, name=_ReadSpecificationFile) ===
def _ReadSpecificationFile(self, path):
    """Reads the format specification file.

    Args:
      path (str): path of the format specification file.

    Returns:
      FormatSpecificationStore: format specification store.
    """
    specification_store = specification.FormatSpecificationStore()

    with io.open(
        path, 'rt', encoding=self._SPECIFICATION_FILE_ENCODING) as file_object:
      for line in file_object.readlines():
        line = line.strip()
        if not line or line.startswith('#'):
          continue

        try:
          identifier, offset, pattern = line.split()
        except ValueError:
          logger.error('[skipping] invalid line: {0:s}'.format(line))
          continue

        try:
          offset = int(offset, 10)
        except ValueError:
          logger.error('[skipping] invalid offset in line: {0:s}'.format(line))
          continue

        try:
          # TODO: find another way to do this that doesn't use an undocumented
          # API.
          pattern = codecs.escape_decode(pattern)[0]
        # ValueError is raised e.g. when the patterns contains "\xg1".
        except ValueError:
          logger.error(
              '[skipping] invalid pattern in line: {0:s}'.format(line))
          continue

        format_specification = specification.FormatSpecification(identifier)
        format_specification.AddNewSignature(pattern, offset=offset)
        specification_store.AddSpecification(format_specification)

    return specification_store

# === BLOCK 2 (label=human, source_idx=line404_human, name=iter_records_for) ===
def iter_records_for(self, package_name):
        """
        Iterate records for a specific package.
        """

        entry_points = self.packages.get(package_name, NotImplemented)
        if entry_points is NotImplemented:
            logger.debug(
                "package '%s' has not declared any entry points for the '%s' "
                "registry for artifact construction",
                package_name, self.registry_name,
            )
            return iter([])

        logger.debug(
            "package '%s' has declared %d entry points for the '%s' "
            "registry for artifact construction",
            package_name, len(entry_points), self.registry_name,
        )
        return iter(entry_points.values())

# === BLOCK 3 (label=lm, source_idx=line3524_lm, name=index) ===
def index(self, axes):
        """
        :param axes: The Axes instance to find the index of.
        :type axes: Axes
        :rtype: int
        """
        return self.axes.index(axes)

# === BLOCK 4 (label=lm, source_idx=line3547_lm, name=BooleanField) ===
def BooleanField(default=NOTHING, required=True, repr=True, cmp=True,
                 key=None):
    """
    Create new bool field on a model.

    :param default: any boolean value
    :param bool required: whether or not the object is invalid if not provided.
    :param bool repr: include this field should appear in object's repr.
    :param bool cmp: include this field in generated comparison.
    :param string key: override name of the value when converted to dict.
    """
    return Field(default, bool, required, repr, cmp, key)

# === BLOCK 5 (label=human, source_idx=line4462_human, name=new) ===
def new(self, page_name, **dict):
        """
        Create a new item with the provided dict information
        at the given page_name.  Returns the new item.

        As of version 2.2 of Redmine, this doesn't seem to function.
        """
        self._item_new_path = '/projects/%s/wiki/%s.json' % \
            (self._project.identifier, page_name)
        # Call the base class new method
        return super(Redmine_Wiki_Pages_Manager, self).new(**dict)

# === BLOCK 6 (label=lm, source_idx=line1272_lm, name=get_subscriber_queue) ===
def get_subscriber_queue(self, event_types=None):
        """Create a new queue for a specific combination of event types
        and return it.

        Returns:
            a :class:`multiprocessing.Queue`.
        Raises:
            RuntimeError if called after `run`
        """
        if self._running:
            raise RuntimeError("Cannot create a new queue after run")
        if event_types is None:
            event_types = self._event_types
        return self._queues[event_types]
