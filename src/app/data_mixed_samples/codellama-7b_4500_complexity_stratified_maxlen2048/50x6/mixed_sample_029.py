# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1595_human, name=add_host) ===
def add_host(host):
    """ Put your host information in the prefix object. """
    p = new_prefix()
    p.prefix = str(host['ipaddr'])
    p.type = "host"
    p.description = host['description']
    p.node = host['fqdn']
    p.avps = {}

    # Use remaining data from ipplan to populate comment field.
    if 'additional' in host:
        p.comment = host['additional']

    # Use specific info to create extra attributes.
    if len(host['location']) > 0:
        p.avps['location'] = host['location']

    if len(host['mac']) > 0:
        p.avps['mac'] = host['mac']

    if len(host['phone']) > 0:
        p.avps['phone'] = host['phone']

    if len(host['user']) > 0:
        p.avps['user'] = host['user']

    return p

# === BLOCK 2 (label=lm, source_idx=line1664_lm, name=_get_url_path) ===
def _get_url_path(list_name):
    """
    Live Dao requires RESTCLIENTS_MAILMAN_KEY in the settings.py
    """
    return '/'.join([
        settings.RESTCLIENTS_MAILMAN_HOST,
        'api',
        'v1',
        'list',
        list_name,
    ])

# === BLOCK 3 (label=human, source_idx=line7661_human, name=get_layout) ===
def get_layout():
    """Specify a hierarchy of our templates."""
    tica_msm = TemplateDir(
        'tica',
        [
            'tica/tica.py',
            'tica/tica-plot.py',
            'tica/tica-sample-coordinate.py',
            'tica/tica-sample-coordinate-plot.py',
        ],
        [
            TemplateDir(
                'cluster',
                [
                    'cluster/cluster.py',
                    'cluster/cluster-plot.py',
                    'cluster/sample-clusters.py',
                    'cluster/sample-clusters-plot.py',
                ],
                [
                    TemplateDir(
                        'msm',
                        [
                            'msm/timescales.py',
                            'msm/timescales-plot.py',
                            'msm/microstate.py',
                            'msm/microstate-plot.py',
                            'msm/microstate-traj.py',
                        ],
                        [],
                    )
                ]
            )
        ]
    )
    layout = TemplateDir(
        '',
        [
            '0-test-install.py',
            '1-get-example-data.py',
            'README.md',
        ],
        [
            TemplateDir(
                'analysis',
                [
                    'analysis/gather-metadata.py',
                    'analysis/gather-metadata-plot.py',
                ],
                [
                    TemplateDir(
                        'rmsd',
                        [
                            'rmsd/rmsd.py',
                            'rmsd/rmsd-plot.py',
                        ],
                        [],
                    ),
                    TemplateDir(
                        'landmarks',
                        [
                            'landmarks/find-landmarks.py',
                            'landmarks/featurize.py',
                            'landmarks/featurize-plot.py',
                        ],
                        [tica_msm],
                    ),
                    TemplateDir(
                        'dihedrals',
                        [
                            'dihedrals/featurize.py',
                            'dihedrals/featurize-plot.py',
                        ],
                        [tica_msm],
                    )
                ]
            )
        ]
    )
    return layout

# === BLOCK 4 (label=lm, source_idx=line7200_lm, name=from_param) ===
def from_param(cls, param):
        """
        Construct a CommandSpec from a parameter to build_scripts, which may
        be None.
        """
        if param is None:
            return None
        elif isinstance(param, cls):
            return param
        elif isinstance(param, dict):
            return cls(**param)
        else:
            raise TypeError("Expected CommandSpec or dict, got %r" % param)

# === BLOCK 5 (label=lm, source_idx=line4534_lm, name=warmup) ===
def warmup(f):
    """ Decorator to run warmup before running a command """

# === BLOCK 6 (label=human, source_idx=line3418_human, name=configure_logger) ===
def configure_logger(level, format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'):
    # type: (int, str) -> None
    """Set logger configuration.

    Args:
        level (int): Logger level
        format (str): Logger format
    """
    logging.basicConfig(format=format, level=level)

    if level >= logging.INFO:
        logging.getLogger('boto3').setLevel(logging.INFO)
        logging.getLogger('s3transfer').setLevel(logging.INFO)
        logging.getLogger('botocore').setLevel(logging.WARN)
