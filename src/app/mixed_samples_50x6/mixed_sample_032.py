# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line2390_lm, name=wiki_revert) ===
def wiki_revert(self, title, version):
        """Function to revert a specific wiki page (Requires login) (UNTESTED).

        Parameters:
            title (str): The title of the wiki page to update.
            version (int): The version to revert to.
        """
        if not self.is_logged_in:
            raise Exception("User is not logged in.")
        self.wiki_update(title, version)

# === BLOCK 2 (label=human, source_idx=line1517_human, name=_usage_endpoint) ===
def _usage_endpoint(self, endpoint, year=None, month=None):
        """
        Common helper for getting usage and billing reports with
        optional year and month URL elements.

        :param str endpoint: Cloudant usage endpoint.
        :param int year: Year to query against.  Optional parameter.
            Defaults to None.  If used, it must be accompanied by ``month``.
        :param int month: Month to query against that must be an integer
            between 1 and 12. Optional parameter. Defaults to None.
            If used, it must be accompanied by ``year``.
        """
        err = False
        if year is None and month is None:
            resp = self.r_session.get(endpoint)
        else:
            try:
                if int(year) > 0 and int(month) in range(1, 13):
                    resp = self.r_session.get(
                        '/'.join((endpoint, str(int(year)), str(int(month)))))
                else:
                    err = True
            except (ValueError, TypeError):
                err = True

        if err:
            raise CloudantArgumentError(101, year, month)

        resp.raise_for_status()
        return response_to_json_dict(resp)

# === BLOCK 3 (label=human, source_idx=line1716_human, name=get_fastq_files_props) ===
def get_fastq_files_props(self,barcode=None):
        """
        Returns the DNAnexus file properties for all FASTQ files in the project that match the 
        specified barcode, or all FASTQ files if not barcode is specified.

        Args:
            barcode: `str`. If set, then only FASTQ file properties for FASTQ files having the specified barcode are returned.

        Returns:
            `dict`. Keys are the FASTQ file DXFile objects; values are the dict of associated properties 
            on DNAnexus on the file. In addition to the properties on the file in DNAnexus, an 
            additional property is added here called 'fastq_file_name'.

        Raises:
            dnanexus_utils.FastqNotFound exception if no FASTQ files were found.
        """
        fastqs = self.get_fastq_dxfile_objects(barcode=barcode)   #FastqNotFound Exception here if no FASTQs found for specified barcode.
        dico = {}
        for f in fastqs:
            #props = dxpy.api.file_describe(object_id=f.id, input_params={"fields": {"properties": True}})["properties"]
            props = f.get_properties()
            dico[f] = props
            dico[f]["fastq_file_name"] = f.name
        return dico

# === BLOCK 4 (label=lm, source_idx=line1487_lm, name=Tube) ===
def Tube(points, r=1, c="r", alpha=1, res=12):
    """Build a tube along the line defined by a set of points.

    :param r: constant radius or list of radii.
    :type r: float, list
    :param c: constant color or list of colors for each point.
    :type c: float, list

    .. hint:: |ribbon| |ribbon.py|_

        |tube| |tube.py|_
    """
    if isinstance(r, list) and len(r)!= len(points):
        raise ValueError("The number of radii must match the number of points.")
    if isinstance(c, list) and len(c)!= len(points):
        raise ValueError("The number of colors must match the number of points.")
    if not isinstance(res, int) or res < 3:
        raise ValueError("The resolution must be an integer greater than or equal to 3.")
    if not isinstance(alpha, float) or not (0 <= alpha <= 1):
        raise ValueError("The alpha value must be a float between 0 and 1.")
    if not isinstance(points, list) or not all(isinstance(p, list) for p in points):
        raise ValueError("The points must be a list of lists.")
    if isinstance(r, list):
        radii = r
    else:
        radii = [r] * len(points)
    if isinstance(c, list):
        colors = c
    else:
        colors = [c] * len(points)
    tube_points = []
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i + 1]
        v = [p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]]
        u = [v[1], -v[0], 0]
        if u == [0, 0, 0]:
            u = [0, 1, 0]
        u_norm = [u[0] / (u[0] ** 2 + u[1] ** 2 + u[2] ** 2) ** 0.5, u[1] / (u[0] ** 2 + u[1] ** 2 + u[2] ** 2) ** 0.5, u[2] / (u[0] ** 2 + u[1] ** 2 + u[2] ** 2) ** 0.5]
        theta = 2 * 3.141592

# === BLOCK 5 (label=human, source_idx=line1409_human, name=__load) ===
def __load(arff):
    """
    load liac-arff to pandas DataFrame
    :param dict arff:arff dict created liac-arff
    :rtype: DataFrame
    :return: pandas DataFrame
    """
    attrs = arff['attributes']
    attrs_t = []
    for attr in attrs:
        if isinstance(attr[1], list):
            attrs_t.append("%s@{%s}" % (attr[0], ','.join(attr[1])))
        else:
            attrs_t.append("%s@%s" % (attr[0], attr[1]))

    df = pd.DataFrame(data=arff['data'], columns=attrs_t)
    return df

# === BLOCK 6 (label=lm, source_idx=line1574_lm, name=tlog) ===
def tlog(x, th=1, r=_display_max, d=_l_mmax):
    """
    Truncated log10 transform.

    Parameters
    ----------
    x : num | num iterable
        values to be transformed.
    th : num
        values below th are transormed to 0.
        Must be positive.
    r : num (default = 10**4)
        maximal transformed value.
    d : num (default = log10(2**18))
        log10 of maximal possible measured value.
        tlog(10**d) = r

    Returns
    -------
    Array of transformed values.
    """
    def tlog(x, th=1, r=10**4, d=np.log10(2**18)):
        x = np.asarray(x)
        x[x < th] = 0
        x = np.log10(x)
        x[x < 0] = 0
        x = x / d * r
        x[x > r] = r

        return x
