# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1202_lm, name=get_ndmapping_label) ===
def get_ndmapping_label(ndmapping, attr):
    """
    Function to get the first non-auxiliary object
    label attribute from an NdMapping.
    """
    for obj in ndmapping.values():
        if not obj.auxiliary:
            return getattr(obj, attr)
    return None

# === BLOCK 2 (label=lm, source_idx=line1472_lm, name=_iter_expand_paths) ===
def _iter_expand_paths(self, paths):
        """Expand the directories in list of paths to the corresponding paths accordingly,

        Note: git will add items multiple times even if a glob overlapped
        with manually specified paths or if paths where specified multiple
        times - we respect that and do not prune"""
        for path in paths:
            if os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for file in files:
                        yield os.path.join(root, file)
            else:
                yield path

# === BLOCK 3 (label=human, source_idx=line2872_human, name=main) ===
def main():
    """
    Main method.
    """
    run_config = _parse_args(sys.argv[1:])
    gitlab_config = GitLabConfig(run_config.url, run_config.token)
    manager = ProjectVariablesManager(gitlab_config, run_config.project)
    output = json.dumps(manager.get(), sort_keys=True, indent=4, separators=(",", ": "))
    print(output)

# === BLOCK 4 (label=lm, source_idx=line293_lm, name=_compute_precision) ===
def _compute_precision(references, translation, n):
    """Compute ngram precision.

    Parameters
    ----------
    references: list(list(str))
        A list of references.
    translation: list(str)
        A translation.
    n: int
        Order of n-gram.

    Returns
    -------
    matches: int
        Number of matched nth order n-grams
    candidates
        Number of possible nth order n-grams
    """
    matches = 0
    candidates = 0
    for ref in references:
        ref_ngrams = Counter(zip(*[ref[i:] for i in range(n)]))
        trans_ngrams = Counter(zip(*[translation[i:] for i in range(n)]))
        matches += sum((trans_ngrams & ref_ngrams).values())
        candidates += len(ref_ngrams)
    return matches, candidates

# === BLOCK 5 (label=human, source_idx=line1097_human, name=_is_exempt) ===
def _is_exempt(self, environ):
        """
        Returns True if this request's URL starts with one of the
        excluded paths.
        """
        exemptions = self.exclude_paths

        if exemptions:
            path = environ.get('PATH_INFO')
            for excluded_p in self.exclude_paths:
                if path.startswith(excluded_p):
                    return True

        return False

# === BLOCK 6 (label=human, source_idx=line3000_human, name=_special_method_cache) ===
def _special_method_cache(method, cache_wrapper):
	"""
	Because Python treats special methods differently, it's not
	possible to use instance attributes to implement the cached
	methods.

	Instead, install the wrapper method under a different name
	and return a simple proxy to that wrapper.

	https://github.com/jaraco/jaraco.functools/issues/5
	"""
	name = method.__name__
	special_names = '__getattr__', '__getitem__'
	if name not in special_names:
		return

	wrapper_name = '__cached' + name

	def proxy(self, *args, **kwargs):
		if wrapper_name not in vars(self):
			bound = types.MethodType(method, self)
			cache = cache_wrapper(bound)
			setattr(self, wrapper_name, cache)
		else:
			cache = getattr(self, wrapper_name)
		return cache(*args, **kwargs)

	return proxy
