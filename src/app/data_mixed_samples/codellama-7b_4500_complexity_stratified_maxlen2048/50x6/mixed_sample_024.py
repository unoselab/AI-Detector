# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line8062_lm, name=_generate_examples) ===
def _generate_examples(self, split_subsets, extraction_map):
    """Returns the examples in the raw (text) form."""
    examples = []
    for split_subset in split_subsets:
      for example in split_subset:
        examples.append(example)
    return examples

# === BLOCK 2 (label=human, source_idx=line8990_human, name=appendChild) ===
def appendChild(self, child: 'WdomElement') -> Node:
        """Append child node at the last of child nodes.

        If this instance is connected to the node on browser, the child node is
        also added to it.
        """
        if self.connected:
            self._append_child_web(child)
        return self._append_child(child)

# === BLOCK 3 (label=human, source_idx=line1550_human, name=_config_section) ===
def _config_section(config, section):
    """Read the configuration file and return a section."""
    path = os.path.join(config.get('config_path'), config.get('config_file'))
    conf = _config_ini(path)
    return conf.get(section)

# === BLOCK 4 (label=lm, source_idx=line8350_lm, name=find_by) ===
def find_by(self, column=None, value=None, order_by=None, limit=0):
        """
            Find all items that matches your a column/value.

            :param column: column to search.
            :param value: value to look for in `column`.
            :param limit: How many rows to fetch.
            :param order_by: column on which to order the results. \
            To change the sort, prepend with < or >.

        """
        if column is None or value is None:
            raise ValueError("column and value must be specified")

        if order_by is None:
            order_by = column
        else:
            order_by = "%s %s" % (order_by, order_by[0])

        query = "SELECT * FROM %s WHERE %s = ? ORDER BY %s LIMIT %s" % (
            self.table_name, column, order_by, limit)

        return self.execute(query, (value,))

# === BLOCK 5 (label=lm, source_idx=line7985_lm, name=recurse) ===
def recurse(self, root_path, dir_cb, listing_cb, max_listing_size=0, 
                max_depth=MAX_REMOTE_RECURSION_DEPTH):
        """Recursively iterate a directory. Invoke callbacks for directories 
        and entries (both are optional, but it doesn't make sense unless one is 
        provided). "max_listing_size" will allow for the file-listing to be 
        chunked into manageable pieces. "max_depth" limited how deep recursion 
        goes. This can be used to make it easy to simply read a single 
        directory in chunks.
        """
        the

# === BLOCK 6 (label=human, source_idx=line6035_human, name=consent) ===
def consent():
    """Return the consent form. Here for backwards-compatibility with 2.x."""
    config = _config()
    return render_template(
        "consent.html",
        hit_id=request.args["hit_id"],
        assignment_id=request.args["assignment_id"],
        worker_id=request.args["worker_id"],
        mode=config.get("mode"),
    )
