# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line111_human, name=getReqId) ===
def getReqId(self) -> int:
        """
        Get new request ID.
        """
        if not self.isReady():
            raise ConnectionError('Not connected')
        newId = self._reqIdSeq
        self._reqIdSeq += 1
        return newId

# === BLOCK 2 (label=human, source_idx=line1241_human, name=query_pathings) ===
async def query_pathings(self, zipped_list: List[List[Union[Unit, Point2, Point3]]]) -> List[Union[float, int]]:
        """ Usage: await self.query_pathings([[unit1, target2], [unit2, target2]])
        -> returns [distance1, distance2]
        Caution: returns 0 when path not found
        Might merge this function with the function above
        """
        assert zipped_list, "No zipped_list"
        assert isinstance(zipped_list, list), f"{type(zipped_list)}"
        assert isinstance(zipped_list[0], list), f"{type(zipped_list[0])}"
        assert len(zipped_list[0]) == 2, f"{len(zipped_list[0])}"
        assert isinstance(zipped_list[0][0], (Point2, Unit)), f"{type(zipped_list[0][0])}"
        assert isinstance(zipped_list[0][1], Point2), f"{type(zipped_list[0][1])}"
        if isinstance(zipped_list[0][0], Point2):
            results = await self._execute(
                query=query_pb.RequestQuery(
                    pathing=[
                        query_pb.RequestQueryPathing(
                            start_pos=common_pb.Point2D(x=p1.x, y=p1.y), end_pos=common_pb.Point2D(x=p2.x, y=p2.y)
                        )
                        for p1, p2 in zipped_list
                    ]
                )
            )
        else:
            results = await self._execute(
                query=query_pb.RequestQuery(
                    pathing=[
                        query_pb.RequestQueryPathing(unit_tag=p1.tag, end_pos=common_pb.Point2D(x=p2.x, y=p2.y))
                        for p1, p2 in zipped_list
                    ]
                )
            )
        results = [float(d.distance) for d in results.query.pathing]
        return results

# === BLOCK 3 (label=lm, source_idx=line2347_lm, name=jd_to_date) ===
def jd_to_date(jd):
    """
    Convert Julian Day to date.

    Algorithm from 'Practical Astronomy with your Calculator or Spreadsheet', 
        4th ed., Duffet-Smith and Zwart, 2011.

    Parameters
    ----------
    jd : float
        Julian Day

    Returns
    -------
    year : int
        Year as integer. Years preceding 1 A.D. should be 0 or negative.
        The year before 1 A.D. is 0, 10 B.C. is year -9.

    month : int
        Month as integer, Jan = 1, Feb. = 2, etc.

    day : float
        Day, may contain fractional part.

    Examples
    --------
    Convert Julian Day 2446113.75 to year, month, and day.

    >>> jd_to_date(2446113.75)
    (1985, 2, 17.25)

    """
    jd = jd + 0.5

    F, I = divmod(jd, 1)
    I = int(I)

    A = I
    B = 0

    if I > 2299160:
        alpha = int((I - 1867216.25) / 36524.25)
        A = I + 1 + alpha - int(alpha / 4)

    C = int((A + B) / 36525)
    D = int(A / 36525)
    E = int((A - D) / 365)

    day = A - D - E + B

    month = 3
    if day > 59:
        month = int((day - 59) / 28)
        day = day - 59 - int(month / 8)
        month = month + 2

    year = C - 4716
    if month > 2:
        year = year - 1

    return year, month, day

# === BLOCK 4 (label=lm, source_idx=line204_lm, name=register) ===
def register(name: str):
    """
    Registers a coverage extractor class under a given name.

    .. code: python

        from bugzoo.mgr.coverage import CoverageExtractor, register

        @register('mycov')
        class MyCoverageExtractor(CoverageExtractor):
            ...
    """
    def decorator(cls):
        cls.registry[name] = cls
        return cls
    return decorator

# === BLOCK 5 (label=human, source_idx=line833_human, name=_op) ===
def _op(self, method, path='', data=None, headers=None):
        """Overrides the base method to support retrying the operation.

        :param method: The HTTP method to be used, e.g: GET, POST,
            PUT, PATCH, etc...
        :param path: The sub-URI path to the resource.
        :param data: Optional JSON data.
        :param headers: Optional dictionary of headers.
        :returns: The response from the connector.Connector's _op method.
        """
        resp = super(HPEConnector, self)._op(method, path, data,
                                             headers, allow_redirects=False)
        # With IPv6, Gen10 server gives redirection response with new path with
        # a prefix of '/' so this check is required
        if resp.status_code == 308:
            path = urlparse(resp.headers['Location']).path
            resp = super(HPEConnector, self)._op(method, path, data, headers)
        return resp

# === BLOCK 6 (label=lm, source_idx=line1182_lm, name=build_gui) ===
def build_gui(self, container):
        """This method is called when the plugin is invoked.  It builds the
        GUI used by the plugin into the widget layout passed as
        ``container``.

        This method could be called several times if the plugin is opened
        and closed.

        """
        layout = QVBoxLayout()
        container.setLayout(layout)
        self.text_edit = QTextEdit()
        layout.addWidget(self.text_edit)
        self.button = QPushButton("Click Me")
        self.button.clicked.connect(self.button_clicked)
        layout.addWidget(self.button)
