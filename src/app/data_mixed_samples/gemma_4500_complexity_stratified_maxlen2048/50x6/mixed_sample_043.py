# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line7785_lm, name=update) ===
def update(self, content):
        """Enumerates the bytes of the supplied bytearray and updates the CRC-64.
           No return value.
        """
        self.crc = self.crc_table[(self.crc ^ byte) & 0xFF] ^ (self.crc >> 8)

# === BLOCK 2 (label=lm, source_idx=line7527_lm, name=make) ===
def make(self, apps):
        """
        Make subreport items from results.
        """
        items = []
        for app in apps:
            items.append(app)
        return items

# === BLOCK 3 (label=human, source_idx=line4447_human, name=extract_function_argument) ===
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

    tree = parse(text)
    return list(filter_function_argument(tree, f_name, f_argn, f_argt))

# === BLOCK 4 (label=lm, source_idx=line6217_lm, name=get_bucket_policy) ===
def get_bucket_policy(self, bucket_name):
        """
        Get bucket policy of given bucket name.

        :param bucket_name: Bucket name.
        """
        try:
            response = self.s3_client.get_bucket_policy(Bucket=bucket_name)
            return response['Policy']
        except self.s3_client.exceptions.NoSuchBucketPolicy:
            return None
        except Exception as e:
            raise e

# === BLOCK 5 (label=human, source_idx=line1966_human, name=check_status_code) ===
def check_status_code(response, verbose):
    """
    Shouldn't happen, thanks to the UploadToDeprecatedPyPIDetected
    exception, but this is in case that breaks and it does.
    """
    if (response.status_code == 410 and
            response.url.startswith(("https://pypi.python.org",
                                     "https://testpypi.python.org"))):
        print("It appears you're uploading to pypi.python.org (or "
              "testpypi.python.org). You've received a 410 error response. "
              "Uploading to those sites is deprecated. The new sites are "
              "pypi.org and test.pypi.org. Try using "
              "https://upload.pypi.org/legacy/ "
              "(or https://test.pypi.org/legacy/) to upload your packages "
              "instead. These are the default URLs for Twine now. More at "
              "https://packaging.python.org/guides/migrating-to-pypi-org/ ")
    try:
        response.raise_for_status()
    except HTTPError as err:
        if response.text:
            if verbose:
                print('Content received from server:\n{}'.format(
                    response.text))
            else:
                print('NOTE: Try --verbose to see response content.')
        raise err

# === BLOCK 6 (label=human, source_idx=line5505_human, name=transform_position_array) ===
def transform_position_array(array, pos, euler, is_normal, reverse=False):
    """
    Transform any Nx3 position array by translating to a center-of-mass 'pos'
    and applying an euler transformation

    :parameter array array: numpy array of Nx3 positions in the original (star)
        coordinate frame
    :parameter array pos: numpy array with length 3 giving cartesian
        coordinates to offset all positions
    :parameter array euler: euler angles (etheta, elongan, eincl) in radians
    :parameter bool is_normal: whether each entry is a normal vector rather
        than position vector.  If true, the quantities won't be offset by
        'pos'
    :return: new positions array with same shape as 'array'.
    """
    trans_matrix = euler_trans_matrix(*euler)

    if not reverse:
        trans_matrix = trans_matrix.T

    if isinstance(array, ComputedColumn):
        array = array.for_computations

    if is_normal:
        # then we don't do an offset by the position
        return np.dot(np.asarray(array), trans_matrix)
    else:
        return np.dot(np.asarray(array), trans_matrix) + np.asarray(pos)
