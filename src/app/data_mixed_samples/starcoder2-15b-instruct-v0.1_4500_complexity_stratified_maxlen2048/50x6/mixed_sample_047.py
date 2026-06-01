# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line4239_lm, name=__generate) ===
def __generate(results):
        """
        Static method which generates the Junit xml string from results

        :param results: Results as ResultList object.
        :return: Junit xml format string.
        """
        xml = ""
        for result in results:
            xml += "<testcase name='{}' time='{}'>".format(result.name, result.time)
            if result.failure:
                xml += "<failure message='{}'>{}</failure>".format(result.failure.message, result.failure.body)
            xml += "</testcase>"
        return xml

# === BLOCK 2 (label=human, source_idx=line627_human, name=batchccn) ===
def batchccn(args):
    """
    %prog batchccn test.csv

    Run CCN script in batch. Write makefile.
    """
    p = OptionParser(batchccn.__doc__)
    opts, args = p.parse_args(args)

    if len(args) != 1:
        sys.exit(not p.print_help())

    csvfile, = args
    mm = MakeManager()
    pf = op.basename(csvfile).split(".")[0]
    mkdir(pf)

    header = next(open(csvfile))
    header = None if header.strip().endswith(".bam") else "infer"
    logging.debug("Header={}".format(header))
    df = pd.read_csv(csvfile, header=header)
    cmd = "perl /mnt/software/ccn_gcn_hg38_script/ccn_gcn_hg38.pl"
    cmd += " -n {} -b {}"
    cmd += " -o {} -r hg38".format(pf)
    for i, (sample_key, bam) in df.iterrows():
        cmdi = cmd.format(sample_key, bam)
        outfile = "{}/{}/{}.ccn".format(pf, sample_key, sample_key)
        mm.add(csvfile, outfile, cmdi)
    mm.write()

# === BLOCK 3 (label=human, source_idx=line1946_human, name=as_span) ===
def as_span(cls, lower_version=None, upper_version=None,
                lower_inclusive=True, upper_inclusive=True):
        """Create a range from lower_version..upper_version.

        Args:
            lower_version: Version object representing lower bound of the range.
            upper_version: Version object representing upper bound of the range.

        Returns:
            `VersionRange` object.
        """
        lower = (None if lower_version is None
                 else _LowerBound(lower_version, lower_inclusive))
        upper = (None if upper_version is None
                 else _UpperBound(upper_version, upper_inclusive))
        bound = _Bound(lower, upper)

        range = cls(None)
        range.bounds = [bound]
        return range

# === BLOCK 4 (label=human, source_idx=line2340_human, name=validate_types) ===
def validate_types(schemas_and_tables):
    """normalize a list of desired annotation types
    if passed None returns all types, otherwise checks that types exist
    Parameters
    ----------
    types: list[str] or None

    Returns
    -------
    list[str]
        list of types

    Raises
    ------
    UnknownAnnotationTypeException
        If types contains an invalid type
    """

    all_types = get_types()
    if not (all(sn in all_types for sn, tn in schemas_and_tables)):
        bad_types = [sn for sn,
                     tn in schemas_and_tables if sn not in all_types]
        msg = '{} are invalid types'.format(bad_types)
        raise UnknownAnnotationTypeException(msg)

# === BLOCK 5 (label=lm, source_idx=line2479_lm, name=_validate_group) ===
def _validate_group(self, group):
        """Validate a Group instance against allowed group IDs or subgroup of a parent group"""
        if group.id in self.allowed_group_ids:
            return True
        for parent_group in self.parent_groups:
            if group in parent_group.subgroups:
                return True
        return False

# === BLOCK 6 (label=lm, source_idx=line3953_lm, name=get_protocol_version) ===
async def get_protocol_version(self):
        """
        This method returns the major and minor values for the protocol
        version, i.e. 2.4

        :returns: Firmata protocol version
        """
        version_info = await self.protocol.send_sysex(PROTOCOL_VERSION)
        major = version_info[0]
        minor = version_info[1]
        return major, minor
