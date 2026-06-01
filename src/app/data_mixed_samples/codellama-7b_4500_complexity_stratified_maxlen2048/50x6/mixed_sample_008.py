# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line373_lm, name=catch_raise_api_exception) ===
def catch_raise_api_exception():
    """Context manager that translates upstream API exceptions."""
    try:
        yield
    except Exception as e:
        raise APIException(e)

# === BLOCK 2 (label=lm, source_idx=line7782_lm, name=get_num_sequenced) ===
def get_num_sequenced(study_id):
    """Return number of sequenced tumors for given study.

    This is useful for calculating mutation statistics in terms of the
    prevalence of certain mutations within a type of cancer.

    Parameters
    ----------
    study_id : str
        The ID of the cBio study.
        Example: 'paad_icgc'

    Returns
    -------
    num_case : int
        The number of sequenced tumors in the given study
    """
    query = """
        SELECT COUNT(DISTINCT(case_id))
        FROM {study_id}_mutations
        """.format(study_id=study_id)
    return _get_num_sequenced(query)

# === BLOCK 3 (label=human, source_idx=line7432_human, name=name) ===
def name(self):
    """str: name of the file entry, without the full path."""
    path = getattr(self.path_spec, 'location', None)
    if path is not None and not isinstance(path, py2to3.UNICODE_TYPE):
      try:
        path = path.decode(self._file_system.encoding)
      except UnicodeDecodeError:
        path = None
    return self._file_system.BasenamePath(path)

# === BLOCK 4 (label=human, source_idx=line3104_human, name=is_a_module) ===
def is_a_module(self, module_type):
        """
        Is the module of the required type?

        :param module_type: module type to check
        :type: str
        :return: True / False
        """
        if hasattr(self, 'type'):
            return module_type in self.type
        return module_type in self.module_types

# === BLOCK 5 (label=human, source_idx=line4352_human, name=translate_to) ===
def translate_to(compound, pos):
    """Translate a compound to a coordinate.

    Parameters
    ----------
    compound : mb.Compound
        The compound being translated.
    pos : np.ndarray, shape=(3,), dtype=float
        The coordinate to translate the compound to.

    """
    atom_positions = compound.xyz_with_ports
    atom_positions -= compound.center
    atom_positions = Translation(pos).apply_to(atom_positions)
    compound.xyz_with_ports = atom_positions

# === BLOCK 6 (label=lm, source_idx=line7652_lm, name=add_member) ===
def add_member(self, login):
        """Add ``login`` to this team.

        :returns: bool
        """
        return self._requester.requestJsonAndCheck(
            "PUT",
            self.url + "/members/" + login,
            None,
            expectedCode=204
        )
