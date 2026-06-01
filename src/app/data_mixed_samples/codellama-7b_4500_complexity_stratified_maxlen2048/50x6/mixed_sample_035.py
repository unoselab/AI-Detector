# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line8896_human, name=save_config) ===
def save_config(
        self,
        cmd="copy running-configuration startup-configuration",
        confirm=False,
        confirm_response="",
    ):
        """Saves Config"""
        return super(DellForce10SSH, self).save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )

# === BLOCK 2 (label=human, source_idx=line2580_human, name=build_url_field) ===
def build_url_field(self, field_name, model_class):
        """
        Create a field representing the object's own URL.
        """
        field_class = self.serializer_url_field
        field_kwargs = get_url_kwargs(model_class)

        return field_class, field_kwargs

# === BLOCK 3 (label=lm, source_idx=line428_lm, name=iter_range) ===
def iter_range(reader, start, end, prev_size=0):
    """
    Creates an iterator which iterates over lines where
    start <= line < end (end exclusive)
    """
    while True:
        line = reader.readline()
        if not line:
            break
        if len(line) < prev_size:
            break
        if start <= int(line) < end:
            yield line

# === BLOCK 4 (label=human, source_idx=line2240_human, name=find_parameter) ===
def find_parameter(parameters, **kwargs):
    """
    Given a list of parameters, find the one with the given name.
    """
    matching_parameters = filter_parameters(parameters, **kwargs)
    if len(matching_parameters) == 1:
        return matching_parameters[0]
    elif len(matching_parameters) > 1:
        raise MultipleParametersFound()
    raise NoParameterFound()

# === BLOCK 5 (label=lm, source_idx=line2444_lm, name=poi_coords) ===
def poi_coords(poi_id, *, raw=False):
    """
    DVB Map Coordinates
    (GET https://www.dvb.de/apps/map/coordinates)

    :param poi_id: Id of poi
    :param raw: Return raw response
    :return: Coordinates of poi
    """
    return get_request(
        'https://www.dvb.de/apps/map/coordinates',
        params={'poi_id': poi_id},
        raw=raw
    )

# === BLOCK 6 (label=lm, source_idx=line2325_lm, name=post) ===
def post(self, request, *args, **kwargs):
        """ Triggers the task that sends invitation messages
        """
        # Get the user
        user = self.get_object()

        # Get the invitation
        invitation = Invitation.objects.get(pk=kwargs['invitation_id'])

        # Send the invitation
        send_invitation_email.delay(user.id, invitation.id)

        # Redirect to the user page
        return HttpResponseRedirect(reverse('users:detail', kwargs={'pk': user.id}))
