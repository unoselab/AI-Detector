# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line7718_human, name=create_attachment) ===
def create_attachment(self, upload_stream, scope_identifier, hub_name, plan_id, timeline_id, record_id, type, name, **kwargs):
        """CreateAttachment.
        [Preview API]
        :param object upload_stream: Stream to upload
        :param str scope_identifier: The project GUID to scope the request
        :param str hub_name: The name of the server hub: "build" for the Build server or "rm" for the Release Management server
        :param str plan_id:
        :param str timeline_id:
        :param str record_id:
        :param str type:
        :param str name:
        :rtype: :class:`<TaskAttachment> <azure.devops.v5_0.task.models.TaskAttachment>`
        """
        route_values = {}
        if scope_identifier is not None:
            route_values['scopeIdentifier'] = self._serialize.url('scope_identifier', scope_identifier, 'str')
        if hub_name is not None:
            route_values['hubName'] = self._serialize.url('hub_name', hub_name, 'str')
        if plan_id is not None:
            route_values['planId'] = self._serialize.url('plan_id', plan_id, 'str')
        if timeline_id is not None:
            route_values['timelineId'] = self._serialize.url('timeline_id', timeline_id, 'str')
        if record_id is not None:
            route_values['recordId'] = self._serialize.url('record_id', record_id, 'str')
        if type is not None:
            route_values['type'] = self._serialize.url('type', type, 'str')
        if name is not None:
            route_values['name'] = self._serialize.url('name', name, 'str')
        if "callback" in kwargs:
            callback = kwargs["callback"]
        else:
            callback = None
        content = self._client.stream_upload(upload_stream, callback=callback)
        response = self._send(http_method='PUT',
                              location_id='7898f959-9cdf-4096-b29e-7f293031629e',
                              version='5.0-preview.1',
                              route_values=route_values,
                              content=content,
                              media_type='application/octet-stream')
        return self._deserialize('TaskAttachment', response)

# === BLOCK 2 (label=lm, source_idx=line1185_lm, name=_walk_through) ===
def _walk_through(job_dir, display_progress=False):
    """
    Walk through the job dir and return jobs
    """
    import os
    from tqdm import tqdm

    jobs = []
    for root, dirs, files in os.walk(job_dir):
        for file in files:
            jobs.append(os.path.join(root, file))

    if display_progress:
        # This is a placeholder for progress display logic 
        # as the walk is already complete.
        tqdm.write(f"Found {len(jobs)} jobs.")

    return jobs

# === BLOCK 3 (label=lm, source_idx=line266_lm, name=engineer_info) ===
def engineer_info(self, action):

        """
        Returns:
            dict: engineer command information
                - arguments (list<dict>): command arguments
                    - args (list):  args to pass through to click.argument
                    - kwargs (dict): keyword arguments to pass through to click.argument
                - options (list<dict>): command options
                    - args (list):  args to pass through to click.option
                    - kwargs (dict): keyword options to pass through to click.option
        """
        info = self.commands.get(action)
        if not info:
            return {"arguments": [], "options": []}
        return {
            "arguments": info.get("arguments", []),
            "options": info.get("options", [])
        }

# === BLOCK 4 (label=human, source_idx=line7674_human, name=unset_required_for) ===
def unset_required_for(cls, sharable_fields):
        """
        Fields borrowed by `SharedGlossaryAdmin` to build its temporary change form, only are
        required if they are declared in `sharable_fields`. Otherwise just deactivate them.
        """
        if 'link_content' in cls.base_fields and 'link_content' not in sharable_fields:
            cls.base_fields['link_content'].required = False
        if 'link_type' in cls.base_fields and 'link' not in sharable_fields:
            cls.base_fields['link_type'].required = False

# === BLOCK 5 (label=human, source_idx=line6120_human, name=get_nested_group_users) ===
def get_nested_group_users(self, groupname):
        """Retrieves a list of all users that directly or indirectly belong to the given groupname.

        Args:
            groupname: The group name.


        Returns:
            list:
                A list of strings of user names.
        """

        response = self._get(self.rest_url + "/group/user/nested",
                             params={"groupname": groupname,
                                     "start-index": 0,
                                     "max-results": 99999})

        if not response.ok:
            return None

        return [u['name'] for u in response.json()['users']]

# === BLOCK 6 (label=lm, source_idx=line2005_lm, name=_to_numeric) ===
def _to_numeric(val):
    """
    Helper function for conversion of various data types into numeric representation.
    """
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None
