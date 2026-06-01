# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line2210_lm, name=moothedata) ===
def moothedata(data, key=None):
    """Return an amusing picture containing an item from a dict.

    Parameters
    ----------
    data: mapping
        A mapping, such as a raster dataset's ``meta`` or ``profile``
        property.
    key:
        A key of the ``data`` mapping.
    """
    if key is None:
        key = next(iter(data))
    return f"A moothed {key} is {data[key]}."

# === BLOCK 2 (label=human, source_idx=line3844_human, name=create_pull_request_iteration_status) ===
def create_pull_request_iteration_status(self, status, repository_id, pull_request_id, iteration_id, project=None):
        """CreatePullRequestIterationStatus.
        [Preview API] Create a pull request status on the iteration. This operation will have the same result as Create status on pull request with specified iteration ID in the request body.
        :param :class:`<GitPullRequestStatus> <azure.devops.v5_0.git.models.GitPullRequestStatus>` status: Pull request status to create.
        :param str repository_id: The repository ID of the pull request’s target branch.
        :param int pull_request_id: ID of the pull request.
        :param int iteration_id: ID of the pull request iteration.
        :param str project: Project ID or project name
        :rtype: :class:`<GitPullRequestStatus> <azure.devops.v5_0.git.models.GitPullRequestStatus>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        if iteration_id is not None:
            route_values['iterationId'] = self._serialize.url('iteration_id', iteration_id, 'int')
        content = self._serialize.body(status, 'GitPullRequestStatus')
        response = self._send(http_method='POST',
                              location_id='75cf11c5-979f-4038-a76e-058a06adf2bf',
                              version='5.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('GitPullRequestStatus', response)

# === BLOCK 3 (label=human, source_idx=line35_human, name=create) ===
def create(self, name, description, data_source_type,
               url, credential_user=None, credential_pass=None,
               is_public=None, is_protected=None, s3_credentials=None):
        """Create a Data Source."""

        data = {
            'name': name,
            'description': description,
            'type': data_source_type,
            'url': url,
        }
        credentials = {}
        self._copy_if_defined(credentials,
                              user=credential_user,
                              password=credential_pass)
        credentials = credentials or s3_credentials
        self._copy_if_defined(data, is_public=is_public,
                              is_protected=is_protected,
                              credentials=credentials)

        return self._create('/data-sources', data, 'data_source')

# === BLOCK 4 (label=lm, source_idx=line840_lm, name=absent) ===
def absent(name):
    """
    Ensure user account is absent

    name : string
        username
    """
    import subprocess
    result = subprocess.run(["id", name], capture_output=True)
    if result.returncode == 0:
        subprocess.run(["userdel", name])

# === BLOCK 5 (label=lm, source_idx=line2884_lm, name=create_default_config) ===
def create_default_config(schema):
    """Create a configuration dictionary from a schema dictionary.
    The schema defines the valid configuration keys and their default
    values.  Each element of ``schema`` should be a tuple/list
    containing (default value,docstring,type) or a dict containing a
    nested schema."""
    config = {}
    for key, value in schema.items():
        if isinstance(value, dict):
            config[key] = create_default_config(value)
        elif isinstance(value, tuple) and len(value) >= 3:
            default_value, _, value_type = value
            if value_type == int:
                config[key] = int(default_value)
            elif value_type == float:
                config[key] = float(default_value)
            elif value_type == str:
                config[key] = str(default_value)
            else:
                config[key] = default_value
        else:
            config[key] = value
    return config

# === BLOCK 6 (label=human, source_idx=line501_human, name=listSerialPorts) ===
def listSerialPorts():
	"""
	http://pyserial.readthedocs.io/en/latest/shortintro.html

	This calls the command line tool from pyserial to list the available
	serial ports.
	"""
	cmd = 'python -m serial.tools.list_ports'
	err, ret = commands.getstatusoutput(cmd)
	if not err:
		r = ret.split('\n')
		ret = []
		for line in r:
			if line.find('/dev/') >= 0:
				line = line.replace(' ', '')
				ret.append(line)
	return err, ret
