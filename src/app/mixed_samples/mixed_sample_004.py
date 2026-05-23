# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line168_human, name=collect_spans) ===
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

    if ast.get("subject", False):
        spans.extend(collect_spans(ast["subject"]))

    if ast.get("object", False):
        spans.extend(collect_spans(ast["object"]))

    if ast.get("nested", False):
        spans.extend(collect_spans(ast["nested"]))

    if ast.get("function", False):
        log.debug(f"Processing function")
        spans.append(("Function", ast["function"]["name_span"]))
        log.debug(f"Spans: {spans}")

    if ast.get("args", False):
        for idx, arg in enumerate(ast["args"]):
            log.debug(f"Arg  {arg}")

            if arg.get("function", False):
                log.debug(f"Recursing on arg function")
                results = collect_spans(arg)
                log.debug(f"Results {results}")
                spans.extend(results)  # Recurse arg function
            elif arg.get("nsarg", False):
                log.debug(f"Processing NSArg   Arg {arg}")
                spans.append(("NSArg", arg["span"]))
                spans.append(("NSPrefix", arg["nsarg"]["ns_span"]))
                spans.append(("NSVal", arg["nsarg"]["ns_val_span"]))
            elif arg["type"] == "StrArg":
                spans.append(("StrArg", arg["span"]))

    log.debug(f"Spans: {spans}")
    return spans

# === BLOCK 2 (label=human, source_idx=line1935_human, name=fo_pct) ===
def fo_pct(self):
        """
        Get the by team overall face-off win %.

        :returns: dict, ``{ 'home': %, 'away': % }``
        """
        tots = self.team_totals
        return {
            t: tots[t]['won']/(1.0*tots[t]['total']) if tots[t]['total'] else 0.0
            for t in [ 'home', 'away' ]
        }

# === BLOCK 3 (label=human, source_idx=line1667_human, name=find_orgs) ===
def find_orgs(query, first_page_size=10):
    """
    :param query: The input to the /system/findOrgs API method.
    :type query: dict

    :param first_page_size: The number of results that the initial
        /system/findOrgs API call will return; default 10, max 1000. Subsequent
        calls will raise the number of returned results exponentially up to a
        max of 1000.
    :type first_page_size: int

    :rtype: generator

    Returns a generator that yields all orgs matching the specified query. Will
    transparently handle pagination as necessary.
    """
    return _find(dxpy.api.system_find_orgs, query, limit=None,
                 return_handler=False, first_page_size=first_page_size)

# === BLOCK 4 (label=human, source_idx=line181_human, name=unwrap_errors) ===
def unwrap_errors(path_replace):
    # type: (Union[Text, Mapping[Text, Text]]) -> Iterator[None]
    """Get a context to map OS errors to their `fs.errors` counterpart.

    The context will re-write the paths in resource exceptions to be
    in the same context as the wrapped filesystem.

    The only parameter may be the path from the parent, if only one path
    is to be unwrapped. Or it may be a dictionary that maps wrapped
    paths on to unwrapped paths.

    """
    try:
        yield
    except errors.ResourceError as e:
        if hasattr(e, "path"):
            if isinstance(path_replace, Mapping):
                e.path = path_replace.get(e.path, e.path)
            else:
                e.path = path_replace
        reraise(type(e), e)

# === BLOCK 5 (label=lm, source_idx=line626_lm, name=diff) ===
def diff(self, y, h, deriv, dim, coefs):
        """The core function to take a partial derivative on a uniform grid.
        """
        if deriv < 0 or deriv >= len(coefs):
            raise ValueError("Derivative order out of bounds")
        if dim < 0 or dim >= len(y.shape):
            raise ValueError("Dimension out of bounds")
        deriv_coefs = coefs[deriv]
        axis = dim
        n = y.shape[axis]
        if n < len(deriv_coefs):
            raise ValueError("Insufficient data points for the given derivative order")
        diff_y = np.zeros_like(y)
        slices = [slice(None)] * y.ndim
        for i in range(len(deriv_coefs)):
            slices[axis] = slice(i, i + n - len(deriv_coefs) + 1)
            diff_y += deriv_coefs[i] * y[tuple(slices)]
        return diff_y / h**deriv
