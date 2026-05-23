# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1522_lm, name=upload_permanent_media) ===
def upload_permanent_media(self, media_type, media_file):
        """
        上传其他类型永久素材。

        :param media_type: 媒体文件类型，分别有图片（image）、语音（voice）和缩略图（thumb）
        :param media_file: 要上传的文件，一个 File-object
        :return: 返回的 JSON 数据包
        """
        data = {
           'media': media_file,
        }
        url = 'https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={}&type={}'.format(self.access_token, media_type)
        return self.post(url, data=data)

# === BLOCK 2 (label=lm, source_idx=line1364_lm, name=get_queryset) ===
def get_queryset(self):  # DROP_WITH_DJANGO15
        """Use the same ordering as TreeManager"""
        return super(TreeManager, self).get_queryset().order_by('tree_id', 'lft')

# === BLOCK 3 (label=lm, source_idx=line1733_lm, name=processTPED) ===
def processTPED(uniqueSNPs, mapF, fileName, tfam, prefix):
    """Process the TPED file.

    :param uniqueSNPs: the unique markers.
    :param mapF: a representation of the ``map`` file.
    :param fileName: the name of the ``tped`` file.
    :param tfam: the name of the ``tfam`` file.
    :param prefix: the prefix of all the files.

    :type uniqueSNPs: dict
    :type mapF: list
    :type fileName: str
    :type tfam: str
    :type prefix: str

    :returns: a tuple with the representation of the ``tped`` file
              (:py:class:`numpy.array`) as first element, and the updated
              position of the duplicated markers in the ``tped``
              representation.

    Copies the ``tfam`` file into ``prefix.unique_snps.tfam``. While reading
    the ``tped`` file, creates a new one (``prefix.unique_snps.tped``)
    containing only unique markers.

    """
    def processTPED(uniqueSNPs, mapF, fileName, tfam, prefix):
        tped = []
        duplicated_positions = []
        with open(fileName, 'r') as f:
            for line in f:
                fields = line.strip().split()
                marker = fields[1]
                if marker in uniqueSNPs:
                    tped.append(fields)
                else:
                    duplicated_positions.append(uniqueSNPs[marker])
        np_tped = np.array(tped)
        with open(f'{prefix}.unique_snps.tfam', 'w') as f:
            with open(tfam, 'r') as tfam_f:
                f.write(tfam_f.read())
        with open(f'{prefix}.unique_snps.tped', 'w') as f:
            for line in np_tped:
                f.write('\t'.join(line) + '\n')

        return np_tped, duplicated_positions

# === BLOCK 4 (label=human, source_idx=line1557_human, name=get_keywords_output) ===
def get_keywords_output(single_keywords, composite_keywords, taxonomy_name,
                        author_keywords=None, acronyms=None,
                        output_mode="text", output_limit=0, spires=False,
                        only_core_tags=False):
    """Return a formatted string representing the keywords in the chosen style.

    This is the main routing call, this function will
    also strip unwanted keywords before output and limits the number
    of returned keywords.

    :param single_keywords: list of single keywords
    :param composite_keywords: list of composite keywords
    :param taxonomy_name: string, taxonomy name
    :param author_keywords: dictionary of author keywords extracted
    :param acronyms: dictionary of extracted acronyms
    :param output_mode: text|html|marc
    :param output_limit: int, number of maximum keywords printed (it applies
            to single and composite keywords separately)
    :param spires: boolen meaning spires output style
    :param only_core_tags: boolean
    """
    categories = {}
    # sort the keywords, but don't limit them (that will be done later)
    single_keywords_p = _sort_kw_matches(single_keywords)

    composite_keywords_p = _sort_kw_matches(composite_keywords)

    for w in single_keywords_p:
        categories[w[0].concept] = w[0].type
    for w in single_keywords_p:
        categories[w[0].concept] = w[0].type

    categories = [{'keyword': key, 'category': value}
                  for key, value in categories.iteritems()]

    complete_output = _output_complete(single_keywords_p, composite_keywords_p,
                                       author_keywords, acronyms, spires,
                                       only_core_tags, limit=output_limit)
    functions = {
        "text": _output_text,
        "marcxml": _output_marc,
        "html": _output_html,
        "dict": _output_dict
    }

    if output_mode != "raw":
        return functions[output_mode](complete_output, categories)
    else:
        if output_limit > 0:
            return (
                _kw(_sort_kw_matches(single_keywords, output_limit)),
                _kw(_sort_kw_matches(composite_keywords, output_limit)),
                author_keywords,  # this we don't limit (?)
                _kw(_sort_kw_matches(acronyms, output_limit))
            )
        else:
            return (single_keywords_p, composite_keywords_p,
                    author_keywords, acronyms)

# === BLOCK 5 (label=lm, source_idx=line1146_lm, name=from_string_pairs) ===
def from_string_pairs(cls, string_value_pairs, **kwargs):
        """Build an :class:`~.REMap` from str, value pairs by applying
        `re.compile` to each string and calling the __init__ of :class:`~.REMap`
        """
        regexes = [re.compile(string) for string, value in string_value_pairs]
        return cls(regexes, [value for string, value in string_value_pairs], **kwargs)

# === BLOCK 6 (label=lm, source_idx=line1935_lm, name=fo_pct) ===
def fo_pct(self):
        """
        Get the by team overall face-off win %.

        :returns: dict, ``{ 'home': %, 'away': % }``
        """
        home_fo = self.home_team_stats['faceOffWinPercentage']
        away_fo = self.away_team_stats['faceOffWinPercentage']
        return {'home': home_fo, 'away': away_fo}
