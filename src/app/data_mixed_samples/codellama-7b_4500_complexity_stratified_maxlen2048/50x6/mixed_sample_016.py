# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line6253_lm, name=contains) ===
def contains(self, location):
    """
    Checks that the provided point is on the sphere.
    """
    return self.contains_point(location)

# === BLOCK 2 (label=human, source_idx=line7357_human, name=load) ===
def load(self):
        """ Method which loads data from the file
        """
        # pylint: disable=too-many-return-statements
        if not os.path.isdir(self.patch_path):
            raise OSError('EOPatch does not exist in path {} anymore'.format(self.patch_path))

        path = self.get_file_path()
        if not os.path.exists(path):
            raise OSError('Feature in path {} does not exist anymore'.format(path))

        file_formats = FileFormat.split_by_extensions(path)[1:]

        if not file_formats or file_formats[-1] is FileFormat.PICKLE:
            with open(path, "rb") as infile:
                data = pickle.load(infile)

                if isinstance(data, sentinelhub.BBox) and not hasattr(data, 'crs'):
                    return self._correctly_load_bbox(data, path)
                return data

        if file_formats[-1] is FileFormat.NPY:
            if self.mmap:
                return np.load(path, mmap_mode='r')
            return np.load(path)

        if file_formats[-1] is FileFormat.GZIP:
            if file_formats[-2] is FileFormat.NPY:
                return np.load(gzip.open(path))

            if len(file_formats) == 1 or file_formats[-2] is FileFormat.PICKLE:
                data = pickle.load(gzip.open(path))

                if isinstance(data, sentinelhub.BBox) and not hasattr(data, 'crs'):
                    return self._correctly_load_bbox(data, path, is_zipped=True)
                return data

        raise ValueError('Could not load data from unsupported file format {}'.format(file_formats[-1]))

# === BLOCK 3 (label=lm, source_idx=line7281_lm, name=export) ===
def export(self, nidm_version, export_dir):
        """
        Create prov entities and activities.
        """
        # Create a new session
        session = self.create_session(nidm_version, export_dir)

        # Create a new project
        project = self.create_project(nidm_version, export_dir)

        # Create a new study
        study = self.create_study(nidm_version, export_dir)

        # Create a new assay
        assay = self.create_assay(nidm_version, export_dir)

        # Create a new dataset
        dataset = self.create_dataset(nidm_version, export_dir)

        # Create a new file
        file = self.create_file(nidm_version, export_dir)

        # Create a new variable
        variable = self.create_variable(nidm_version, export_dir)

        # Create a new variable
        variable_unit = self.create_variable_unit(nidm_version, export_dir)

        # Create a new variable
        variable_value = self.create_variable_value(nidm_version, export_dir)

        # Create a new variable
        variable_value_unit = self.create_variable_value_unit(nidm_version, export_dir)

        # Create a new variable
        variable_value_unit_value = self.create_variable_value_unit_value(nidm_version, export_dir)

        # Create a new variable
        variable_value_unit_value_unit = self.create_variable_value_unit_value_unit(nidm_version, export_dir)

        # Create a new variable
        variable_value_unit_value_unit_value = self.create_variable_value_unit_value_unit_value(nidm_version, export_dir)

        # Create a new variable
        variable_value_unit_value_unit_value_unit = self.create_variable_value_unit_value_unit_value_unit(nidm_version, export_dir)

        # Create a new variable
        variable_value_unit_value_unit_value_unit_value = self.create

# === BLOCK 4 (label=lm, source_idx=line3113_lm, name=_get_str_range) ===
def _get_str_range(self, vals_stats):
        """Return a string containing the range of values."""
        return "{} to {}".format(vals_stats.min(), vals_stats.max())

# === BLOCK 5 (label=human, source_idx=line7528_human, name=pulse) ===
def pulse(time, start, duration):
    """ Implements vensim's PULSE function

    In range [-inf, start) returns 0
    In range [start, start + duration) returns 1
    In range [start + duration, +inf] returns 0
    """
    t = time()
    return 1 if start <= t < start + duration else 0

# === BLOCK 6 (label=human, source_idx=line4016_human, name=find_port) ===
def find_port(addr, user):
    """Find local port in existing tunnels"""
    import pwd
    home = pwd.getpwuid(os.getuid()).pw_dir
    for name in os.listdir('%s/.ssh/' % home):
        if name.startswith('unixpipe_%s@%s_' % (user, addr,)):
            return int(name.split('_')[2])
