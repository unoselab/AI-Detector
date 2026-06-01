# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line4196_lm, name=as_version) ===
def as_version(self, version=Version.latest):
        """Returns a dict that has been modified based on versioning
        in order to be represented in JSON properly

        A class should overload as_version(self, version)
        implementation in order to tailor a more specific representation

        :param version: the relevant version. This allows for variance
         between versions
        :type version: str | unicode

        """
        return self.as_dict()

# === BLOCK 2 (label=human, source_idx=line5217_human, name=readline) ===
def readline(self):
        """
        Readline implementation.

        :return: popped line from descriptor queue. None if nothing found
        :raises: RuntimeError if errors happened while reading PIPE
        """
        try:
            return self._descriptor.read_queue.pop()
        except IndexError:
            # No lines in queue
            if self.has_error():
                raise RuntimeError("Errors reading PIPE")
        return None

# === BLOCK 3 (label=lm, source_idx=line1345_lm, name=activations) ===
def activations(self):
        """Iterate over the Activations in the Agenda."""
        return iter(self._activations)

# === BLOCK 4 (label=lm, source_idx=line4761_lm, name=save_model) ===
def save_model(model, filename):
    """Save the model into a file.

    :param model: HTK model to be saved
    :param filename: File where to save the model
    """
    with open(filename, 'wb') as f:
        pickle.dump(model, f)

# === BLOCK 5 (label=human, source_idx=line235_human, name=parse_datetime) ===
def parse_datetime(time_str):
    """
    Wraps dateutil's parser function to set an explicit UTC timezone, and
    to make sure microseconds are 0. Unified Uploader format and EMK format
    bother don't use microseconds at all.

    :param str time_str: The date/time str to parse.
    :rtype: datetime.datetime
    :returns: A parsed, UTC datetime.
    """
    try:
        return dateutil.parser.parse(
            time_str
        ).replace(microsecond=0).astimezone(UTC_TZINFO)
    except ValueError:
        # This was some kind of unrecognizable time string.
        raise ParseError("Invalid time string: %s" % time_str)

# === BLOCK 6 (label=human, source_idx=line1336_human, name=lowercase) ===
def lowercase(text_string):
    """
    Converts text_string into lowercase and returns the converted string as type str.

    Keyword argument:

    - text_string: string instance

    Exceptions raised:

    - InputError: occurs should a non-string argument be passed
    """
    if text_string is None or text_string == "":
        return ""
    elif isinstance(text_string, str):
        return text_string.lower()
    else:
        raise InputError("string not passed as argument for text_string")
