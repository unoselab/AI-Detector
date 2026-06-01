# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1421_human, name=gc) ===
def gc(self):
        """ Garbage collect overflow and/or aged entries. """
        manifest = []
        overlimit = len(self.data) - self.maxsize \
            if self.maxsize is not None else 0
        now = self.ttl is not None and self.timer()
        for key, entry in self.data.items():
            if overlimit > 0 or (now and self.is_expired(entry, time=now)):
                overlimit -= 1
                manifest.append(key)
            else:
                break
        for x in manifest:
            del self.data[x]

# === BLOCK 2 (label=lm, source_idx=line1473_lm, name=length) ===
def length(ext_id, ext_des, ext_src):
        # type: (bytes, bytes, bytes) -> int
        """
        Static method to return the length of the Rock Ridge Extensions Reference
        record.

        Parameters:
         ext_id - The extension identifier to use.
         ext_des - The extension descriptor to use.
         ext_src - The extension specification source to use.
        Returns:
         The length of this record in bytes.
        """
        return len(ext_id) + len(ext_des) + len(ext_src)

# === BLOCK 3 (label=human, source_idx=line4814_human, name=options) ===
def options(self, request, *args, **kwargs):
        """
        Implements a OPTIONS HTTP method function returning all allowed HTTP
        methods.
        """
        allow = []
        for method in self.http_method_names:
            if hasattr(self, method):
                allow.append(method.upper())
        r = self.render_to_response(None)
        r['Allow'] = ','.join(allow)
        return r

# === BLOCK 4 (label=lm, source_idx=line455_lm, name=pixy_init) ===
def pixy_init(self, max_blocks=5, cb=None, cb_type=None):
        """
        Initialize Pixy and will enable Pixy block reporting.
        This is a FirmataPlusRB feature.

        :param cb: callback function to report Pixy blocks

        :param cb_type: Constants.CB_TYPE_DIRECT = direct call or
                        Constants.CB_TYPE_ASYNCIO = asyncio coroutine

        :param max_blocks: Maximum number of Pixy blocks to report when many
                           signatures are found.

        :returns: No return value.
        """
        self.max_blocks = max_blocks
        self.cb = cb
        self.cb_type = cb_type

# === BLOCK 5 (label=lm, source_idx=line3131_lm, name=main) ===
def main(is_server, discoveries, transports, http_port, other_arguments):
    """
    Runs the framework

    :param is_server: If True, starts the provider bundle,
                      else the consumer one
    :param discoveries: List of discovery protocols
    :param transports: List of RPC protocols
    :param http_port: Port of the HTTP server
    :param other_arguments: Other arguments
    """
    if is_server:
        start_provider_bundle(discoveries, transports, http_port, other_arguments)
    else:
        start_consumer_bundle(discoveries, transports, http_port, other_arguments)

# === BLOCK 6 (label=human, source_idx=line2305_human, name=ignore_broken_pipe) ===
def ignore_broken_pipe():
    """ If a shellish program has redirected stdio it is subject to erroneous
    "ignored" exceptions during the interpretor shutdown. This essentially
    beats the interpretor to the punch by closing them early and ignoring any
    broken pipe exceptions. """
    for f in sys.stdin, sys.stdout, sys.stderr:
        try:
            f.close()
        except BrokenPipeError:
            pass
