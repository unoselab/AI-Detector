# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line148_human, name=determineLength) ===
def determineLength(length):
        """
        Given first read byte, determine how many more bytes
        needs to be known in order to get fully encoded length.

        :param length: First read byte.
        :return: How many bytes to read.
        """
        integer = ord(length)

        if integer < 128:
            return 0
        elif integer < 192:
            return 1
        elif integer < 224:
            return 2
        elif integer < 240:
            return 3
        else:
            raise ConnectionError('Unknown controll byte {}'.format(length))

# === BLOCK 2 (label=lm, source_idx=line249_lm, name=on_select_level_name) ===
def on_select_level_name(self,event,called_by_parent=False):
        """
        change this objects specimens_list to control which specimen interpretatoins are displayed in this objects logger
        @param: event -> the wx.ComboBoxEvent that triggered this function
        """
        if not called_by_parent:
            self.parent.on_select_level_name(event, called_by_parent=True)

# === BLOCK 3 (label=human, source_idx=line841_human, name=_list_archive_members) ===
def _list_archive_members(archive):
    """
    :param archive:
        An archive from _open_archive()

    :return:
        A list of info objects to be used with _info_name() and _extract_info()
    """

    if isinstance(archive, zipfile.ZipFile):
        return archive.infolist()
    return archive.getmembers()

# === BLOCK 4 (label=lm, source_idx=line1104_lm, name=parse_coach_go) ===
def parse_coach_go(infile):
    """Parse a GO output file from COACH and return a rank-ordered list of GO term predictions

    The columns in all files are: GO terms, Confidence score, Name of GO terms. The files are:

        - GO_MF.dat - GO terms in 'molecular function'
        - GO_BP.dat - GO terms in 'biological process'
        - GO_CC.dat - GO terms in 'cellular component'

    Args:
        infile (str): Path to any COACH GO prediction file

    Returns:
        Pandas DataFrame: Organized dataframe of results, columns defined below

            - ``go_id``: GO term ID
            - ``go_term``: GO term text
            - ``c_score``: confidence score of the GO prediction

    """
    def parse_coach_go(infile):
        column_names = ['go_id', 'c_score', 'go_term']
        df = pd.read_csv(infile, sep='\t', names=column_names)
        df = df.sort_values(by='c_score', ascending=False)
        return df

# === BLOCK 5 (label=lm, source_idx=line1420_lm, name=find_synonymous) ===
def find_synonymous(input_file, work_dir):
    """Run yn00 to find the synonymous subsitution rate for the alignment.
    """
    def find_synonymous(input_file, work_dir):
        os.chdir(work_dir)
        with open(input_file, 'r') as f:
            input_data = f.read()
        output_data = run_yn00(input_data)
        return output_data

# === BLOCK 6 (label=human, source_idx=line1464_human, name=_match_vcs_scheme) ===
def _match_vcs_scheme(url):
    # type: (str) -> Optional[str]
    """Look for VCS schemes in the URL.

    Returns the matched VCS scheme, or None if there's no match.
    """
    from pipenv.patched.notpip._internal.vcs import VcsSupport
    for scheme in VcsSupport.schemes:
        if url.lower().startswith(scheme) and url[len(scheme)] in '+:':
            return scheme
    return None
