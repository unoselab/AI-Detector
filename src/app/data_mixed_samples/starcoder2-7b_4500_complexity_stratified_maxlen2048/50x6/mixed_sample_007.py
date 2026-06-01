# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1875_lm, name=getWindowTitle) ===
def getWindowTitle(self, hwnd):
        """ Gets the title for the specified window """
        length = User32.GetWindowTextLength(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        User32.GetWindowText(hwnd, buff, length + 1)
        return buff.value

# === BLOCK 2 (label=human, source_idx=line3217_human, name=_get_calculated_value) ===
def _get_calculated_value(self, value):
        """
        Get's the final value of the field and runs the lambda functions
        recursively until a final value is derived.

        :param value: The value to calculate/expand
        :return: The final value
        """
        if isinstance(value, types.LambdaType):
            expanded_value = value(self.structure)
            return self._get_calculated_value(expanded_value)
        else:
            # perform one final parsing of the value in case lambda value
            # returned a different type
            return self._parse_value(value)

# === BLOCK 3 (label=human, source_idx=line6902_human, name=validate_context) ===
def validate_context(self, context):
        """
        Checks to see if we're working with a valid lambda context object.

        :returns: True if valid, False if not
        :rtype: bool
        """
        return all(
            [
                hasattr(context, attr)
                for attr in [
                    "aws_request_id",
                    "function_name",
                    "function_version",
                    "get_remaining_time_in_millis",
                    "invoked_function_arn",
                    "log_group_name",
                    "log_stream_name",
                    "memory_limit_in_mb",
                ]
            ]
        ) and callable(context.get_remaining_time_in_millis)

# === BLOCK 4 (label=lm, source_idx=line3914_lm, name=load) ===
def load(self, filename, bs=512):
        """Loads GPT partition table.

        Args:
            filename (str): path to file or device to open for reading
            bs (uint): Block size of the volume, default: 512

        Raises:
            IOError: If file does not exist or not readable
        """
        with open(filename, 'rb') as f:
            self.load_from_stream(f, bs)

# === BLOCK 5 (label=lm, source_idx=line2910_lm, name=get_stream_url) ===
def get_stream_url(self, session_id, stream_id=None):
        """ this method returns the url to get streams information """
        if stream_id is None:
            return self.base_url + '/sessions/' + session_id + '/streams'
        else:
            return self.base_url + '/sessions/' + session_id + '/streams/' + stream_id

# === BLOCK 6 (label=human, source_idx=line1564_human, name=streamify) ===
def streamify(self, state, frame):
        """Prepare frame for output as a byte-stuffed stream."""

        # Split the frame apart for stuffing...
        pieces = frame.split(self.prefix)

        return '%s%s%s%s%s' % (self.prefix, self.begin,
                               (self.prefix + self.nop).join(pieces),
                               self.prefix, self.end)
