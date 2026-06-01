# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1997_human, name=get_ngrams) ===
def get_ngrams(path):
    """Returns a list of n-grams read from the file at `path`."""
    with open(path, encoding='utf-8') as fh:
        ngrams = [ngram.strip() for ngram in fh.readlines()]
    return ngrams

# === BLOCK 2 (label=lm, source_idx=line5376_lm, name=dockerCall) ===
def dockerCall(*args, **kwargs):
    """
    Deprecated.  Runs subprocessDockerCall() using 'subprocess.check_output()'.

    Provided for backwards compatibility with a previous implementation that
    used 'subprocess.check_call()'.  This has since been supplanted and
    apiDockerCall() is recommended.
    """
    import subprocess
    return subprocess.check_output(args, **kwargs)

# === BLOCK 3 (label=human, source_idx=line5382_human, name=gen_unique_id) ===
def gen_unique_id(serialized_name, args, kwargs):
    """
    Generates and returns a hex-encoded 256-bit ID for the given task name and
    args. Used to generate IDs for unique tasks or for task locks.
    """
    return hashlib.sha256(json.dumps({
        'func': serialized_name,
        'args': args,
        'kwargs': kwargs,
    }, sort_keys=True).encode('utf8')).hexdigest()

# === BLOCK 4 (label=lm, source_idx=line7591_lm, name=show) ===
def show(self, qname):
        """
        Show information about Queue
        """
        queue = self.get_queue(qname)
        if not queue:
            print(f"Queue {qname} not found.")
            return

        info = {
            "name": queue.name,
            "size": queue.size(),
            "status": queue.status,
            "created": queue.created_at
        }

        for key, value in info.items():
            print(f"{key.capitalize()}: {value}")

# === BLOCK 5 (label=lm, source_idx=line2951_lm, name=build) ===
def build(self, **kw):
        """Actually build the node.

        This is called by the Taskmaster after it's decided that the
        Node is out-of-date and must be rebuilt, and after the prepare()
        method has gotten everything, uh, prepared.

        This method is called from multiple threads in a parallel build,
        so only do thread safe stuff here. Do thread unsafe stuff
        in built().

        """
        self.built()

# === BLOCK 6 (label=human, source_idx=line5174_human, name=get_valid_task_types) ===
def get_valid_task_types():
    """Get the valid task types, e.g. signing.

    No longer a constant, due to code ordering issues.

    Returns:
        frozendict: maps the valid task types (e.g., signing) to their validation functions.

    """
    return frozendict({
        'scriptworker': verify_scriptworker_task,
        'balrog': verify_balrog_task,
        'beetmover': verify_beetmover_task,
        'bouncer': verify_bouncer_task,
        'build': verify_build_task,
        'l10n': verify_build_task,
        'repackage': verify_build_task,
        'action': verify_parent_task,
        'decision': verify_parent_task,
        'docker-image': verify_docker_image_task,
        'pushapk': verify_pushapk_task,
        'pushsnap': verify_pushsnap_task,
        'shipit': verify_shipit_task,
        'signing': verify_signing_task,
        'partials': verify_partials_task,
    })
