# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line3256_human, name=is_punctuation) ===
def is_punctuation(text):
    """Check if given string is a punctuation"""
    return not (text.lower() in config.AVRO_VOWELS or
                text.lower() in config.AVRO_CONSONANTS)

# === BLOCK 2 (label=lm, source_idx=line1833_lm, name=run) ===
def run(self, build_requests=None, callback=None):
        """
        Run the client in a loop, calling the callback each time the debugger
        stops.
        """
        if build_requests is None:
            build_requests = []
        for build_request in build_requests:
            self.build_request(build_request)
        while True:
            if callback is not None:
                callback()
            self.wait_for_event()

# === BLOCK 3 (label=lm, source_idx=line1851_lm, name=make_stone_friendly) ===
def make_stone_friendly(self, data_type, val, validate):
        """
        Convert a Python object to a type that will pass validation by its
        validator.
        Validation by ``alias_validators`` is performed even if ``validate`` is
        false.
        """
        if validate:
            self.validate_value(data_type, val)
        if data_type.alias_validators:
            val = self.convert_value(data_type, val)
        return val

# === BLOCK 4 (label=human, source_idx=line3645_human, name=_update_request_context_with_user) ===
def _update_request_context_with_user(self, user=None):
        """Store the given user as ctx.user."""

        ctx = _request_ctx_stack.top
        ctx.user = self.anonymous_user() if user is None else user

# === BLOCK 5 (label=lm, source_idx=line2493_lm, name=monitor) ===
def monitor(self, name, cb, request=None, notify_disconnect=False, queue=None):
        """Create a subscription.

        :param str name: PV name string
        :param callable cb: Processing callback
        :param request: A :py:class:`p4p.Value` or string to qualify this request, or None to use a default.
        :param bool notify_disconnect: In additional to Values, the callback may also be call with instances of Exception.
                                       Specifically: Disconnected , RemoteError, or Cancelled
        :param WorkQueue queue: A work queue through which monitor callbacks are dispatched.
        :returns: a :py:class:`Subscription` instance

        The callable will be invoked with one argument which is either.

        * A p4p.Value (Subject to :py:ref:`unwrap`)
        * A sub-class of Exception (Disconnected , RemoteError, or Cancelled)
        """
        if not isinstance(name, str):
            raise TypeError("name must be a string")
        if not callable(cb):
            raise TypeError("cb must be a callable")
        if request is not None and not isinstance(request, (p4p.Value, str)):
            raise TypeError("request must be a p4p.Value or string")
        if not isinstance(notify_disconnect, bool):
            raise TypeError("notify_disconnect must be a bool")
        if queue is not None and not isinstance(queue, WorkQueue):
            raise TypeError("queue must be a WorkQueue")
        return Subscription(self, name, cb, request, notify_disconnect, queue)

# === BLOCK 6 (label=human, source_idx=line4612_human, name=getreferingobjs) ===
def getreferingobjs(referedobj, iddgroups=None, fields=None):
    """Get a list of objects that refer to this object"""
    # pseudocode for code below
    # referringobjs = []
    # referedobj has: -> Name
    #                 -> reference
    # for each obj in idf:
    # [optional filter -> objects in iddgroup]
    #     each field of obj:
    #     [optional filter -> field in fields]
    #         has object-list [refname]:
    #             if refname in reference:
    #                 if Name = field value:
    #                     referringobjs.append()
    referringobjs = []
    idf = referedobj.theidf
    referedidd = referedobj.getfieldidd("Name")
    try:
        references = referedidd['reference']
    except KeyError as e:
        return referringobjs
    idfobjs = idf.idfobjects.values()
    idfobjs = list(itertools.chain.from_iterable(idfobjs))  # flatten list
    if iddgroups:  # optional filter
        idfobjs = [anobj for anobj in idfobjs
            if anobj.getfieldidd('key')['group'] in iddgroups]
    for anobj in idfobjs:
        if not fields:
            thefields = anobj.objls
        else:
            thefields = fields
        for field in thefields:
            try:
                itsidd = anobj.getfieldidd(field)
            except ValueError as e:
                continue
            if 'object-list' in itsidd:
                refname = itsidd['object-list'][0]
                if refname in references:
                    if referedobj.isequal('Name', anobj[field]):
                        referringobjs.append(anobj)
    return referringobjs
