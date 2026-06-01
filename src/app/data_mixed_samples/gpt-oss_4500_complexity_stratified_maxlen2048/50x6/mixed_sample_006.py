# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line3884_lm, name=decode_network) ===
def decode_network(objects):
    """Return root object from ref-containing obj table entries"""
    # Build a mapping from object IDs to their data (shallow copy to avoid mutating input)
    id_map = {}
    for obj in objects:
        # Expect each entry to have a unique identifier under the key 'id'
        if isinstance(obj, dict) and 'id' in obj:
            oid = obj['id']
            # Store a shallow copy; deep resolution will happen later
            id_map[oid] = dict(obj)
        else:
            raise ValueError("Each object must be a dict containing an 'id' key")

    # Helper to recursively resolve references
    def _resolve(value, _seen):
        if isinstance(value, dict):
            # Reference marker: a dict with a single key '$ref'
            if set(value.keys()) == {'$ref'}:
                ref_id = value['$ref']
                if ref_id not in id_map:
                    raise KeyError(f"Reference to unknown id '{ref_id}'")
                if ref_id in _seen:
                    # Circular reference detected; return the already‑resolved object to avoid infinite recursion
                    return id_map[ref_id]
                # Mark as seen before descending
                _seen.add(ref_id)

# === BLOCK 2 (label=human, source_idx=line819_human, name=AddExtensionDescriptor) ===
def AddExtensionDescriptor(self, extension):
    """Adds a FieldDescriptor describing an extension to the pool.

    Args:
      extension: A FieldDescriptor.

    Raises:
      AssertionError: when another extension with the same number extends the
        same message.
      TypeError: when the specified extension is not a
        descriptor.FieldDescriptor.
    """
    if not (isinstance(extension, descriptor.FieldDescriptor) and
            extension.is_extension):
      raise TypeError('Expected an extension descriptor.')

    if extension.extension_scope is None:
      self._toplevel_extensions[extension.full_name] = extension

    try:
      existing_desc = self._extensions_by_number[
          extension.containing_type][extension.number]
    except KeyError:
      pass
    else:
      if extension is not existing_desc:
        raise AssertionError(
            'Extensions "%s" and "%s" both try to extend message type "%s" '
            'with field number %d.' %
            (extension.full_name, existing_desc.full_name,
             extension.containing_type.full_name, extension.number))

    self._extensions_by_number[extension.containing_type][
        extension.number] = extension
    self._extensions_by_name[extension.containing_type][
        extension.full_name] = extension

    # Also register MessageSet extensions with the type name.
    if _IsMessageSetExtension(extension):
      self._extensions_by_name[extension.containing_type][
          extension.message_type.full_name] = extension

# === BLOCK 3 (label=lm, source_idx=line5594_lm, name=sheets) ===
def sheets(self):
        """
        Collection of sheets in this document.
        """

# === BLOCK 4 (label=human, source_idx=line5084_human, name=replace_cancel_operation_by_id) ===
def replace_cancel_operation_by_id(cls, cancel_operation_id, cancel_operation, **kwargs):
        """Replace CancelOperation

        Replace all attributes of CancelOperation
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async=True
        >>> thread = api.replace_cancel_operation_by_id(cancel_operation_id, cancel_operation, async=True)
        >>> result = thread.get()

        :param async bool
        :param str cancel_operation_id: ID of cancelOperation to replace (required)
        :param CancelOperation cancel_operation: Attributes of cancelOperation to replace (required)
        :return: CancelOperation
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        if kwargs.get('async'):
            return cls._replace_cancel_operation_by_id_with_http_info(cancel_operation_id, cancel_operation, **kwargs)
        else:
            (data) = cls._replace_cancel_operation_by_id_with_http_info(cancel_operation_id, cancel_operation, **kwargs)
            return data

# === BLOCK 5 (label=human, source_idx=line323_human, name=add_nio) ===
def add_nio(self, nio, port_number):
        """
        Adds a NIO as new port on this cloud.

        :param nio: NIO instance to add
        :param port_number: port to allocate for the NIO
        """

        if port_number in self._nios:
            raise NodeError("Port {} isn't free".format(port_number))

        log.info('Cloud "{name}" [{id}]: NIO {nio} bound to port {port}'.format(name=self._name,
                                                                                id=self._id,
                                                                                nio=nio,
                                                                                port=port_number))
        try:
            yield from self.start()
            yield from self._add_ubridge_connection(nio, port_number)
            self._nios[port_number] = nio
        except NodeError as e:
            self.project.emit("log.error", {"message": str(e)})
            yield from self._stop_ubridge()
            self.status = "stopped"
            self._nios[port_number] = nio
        # Cleanup stuff
        except UbridgeError as e:
            self.project.emit("log.error", {"message": str(e)})
            yield from self._stop_ubridge()
            self.status = "stopped"
            self._nios[port_number] = nio

# === BLOCK 6 (label=lm, source_idx=line5572_lm, name=_post_master_init) ===
def _post_master_init(self, master):
        """
        Function to finish init after connecting to a master

        This is primarily loading modules, pillars, etc. (since they need
        to know which master they connected to)

        If this function is changed, please check Minion._post_master_init
        to see if those changes need to be propagated.

        ProxyMinions need a significantly different post master setup,
        which is why the differences are not factored out into separate helper
        functions.
        """
