# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line782_human, name=clear_extensions) ===
def clear_extensions(self, group=None):
        """Clear all previously registered extensions."""

        if group is None:
            ComponentRegistry._registered_extensions = {}
            return

        if group in self._registered_extensions:
            self._registered_extensions[group] = []

# === BLOCK 2 (label=human, source_idx=line2419_human, name=write_pid_file) ===
def write_pid_file():
    """Write a file with the PID of this server instance.

    Call when setting up a command line testserver.
    """
    pidfile = os.path.basename(sys.argv[0])[:-3] + '.pid'  # strip .py, add .pid
    with open(pidfile, 'w') as fh:
        fh.write("%d\n" % os.getpid())
        fh.close()

# === BLOCK 3 (label=lm, source_idx=line3628_lm, name=_run_spellcheck_linter) ===
def _run_spellcheck_linter(matched_filenames, cache_dir, show_lint_files):
    """Run spellcheck-linter on matched_filenames."""
    if not matched_filenames:
        return

    # We need to create a temporary directory for the cache.
    # We can't use the cache_dir because it's a symlink.
    cache_dir = tempfile.mkdtemp()
    try:
        # Run the linter.
        spellcheck_linter.main(
            matched_filenames,
            cache_dir=cache_dir,
            show_lint_files=show_lint_files,
        )
    finally:
        shutil.rmtree(cache_dir)

# === BLOCK 4 (label=human, source_idx=line2043_human, name=_convert_point) ===
def _convert_point(self, metric, ts, point, sd_point):
        """Convert an OC metric point to a SD point."""
        if (metric.descriptor.type == metric_descriptor.MetricDescriptorType
                .CUMULATIVE_DISTRIBUTION):

            sd_dist_val = sd_point.value.distribution_value
            sd_dist_val.count = point.value.count
            sd_dist_val.sum_of_squared_deviation =\
                point.value.sum_of_squared_deviation

            assert sd_dist_val.bucket_options.explicit_buckets.bounds == []
            sd_dist_val.bucket_options.explicit_buckets.bounds.extend(
                [0.0] +
                list(map(float, point.value.bucket_options.type_.bounds))
            )

            assert sd_dist_val.bucket_counts == []
            sd_dist_val.bucket_counts.extend(
                [0] +
                [bb.count for bb in point.value.buckets]
            )

        elif (metric.descriptor.type ==
              metric_descriptor.MetricDescriptorType.CUMULATIVE_INT64):
            sd_point.value.int64_value = int(point.value.value)

        elif (metric.descriptor.type ==
              metric_descriptor.MetricDescriptorType.CUMULATIVE_DOUBLE):
            sd_point.value.double_value = float(point.value.value)

        elif (metric.descriptor.type ==
              metric_descriptor.MetricDescriptorType.GAUGE_INT64):
            sd_point.value.int64_value = int(point.value.value)

        elif (metric.descriptor.type ==
              metric_descriptor.MetricDescriptorType.GAUGE_DOUBLE):
            sd_point.value.double_value = float(point.value.value)

        # TODO: handle SUMMARY metrics, #567
        else:  # pragma: NO COVER
            raise TypeError("Unsupported metric type: {}"
                            .format(metric.descriptor.type))

        end = point.timestamp
        if ts.start_timestamp is None:
            start = end
        else:
            start = datetime.strptime(ts.start_timestamp, EPOCH_PATTERN)

        timestamp_start = (start - EPOCH_DATETIME).total_seconds()
        timestamp_end = (end - EPOCH_DATETIME).total_seconds()

        sd_point.interval.end_time.seconds = int(timestamp_end)

        secs = sd_point.interval.end_time.seconds
        sd_point.interval.end_time.nanos = int((timestamp_end - secs) * 1e9)

        start_time = sd_point.interval.start_time
        start_time.seconds = int(timestamp_start)
        start_time.nanos = int((timestamp_start - start_time.seconds) * 1e9)

# === BLOCK 5 (label=lm, source_idx=line235_lm, name=parse_datetime) ===
def parse_datetime(time_str):
    """
    Wraps dateutil's parser function to set an explicit UTC timezone, and
    to make sure microseconds are 0. Unified Uploader format and EMK format
    bother don't use microseconds at all.

    :param str time_str: The date/time str to parse.
    :rtype: datetime.datetime
    :returns: A parsed, UTC datetime.
    """
    dt = dateutil.parser.parse(time_str)
    dt = dt.replace(tzinfo=dateutil.tz.tzutc())
    dt = dt.replace(microsecond=0)
    return dt

# === BLOCK 6 (label=lm, source_idx=line2188_lm, name=write_paula) ===
def write_paula(docgraph, output_root_dir, human_readable=False):
    """
    converts a DiscourseDocumentGraph into a set of PAULA XML files
    representing the same document.

    Parameters
    ----------
    docgraph : DiscourseDocumentGraph
        the document graph to be converted
    """
    if not os.path.exists(output_root_dir):
        os.makedirs(output_root_dir)

    for doc in docgraph.documents:
        doc_dir = os.path.join(output_root_dir, doc.doc_id)
        if not os.path.exists(doc_dir):
            os.makedirs(doc_dir)

        doc_file = os.path.join(doc_dir, doc.doc_id + '.xml')
        with open(doc_file, 'w') as f:
            f.write(doc.to_paula_xml(human_readable))
