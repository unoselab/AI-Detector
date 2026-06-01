# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line5516_human, name=file_data_to_str) ===
def file_data_to_str(data):
    """
    Convert file data to a string for display.

    This function takes the file data produced by gather_file_data().
    """
    if not data:
        return _('<i>File name not recorded</i>')
    res = data['name']
    try:
        mtime_as_str = time.strftime('%Y-%m-%d %H:%M:%S',
                                     time.localtime(data['mtime']))
        res += '<br><i>{}</i>: {}'.format(_('Last modified'), mtime_as_str)
        res += '<br><i>{}</i>: {} {}'.format(
                _('Size'), data['size'], _('bytes'))
    except KeyError:
        res += '<br>' + _('<i>File no longer exists</i>')
    return res

# === BLOCK 2 (label=human, source_idx=line410_human, name=load_entry_point_group) ===
def load_entry_point_group(self, entry_point_group):
        """Load actions from an entry point group.

        :param entry_point_group: The entrypoint group name to load plugins.
        """
        for ep in pkg_resources.iter_entry_points(group=entry_point_group):
            self.register_scope(ep.load())

# === BLOCK 3 (label=lm, source_idx=line3491_lm, name=is_full_overlap) ===
def is_full_overlap(self1):
      """true if they are a full overlap

      :return: is full overlap
      :rtype: bool
      """
      return (self.start <= self1.start and self.end >= self1.end) or (self1.start <= self.start and self1.end >= self.end)

# === BLOCK 4 (label=lm, source_idx=line3536_lm, name=set_children) ===
def set_children(self, child_ids):
        """Sets the children.

        arg:    child_ids (osid.id.Id[]): the children``Ids``
        raise:  InvalidArgument - ``child_ids`` is invalid
        raise:  NoAccess - ``Metadata.isReadOnly()`` is ``true``
        *compliance: mandatory -- This method must be implemented.*

        """
        # Check for read‑only metadata
        if getattr(self, "_metadata", None) and self._metadata.isReadOnly():
            raise NoAccess("Metadata is read‑only")
        # Validate that child_ids is an iterable of Id objects
        if child_ids is None:
            raise InvalidArgument("child_ids cannot be None")
        try:
            iterator = iter(child_ids)
        except TypeError:
            raise InvalidArgument("child_ids must be iterable")
        # Ensure we are not treating a string as an iterable of Ids
        if isinstance(child_ids, (str, bytes)):
            raise InvalidArgument("child_ids must not be a string")
        # Optionally, verify each element looks like an Id (has an 'identifier' attribute)
        for cid in iterator:
            if not hasattr(cid, "identifier"):
                raise InvalidArgument("Each child_id must be an Id object")
        # Store the children
        self._children = list(child_ids)

# === BLOCK 5 (label=human, source_idx=line4550_human, name=update) ===
def update(self, url, doc):
        """Update metadata associated with a DOI.

        This can be called before/after a DOI is registered.

        :param doc: Set metadata for DOI.
        :returns: `True` if is updated successfully.
        """
        if self.pid.is_deleted():
            logger.info("Reactivate in DataCite",
                        extra=dict(pid=self.pid))

        try:
            # Set metadata
            self.api.metadata_post(doc)
            self.api.doi_post(self.pid.pid_value, url)
        except (DataCiteError, HttpError):
            logger.exception("Failed to update in DataCite",
                             extra=dict(pid=self.pid))
            raise

        if self.pid.is_deleted():
            self.pid.sync_status(PIDStatus.REGISTERED)
        logger.info("Successfully updated in DataCite",
                    extra=dict(pid=self.pid))
        return True

# === BLOCK 6 (label=lm, source_idx=line1308_lm, name=show_network_ip_availability) ===
def show_network_ip_availability(self, network, **_params):
        """Fetches IP availability information for a specified network"""
        # Resolve network identifier
        network_id = getattr(network, "id", network)
        # Build request URL
        base = getattr(self, "base_url", "").rstrip("/")
        url = f"{base}/v2.0/network-ip-availabilities/{network_id}"
        # Perform request
        response = getattr(self, "session", None).get(url, params=_params)
        # Raise for HTTP errors
        response.raise_for_status()
        # Return parsed JSON payload
        return response.json()
