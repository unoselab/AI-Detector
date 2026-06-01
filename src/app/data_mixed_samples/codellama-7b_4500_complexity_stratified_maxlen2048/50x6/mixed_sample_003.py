# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line7069_human, name=run_riemannian_relaxation) ===
def run_riemannian_relaxation(laplacian, initial_guess,
                              intrinsic_dim, relaxation_kwds):
    """Helper function for creating a RiemannianRelaxation class."""
    n, s = initial_guess.shape
    relaxation_kwds = initialize_kwds(relaxation_kwds, n, s, intrinsic_dim)
    if relaxation_kwds['save_init']:
        directory = relaxation_kwds['backup_dir']
        np.save(os.path.join(directory, 'Y0.npy'),initial_guess)
        sp.io.mmwrite(os.path.join(directory, 'L_used.mtx'),
                      sp.sparse.csc_matrix(laplacian))

    lossf = relaxation_kwds['lossf']
    return RiemannianRelaxation.init(lossf, laplacian, initial_guess,
                                     intrinsic_dim, relaxation_kwds)

# === BLOCK 2 (label=lm, source_idx=line3165_lm, name=walk) ===
def walk(self, top, file_list={}):
        """Walks the walk. nah, seriously: reads the file and stores a hashkey
        corresponding to its content."""
        for root, dirs, files in os.walk(top):
            for name in files:
                path = os.path.join(root, name)
                if path not in file_list:
                    file_list[path] = self.hashfile(path)

# === BLOCK 3 (label=human, source_idx=line7689_human, name=reporter) ===
def reporter(self):
        """
        Create a .csv file with the strain name, and the number of core genes present/the total number of core genes
        """
        with open(os.path.join(self.reportpath, 'Escherichia_core.csv'), 'w') as report:
            data = 'Strain,Genes Present/Total\n'
            for sample in self.runmetadata.samples:
                # Convert the set to a list for JSON serialization
                sample[self.analysistype].coreset = list(sample[self.analysistype].coreset)
                sample[self.analysistype].coreresults = '{cs}/{cg}'.format(cs=len(sample[self.analysistype].coreset),
                                                                           cg=len(self.coregenomes))
                # Add strain name, the number of core genes present, and the number of total core genes to the string
                data += '{sn},{cr}\n'.format(sn=sample.name,
                                             cr=sample[self.analysistype].coreresults)
            report.write(data)

        for sample in self.metadata:
            # Remove the messy blast results and set/list of core genes from the object
            try:
                delattr(sample[self.analysistype], "blastresults")
            except AttributeError:
                pass
            try:
                delattr(sample[self.analysistype], 'coreset')
            except AttributeError:
                pass

# === BLOCK 4 (label=human, source_idx=line7549_human, name=get) ===
def get(key, default=-1):
        """Backport support for original codes."""
        if isinstance(key, int):
            return Suite(key)
        if key not in Suite._member_map_:
            extend_enum(Suite, key, default)
        return Suite[key]

# === BLOCK 5 (label=lm, source_idx=line4851_lm, name=sorted_by_field) ===
def sorted_by_field(issues, field='closed_at', reverse=False):
    """Return a list of issues sorted by closing date date."""
    return sorted(issues, key=lambda x: x[field], reverse=reverse)

# === BLOCK 6 (label=lm, source_idx=line6133_lm, name=get_type) ===
def get_type(full_path):
    """Get the type (socket, file, dir, symlink, ...) for the provided path"""
    if os.path.isdir(full_path):
        return 'dir'
    elif os.path.isfile(full_path):
        return 'file'
    elif os.path.islink(full_path):
        return 'symlink'
    elif os.path.ismount(full_path):
        return 'mount'
    elif os.path.issocket(full_path):
        return 'socket'
    elif os.path.isblockdev(full_path):
        return 'blockdev'
    elif os.path.isfifo(full_path):
        return 'fifo'
    else:
        return 'unknown'
