# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line3011_human, name=write) ===
def write(
        frame,
        writer: Callable[[bytes], Any],
        *,
        mask: bool,
        extensions: Optional[Sequence["websockets.extensions.base.Extension"]] = None,
    ) -> None:
        """
        Write a WebSocket frame.

        ``frame`` is the :class:`Frame` object to write.

        ``writer`` is a function accepting bytes.

        ``mask`` is a :class:`bool` telling whether the frame should be masked
        i.e. whether the write happens on the client side.

        If ``extensions`` is provided, it's a list of classes with an
        ``encode()`` method that transform the frame and return a new frame.
        They are applied in order.

        This function validates the frame before sending it and raises
        :exc:`~websockets.exceptions.WebSocketProtocolError` if it contains
        incorrect values.

        """
        # The first parameter is called `frame` rather than `self`,
        # but it's the instance of class to which this method is bound.

        frame.check()

        if extensions is None:
            extensions = []
        for extension in extensions:
            frame = extension.encode(frame)

        output = io.BytesIO()

        # Prepare the header.
        head1 = (
            (0b10000000 if frame.fin else 0)
            | (0b01000000 if frame.rsv1 else 0)
            | (0b00100000 if frame.rsv2 else 0)
            | (0b00010000 if frame.rsv3 else 0)
            | frame.opcode
        )

        head2 = 0b10000000 if mask else 0

        length = len(frame.data)
        if length < 126:
            output.write(struct.pack("!BB", head1, head2 | length))
        elif length < 65536:
            output.write(struct.pack("!BBH", head1, head2 | 126, length))
        else:
            output.write(struct.pack("!BBQ", head1, head2 | 127, length))

        if mask:
            mask_bits = struct.pack("!I", random.getrandbits(32))
            output.write(mask_bits)

        # Prepare the data.
        if mask:
            data = apply_mask(frame.data, mask_bits)
        else:
            data = frame.data
        output.write(data)

        # Send the frame.

        # The frame is written in a single call to writer in order to prevent
        # TCP fragmentation. See #68 for details. This also makes it safe to
        # send frames concurrently from multiple coroutines.
        writer(output.getvalue())

# === BLOCK 2 (label=lm, source_idx=line3786_lm, name=compare_bpdu_info) ===
def compare_bpdu_info(my_priority, my_times, rcv_priority, rcv_times):
        """ Check received BPDU is superior to currently held BPDU
             by the following comparison.
             - root bridge ID value
             - root path cost
             - designated bridge ID value
             - designated port ID value
             - times """

# === BLOCK 3 (label=human, source_idx=line6665_human, name=draw) ===
def draw(self, mode=None):
        """ Draw collection """

        if self._need_update:
            self._update()

        program = self._programs[0]

        mode = mode or self._mode
        if self._indices_list is not None:
            program.draw(mode, self._indices_buffer)
        else:
            program.draw(mode)

# === BLOCK 4 (label=human, source_idx=line4363_human, name=summarize) ===
def summarize(self, interval, bins=None, method='summarize',
                  function='mean', zero_inf=True, zero_nan=True):
        """
        Parameters
        ----------

        interval : object
            Object with chrom (str), start (int) and stop (int) attributes.

        bins : int or None
            Number of bins; if None, bins will be the length of the interval

        method : summarize | ucsc_summarize | get_as_array
            "summarize" and "get_as_array" use bx-python; "ucsc_summarize" uses
            bigWigSummarize. See other notes in docstring for
            metaseq.array_helpers._local_coverage. If None, defaults to
            "summarize".

        function : mean | min | max | std | coverage
            Determines the nature of the summarized values. Ignored if
            `method="get_as_array"`; "coverage" is only valid if method is
            "ucsc_summarize".

        zero_inf, zero_nan : bool
            If `zero_inf` is True, set any inf or -inf to zero before
            returning. If `zero_nan` is True, set any nan values to zero before
            returning.
        """

        if method is None:
            method = 'summarize'

        # We may be dividing by zero in some cases, which raises a warning in
        # NumPy based on the IEEE 754 standard (see
        # http://docs.scipy.org/doc/numpy/reference/generated/
        #       numpy.seterr.html)
        #
        # That's OK -- we're expecting that to happen sometimes. So temporarily
        # disable this error reporting for the duration of this method.
        orig = np.geterr()['invalid']
        np.seterr(invalid='ignore')

        if (bins is None) or (method == 'get_as_array'):
            bw = BigWigFile(open(self.fn))
            s = bw.get_as_array(
                interval.chrom,
                interval.start,
                interval.stop,)
            if s is None:
                s = np.zeros((interval.stop - interval.start,))
            else:
                if zero_nan:
                    s[np.isnan(s)] = 0
                if zero_inf:
                    s[np.isinf(s)] = 0

        elif method == 'ucsc_summarize':
            if function in ['mean', 'min', 'max', 'std', 'coverage']:
                return self.ucsc_summarize(interval, bins, function=function)
            else:
                raise ValueError('function "%s" not supported by UCSC\'s'
                                 'bigWigSummary')

        elif method == 'summarize':
            bw = BigWigFile(open(self.fn))
            s = bw.summarize(
                interval.chrom,
                interval.start,
                interval.stop, bins)
            if s is None:
                s = np.zeros((bins,))
            else:
                if function == 'sum':
                    s = s.sum_data
                elif function == 'mean':
                    s = s.sum_data / s.valid_count
                    if zero_nan:
                        s[np.isnan(s)] = 0
                elif function == 'min':
                    s = s.min_val
                    if zero_inf:
                        s[np.isinf(s)] = 0
                elif function == 'max':
                    s = s.max_val
                    if zero_inf:
                        s[np.isinf(s)] = 0
                elif function == 'std':
                    s = (s.sum_squares / s.valid_count)
                    if zero_nan:
                        s[np.isnan(s)] = 0
                else:
                    raise ValueError(
                            'function "%s" not supported by bx-python'
                            % function
                    )
        else:
            raise ValueError("method '%s' not in [summarize, ucsc_summarize, get_as_array]" % method)

        # Reset NumPy error reporting
        np.seterr(divide=orig)
        return s

# === BLOCK 5 (label=lm, source_idx=line3177_lm, name=gets) ===
def gets(self, conn, key, default=None):
        """Gets a single value from the server together with the cas token.

        :param key: ``bytes``, is the key for the item being fetched
        :param default: default value if there is no value.
        :return: ``bytes``, ``bytes tuple with the value and the cas
        """

# === BLOCK 6 (label=lm, source_idx=line6978_lm, name=_batched_write_command) ===
def _batched_write_command(
        namespace, operation, command, docs, check_keys, opts, ctx):
    """Create the next batched insert, update, or delete command.
    """
    import copy
    from bson import encode as bson_encode

    MAX_BATCH_SIZE = 1000
    MAX_BATCH_BYTES = 16 * 102
