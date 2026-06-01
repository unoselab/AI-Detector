# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1599_human, name=add_parameter) ===
def add_parameter(self, name, value, meta=None):
        """Add a parameter to the parameter list.

        :param name: New parameter's name.
        :type name: str

        :param value: New parameter's value.
        :type value: float

        :param meta: New parameter's meta property.
        :type meta: dict
        """
        parameter = Parameter(name, value)
        if meta: parameter.meta = meta
        self.parameters.append(parameter)

# === BLOCK 2 (label=lm, source_idx=line3492_lm, name=_gatherLookupIndexes) ===
def _gatherLookupIndexes(gpos):
    """
    Gather a mapping of script to lookup indexes
    referenced by the kern feature for each script.
    Returns a dictionary of this structure:
        {
            "latn" : [0],
            "DFLT" : [0]
        }
    """

# === BLOCK 3 (label=human, source_idx=line2921_human, name=_draw_error_underline) ===
def _draw_error_underline(self, ptx, pango_layout, start, stop):
        """Draws an error underline"""

        self.context.save()
        self.context.set_source_rgb(1.0, 0.0, 0.0)

        pit = pango_layout.get_iter()

        # Skip characters until start
        for i in xrange(start):
            pit.next_char()

        extents_list = []

        for char_no in xrange(start, stop):
            char_extents = pit.get_char_extents()
            underline_pixel_extents = [
                char_extents[0] / pango.SCALE,
                (char_extents[1] + char_extents[3]) / pango.SCALE - 2,
                char_extents[2] / pango.SCALE,
                4,
            ]
            if extents_list:
                if extents_list[-1][1] == underline_pixel_extents[1]:
                    # Same line
                    extents_list[-1][2] = extents_list[-1][2] + \
                        underline_pixel_extents[2]
                else:
                    # Line break
                    extents_list.append(underline_pixel_extents)
            else:
                extents_list.append(underline_pixel_extents)

            pit.next_char()

        for extent in extents_list:
            pangocairo.show_error_underline(ptx, *extent)

        self.context.restore()

# === BLOCK 4 (label=lm, source_idx=line5108_lm, name=_make_line) ===
def _make_line(self, uid, command=None):
        """
        Prepares an IRC line in Herald's format
        """
        # Ensure uid is a string and strip any leading colon
        uid_str = str(uid).lstrip(":")
        # Prepare the base line with the prefix
        line = f":{uid_str}"
        # Append command if provided
        if command is not None:
            line += f" {command}"
        # IRC messages are terminated with CRLF
        return f"{line}\r\n"

# === BLOCK 5 (label=lm, source_idx=line6652_lm, name=get_channel) ===
def get_channel(self, name):
        """Return the channel for the given name

        :param name: the channel name
        :type name: :class:`str`
        :returns: the model instance
        :rtype: :class:`models.Channel`
        :raises: None
        """
        from . import models
        try:
            return models.Channel.objects.get(name=name)
        except models.Channel.DoesNotExist:
            return None

# === BLOCK 6 (label=human, source_idx=line5205_human, name=get_signalcheck) ===
def get_signalcheck(self, sar, **params):
        """get_signalcheck -  perform a signal check.

        Parameters
        ----------
        sar : dict
            signal-api-request specified as a dictionary of parameters.
            All of these parameters are optional. For details
            check https://api.postcode.nl/documentation/signal-api-example.

        returns :
            a response dictionary
        """
        params = sar
        endpoint = 'rest/signal/check'

        # The 'sar'-request dictionary should be sent as valid JSON data, so
        # we need to convert it to JSON
        # when we construct the request in API.request
        retValue = self._API__request(endpoint, 'POST',
                                      params=params, convJSON=True)

        return retValue
