# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1638_human, name=get_learned_skills) ===
def get_learned_skills(self, lang):
        """
        Return the learned skill objects sorted by the order they were learned
        in.
        """
        skills = [skill for skill in
                  self.user_data.language_data[lang]['skills']]

        self._compute_dependency_order(skills)

        return [skill for skill in
                sorted(skills, key=lambda skill: skill['dependency_order'])
                if skill['learned']]

# === BLOCK 2 (label=lm, source_idx=line3401_lm, name=read_kw_file) ===
def read_kw_file():
    """
    Read content of the file containing keyword informations in JSON. File is
    packed using BZIP.

    Returns:
        list: List of dictionaries containing keywords.
    """
    with bz2.open('keywords.json.bz2', 'rb') as f:
        return json.load(f)

# === BLOCK 3 (label=human, source_idx=line3402_human, name=libvlc_vlm_set_output) ===
def libvlc_vlm_set_output(p_instance, psz_name, psz_output):
    """Set the output for a media.
    @param p_instance: the instance.
    @param psz_name: the media to work on.
    @param psz_output: the output MRL (the parameter to the "sout" variable).
    @return: 0 on success, -1 on error.
    """
    f = _Cfunctions.get('libvlc_vlm_set_output', None) or \
        _Cfunction('libvlc_vlm_set_output', ((1,), (1,), (1,),), None,
                    ctypes.c_int, Instance, ctypes.c_char_p, ctypes.c_char_p)
    return f(p_instance, psz_name, psz_output)

# === BLOCK 4 (label=lm, source_idx=line4868_lm, name=cortex_rgba_plot_2D) ===
def cortex_rgba_plot_2D(the_map, rgba, axes=None, triangulation=None):
    """
    cortex_rgba_plot_2D(map, rgba, axes) plots the given cortical map on the given axes using the
      given (n x 4) matrix of vertex colors and yields the resulting polygon collection object.
    cortex_rgba_plot_2D(map, rgba) uses matplotlib.pyplot.gca() for the axes.

    The option triangulation may also be passed if the triangularion object has already been
    created; otherwise it is generated fresh.
    """
    if axes is None:
        axes = plt.gca()
    if triangulation is None:
        triangulation = tri.Triangulation(the_map[:, 0], the_map[:, 1])
    polygon_collection = axes.tripcolor(triangulation, rgba[:, 3], shading='gouraud')

    return polygon_collection

# === BLOCK 5 (label=lm, source_idx=line2013_lm, name=parse_command_line_arguments) ===
def parse_command_line_arguments(argparse_parser, init_indent=5, subs_indent=5,
                                 line_width=76):
    """Main routine to call to execute the command parsing.  Returns an object
    from argparse's parse_args() routine."""
    return argparse_parser.parse_args()

# === BLOCK 6 (label=human, source_idx=line3323_human, name=walk_dir_with_filter) ===
def walk_dir_with_filter(pth, prefix=None, suffix=None):
    """
        默认情况下,会遍历目录下所有文件,写入数组返回.

    - ``prefix`` 会过滤以 其开头的所有文件
    - ``suffix`` 结尾

    :param pth:
    :type pth:
    :param prefix:
    :type prefix:
    :param suffix:
    :type suffix:
    :return:
    :rtype:
    """
    if suffix is None or type(suffix) != list:
        suffix = []
    if prefix is None or type(prefix) != list:
        prefix = []

    r = []
    for root_, dirs, files in os.walk(pth):
        for file_ in files:
            full_pth = os.path.join(root_, file_)

            # 排除 \.开头文件, 及 .pyc .md 结尾文件
            c = False
            for x in prefix:
                if file_.startswith(x):
                    c = True
                    break
            if c:
                continue
            # if runs here , c is False
            for x in suffix:
                if file_.endswith(x):
                    c = True
                    break
            if c:
                continue

            r.append(full_pth)
    return r
