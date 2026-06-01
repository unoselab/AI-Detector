# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line6376_human, name=prepare) ===
def prepare(self):
        """Behaves like a middleware between raw request and handling process,

        If `PREPARES` is defined on handler class, which should be
        a list, for example, ['auth', 'context'], method whose name
        is constitute by prefix '_prepare_' and string in this list
        will be executed by sequence. In this example, those methods are
        `_prepare_auth` and `_prepare_context`
        """
        if settings['LOG_REQUEST']:
            log_request(self)

        for i in self.PREPARES:
            getattr(self, 'prepare_' + i)()
            if self._finished:
                return

# === BLOCK 2 (label=lm, source_idx=line2240_lm, name=find_parameter) ===
def find_parameter(parameters, **kwargs):
    """
    Given a list of parameters, find the one with the given name.
    """
    for parameter in parameters:
        if parameter.name == kwargs["name"]:
            return parameter
    return None

# === BLOCK 3 (label=lm, source_idx=line3777_lm, name=convert_machine_list_value) ===
def convert_machine_list_value(name: str, value: str) -> \
        Union[datetime.datetime, str, int]:
    """Convert sizes and time values.

    Size will be ``int`` while time value will be :class:`datetime.datetime`.
    """
    if name in ('size', 'time'):
        return int(value)
    elif name == 'time':
        return datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    return value

# === BLOCK 4 (label=lm, source_idx=line3505_lm, name=_matmul_with_relative_keys_2d) ===
def _matmul_with_relative_keys_2d(x, y, heads_share_relative_embedding):
  """Helper function for dot_product_unmasked_self_attention_relative_2d."""

# === BLOCK 5 (label=human, source_idx=line5764_human, name=_set_vibration_win) ===
def _set_vibration_win(self, left_motor, right_motor, duration):
        """Control the motors on Windows."""
        self._start_vibration_win(left_motor, right_motor)
        stop_process = Process(target=delay_and_stop,
                               args=(duration,
                                     self.manager.xinput_dll,
                                     self.__device_number))
        stop_process.start()

# === BLOCK 6 (label=human, source_idx=line5684_human, name=container_remove_objects) ===
def container_remove_objects(object_id, input_params={}, always_retry=False, **kwargs):
    """
    Invokes the /container-xxxx/removeObjects API method.

    For more info, see: https://wiki.dnanexus.com/API-Specification-v1.0.0/Folders-and-Deletion#API-method%3A-%2Fclass-xxxx%2FremoveObjects
    """
    return DXHTTPRequest('/%s/removeObjects' % object_id, input_params, always_retry=always_retry, **kwargs)
