# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1925_human, name=ctcp) ===
async def ctcp(self, target, query, contents=None):
        """ Send a CTCP request to a target. """
        if self.is_channel(target) and not self.in_channel(target):
            raise client.NotInChannel(target)

        await self.message(target, construct_ctcp(query, contents))

# === BLOCK 2 (label=human, source_idx=line2606_human, name=parse_rRNA) ===
def parse_rRNA(insertion, seq, gff):
    """
    parse rRNA to gff format
    """
    offset = insertion['offset']
    strand = insertion['strand']
    for rRNA in parse_masked(seq, 0)[0]:
        rRNA = ''.join(rRNA)
        Start = seq[1].find(rRNA) + 1
        End = Start + len(rRNA) - 1
        if strand == '-':
            Start, End = End - 2, Start - 2
        pos = (abs(Start + offset) - 1, abs(End + offset) - 1)
        Start, End = min(pos), max(pos)
        source = insertion['source']
        annot = '%s rRNA' % (source.split('from', 1)[0])
        gff['#seqname'].append(insertion['ID'])
        gff['source'].append(source)
        gff['feature'].append('rRNA')
        gff['start'].append(Start)
        gff['end'].append(End)
        gff['score'].append('.')
        gff['strand'].append(strand)
        gff['frame'].append('.')
        gff['attribute'].append('Name=%s' % (annot))
    return gff

# === BLOCK 3 (label=lm, source_idx=line5532_lm, name=from_response_data) ===
def from_response_data(cls, response_data):
        """
        Response factory

        :param response_data: requests.models.Response
        :return: pybomb.clients.Response
        """
        if response_data is None:
            raise ValueError("response_data cannot be None")
        try:
            json_data = response_data.json()
        except Exception:
            json_data = None
        instance = cls()
        instance.status_code = response_data.status_code
        instance.headers = dict(response_data.headers)
        instance.body = response_data.content
        instance.text = response_data.text
        instance.json = json_data
        instance.url = getattr(response_data, "url", None)
        return instance

# === BLOCK 4 (label=lm, source_idx=line4871_lm, name=_check_id) ===
def _check_id(entity, entity_type):
    """Check whether the ID is valid.

    First check if the ID is missing, and then check if it is a qualified
    string type, finally check if the string is empty. For all checks, it
    would raise a ParseError with the corresponding message.

    Args:
        entity: a string type object to be checked.
        entity_type: a string that shows the type of entities to check, usually
            `Compound` or 'Reaction'.
    """
    if entity is None:
        raise ParseError(f"{entity_type} ID is missing")
    if not isinstance(entity, str):
        raise ParseError(f"{entity_type} ID must be a string")
    if entity == "":
        raise ParseError(f"{entity_type} ID is empty")

# === BLOCK 5 (label=lm, source_idx=line2767_lm, name=create_on_demand) ===
def create_on_demand(self,
                         instance_type='default',
                         tags=None,
                         root_device_type='ebs',
                         size='default',
                         vol_type='gp2',
                         delete_on_termination=False):
        """Create one or more EC2 on-demand instances.

        :param size: Size of root device
        :type size: int
        :param delete_on_termination:
        :type delete_on_termination: boolean
        :param vol_type:
        :type vol_type: str
        :param root_device_type: The type of the root device.
        :type root_device_type: str
        :param instance_type: A section name in amazon.json
        :type instance_type: str
        :param tags:
        :type tags: dict
        :return: List of instances created
        :rtype: list
        """

# === BLOCK 6 (label=human, source_idx=line3126_human, name=_merge_args) ===
def _merge_args(qCmd, parsed_args, _extra_values, value_specs):
    """Merge arguments from _extra_values into parsed_args.

    If an argument value are provided in both and it is a list,
    the values in _extra_values will be merged into parsed_args.

    @param parsed_args: the parsed args from known options
    @param _extra_values: the other parsed arguments in unknown parts
    @param values_specs: the unparsed unknown parts
    """
    temp_values = _extra_values.copy()
    for key, value in six.iteritems(temp_values):
        if hasattr(parsed_args, key):
            arg_value = getattr(parsed_args, key)
            if arg_value is not None and value is not None:
                if isinstance(arg_value, list):
                    if value and isinstance(value, list):
                        if (not arg_value or
                                isinstance(arg_value[0], type(value[0]))):
                            arg_value.extend(value)
                            _extra_values.pop(key)
