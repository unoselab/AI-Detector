# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line8049_lm, name=new) ===
def new(self):
        # type: () -> None
        """
        A method to create a new UDF Implementation Use Volume Descriptor.

        Parameters:
         None:
        Returns:
         Nothing.
        """
        self._volume_descriptor = {}
        self._is_initialized = True

# === BLOCK 2 (label=human, source_idx=line7633_human, name=_add_user_source) ===
def _add_user_source(self):
        """Add the configuration options from the YAML file in the
        user's configuration directory (given by `config_dir`) if it
        exists.
        """
        filename = self.user_config_path()
        if os.path.isfile(filename):
            self.add(ConfigSource(load_yaml(filename) or {}, filename))

# === BLOCK 3 (label=human, source_idx=line7738_human, name=enter_bootloader) ===
async def enter_bootloader(driver, model):
    """
    Using the driver method, enter bootloader mode of the atmega32u4.
    The bootloader mode opens a new port on the uC to upload the hex file.
    After receiving a 'dfu' command, the firmware provides a 3-second window to
    close the current port so as to do a clean switch to the bootloader port.
    The new port shows up as 'ttyn_bootloader' on the pi; upload fw through it.
    NOTE: Modules with old bootloader will have the bootloader port show up as
    a regular module port- 'ttyn_tempdeck'/ 'ttyn_magdeck' with the port number
    being either different or same as the one that the module was originally on
    So we check for changes in ports and use the appropriate one
    """
    # Required for old bootloader
    ports_before_dfu_mode = await _discover_ports()

    driver.enter_programming_mode()
    driver.disconnect()
    new_port = ''
    try:
        new_port = await asyncio.wait_for(
            _port_poll(_has_old_bootloader(model), ports_before_dfu_mode),
            PORT_SEARCH_TIMEOUT)
    except asyncio.TimeoutError:
        pass
    return new_port

# === BLOCK 4 (label=human, source_idx=line1445_human, name=sendPacket) ===
def sendPacket(self, completeBox):
        """
        Send a juice.Box to my peer.

        Note: transport.write is never called outside of this method.
        """
        assert not self.__locked, "You cannot send juice packets when a connection is locked"
        if self._startingTLSBuffer is not None:
            self._startingTLSBuffer.append(completeBox)
        else:
            if debug:
                log.msg("Juice send: %s" % pprint.pformat(dict(completeBox.iteritems())))

            self.transport.write(completeBox.serialize())

# === BLOCK 5 (label=lm, source_idx=line1997_lm, name=get_ngrams) ===
def get_ngrams(path):
    """Returns a list of n-grams read from the file at `path`."""
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read().split()
    ngrams = []
    for n in range(1, len(text) + 1):
        for i in range(len(text) - n + 1):
            ngrams.append(tuple(text[i:i+n]))
    return ngrams

# === BLOCK 6 (label=lm, source_idx=line5865_lm, name=message_proxy) ===
def message_proxy(self, work_dir):
        """
        drone_data_inboud   is for data comming from drones
        drone_data_outbound is for commands to the drones, topic must either be a drone ID or all for sending
                            a broadcast message to all drones
        """
        self.drone_data_inbound = os.path.join(work_dir, 'drone_data_inbound')
        self.drone_data_outbound = os.path.join(work_dir, 'drone_data_outbound')
        os.makedirs(self.drone_data_inbound, exist_ok=True)
        os.makedirs(self.drone_data_outbound, exist_ok=True)
