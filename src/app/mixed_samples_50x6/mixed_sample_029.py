# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line50_human, name=find_movie) ===
async def find_movie(self, query):
        """Retrieve movie data by search query.

        Arguments:
          query (:py:class:`str`): Query to search for.

        Returns:
          :py:class:`list`: Possible matches.

        """
        params = OrderedDict([
            ('query', query), ('include_adult', False),
        ])
        url = self.url_builder('search/movie', {}, params)
        data = await self.get_data(url)
        if data is None:
            return
        return [
            Movie.from_json(item, self.config['data'].get('images'))
            for item in data.get('results', [])
        ]

# === BLOCK 2 (label=lm, source_idx=line2881_lm, name=_fix_namespace) ===
def _fix_namespace(self):
    """Internal helper to fix the namespace.

    This is called to ensure that for queries without an explicit
    namespace, the namespace used by async calls is the one in effect
    at the time the async call is made, not the one in effect when the
    the request is actually generated.
    """
    self._namespace = self._client._namespace

# === BLOCK 3 (label=human, source_idx=line754_human, name=_parse_description) ===
def _parse_description(self, node):
        # type: (ElementTree.Element) -> EndpointDescription
        """
        Parse an endpoint description node

        :param node: The endpoint description node
        :return: The parsed EndpointDescription bean
        :raise KeyError: Attribute missing
        :raise ValueError: Invalid description
        """
        endpoint = {}
        for prop_node in node.findall(TAG_PROPERTY):
            name, value = self._parse_property(prop_node)
            endpoint[name] = value

        return EndpointDescription(None, endpoint)

# === BLOCK 4 (label=lm, source_idx=line964_lm, name=check_args) ===
def check_args(args):
    """Checks the arguments and options."""
    if not args:
        raise ValueError("No arguments provided")
    if not isinstance(args, dict):
        raise TypeError("Arguments must be a dictionary")
    if "input" not in args:
        raise KeyError("Missing required argument: input")
    if "output" not in args:
        raise KeyError("Missing required argument: output")
    if "input" in args and not isinstance(args["input"], str):
        raise TypeError("Argument input must be a string")
    if "output" in args and not isinstance(args["output"], str):
        raise TypeError("Argument output must be a string")
    if "verbose" in args and not isinstance(args["verbose"], bool):
        raise TypeError("Argument verbose must be a boolean")

# === BLOCK 5 (label=lm, source_idx=line2583_lm, name=copy_data_ext) ===
def copy_data_ext(self, model, field, dest=None, idx=None, astype=None):
        """
        Retrieve the field of another model and store it as a field.

        :param model: name of the source model being a model name or a group name
        :param field: name of the field to retrieve
        :param dest: name of the destination field in ``self``
        :param idx: idx of elements to access
        :param astype: type cast

        :type model: str
        :type field: str
        :type dest: str
        :type idx: list, matrix
        :type astype: None, list, matrix

        :return: None

        """
        if dest is None:
            dest = field
        if idx is not None:
            data = self.get_data(model, field, idx=idx)
        else:
            data = self.get_data(model, field)
        if astype is not None:
            data = data.astype(astype)
        self.set_data(dest, data)

# === BLOCK 6 (label=human, source_idx=line2158_human, name=trustRootValid) ===
def trustRootValid(self):
        """Is my return_to under my trust_root?

        @returntype: bool
        """
        if not self.trust_root:
            return True
        tr = TrustRoot.parse(self.trust_root)
        if tr is None:
            raise MalformedTrustRoot(self.message, self.trust_root)

        if self.return_to is not None:
            return tr.validateURL(self.return_to)
        else:
            return True
