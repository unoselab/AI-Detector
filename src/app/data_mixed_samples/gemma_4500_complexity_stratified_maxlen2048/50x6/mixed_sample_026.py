# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1866_human, name=sense) ===
def sense(self):
        """
            Launches a few "sensing" commands such as 'ls', or 'pwd'
            and updates the current bait state.
        """
        cmd_name = random.choice(self.senses)
        command = getattr(self, cmd_name)
        self.state['last_command'] = cmd_name
        command()

# === BLOCK 2 (label=human, source_idx=line5863_human, name=revisions) ===
def revisions(self, path, max_revisions):
        """
        Get the list of revisions.

        :param path: the path to target.
        :type  path: ``str``

        :param max_revisions: the maximum number of revisions.
        :type  max_revisions: ``int``

        :return: A list of revisions.
        :rtype: ``list`` of :class:`Revision`
        """
        if self.repo.is_dirty():
            raise DirtyGitRepositoryError(self.repo.untracked_files)

        revisions = []
        for commit in self.repo.iter_commits(
            self.current_branch, max_count=max_revisions
        ):
            rev = Revision(
                key=commit.name_rev.split(" ")[0],
                author_name=commit.author.name,
                author_email=commit.author.email,
                date=commit.committed_date,
                message=commit.message,
            )
            revisions.append(rev)
        return revisions

# === BLOCK 3 (label=lm, source_idx=line7134_lm, name=intersection) ===
def intersection(self, other):
        """Returns a MOC representing the intersection with another MOC.

        >>> p = MOC(2, (3, 4, 5))
        >>> q = MOC(2, (4, 5, 6))
        >>> p.intersection(q)
        <MOC: [(2, [4, 5])]>
        """
        common_elements = sorted(list(set(self.elements) & set(other.elements)))
        return MOC(self.id, tuple(common_elements))

# === BLOCK 4 (label=human, source_idx=line3742_human, name=sort_dicoms) ===
def sort_dicoms(dicoms):
    """
    Sort the dicoms based om the image possition patient

    :param dicoms: list of dicoms
    """
    # find most significant axis to use during sorting
    # the original way of sorting (first x than y than z) does not work in certain border situations
    # where for exampe the X will only slightly change causing the values to remain equal on multiple slices
    # messing up the sorting completely)
    dicom_input_sorted_x = sorted(dicoms, key=lambda x: (x.ImagePositionPatient[0]))
    dicom_input_sorted_y = sorted(dicoms, key=lambda x: (x.ImagePositionPatient[1]))
    dicom_input_sorted_z = sorted(dicoms, key=lambda x: (x.ImagePositionPatient[2]))
    diff_x = abs(dicom_input_sorted_x[-1].ImagePositionPatient[0] - dicom_input_sorted_x[0].ImagePositionPatient[0])
    diff_y = abs(dicom_input_sorted_y[-1].ImagePositionPatient[1] - dicom_input_sorted_y[0].ImagePositionPatient[1])
    diff_z = abs(dicom_input_sorted_z[-1].ImagePositionPatient[2] - dicom_input_sorted_z[0].ImagePositionPatient[2])
    if diff_x >= diff_y and diff_x >= diff_z:
        return dicom_input_sorted_x
    if diff_y >= diff_x and diff_y >= diff_z:
        return dicom_input_sorted_y
    if diff_z >= diff_x and diff_z >= diff_y:
        return dicom_input_sorted_z

# === BLOCK 5 (label=lm, source_idx=line2156_lm, name=_result) ===
def _result(self):  # type: () -> SolverResult
        """
        Creates a #SolverResult from the decisions in _solution
        """
        return SolverResult(self._solution)

# === BLOCK 6 (label=lm, source_idx=line1605_lm, name=extend_schema_spec) ===
def extend_schema_spec(self) -> None:
        """ Injects the block start and end times """
        if hasattr(self, 'schema_spec') and self.schema_spec is not None:
            self.schema_spec['block_start_time'] = self.block_start_time
            self.schema_spec['block_end_time'] = self.block_end_time
