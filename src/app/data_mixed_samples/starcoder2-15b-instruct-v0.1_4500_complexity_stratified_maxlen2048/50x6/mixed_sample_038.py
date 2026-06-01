# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line496_human, name=iob2json) ===
def iob2json(input_data, n_sents=10, *args, **kwargs):
    """
    Convert IOB files into JSON format for use with train cli.
    """
    docs = []
    for group in minibatch(docs, n_sents):
        group = list(group)
        first = group.pop(0)
        to_extend = first["paragraphs"][0]["sentences"]
        for sent in group[1:]:
            to_extend.extend(sent["paragraphs"][0]["sentences"])
        docs.append(first)
    return docs

# === BLOCK 2 (label=lm, source_idx=line1080_lm, name=all) ===
def all(self):
        """ -> #dict of all |{key: value}| entries in :prop:key_prefix of
                :prop:_client
        """
        return self._client.get_all(self.key_prefix)

# === BLOCK 3 (label=lm, source_idx=line1915_lm, name=thread_debug) ===
def thread_debug(self, *args, **kwargs):
        """
        Wrap debug to include thread information
        """
        thread_name = threading.current_thread().name
        logging.debug("Thread: %s, Args: %s, kwargs: %s", thread_name, args, kwargs)

# === BLOCK 4 (label=human, source_idx=line4888_human, name=get_notes) ===
def get_notes(self, folderid="", offset=0, limit=10):

        """Fetch notes

        :param folderid: The UUID of the folder to fetch notes from
        :param offset: the pagination offset
        :param limit: the pagination limit
        """

        if self.standard_grant_type is not "authorization_code":
            raise DeviantartError("Authentication through Authorization Code (Grant Type) is required in order to connect to this endpoint.")

        response = self._req('/notes', {
            'folderid' : folderid,
            'offset' : offset,
            'limit' : limit
        })

        notes = []

        for item in response['results']:
            n = {}

            n['noteid'] = item['noteid']
            n['ts'] = item['ts']
            n['unread'] = item['unread']
            n['starred'] = item['starred']
            n['sent'] = item['sent']
            n['subject'] = item['subject']
            n['preview'] = item['preview']
            n['body'] = item['body']
            n['user'] = User()
            n['user'].from_dict(item['user'])
            n['recipients'] = []

            for recipient_item in item['recipients']:
                u = User()
                u.from_dict(recipient_item)
                n['recipients'].append(u)

            notes.append(n)

        return {
            "results" : notes,
            "has_more" : response['has_more'],
            "next_offset" : response['next_offset']
        }

# === BLOCK 5 (label=human, source_idx=line3969_human, name=timer) ===
def timer(name, count):
    """Time this block."""
    start = time.time()
    try:
        yield count
    finally:
        duration = time.time() - start
        print(name)
        print('=' * 10)
        print('Total: %s' % duration)
        print('  Avg: %s' % (duration / count))
        print(' Rate: %s' % (count / duration))
        print('')

# === BLOCK 6 (label=lm, source_idx=line1642_lm, name=_astype) ===
def _astype(self, dtype):
        """Internal helper for ``astype``."""
        if dtype == "int64":
            return [int(x) for x in self]
        elif dtype == "float64":
            return [float(x) for x in self]
        else:
            raise ValueError(f"Invalid dtype: {dtype}")
