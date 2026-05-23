# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1603_lm, name=_variant_po_to_dict) ===
def _variant_po_to_dict(tokens) -> CentralDogma:
    """Convert a PyParsing data dictionary to a central dogma abundance (i.e., Protein, RNA, miRNA, Gene).

    :type tokens: ParseResult
    """
    return CentralDogma(
        protein=tokens["protein"],
        rna=tokens["rna"],
        mirna=tokens["mirna"],
        gene=tokens["gene"],
    )

# === BLOCK 2 (label=lm, source_idx=line1494_lm, name=to_env_var) ===
def to_env_var(env_var: str, value) -> str:
    """
    Create an environment variable from a name and a value.

    This generates a shell-compatible representation of an
    environment variable that is assigned a YAML representation of
    a value.

    Args:
        env_var (str): Name of the environment variable.
        value (Any): A value we convert from.
    """
    return f"{env_var}={yaml.dump(value)}"

# === BLOCK 3 (label=human, source_idx=line900_human, name=get_doc) ===
def get_doc(logger=None, plugin=None, reporthook=None):
    """
    Return URL to documentation. Attempt download if does not exist.

    Parameters
    ----------
    logger : obj or `None`
        Ginga logger.

    plugin : obj or `None`
        Plugin object. If given, URL points to plugin doc directly.
        If this function is called from within plugin class,
        pass ``self`` here.

    reporthook : callable or `None`
        Report hook for ``urlretrieve()``.

    Returns
    -------
    url : str or `None`
        URL to local documentation, if available.

    """
    from ginga.GingaPlugin import GlobalPlugin, LocalPlugin

    if isinstance(plugin, GlobalPlugin):
        plugin_page = 'plugins_global'
        plugin_name = str(plugin)
    elif isinstance(plugin, LocalPlugin):
        plugin_page = 'plugins_local'
        plugin_name = str(plugin)
    else:
        plugin_page = None
        plugin_name = None

    try:
        index_html = _download_rtd_zip(reporthook=reporthook)

    # Download failed, use online resource
    except Exception as e:
        url = 'https://ginga.readthedocs.io/en/latest/'

        if plugin_name is not None:
            if toolkit.family.startswith('qt'):
                # This displays plugin docstring.
                url = None
            else:
                # This redirects to online doc.
                url += 'manual/{}/{}.html'.format(plugin_page, plugin_name)

        if logger is not None:
            logger.error(str(e))

    # Use local resource
    else:
        pfx = 'file:'
        url = '{}{}'.format(pfx, index_html)

        # https://github.com/rtfd/readthedocs.org/issues/2803
        if plugin_name is not None:
            url += '#{}'.format(plugin_name)

    return url

# === BLOCK 4 (label=human, source_idx=line1487_human, name=Tube) ===
def Tube(points, r=1, c="r", alpha=1, res=12):
    """Build a tube along the line defined by a set of points.

    :param r: constant radius or list of radii.
    :type r: float, list
    :param c: constant color or list of colors for each point.
    :type c: float, list

    .. hint:: |ribbon| |ribbon.py|_

        |tube| |tube.py|_
    """
    ppoints = vtk.vtkPoints()  # Generate the polyline
    ppoints.SetData(numpy_to_vtk(points, deep=True))
    lines = vtk.vtkCellArray()
    lines.InsertNextCell(len(points))
    for i in range(len(points)):
        lines.InsertCellPoint(i)
    polyln = vtk.vtkPolyData()
    polyln.SetPoints(ppoints)
    polyln.SetLines(lines)

    tuf = vtk.vtkTubeFilter()
    tuf.CappingOn()
    tuf.SetNumberOfSides(res)
    tuf.SetInputData(polyln)
    if utils.isSequence(r):
        arr = numpy_to_vtk(np.ascontiguousarray(r), deep=True)
        arr.SetName("TubeRadius")
        polyln.GetPointData().AddArray(arr)
        polyln.GetPointData().SetActiveScalars("TubeRadius")
        tuf.SetVaryRadiusToVaryRadiusByAbsoluteScalar()
    else:
        tuf.SetRadius(r)

    usingColScals = False
    if utils.isSequence(c) and len(c) != 3:
        usingColScals = True
        cc = vtk.vtkUnsignedCharArray()
        cc.SetName("TubeColors")
        cc.SetNumberOfComponents(3)
        cc.SetNumberOfTuples(len(c))
        for i, ic in enumerate(c):
            r, g, b = colors.getColor(ic)
            cc.InsertTuple3(i, int(255 * r), int(255 * g), int(255 * b))
        polyln.GetPointData().AddArray(cc)
        c = None

    tuf.Update()
    polytu = tuf.GetOutput()

    actor = Actor(polytu, c=c, alpha=alpha, computeNormals=0)
    actor.phong()
    if usingColScals:
        actor.mapper.SetScalarModeToUsePointFieldData()
        actor.mapper.ScalarVisibilityOn()
        actor.mapper.SelectColorArray("TubeColors")
        actor.mapper.Modified()

    actor.base = np.array(points[0])
    actor.top = np.array(points[-1])
    settings.collectable_actors.append(actor)
    return actor

# === BLOCK 5 (label=human, source_idx=line36_human, name=translate_text) ===
def translate_text(estimator, subtokenizer, txt):
  """Translate a single string."""
  encoded_txt = _encode_and_add_eos(txt, subtokenizer)

  def input_fn():
    ds = tf.data.Dataset.from_tensors(encoded_txt)
    ds = ds.batch(_DECODE_BATCH_SIZE)
    return ds

  predictions = estimator.predict(input_fn)
  translation = next(predictions)["outputs"]
  translation = _trim_and_decode(translation, subtokenizer)
  print("Translation of \"%s\": \"%s\"" % (txt, translation))

# === BLOCK 6 (label=lm, source_idx=line1801_lm, name=remove_fpaths) ===
def remove_fpaths(fpaths, verbose=VERBOSE, quiet=QUIET, strict=False,
                  print_caller=PRINT_CALLER, lbl='files'):
    """
    Removes multiple file paths
    """
    if not isinstance(fpaths, list):
        raise TypeError('fpaths must be a list')
    if not all(isinstance(fpath, str) for fpath in fpaths):
        raise TypeError('all elements of fpaths must be strings')
    if not all(os.path.exists(fpath) for fpath in fpaths):
        if strict:
            raise FileNotFoundError('one or more file paths do not exist')
        else:
            fpaths = [fpath for fpath in fpaths if os.path.exists(fpath)]
    if print_caller:
        caller = get_caller()
        print(f'Called by {caller}')
    for fpath in fpaths:
        try:
            os.remove(fpath)
        except OSError as e:
            if not quiet:
                print(f'Error removing {fpath}: {e}')
    if verbose:
        print(f'Removed {len(fpaths)} {lbl}')
