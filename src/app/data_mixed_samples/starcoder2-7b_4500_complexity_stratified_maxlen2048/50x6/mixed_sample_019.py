# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line3173_human, name=render_dot) ===
def render_dot(self, code, options, format, prefix='graphviz'):
    # type: (nodes.NodeVisitor, unicode, Dict, unicode, unicode) -> Tuple[unicode, unicode]
    """Render graphviz code into a PNG or PDF output file."""
    graphviz_dot = options.get('graphviz_dot', self.builder.config.graphviz_dot)
    hashkey = (code + str(options) + str(graphviz_dot) +
               str(self.builder.config.graphviz_dot_args)).encode('utf-8')

    fname = '%s-%s.%s' % (prefix, sha1(hashkey).hexdigest(), format)
    relfn = posixpath.join(self.builder.imgpath, fname)
    outfn = path.join(self.builder.outdir, self.builder.imagedir, fname)

    if path.isfile(outfn):
        return relfn, outfn

    if (hasattr(self.builder, '_graphviz_warned_dot') and
       self.builder._graphviz_warned_dot.get(graphviz_dot)):
        return None, None

    ensuredir(path.dirname(outfn))

    # graphviz expects UTF-8 by default
    if isinstance(code, text_type):
        code = code.encode('utf-8')

    dot_args = [graphviz_dot]
    dot_args.extend(self.builder.config.graphviz_dot_args)
    dot_args.extend(['-T' + format, '-o' + outfn])
    if format == 'png':
        dot_args.extend(['-Tcmapx', '-o%s.map' % outfn])
    try:
        p = Popen(dot_args, stdout=PIPE, stdin=PIPE, stderr=PIPE)
    except OSError as err:
        if err.errno != ENOENT:   # No such file or directory
            raise
        logger.warning(__('dot command %r cannot be run (needed for graphviz '
                          'output), check the graphviz_dot setting'), graphviz_dot)
        if not hasattr(self.builder, '_graphviz_warned_dot'):
            self.builder._graphviz_warned_dot = {}
        self.builder._graphviz_warned_dot[graphviz_dot] = True
        return None, None
    try:
        # Graphviz may close standard input when an error occurs,
        # resulting in a broken pipe on communicate()
        stdout, stderr = p.communicate(code)
    except (OSError, IOError) as err:
        if err.errno not in (EPIPE, EINVAL):
            raise
        # in this case, read the standard output and standard error streams
        # directly, to get the error message(s)
        stdout, stderr = p.stdout.read(), p.stderr.read()
        p.wait()
    if p.returncode != 0:
        raise GraphvizError(__('dot exited with error:\n[stderr]\n%s\n'
                               '[stdout]\n%s') % (stderr, stdout))
    if not path.isfile(outfn):
        raise GraphvizError(__('dot did not produce an output file:\n[stderr]\n%s\n'
                               '[stdout]\n%s') % (stderr, stdout))
    return relfn, outfn

# === BLOCK 2 (label=lm, source_idx=line4578_lm, name=search) ===
def search(self, search_term, num_results, **kwargs):
        """Gets x number of Google image result urls for
        a given search term.
        Arguments
        search_term: str
            tearm to search for
        num_results: int
            number of url results to return
        return ['url','url']
        """
        # build the url
        url = self.build_url(search_term, num_results, **kwargs)
        # get the html
        html = self.get_html(url)
        # parse the html
        return self.parse_html(html)

# === BLOCK 3 (label=lm, source_idx=line2921_lm, name=p_namedblock_statement) ===
def p_namedblock_statement(self, p):
        """namedblock_statement : basic_statement
        | decl
        | integerdecl
        | realdecl
        | parameterdecl
        | localparamdecl
        """
        p[0] = p[1]

# === BLOCK 4 (label=human, source_idx=line5983_human, name=_from_dict) ===
def _from_dict(cls, _dict):
        """Initialize a DialogRuntimeResponseGeneric object from a json dictionary."""
        args = {}
        if 'response_type' in _dict:
            args['response_type'] = _dict.get('response_type')
        else:
            raise ValueError(
                'Required property \'response_type\' not present in DialogRuntimeResponseGeneric JSON'
            )
        if 'text' in _dict:
            args['text'] = _dict.get('text')
        if 'time' in _dict:
            args['time'] = _dict.get('time')
        if 'typing' in _dict:
            args['typing'] = _dict.get('typing')
        if 'source' in _dict:
            args['source'] = _dict.get('source')
        if 'title' in _dict:
            args['title'] = _dict.get('title')
        if 'description' in _dict:
            args['description'] = _dict.get('description')
        if 'preference' in _dict:
            args['preference'] = _dict.get('preference')
        if 'options' in _dict:
            args['options'] = [
                DialogNodeOutputOptionsElement._from_dict(x)
                for x in (_dict.get('options'))
            ]
        if 'message_to_human_agent' in _dict:
            args['message_to_human_agent'] = _dict.get('message_to_human_agent')
        if 'topic' in _dict:
            args['topic'] = _dict.get('topic')
        if 'dialog_node' in _dict:
            args['dialog_node'] = _dict.get('dialog_node')
        if 'suggestions' in _dict:
            args['suggestions'] = [
                DialogSuggestion._from_dict(x)
                for x in (_dict.get('suggestions'))
            ]
        return cls(**args)

# === BLOCK 5 (label=human, source_idx=line5307_human, name=isPlantOrigin) ===
def isPlantOrigin(taxid):
    """
    Given a taxid, this gets the expanded tree which can then be checked to
    see if the organism is a plant or not

    >>> isPlantOrigin(29760)
    True
    """

    assert isinstance(taxid, int)

    t = TaxIDTree(taxid)
    try:
        return "Viridiplantae" in str(t)
    except AttributeError:
        raise ValueError("{0} is not a valid ID".format(taxid))

# === BLOCK 6 (label=lm, source_idx=line5478_lm, name=build) ===
def build(self):
        """Build all added items.

        Visuals are created, added, and built. The `set_data()` methods can
        be called afterwards.

        """
        self.visuals = []
        for item in self.items:
            visual = item.build()
            self.visuals.append(visual)
