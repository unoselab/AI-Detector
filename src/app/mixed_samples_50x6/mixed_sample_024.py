# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line2047_human, name=lower_ext) ===
def lower_ext(abspath):
    """Convert file extension to lowercase.
    """
    fname, ext = os.path.splitext(abspath)
    return fname + ext.lower()

# === BLOCK 2 (label=human, source_idx=line1138_human, name=shift_display) ===
def shift_display(self, amount):
        """Shift the display. Use negative amounts to shift left and positive
        amounts to shift right."""
        if amount == 0:
            return
        direction = c.LCD_MOVERIGHT if amount > 0 else c.LCD_MOVELEFT
        for i in range(abs(amount)):
            self.command(c.LCD_CURSORSHIFT | c.LCD_DISPLAYMOVE | direction)
            c.usleep(50)

# === BLOCK 3 (label=lm, source_idx=line1948_lm, name=get_splits) ===
def get_splits(self, n_splits=1):
        """Return splits of this dataset ready for Cross Validation.

        If n_splits is 1, a tuple containing the X for train and test
        and the y for train and test is returned.
        Otherwise, if n_splits is bigger than 1, a list of such tuples
        is returned, one for each split.

        Args:
            n_splits (int): Number of times that the data needs to be splitted.

        Returns:
            tuple or list:
                if n_splits is 1, a tuple containing the X for train and test
                and the y for train and test is returned.
                Otherwise, if n_splits is bigger than 1, a list of such tuples
                is returned, one for each split.
        """
        if n_splits == 1:
            X_train, X_test, y_train, y_test = train_test_split(self.X, self.y, test_size=0.2)
            return (X_train, X_test, y_train, y_test)
        else:
            kf = KFold(n_splits=n_splits, shuffle=True)
            splits = []
            for train_index, test_index in kf.split(self.X):
                X_train, X_test = self.X[train_index], self.X[test_index]
                y_train, y_test = self.y[train_index], self.y[test_index]
                splits.append((X_train, X_test, y_train, y_test))
            return splits

# === BLOCK 4 (label=lm, source_idx=line1236_lm, name=_make_lib_file_symbolic_links) ===
def _make_lib_file_symbolic_links(self):
        """Make symbolic links for lib files.

        Make symbolic links from system library files or downloaded lib files
        to downloaded source library files.

        For example, case: Fedora x86_64
        Make symbolic links
        from
            a. /usr/lib64/librpmio.so* (one of them)
            b. /usr/lib64/librpm.so* (one of them)
            c. If rpm-build-libs package is installed,
               /usr/lib64/librpmbuild.so* (one of them)
               otherwise, downloaded and extracted rpm-build-libs.
               ./usr/lib64/librpmbuild.so* (one of them)
            c. If rpm-build-libs package is installed,
               /usr/lib64/librpmsign.so* (one of them)
               otherwise, downloaded and extracted rpm-build-libs.
               ./usr/lib64/librpmsign.so* (one of them)
        to
            a. rpm/rpmio/.libs/librpmio.so
            b. rpm/lib/.libs/librpm.so
            c. rpm/build/.libs/librpmbuild.so
            d. rpm/sign/.libs/librpmsign.so
        .
        This is a status after running "make" on actual rpm build process.
        """
        pass

# === BLOCK 5 (label=human, source_idx=line2864_human, name=_sort_dd_skips) ===
def _sort_dd_skips(configs, dd_indices_all):
    """Given a set of dipole-dipole configurations, sort them according to
    their current skip.

    Parameters
    ----------
    configs: Nx4 numpy.ndarray
        Dipole-Dipole configurations

    Returns
    -------
    dd_configs_sorted: dict
        dictionary with the skip as keys, and arrays/lists with indices to
        these skips.
    """
    config_current_skips = np.abs(configs[:, 1] - configs[:, 0])
    if np.all(np.isnan(config_current_skips)):
        return {0: []}

    # determine skips
    available_skips_raw = np.unique(config_current_skips)
    available_skips = available_skips_raw[
        ~np.isnan(available_skips_raw)
    ].astype(int)

    # now determine the configurations
    dd_configs_sorted = {}
    for skip in available_skips:
        indices = np.where(config_current_skips == skip)[0]
        dd_configs_sorted[skip - 1] = dd_indices_all[indices]

    return dd_configs_sorted

# === BLOCK 6 (label=lm, source_idx=line2477_lm, name=assemble_loopy) ===
def assemble_loopy():
    """Assemble INDRA Statements into a Loopy model using SIF Assembler."""
    pass
