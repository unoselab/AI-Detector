# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line486_lm, name=get_region_size) ===
def get_region_size(region):
        """ Finds and returns the approximate size of region (in degrees)  
        from a HEALPix region string.   
        """
        match = re.search(r'nside(\d+)', region)
        if match:
            nside = int(match.group(1))
            pixel_area = 41253.0 / nside**2
            return pixel_area * len(re.findall(r'[\d]+', region))
        else:
            raise ValueError('Invalid region string')

# === BLOCK 2 (label=lm, source_idx=line2518_lm, name=help) ===
def help(cls, task=None):
        """Describe available tasks or one specific task"""
        if task is None:
            print("Available tasks:")
            for task in cls.tasks:
                print(f"- {task}")
        else:
            if task in cls.tasks:
                print(f"Description of {task} task:")
                print(cls.tasks[task].__doc__)
            else:
                print(f"Task {task} not found.")

# === BLOCK 3 (label=human, source_idx=line1924_human, name=get) ===
def get(cls, mastercard_action_id, note_text_master_card_action_id,
            monetary_account_id=None, custom_headers=None):
        """
        :type api_context: context.ApiContext
        :type user_id: int
        :type monetary_account_id: int
        :type mastercard_action_id: int
        :type note_text_master_card_action_id: int
        :type custom_headers: dict[str, str]|None

        :rtype: BunqResponseNoteTextMasterCardAction
        """

        if custom_headers is None:
            custom_headers = {}

        api_client = client.ApiClient(cls._get_api_context())
        endpoint_url = cls._ENDPOINT_URL_READ.format(cls._determine_user_id(),
                                                     cls._determine_monetary_account_id(
                                                         monetary_account_id),
                                                     mastercard_action_id,
                                                     note_text_master_card_action_id)
        response_raw = api_client.get(endpoint_url, {}, custom_headers)

        return BunqResponseNoteTextMasterCardAction.cast_from_bunq_response(
            cls._from_json(response_raw, cls._OBJECT_TYPE_GET)
        )

# === BLOCK 4 (label=human, source_idx=line3185_human, name=describe) ===
def describe(value):
    """Describe any value as a descriptor.

    Helper function for describing any object with an appropriate descriptor
    object.

    Args:
      value: Value to describe as a descriptor.

    Returns:
      Descriptor message class if object is describable as a descriptor, else
      None.
    """
    if isinstance(value, types.ModuleType):
        return describe_file(value)
    elif isinstance(value, messages.Field):
        return describe_field(value)
    elif isinstance(value, messages.Enum):
        return describe_enum_value(value)
    elif isinstance(value, type):
        if issubclass(value, messages.Message):
            return describe_message(value)
        elif issubclass(value, messages.Enum):
            return describe_enum(value)
    return None

# === BLOCK 5 (label=human, source_idx=line3600_human, name=compute_texptime) ===
def compute_texptime(imageObjectList):
    """
    Add up the exposure time for all the members in
    the pattern, since 'drizzle' doesn't have the necessary
    information to correctly set this itself.
    """
    expnames = []
    exptimes = []
    start = []
    end = []
    for img in imageObjectList:
        expnames += img.getKeywordList('_expname')
        exptimes += img.getKeywordList('_exptime')
        start += img.getKeywordList('_expstart')
        end += img.getKeywordList('_expend')

    exptime = 0.
    expstart = min(start)
    expend = max(end)
    exposure = None
    for n in range(len(expnames)):
        if expnames[n] != exposure:
            exposure = expnames[n]
            exptime += exptimes[n]

    return (exptime,expstart,expend)

# === BLOCK 6 (label=lm, source_idx=line4601_lm, name=find_message) ===
def find_message(current):
    """
        Search in messages. If "channel_key" given, search will be limited to that channel,
        otherwise search will be performed on all of user's subscribed channels.

        .. code-block:: python

            #  request:
                {
                'view':'_zops_search_unit,
                'channel_key': key,
                'query': string,
                'page': int,
                }

            #  response:
                {
                'results': [MSG_DICT, ],
                'pagination': {
                    'page': int, # current page
                    'total_pages': int,
                    'total_objects': int,
                    'per_page': int, # object per page
                    },
                'status': 'OK',
                'code': 200
                }
    """
    if "channel_key" in current:
        channel_key = current["channel_key"]
        search_results = search_messages_in_channel(channel_key)
    else:
        search_results = search_messages_in_all_channels()
    return search_results
