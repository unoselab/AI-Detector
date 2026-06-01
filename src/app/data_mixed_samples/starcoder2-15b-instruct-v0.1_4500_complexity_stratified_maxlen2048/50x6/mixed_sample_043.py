# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line4990_lm, name=index_by) ===
def index_by(self, field):
        """
        Returns a dict with a key for each value of `field` and the first record with that value as value.
        :param field: Name of the field to index by.
        :type field: string.
        """
        return {record[field]: record for record in self}

# === BLOCK 2 (label=lm, source_idx=line4748_lm, name=resolve_freezer) ===
def resolve_freezer(freezer):
    """
    Locate the appropriate freezer given FREEZER or string input from the programmer.

    :param freezer: FREEZER constant or string for the freezer that is requested.  (None = FREEZER.DEFAULT)
    :return:
    """
    if isinstance(freezer, str):
        return getattr(FREEZER, freezer.upper(), FREEZER.DEFAULT)
    return freezer

# === BLOCK 3 (label=human, source_idx=line3045_human, name=expand_paths) ===
def expand_paths(inputs):
    """Yield sys.path directories that might contain "old-style" packages"""

    seen = {}

    for dirname in inputs:
        dirname = normalize_path(dirname)
        if dirname in seen:
            continue

        seen[dirname] = 1
        if not os.path.isdir(dirname):
            continue

        files = os.listdir(dirname)
        yield dirname, files

        for name in files:
            if not name.endswith('.pth'):
                # We only care about the .pth files
                continue
            if name in ('easy-install.pth', 'setuptools.pth'):
                # Ignore .pth files that we control
                continue

            # Read the .pth file
            f = open(os.path.join(dirname, name))
            lines = list(yield_lines(f))
            f.close()

            # Yield existing non-dupe, non-import directory lines from it
            for line in lines:
                if not line.startswith("import"):
                    line = normalize_path(line.rstrip())
                    if line not in seen:
                        seen[line] = 1
                        if not os.path.isdir(line):
                            continue
                        yield line, os.listdir(line)

# === BLOCK 4 (label=lm, source_idx=line4025_lm, name=flip_iterable_dict) ===
def flip_iterable_dict(d: dict) -> dict:
    """Transform dictionary to unpack values to map to respective key."""
    return {v: k for k, v in d.items()}

# === BLOCK 5 (label=human, source_idx=line162_human, name=new_stats_exporter) ===
def new_stats_exporter(options=None, interval=None):
    """Get a stats exporter and running transport thread.

    Create a new `StackdriverStatsExporter` with the given options and start
    periodically exporting stats to stackdriver in the background.

    Fall back to default auth if `options` is null. This will raise
    `google.auth.exceptions.DefaultCredentialsError` if default credentials
    aren't configured.

    See `opencensus.metrics.transport.get_exporter_thread` for details on the
    transport thread.

    :type options: :class:`Options`
    :param exporter: Options to pass to the exporter

    :type interval: int or float
    :param interval: Seconds between export calls.

    :rtype: :class:`StackdriverStatsExporter`
    :return: The newly-created exporter.
    """
    if options is None:
        _, project_id = google.auth.default()
        options = Options(project_id=project_id)
    if str(options.project_id).strip() == "":
        raise ValueError(ERROR_BLANK_PROJECT_ID)

    ci = client_info.ClientInfo(client_library_version=get_user_agent_slug())
    client = monitoring_v3.MetricServiceClient(client_info=ci)
    exporter = StackdriverStatsExporter(client=client, options=options)

    transport.get_exporter_thread(stats.stats, exporter, interval=interval)
    return exporter

# === BLOCK 6 (label=human, source_idx=line3519_human, name=initLogger) ===
def initLogger():
    """
    This code taken from Matt's Suspenders for initializing a logger
    """
    global logger
    logger = logging.getLogger('root')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
