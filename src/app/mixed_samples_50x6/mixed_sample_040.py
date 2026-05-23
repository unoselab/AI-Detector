# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1111_lm, name=send_message) ===
def send_message(message, pipe='public'):
    """
    writes message to pipe
    """
    with open(pipe, 'w') as f:
        f.write(message)

# === BLOCK 2 (label=human, source_idx=line2869_human, name=resolve_secrets) ===
def resolve_secrets(self):
        """Retrieve handles for all basic:secret: fields on input.

        The process must have the ``secrets`` resource requirement
        specified in order to access any secrets. Otherwise this method
        will raise a ``PermissionDenied`` exception.

        :return: A dictionary of secrets where key is the secret handle
            and value is the secret value.
        """
        secrets = {}
        for field_schema, fields in iterate_fields(self.input, self.process.input_schema):  # pylint: disable=no-member
            if not field_schema.get('type', '').startswith('basic:secret:'):
                continue

            name = field_schema['name']
            value = fields[name]
            try:
                handle = value['handle']
            except KeyError:
                continue

            try:
                secrets[handle] = Secret.objects.get_secret(
                    handle,
                    contributor=self.contributor
                )
            except Secret.DoesNotExist:
                raise PermissionDenied("Access to secret not allowed or secret does not exist")

        # If the process does not not have the right requirements it is not
        # allowed to access any secrets.
        allowed = self.process.requirements.get('resources', {}).get('secrets', False)  # pylint: disable=no-member
        if secrets and not allowed:
            raise PermissionDenied(
                "Process '{}' has secret inputs, but no permission to see secrets".format(
                    self.process.slug  # pylint: disable=no-member
                )
            )

        return secrets

# === BLOCK 3 (label=lm, source_idx=line1816_lm, name=reorder) ===
def reorder(self, index, direction):
        """
        Reorders the data being displayed in this tree.  It will check to
        see if a server side requery needs to happen based on the paging
        information for this tree.

        :param      index     | <column>
                    direction | <Qt.SortOrder>

        :sa         setOrder
        """
        if direction == Qt.AscendingOrder:
            self.model().sort(index, Qt.AscendingOrder)
        else:
            self.model().sort(index, Qt.DescendingOrder)

# === BLOCK 4 (label=lm, source_idx=line841_lm, name=_list_archive_members) ===
def _list_archive_members(archive):
    """
    :param archive:
        An archive from _open_archive()

    :return:
        A list of info objects to be used with _info_name() and _extract_info()
    """
    return archive.infolist()

# === BLOCK 5 (label=human, source_idx=line1143_human, name=parseCmdline) ===
def parseCmdline(rh):
    """
    Parse the request command input.

    Input:
       Request Handle

    Output:
       Request Handle updated with parsed input.
       Return code - 0: ok, non-zero: error
    """

    rh.printSysLog("Enter cmdVM.parseCmdline")

    if rh.totalParms >= 2:
        rh.userid = rh.request[1].upper()
    else:
        # Userid is missing.
        msg = msgs.msg['0010'][1] % modId
        rh.printLn("ES", msg)
        rh.updateResults(msgs.msg['0010'][0])
        rh.printSysLog("Exit cmdVM.parseCmdLine, rc: " +
            rh.results['overallRC'])
        return rh.results['overallRC']

    if rh.totalParms == 2:
        rh.subfunction = rh.userid
        rh.userid = ''

    if rh.totalParms >= 3:
        rh.subfunction = rh.request[2].upper()

    # Verify the subfunction is valid.
    if rh.subfunction not in subfuncHandler:
        # Subfunction is missing.
        subList = ', '.join(sorted(subfuncHandler.keys()))
        msg = msgs.msg['0011'][1] % (modId, subList)
        rh.printLn("ES", msg)
        rh.updateResults(msgs.msg['0011'][0])

    # Parse the rest of the command line.
    if rh.results['overallRC'] == 0:
        rh.argPos = 3               # Begin Parsing at 4th operand
        generalUtils.parseCmdline(rh, posOpsList, keyOpsList)

    rh.printSysLog("Exit cmdVM.parseCmdLine, rc: " +
        str(rh.results['overallRC']))
    return rh.results['overallRC']

# === BLOCK 6 (label=human, source_idx=line2619_human, name=plot) ===
def plot(self, **plot_kwargs: Any) -> None:
        """Plots excited state probability vs the Rabi angle (angle of rotation
        around the x-axis).

        Args:
            **plot_kwargs: Arguments to be passed to matplotlib.pyplot.plot.
        """
        fig = plt.figure()
        plt.plot(self._rabi_angles, self._excited_state_probs, 'ro-',
                 figure=fig, **plot_kwargs)
        plt.xlabel(r"Rabi Angle (Radian)", figure=fig)
        plt.ylabel('Excited State Probability', figure=fig)
        fig.show()
