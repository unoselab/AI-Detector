# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line2501_human, name=dinf_downslope_direction) ===
def dinf_downslope_direction(a):
        """Get the downslope directions of an dinf direction value
        Args:
            a: Dinf value

        Returns:
            downslope directions
        """
        taud, d = DinfUtil.check_orthogonal(a)
        if d != -1:
            down = [d]
            return down
        else:
            if a < FlowModelConst.ne:  # 129 = 1+128
                down = [1, 2]
            elif a < FlowModelConst.n:  # 192 = 128+64
                down = [2, 3]
            elif a < FlowModelConst.nw:  # 96 = 64+32
                down = [3, 4]
            elif a < FlowModelConst.w:  # 48 = 32+16
                down = [4, 5]
            elif a < FlowModelConst.sw:  # 24 = 16+8
                down = [5, 6]
            elif a < FlowModelConst.s:  # 12 = 8+4
                down = [6, 7]
            elif a < FlowModelConst.se:  # 6 = 4+2
                down = [7, 8]
            else:  # 3 = 2+1
                down = [8, 1]
            return down

# === BLOCK 2 (label=lm, source_idx=line3614_lm, name=switchCurrentView) ===
def switchCurrentView(self, viewType):
        """
        Swaps the current tab view for the inputed action's type.

        :param      action | <QAction>

        :return     <XView> || None
        """
        if viewType == "home":
            return self.homeView
        elif viewType == "search":
            return self.searchView
        elif viewType == "settings":
            return self.settingsView
        else:
            return None

# === BLOCK 3 (label=lm, source_idx=line2294_lm, name=list_ebs) ===
def list_ebs(region, filter_by_kwargs):
    """List running ebs volumes."""
    client = boto3.client('ec2', region_name=region)
    response = client.describe_instances(Filters=[
        {
            'Name': 'instance-state-name',
            'Values': ['running']
        }
    ])
    instances = [instance for reservation in response['Reservations'] for instance in reservation['Instances']]
    volumes = []
    for instance in instances:
        for volume in instance['BlockDeviceMappings']:
            if 'Ebs' in volume:
                volumes.append(volume['Ebs'])
    if filter_by_kwargs:
        filtered_volumes = []
        for volume in volumes:
            match = True
            for key, value in filter_by_kwargs.items():
                if volume.get(key)!= value:
                    match = False
                    break
            if match:
                filtered_volumes.append(volume)
        return filtered_volumes
    return volumes

# === BLOCK 4 (label=human, source_idx=line4615_human, name=array) ===
def array(_object):
    """
    Validates a given input is of type list.

    Example usage::

        data = {'a' : [1,2]}
        schema = ('a', array)

    You can also use this as a decorator, as a way to check for the
    input before it even hits a validator you may be writing.

    .. note::
        If the argument is a callable, the decorating behavior will be
        triggered, otherwise it will act as a normal function.

    """
    if is_callable(_object):
        _validator = _object

        @wraps(_validator)
        def decorated(value):
            ensure(isinstance(value, list), "not of type array")
            return _validator(value)
        return decorated
    ensure(isinstance(_object, list), "not of type array")

# === BLOCK 5 (label=human, source_idx=line4094_human, name=_interpolate_scipy_wrapper) ===
def _interpolate_scipy_wrapper(x, y, new_x, method, fill_value=None,
                               bounds_error=False, order=None, **kwargs):
    """
    Passed off to scipy.interpolate.interp1d. method is scipy's kind.
    Returns an array interpolated at new_x.  Add any new methods to
    the list in _clean_interp_method.
    """
    try:
        from scipy import interpolate
        # TODO: Why is DatetimeIndex being imported here?
        from pandas import DatetimeIndex  # noqa
    except ImportError:
        raise ImportError('{method} interpolation requires SciPy'
                          .format(method=method))

    new_x = np.asarray(new_x)

    # ignores some kwargs that could be passed along.
    alt_methods = {
        'barycentric': interpolate.barycentric_interpolate,
        'krogh': interpolate.krogh_interpolate,
        'from_derivatives': _from_derivatives,
        'piecewise_polynomial': _from_derivatives,
    }

    if getattr(x, 'is_all_dates', False):
        # GH 5975, scipy.interp1d can't hande datetime64s
        x, new_x = x._values.astype('i8'), new_x.astype('i8')

    if method == 'pchip':
        try:
            alt_methods['pchip'] = interpolate.pchip_interpolate
        except AttributeError:
            raise ImportError("Your version of Scipy does not support "
                              "PCHIP interpolation.")
    elif method == 'akima':
        try:
            from scipy.interpolate import Akima1DInterpolator  # noqa
            alt_methods['akima'] = _akima_interpolate
        except ImportError:
            raise ImportError("Your version of Scipy does not support "
                              "Akima interpolation.")

    interp1d_methods = ['nearest', 'zero', 'slinear', 'quadratic', 'cubic',
                        'polynomial']
    if method in interp1d_methods:
        if method == 'polynomial':
            method = order
        terp = interpolate.interp1d(x, y, kind=method, fill_value=fill_value,
                                    bounds_error=bounds_error)
        new_y = terp(new_x)
    elif method == 'spline':
        # GH #10633, #24014
        if isna(order) or (order <= 0):
            raise ValueError("order needs to be specified and greater than 0; "
                             "got order: {}".format(order))
        terp = interpolate.UnivariateSpline(x, y, k=order, **kwargs)
        new_y = terp(new_x)
    else:
        # GH 7295: need to be able to write for some reason
        # in some circumstances: check all three
        if not x.flags.writeable:
            x = x.copy()
        if not y.flags.writeable:
            y = y.copy()
        if not new_x.flags.writeable:
            new_x = new_x.copy()
        method = alt_methods[method]
        new_y = method(x, y, new_x, **kwargs)
    return new_y

# === BLOCK 6 (label=lm, source_idx=line4230_lm, name=on_api_error_14) ===
def on_api_error_14(self, request):
        """
        14. Captcha needed
        """
        captcha_url = 'https://www.google.com/recaptcha/api/image?c=' + request.captcha_id
        captcha_solution = input('Please solve the captcha at {}: '.format(captcha_url))
        request.captcha_solution = captcha_solution
