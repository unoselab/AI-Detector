# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line4447_lm, name=extract_function_argument) ===
def extract_function_argument(text, f_name, f_argn, f_argt=asttypes.String):
    """
    Extract a specific argument from a specific function name.

    Arguments:

    text
        The source text.
    f_name
        The name of the function
    f_argn
        The argument position
    f_argt
        The argument type from calmjs.parse.asttypes;
        default: calmjs.parse.asttypes.String
    """
    import calmjs.parse
    ast = calmjs.parse.parse(text)
    for node in ast.body:
        if isinstance(node, calmjs.parse.asttypes.FunctionDeclaration) and node.name == f_name:
            if len(node.params) > f_argn:
                arg = node.params[f_argn]
                if isinstance(arg, f_argt):
                    return arg.value
    return None

# === BLOCK 2 (label=human, source_idx=line8769_human, name=get_imageid) ===
def get_imageid(vm_):
    """
    Returns the ImageId to use
    """
    image = config.get_cloud_config_value(
        'image', vm_, __opts__, search_global=False
    )
    if image.startswith('ami-'):
        return image
    # a poor man's cache
    if not hasattr(get_imageid, 'images'):
        get_imageid.images = {}
    elif image in get_imageid.images:
        return get_imageid.images[image]
    params = {'Action': 'DescribeImages',
              'Filter.0.Name': 'name',
              'Filter.0.Value.0': image}
    # Query AWS, sort by 'creationDate' and get the last imageId
    _t = lambda x: datetime.datetime.strptime(x['creationDate'], '%Y-%m-%dT%H:%M:%S.%fZ')
    image_id = sorted(aws.query(params, location=get_location(),
                                 provider=get_provider(), opts=__opts__, sigver='4'),
                      lambda i, j: salt.utils.compat.cmp(_t(i), _t(j))
                      )[-1]['imageId']
    get_imageid.images[image] = image_id
    return image_id

# === BLOCK 3 (label=lm, source_idx=line7026_lm, name=handler) ===
async def handler(self, request: Request) -> Tuple[int, str, List[Tuple[str, str]], bytes]:
        """
        The handler handling each request
        :param request: the Request instance
        :return: The Response instance
        """
        try:
            response_body = await request.app.handle_request(request)
            status_code = 200
            headers = [("Content-Type", "text/plain")]
            return status_code, "OK", headers, response_body
        except Exception as e:
            return 500, "Internal Server Error", [("Content-Type", "text/plain")], str(e).encode()

# === BLOCK 4 (label=human, source_idx=line6124_human, name=traverse) ===
def traverse(data, key, delim=defaults.DEFAULT_DELIM):
    """
    Traverse a dict or list using a slash delimiter target string.
    The target 'foo/bar/0' will return data['foo']['bar'][0] if
    this value exists, otherwise will return empty dict.
    Return None when not found.
    This can be used to verify if a certain key exists under
    dictionary hierarchy.
    """
    for each in key.split(delim):
        if isinstance(data, list):
            if isinstance(each, six.string_type):
                embed_match = False
                # Index was not numeric, lets look at any embedded dicts
                for embedded in (x for x in data if isinstance(x, dict)):
                    try:
                        data = embedded[each]
                        embed_match = True
                        break
                    except KeyError:
                        pass
                if not embed_match:
                    # No embedded dicts matched
                    return None
            else:
                try:
                    data = data[int(each)]
                except IndexError:
                    return None
        else:
            try:
                data = data[each]
            except (KeyError, TypeError):
                return None
    return data

# === BLOCK 5 (label=human, source_idx=line3845_human, name=cors_allow_any) ===
def cors_allow_any(request, response):
    """
    Add headers to permit CORS requests from any origin, with or without credentials,
    with any headers.
    """
    origin = request.META.get('HTTP_ORIGIN')
    if not origin:
        return response

    # From the CORS spec: The string "*" cannot be used for a resource that supports credentials.
    response['Access-Control-Allow-Origin'] = origin
    patch_vary_headers(response, ['Origin'])
    response['Access-Control-Allow-Credentials'] = 'true'

    if request.method == 'OPTIONS':
        if 'HTTP_ACCESS_CONTROL_REQUEST_HEADERS' in request.META:
            response['Access-Control-Allow-Headers'] \
                = request.META['HTTP_ACCESS_CONTROL_REQUEST_HEADERS']
        response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'

    return response

# === BLOCK 6 (label=lm, source_idx=line6911_lm, name=getModifiers) ===
def getModifiers(chart):
    """ Returns the factors of the temperament modifiers. """
    modifiers = []
    for note in chart:
        if 'modifier' in note:
            modifiers.append(note['modifier'])
    return modifiers
