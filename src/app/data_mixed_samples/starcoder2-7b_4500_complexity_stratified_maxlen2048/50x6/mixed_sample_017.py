# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1987_lm, name=create_webhook_app) ===
def create_webhook_app(self, path, loop=None):
        """
        Shorthand for creating aiohttp.web.Application with registered webhook hanlde
        """
        app = web.Application(loop=loop)
        app.router.add_post(path, self.handle)
        return app

# === BLOCK 2 (label=lm, source_idx=line404_lm, name=iter_records_for) ===
def iter_records_for(self, package_name):
        """
        Iterate records for a specific package.
        """
        for record in self.iter_records():
            if record.package_name == package_name:
                yield record

# === BLOCK 3 (label=lm, source_idx=line1191_lm, name=get_waiting_list) ===
def get_waiting_list(self, force=False):
        """ Add lines for any waiting fields that can be completed now. """
        if not force and self.waiting_list:
            return self.waiting_list
        self.waiting_list = []
        for field in self.fields:
            if field.waiting:
                self.waiting_list.append(field)
        return self.waiting_list

# === BLOCK 4 (label=human, source_idx=line5799_human, name=_insert_url) ===
def _insert_url(request, redirect_field_name=REDIRECT_FIELD_NAME,
                inserted_url=None):
    """Redirects to the *inserted_url* before going to the orginal
    request path."""
    # This code is pretty much straightforward
    # from contrib.auth.user_passes_test
    path = request.build_absolute_uri()
    # If the login url is the same scheme and net location then just
    # use the path as the "next" url.
    login_scheme, login_netloc = six.moves.urllib.parse.urlparse(
        inserted_url)[:2]
    current_scheme, current_netloc = six.moves.urllib.parse.urlparse(path)[:2]
    if ((not login_scheme or login_scheme == current_scheme) and
        (not login_netloc or login_netloc == current_netloc)):
        path = request.get_full_path()
    # As long as *inserted_url* is not None, this call will redirect
    # anything (i.e. inserted_url), not just the login.
    from django.contrib.auth.views import redirect_to_login
    return redirect_to_login(path, inserted_url, redirect_field_name)

# === BLOCK 5 (label=human, source_idx=line3606_human, name=create_node) ===
def create_node(participant_id):
    """Send a POST request to the node table.

    This makes a new node for the participant, it calls:
        1. exp.get_network_for_participant
        2. exp.create_node
        3. exp.add_node_to_network
        4. exp.node_post_request
    """
    exp = experiment(session)

    # Get the participant.
    try:
        participant = models.Participant.\
            query.filter_by(id=participant_id).one()
    except NoResultFound:
        return error_response(error_type="/node POST no participant found",
                              status=403)

    # replace any duplicate assignments
    check_for_duplicate_assignments(participant)

    # Make sure the participant status is working
    if participant.status != "working":
        error_type = "/node POST, status = {}".format(participant.status)
        return error_response(error_type=error_type,
                              participant=participant)

    try:
        # execute the request
        network = exp.get_network_for_participant(participant=participant)

        if network is None:
            return Response(dumps({"status": "error"}), status=403)

        node = exp.create_node(
            participant=participant,
            network=network)

        assign_properties(node)

        exp.add_node_to_network(
            node=node,
            network=network)

        session.commit()

        # ping the experiment
        exp.node_post_request(participant=participant, node=node)
        session.commit()
    except:
        return error_response(error_type="/node POST server error",
                              status=403,
                              participant=participant)

    # return the data
    return success_response(field="node",
                            data=node.__json__(),
                            request_type="/node POST")

# === BLOCK 6 (label=human, source_idx=line50_human, name=get_fptr) ===
def get_fptr(self):
        """Get the function pointer."""
        cmpfunc = ctypes.CFUNCTYPE(ctypes.c_int,
                                   WPARAM,
                                   LPARAM,
                                   ctypes.POINTER(KBDLLHookStruct))
        return cmpfunc(self.handle_input)
