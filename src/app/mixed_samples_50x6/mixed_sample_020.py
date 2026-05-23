# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1973_lm, name=VCStoreRefs) ===
def VCStoreRefs(self):
        """
        Microsoft Visual C++ store references Libraries
        """
        self.StoreRefs(self.msvcr_libs)

# === BLOCK 2 (label=human, source_idx=line1539_human, name=crossover) ===
def crossover(self, chromosome, point1, point2=None):
        """
        Exchange DNA with another chromosome of equal length at one or two common points.

        For example, consider chromosomes:
          1. 11110000
          2. 00001111

        If the crossover point is 4, the exchange results in a new DNA arrangement:
          1. 11111111
          2. 00000000

        If 2 points are used--3 and 6--this happens:

          1. 11001100
          2. 00110011

        chromosome:  other ``Chromosome`` to exchange DNA with
        point1:  zero-based index used for the first (and possibly only) crossover point
        point2:  zero-based index used for the second (optional) crossover point; must be > point1
        """
        assert self.length == chromosome.length

        if point2 is None:
            new_dna = self.dna[:point1] + chromosome.dna[point1:]
            other_new_dna = chromosome.dna[:point1] + self.dna[point1:]

            self.dna = new_dna
            chromosome.dna = other_new_dna
        else:
            assert point2 > point1
            self_substr = self.dna[point1:point2 + 1]
            other_substr = chromosome.dna[point1:point2 + 1]

            self.dna = self.dna[:point1] + other_substr + self.dna[point2 + 1:]
            chromosome.dna = chromosome.dna[:point1] + self_substr + chromosome.dna[point2 + 1:]

# === BLOCK 3 (label=lm, source_idx=line123_lm, name=get_glacier_poly) ===
def get_glacier_poly():
    """Calls external shell script `get_rgi.sh` to fetch:

    Randolph Glacier Inventory (RGI) glacier outline shapefiles 

    Full RGI database: rgi50.zip is 410 MB

    The shell script will unzip and merge regional shp into single global shp

    http://www.glims.org/RGI/
    """
    subprocess.run(["./get_rgi.sh"])

# === BLOCK 4 (label=human, source_idx=line2332_human, name=libvlc_media_parse_with_options) ===
def libvlc_media_parse_with_options(p_md, parse_flag):
    """Parse the media asynchronously with options.
    This fetches (local or network) art, meta data and/or tracks information.
    This method is the extended version of L{libvlc_media_parse_async}().
    To track when this is over you can listen to libvlc_MediaParsedChanged
    event. However if this functions returns an error, you will not receive this
    event.
    It uses a flag to specify parse options (see libvlc_media_parse_flag_t). All
    these flags can be combined. By default, media is parsed if it's a local
    file.
    See libvlc_MediaParsedChanged
    See L{libvlc_media_get_meta}
    See L{libvlc_media_tracks_get}
    See libvlc_media_parse_flag_t.
    @param p_md: media descriptor object.
    @param parse_flag: parse options:
    @return: -1 in case of error, 0 otherwise.
    @version: LibVLC 3.0.0 or later.
    """
    f = _Cfunctions.get('libvlc_media_parse_with_options', None) or \
        _Cfunction('libvlc_media_parse_with_options', ((1,), (1,),), None,
                    ctypes.c_int, Media, MediaParseFlag)
    return f(p_md, parse_flag)

# === BLOCK 5 (label=human, source_idx=line1104_human, name=parse_coach_go) ===
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
    go_list = []

    with open(infile) as go_file:
        for line in go_file.readlines():
            go_dict = {}

            go_split = line.split()
            go_dict['go_id'] = go_split[0]
            go_dict['c_score'] = go_split[1]
            go_dict['go_term'] = ' '.join(go_split[2:])

            go_list.append(go_dict)

    return go_list

# === BLOCK 6 (label=lm, source_idx=line1552_lm, name=to_dict) ===
def to_dict(self):
        """ Convert the Paginator into a dict """
        return {
            'count': self.count,
            'num_pages': self.num_pages,
            'page_size': self.page_size,
           'results': [item.to_dict() for item in self.results]
        }
