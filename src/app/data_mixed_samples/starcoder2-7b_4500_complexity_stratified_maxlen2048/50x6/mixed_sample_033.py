# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line6187_lm, name=get_object_id_from_graph) ===
def get_object_id_from_graph(access_token=None):
    """Return the object ID for the Graph user who owns the access token.

    Args:
        access_token (str): A Microsoft Graph access token. (Not an Azure access token.)
                            If not provided, attempt to get it from MSI_ENDPOINT.

    Returns:
        An object ID string for a user or service principal.
    """
    if not access_token:
        access_token = get_access_token_from_msi()

    if not access_token:
        raise ValueError("No access token provided.")

    # Get the object ID from the Graph API.
    graph_url = "https://graph.microsoft.com/v1.0/me"
    headers = {"Authorization": "Bearer " + access_token}
    response = requests.get(graph_url, headers=headers)
    response.raise_for_status()
    response_json = response.json()
    return response_json["id"]

# === BLOCK 2 (label=lm, source_idx=line1697_lm, name=warn_about_unmanaged_parameters) ===
def warn_about_unmanaged_parameters(self):
        """used to raise warning if the user got parameter
        that we do not manage from now

        :return: None
        """
        if self.unmanaged_parameters:
            warnings.warn("Unmanaged parameters: %s" %
                          self.unmanaged_parameters)

# === BLOCK 3 (label=human, source_idx=line1117_human, name=_discretize_check) ===
def _discretize_check(self, table, att, col):
        """
        Replaces the value with an appropriate interval symbol, if available.
        """
        label = "'%s'" % col
        if table in self.discr_intervals and att in self.discr_intervals[table]:
            intervals = self.discr_intervals[table][att]
            n_intervals = len(intervals)

            prev_value = None
            for i, value in enumerate(intervals):

                if i > 0:
                    prev_value = intervals[i - 1]

                if not prev_value and col <= value:
                    label = "'=<%.2f'" % value
                    break
                elif prev_value and col <= value:
                    label = "'(%.2f;%.2f]'" % (prev_value, value)
                    break
                elif col > value and i == n_intervals - 1:
                    label = "'>%.2f'" % value
                    break
        else:
            # For some reason using [ and ] crashes TreeLiker
            label = label.replace('[', 'I')
            label = label.replace(']', 'I')

        return label

# === BLOCK 4 (label=human, source_idx=line6814_human, name=hosts) ===
def hosts(self):
        """Generate Iterator over usable hosts in a network.

          This is like __iter__ except it doesn't return the
          Subnet-Router anycast address.

        """
        network = int(self.network_address)
        broadcast = int(self.broadcast_address)
        for x in long_range(1, broadcast - network + 1):
            yield self._address_class(network + x)

# === BLOCK 5 (label=human, source_idx=line5226_human, name=save_file_list) ===
def save_file_list(key, *files_refs):
    """Convert the given parameters to a special JSON object.

    Each parameter is a file-refs specification of the form:
    <file-path>:<reference1>,<reference2>, ...,
    where the colon ':' and the list of references are optional.

    JSON object is of the form:
    { key: {"file": file_path}}, or
    { key: {"file": file_path, "refs": [refs[0], refs[1], ... ]}}

    """
    file_list = []
    for file_refs in files_refs:
        if ':' in file_refs:
            try:
                file_name, refs = file_refs.split(':')
            except ValueError as e:
                return error("Only one colon ':' allowed in file-refs specification.")
        else:
            file_name, refs = file_refs, None
        if not os.path.isfile(file_name):
            return error(
                "Output '{}' set to a missing file: '{}'.".format(key, file_name)
            )
        file_obj = {'file': file_name}

        if refs:
            refs = [ref_path.strip() for ref_path in refs.split(',')]
            missing_refs = [
                ref for ref in refs if not (os.path.isfile(ref) or os.path.isdir(ref))
            ]
            if len(missing_refs) > 0:
                return error(
                    "Output '{}' set to missing references: '{}'.".format(
                        key, ', '.join(missing_refs)
                    )
                )
            file_obj['refs'] = refs

        file_list.append(file_obj)

    return json.dumps({key: file_list})

# === BLOCK 6 (label=lm, source_idx=line2017_lm, name=_should_split_cell) ===
def _should_split_cell(cls, cell_text: str) -> bool:
        """
        Checks whether the cell should be split.  We're just doing the same thing that SEMPRE did
        here.
        """
        return cell_text.strip().startswith("(") or cell_text.strip().startswith(")")
