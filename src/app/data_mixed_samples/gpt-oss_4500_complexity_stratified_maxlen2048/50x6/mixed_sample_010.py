# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line35_lm, name=queries) ===
def queries(self):
        """
        Access the queries

        :returns: twilio.rest.autopilot.v1.assistant.query.QueryList
        :rtype: twilio.rest.autopilot.v1.assistant.query.QueryList
        """

# === BLOCK 2 (label=lm, source_idx=line4240_lm, name=login) ===
def login(self):
        """Logon to the server."""

# === BLOCK 3 (label=lm, source_idx=line3162_lm, name=DP_calc) ===
def DP_calc(TPR, TNR):
    """
    Calculate DP (Discriminant power).

    :param TNR: specificity or true negative rate
    :type TNR : float
    :param TPR: sensitivity, recall, hit rate, or true positive rate
    :type TPR : float
    :return: DP as float
    """
    from math import sqrt, pi, log

    if not (0 < TPR < 1):
        raise ValueError("TPR must be between 0 and 1 (exclusive).")
    if not (0 < TNR < 1):
        raise ValueError("TNR must be between 0 and 1 (exclusive).")
    ln_tpr = log(TPR / (1 - TPR))
    ln_tnr = log(TNR / (1 - TNR))
    return (sqrt(3) / pi) * (ln_tpr - ln_tnr)

# === BLOCK 4 (label=human, source_idx=line816_human, name=use_plenary_family_view) ===
def use_plenary_family_view(self):
        """Pass through to provider FamilyLookupSession.use_plenary_family_view"""
        self._family_view = PLENARY
        # self._get_provider_session('family_lookup_session') # To make sure the session is tracked
        for session in self._get_provider_sessions():
            try:
                session.use_plenary_family_view()
            except AttributeError:
                pass

# === BLOCK 5 (label=human, source_idx=line1295_human, name=get_legacy_build_wheel_path) ===
def get_legacy_build_wheel_path(
    names,  # type: List[str]
    temp_dir,  # type: str
    req,  # type: InstallRequirement
    command_args,  # type: List[str]
    command_output,  # type: str
):
    # type: (...) -> Optional[str]
    """
    Return the path to the wheel in the temporary build directory.
    """
    # Sort for determinism.
    names = sorted(names)
    if not names:
        msg = (
            'Legacy build of wheel for {!r} created no files.\n'
        ).format(req.name)
        msg += format_command(command_args, command_output)
        logger.warning(msg)
        return None

    if len(names) > 1:
        msg = (
            'Legacy build of wheel for {!r} created more than one file.\n'
            'Filenames (choosing first): {}\n'
        ).format(req.name, names)
        msg += format_command(command_args, command_output)
        logger.warning(msg)

    return os.path.join(temp_dir, names[0])

# === BLOCK 6 (label=human, source_idx=line969_human, name=_clone_node) ===
def _clone_node(self) -> 'Tag':
        """Need to copy class, not tag.

        So need to re-implement copy.
        """
        clone = type(self)()
        for attr in self.attributes:
            clone.setAttribute(attr, self.getAttribute(attr))
        for c in self.classList:
            clone.addClass(c)
        clone.style.update(self.style)
        # TODO: should clone event listeners???
        return clone
