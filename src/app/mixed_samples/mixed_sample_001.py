# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line50_human, name=find_movie) ===
async def find_movie(self, query):
        """Retrieve movie data by search query.

        Arguments:
          query (:py:class:`str`): Query to search for.

        Returns:
          :py:class:`list`: Possible matches.

        """
        params = OrderedDict([
            ('query', query), ('include_adult', False),
        ])
        url = self.url_builder('search/movie', {}, params)
        data = await self.get_data(url)
        if data is None:
            return
        return [
            Movie.from_json(item, self.config['data'].get('images'))
            for item in data.get('results', [])
        ]

# === BLOCK 2 (label=lm, source_idx=line168_lm, name=collect_spans) ===
def collect_spans(ast: AST) -> List[Tuple[str, Tuple[int, int]]]:
    """Collect flattened list of spans of BEL syntax types

    Provide simple list of BEL syntax type spans for highlighting.
    Function names, NSargs, NS prefix, NS value and StrArgs will be
    tagged.

    Args:
        ast: AST of BEL assertion

    Returns:
        List[Tuple[str, Tuple[int, int]]]: list of span objects (<type>, (<start>, <end>))
    """
    spans = []

    def collect(node):
        if isinstance(node, Function):
            spans.append(("function", node.span))
        elif isinstance(node, NSArg):
            spans.append(("nsarg", node.span))
        elif isinstance(node, NS):
            spans.append(("ns", node.span))
        elif isinstance(node, StrArg):
            spans.append(("strarg", node.span))

        for child in node.children:
            collect(child)

    collect(ast)
    return spans

# === BLOCK 3 (label=human, source_idx=line1957_human, name=_maybe_append_chunk) ===
def _maybe_append_chunk(chunk_info, line_index, column, contents, chunks):
    """Append chunk_info to chunks if it is set."""
    if chunk_info:
        chunks.append(_chunk_from_ranges(contents,
                                         chunk_info[0],
                                         chunk_info[1],
                                         line_index,
                                         column))

# === BLOCK 4 (label=human, source_idx=line2144_human, name=get_listener_instance) ===
def get_listener_instance(self, cls):
        """If a listener of the specified type is registered, returns the
        instance.

        :type cls: :class:`SessionListener`
        """
        with self._lock:
            for listener in self._listeners:
                if isinstance(listener, cls):
                    return listener
