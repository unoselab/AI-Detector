# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line4762_lm, name=_other_to_dict) ===
def _other_to_dict(self, other):
    """When serializing models, this allows attached models (children, parents, etc.) to also be
    serialized.
    """
    if hasattr(other, 'to_dict'):
        return other.to_dict()
    elif hasattr(other, '__dict__'):
        return other.__dict__
    else:
        return other

# === BLOCK 2 (label=lm, source_idx=line1614_lm, name=join_header_words) ===
def join_header_words(lists):
    """Do the inverse (almost) of the conversion done by split_header_words.

    Takes a list of lists of (key, value) pairs and produces a single header
    value.  Attribute values are quoted if needed.

    >>> join_header_words([[("text/plain", None), ("charset", "iso-8859/1")]])
    'text/plain; charset="iso-8859/1"'
    >>> join_header_words([[("text/plain", None)], [("charset", "iso-8859/1")]])
    'text/plain, charset="iso-8859/1"'

    """
    result = []
    for sublist in lists:
        words = []
        for key, value in sublist:
            if value is None:
                words.append(key)
            else:
                words.append(f'{key}="{value}"')
        result.append("; ".join(words))
    return ", ".join(result)

# === BLOCK 3 (label=human, source_idx=line1061_human, name=_apply_key_type) ===
def _apply_key_type(self, keys):
        """
        If a type is specified by the corresponding key dimension,
        this method applies the type to the supplied key.
        """
        typed_key = ()
        for dim, key in zip(self.kdims, keys):
            key_type = dim.type
            if key_type is None:
                typed_key += (key,)
            elif isinstance(key, slice):
                sl_vals = [key.start, key.stop, key.step]
                typed_key += (slice(*[key_type(el) if el is not None else None
                                      for el in sl_vals]),)
            elif key is Ellipsis:
                typed_key += (key,)
            elif isinstance(key, list):
                typed_key += ([key_type(k) for k in key],)
            else:
                typed_key += (key_type(key),)
        return typed_key

# === BLOCK 4 (label=human, source_idx=line604_human, name=commit_comment) ===
def commit_comment(self, comment_id):
        """Get a single commit comment.

        :param int comment_id: (required), id of the comment used by GitHub
        :returns: :class:`RepoComment <github3.repos.comment.RepoComment>` if
            successful, otherwise None
        """
        url = self._build_url('comments', str(comment_id), base_url=self._api)
        json = self._json(self._get(url), 200)
        return RepoComment(json, self) if json else None

# === BLOCK 5 (label=human, source_idx=line4026_human, name=render_to_response) ===
def render_to_response(self, context, **response_kwargs):
        """
        This endpoint sets very permiscuous CORS headers.

        Access-Control-Allow-Origin is set to the request Origin. This allows
          a page from ANY domain to make a request to this endpoint.

        Access-Control-Allow-Credentials is set to true. This allows requesting
          poll data in our authenticated test/staff environments.

        This particular combination of headers means this endpoint is a potential
            CSRF target.

        This enpoint MUST NOT write data. And it MUST NOT return any sensitive data.
        """
        serializer = PollPublicSerializer(self.object)
        response = HttpResponse(
            json.dumps(serializer.data),
            content_type="application/json"
        )
        if "HTTP_ORIGIN" in self.request.META:
            response["Access-Control-Allow-Origin"] = self.request.META["HTTP_ORIGIN"]
            response["Access-Control-Allow-Credentials"] = 'true'

        return response

# === BLOCK 6 (label=lm, source_idx=line1770_lm, name=timespan_type) ===
def timespan_type(arg):
	"""An argparse type representing a timespan such as 6h for 6 hours."""
	pattern = re.compile(r'^(\d+)h$')
	match = pattern.match(arg)
	if match:
		hours = int(match.group(1))
		return hours * 60 * 60
	else:
		raise ValueError(f'Invalid timespan: {arg}')
