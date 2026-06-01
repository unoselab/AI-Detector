# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line834_lm, name=send) ===
def send(self, message, _sender=None):
        """Sends a message to the actor represented by this `Ref`."""
        self.mailbox.put(message)

# === BLOCK 2 (label=human, source_idx=line1618_human, name=secondary_xi) ===
def secondary_xi(mass1, mass2, spin1x, spin1y, spin2x, spin2y):
    """Returns the effective precession spin argument for the smaller mass.
    """
    spinx = secondary_spin(mass1, mass2, spin1x, spin2x)
    spiny = secondary_spin(mass1, mass2, spin1y, spin2y)
    return xi2_from_mass1_mass2_spin2x_spin2y(mass1, mass2, spinx, spiny)

# === BLOCK 3 (label=human, source_idx=line5_human, name=_write_new_chunk) ===
def _write_new_chunk(self):
        """
        Called to request a new chunk of data to be read from the Crazyflie
        """
        # Figure out the length of the next request
        new_len = len(self._data)
        if new_len > _WriteRequest.MAX_DATA_LENGTH:
            new_len = _WriteRequest.MAX_DATA_LENGTH

        logger.debug('Writing new chunk of {}bytes at 0x{:X}'.format(
            new_len, self._current_addr))

        data = self._data[:new_len]
        self._data = self._data[new_len:]

        pk = CRTPPacket()
        pk.set_header(CRTPPort.MEM, CHAN_WRITE)
        pk.data = struct.pack('<BI', self.mem.id, self._current_addr)
        # Create a tuple used for matching the reply using id and address
        reply = struct.unpack('<BBBBB', pk.data)
        self._sent_reply = reply
        # Add the data
        pk.data += struct.pack('B' * len(data), *data)
        self._sent_packet = pk
        self.cf.send_packet(pk, expected_reply=reply, timeout=1)

        self._addr_add = len(data)

# === BLOCK 4 (label=lm, source_idx=line155_lm, name=get) ===
def get(self, request, format=None):
        """ get HTTP method """
        if request.method == 'GET':
            return Response(status=status.HTTP_200_OK)

# === BLOCK 5 (label=lm, source_idx=line5400_lm, name=register_plugin) ===
def register_plugin(self, name):
        """Load and register a plugin given its package name."""
        try:
            plugin = self.load_plugin(name)
        except ImportError as e:
            raise PluginError(e)

        self.register_plugin_class(plugin)

# === BLOCK 6 (label=human, source_idx=line6988_human, name=get_advances_declines) ===
def get_advances_declines(self, as_json=False):
        """
        :return: a list of dictionaries with advance decline data
        :raises: URLError, HTTPError
        """
        url = self.advances_declines_url
        req = Request(url, None, self.headers)
        # raises URLError or HTTPError
        resp = self.opener.open(req)
        # for py3 compat covert byte file like object to
        # string file like object
        resp = byte_adaptor(resp)
        resp_dict = json.load(resp)
        resp_list = [self.clean_server_response(item)
                     for item in resp_dict['data']]
        return self.render_response(resp_list, as_json)
