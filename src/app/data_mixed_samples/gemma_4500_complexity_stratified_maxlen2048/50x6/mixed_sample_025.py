# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line2167_human, name=suppressionlist) ===
def suppressionlist(self, page=1, page_size=1000, order_field="email", order_direction="asc"):
        """Gets this client's suppression list."""
        params = {
            "page": page,
            "pagesize": page_size,
            "orderfield": order_field,
            "orderdirection": order_direction}
        response = self._get(self.uri_for("suppressionlist"), params=params)
        return json_to_py(response)

# === BLOCK 2 (label=human, source_idx=line3071_human, name=numeric_function_clean_dataframe) ===
def numeric_function_clean_dataframe(self, axis):
        """Preprocesses numeric functions to clean dataframe and pick numeric indices.

        Args:
            axis: '0' if columns and '1' if rows.

        Returns:
            Tuple with return value(if any), indices to apply func to & cleaned Manager.
        """
        result = None
        query_compiler = self
        # If no numeric columns and over columns, then return empty Series
        if not axis and len(self.index) == 0:
            result = pandas.Series(dtype=np.int64)

        nonnumeric = [
            col
            for col, dtype in zip(self.columns, self.dtypes)
            if not is_numeric_dtype(dtype)
        ]
        if len(nonnumeric) == len(self.columns):
            # If over rows and no numeric columns, return this
            if axis:
                result = pandas.Series([np.nan for _ in self.index])
            else:
                result = pandas.Series([0 for _ in self.index])
        else:
            query_compiler = self.drop(columns=nonnumeric)
        return result, query_compiler

# === BLOCK 3 (label=lm, source_idx=line685_lm, name=FoldByteStream) ===
def FoldByteStream(self, mapped_value, context=None, **unused_kwargs):
    """Folds the data type into a byte stream.

    Args:
      mapped_value (object): mapped value.
      context (Optional[DataTypeMapContext]): data type map context.

    Returns:
      bytes: byte stream.

    Raises:
      FoldingError: if the data type definition cannot be folded into
          the byte stream.
    """
    try:
        if isinstance(mapped_value, bytes):
            return mapped_value
        if isinstance(mapped_value, bytearray):
            return bytes(mapped_value)
        return bytes(mapped_value)
    except (TypeError, ValueError) as e:
        raise FoldingError(f"Failed to fold value into byte stream: {e}") from e

# === BLOCK 4 (label=lm, source_idx=line5895_lm, name=_get_dcd) ===
def _get_dcd(self, alias):
        """
        Get the Docker-Content-Digest header for an alias.

        :param alias: Alias name.
        :type alias: str

        :rtype: str
        :returns: DCD header for the alias.
        """
        dcd = self._get_header(alias, 'Docker-Content-Digest')
        if not dcd:
            raise KeyError(f"Docker-Content-Digest header not found for alias: {alias}")
        return dcd

# === BLOCK 5 (label=lm, source_idx=line3220_lm, name=add_sort) ===
def add_sort(self, field, ascending=True):
        """Sort the search results by a certain field.

        If this method is called multiple times, the later sort fields are given lower priority,
        and will only be considered when the eariler fields have the same value.

        Arguments:
            field (str): The field to sort by.
                    The field must be namespaced according to Elasticsearch rules
                    using the dot syntax.
                    For example, ``"mdf.source_name"`` is the ``source_name`` field
                    of the ``mdf`` dictionary.
            ascending (bool): If ``True``, the results will be sorted in ascending order.
                    If ``False``, the results will be sorted in descending order.
                    **Default**: ``True``.
        Returns:
            SearchHelper: Self
        """
        order = "asc" if ascending else "desc"
        if "sort" not in self._query:
            self._query["sort"] = []
        self._query["sort"].append({field: {"order": order}})
        return self

# === BLOCK 6 (label=human, source_idx=line3690_human, name=HandleWellKnownFlows) ===
def HandleWellKnownFlows(self, messages):
    """Hands off messages to well known flows."""
    msgs_by_wkf = {}
    result = []
    for msg in messages:
      # Regular message - queue it.
      if msg.response_id != 0:
        result.append(msg)
        continue

      # Well known flows:
      flow_name = msg.session_id.FlowName()

      if flow_name in self.well_known_flows:
        # This message should be processed directly on the front end.
        msgs_by_wkf.setdefault(flow_name, []).append(msg)

        # TODO(user): Deprecate in favor of 'well_known_flow_requests'
        # metric.
        stats_collector_instance.Get().IncrementCounter(
            "grr_well_known_flow_requests")

        stats_collector_instance.Get().IncrementCounter(
            "well_known_flow_requests", fields=[str(msg.session_id)])
      else:
        # Message should be queued to be processed in the backend.

        # Well known flows have a response_id==0, but if we queue up the state
        # as that it will overwrite some other message that is queued. So we
        # change it to a random number here.
        msg.response_id = random.UInt32()

        # Queue the message in the data store.
        result.append(msg)

    for flow_name, msg_list in iteritems(msgs_by_wkf):
      wkf = self.well_known_flows[flow_name]
      wkf.ProcessMessages(msg_list)

    return result
