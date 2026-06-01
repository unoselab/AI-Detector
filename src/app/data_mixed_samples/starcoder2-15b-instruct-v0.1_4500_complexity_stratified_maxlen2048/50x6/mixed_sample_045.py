# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line4296_lm, name=get_factory) ===
def get_factory(self, factory, default='File'):
        """Return a factory function for creating Nodes for this
        construction environment.
        """
        if factory is None:
            return self.get_factory(default)
        return factory

# === BLOCK 2 (label=human, source_idx=line2290_human, name=merge_leaderboards) ===
def merge_leaderboards(self, destination, keys, aggregate='SUM'):
        """
        Merge leaderboards given by keys with this leaderboard into a named destination leaderboard.

        @param destination [String] Destination leaderboard name.
        @param keys [Array] Leaderboards to be merged with the current leaderboard.
        @param options [Hash] Options for merging the leaderboards.
        """
        keys.insert(0, self.leaderboard_name)
        self.redis_connection.zunionstore(destination, keys, aggregate)

# === BLOCK 3 (label=lm, source_idx=line3152_lm, name=_se_all) ===
def _se_all(self):
        """Standard errors (SE) for all parameters, including the intercept."""
        X = self._add_intercept(self.X)
        vcov = self._vcov(X, self.y)
        se = np.sqrt(np.diag(vcov))
        return se

# === BLOCK 4 (label=human, source_idx=line694_human, name=update_firmware) ===
def update_firmware(self, device, id_override=None, type_override=None):
        """
        Make a call to the update_firmware endpoint. As far as I know this
        is only valid for Wink hubs.

        Args:
            device (WinkDevice): The device the change is being requested for.
            id_override (String, optional): A device ID used to override the
                passed in device's ID. Used to make changes on sub-devices.
                i.e. Outlet in a Powerstrip. The Parent device's ID.
            type_override (String, optional): Used to override the device type
                when a device inherits from a device other than WinkDevice.
        Returns:
            response_json (Dict): The API's response in dictionary format
        """
        object_id = id_override or device.object_id()
        object_type = type_override or device.object_type()
        url_string = "{}/{}s/{}/update_firmware".format(self.BASE_URL,
                                                        object_type,
                                                        object_id)
        try:
            arequest = requests.post(url_string,
                                     headers=API_HEADERS)
            response_json = arequest.json()
            return response_json
        except requests.exceptions.RequestException:
            return None

# === BLOCK 5 (label=lm, source_idx=line1421_lm, name=gc) ===
def gc(self):
        """ Garbage collect overflow and/or aged entries. """
        self.overflow = []
        self.aged = []

# === BLOCK 6 (label=human, source_idx=line3835_human, name=Glyph) ===
def Glyph(actor, glyphObj, orientationArray="", 
          scaleByVectorSize=False, c=None, alpha=1):
    """
    At each vertex of a mesh, another mesh - a `'glyph'` - is shown with
    various orientation options and coloring.

    Color can be specfied as a colormap which maps the size of the orientation
    vectors in `orientationArray`.

    :param orientationArray: list of vectors, ``vtkAbstractArray``
        or the name of an already existing points array.
    :type orientationArray: list, str, vtkAbstractArray
    :param bool scaleByVectorSize: glyph mesh is scaled by the size of
        the vectors.

    .. hint:: |glyphs| |glyphs.py|_

        |glyphs_arrow| |glyphs_arrow.py|_
    """
    cmap = None
    # user passing a color map to map orientationArray sizes
    if c in list(colors._mapscales.keys()):
        cmap = c
        c = None

    # user is passing an array of point colors
    if utils.isSequence(c) and len(c) > 3:
        ucols = vtk.vtkUnsignedCharArray()
        ucols.SetNumberOfComponents(3)
        ucols.SetName("glyphRGB")
        for col in c:
            cl = colors.getColor(col)
            ucols.InsertNextTuple3(cl[0]*255, cl[1]*255, cl[2]*255)
        actor.polydata().GetPointData().SetScalars(ucols)
        c = None

    if isinstance(glyphObj, Actor):
        glyphObj = glyphObj.clean().polydata()

    gly = vtk.vtkGlyph3D()
    gly.SetInputData(actor.polydata())
    gly.SetSourceData(glyphObj)
    gly.SetColorModeToColorByScalar()

    if orientationArray != "":
        gly.OrientOn()
        gly.SetScaleFactor(1)

        if scaleByVectorSize:
            gly.SetScaleModeToScaleByVector()
        else:
            gly.SetScaleModeToDataScalingOff()

        if orientationArray == "normals" or orientationArray == "Normals":
            gly.SetVectorModeToUseNormal()
        elif isinstance(orientationArray, vtk.vtkAbstractArray):
            actor.GetMapper().GetInput().GetPointData().AddArray(orientationArray)
            actor.GetMapper().GetInput().GetPointData().SetActiveVectors("glyph_vectors")
            gly.SetInputArrayToProcess(0, 0, 0, 0, "glyph_vectors")
            gly.SetVectorModeToUseVector()
        elif utils.isSequence(orientationArray):  # passing a list
            actor.addPointVectors(orientationArray, "glyph_vectors")
            gly.SetInputArrayToProcess(0, 0, 0, 0, "glyph_vectors")
        else:  # passing a name
            gly.SetInputArrayToProcess(0, 0, 0, 0, orientationArray)
            gly.SetVectorModeToUseVector()
        if cmap:
            gly.SetColorModeToColorByVector ()
        else:
            gly.SetColorModeToColorByScalar ()


    gly.Update()
    pd = gly.GetOutput()

    actor = Actor(pd, c, alpha)

    if cmap:
        lut = vtk.vtkLookupTable()
        lut.SetNumberOfTableValues(512)
        lut.Build()
        for i in range(512):
            r, g, b = colors.colorMap(i, cmap, 0, 512)
            lut.SetTableValue(i, r, g, b, 1)
        actor.mapper.SetLookupTable(lut)
        actor.mapper.ScalarVisibilityOn()
        actor.mapper.SetScalarModeToUsePointData()    
        rng = pd.GetPointData().GetScalars().GetRange()
        actor.mapper.SetScalarRange(rng[0], rng[1])

    actor.GetProperty().SetInterpolationToFlat()
    settings.collectable_actors.append(actor)
    return actor
