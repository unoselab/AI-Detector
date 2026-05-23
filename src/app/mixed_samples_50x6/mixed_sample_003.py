# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1165_lm, name=cartpole) ===
def cartpole():
  """Configuration for the cart pole classic control task."""
  return cartpole.CartpoleEnv()

# === BLOCK 2 (label=lm, source_idx=line2852_lm, name=_needs_git) ===
def _needs_git(func):
    """
    Small decorator to make sure we have the git repo, or report error
    otherwise.
    """
    def wrapper(*args, **kwargs):
        try:
            import git
        except ImportError:
            raise RuntimeError("You need to install the gitpython package")
        return func(*args, **kwargs)
    return wrapper

# === BLOCK 3 (label=human, source_idx=line1514_human, name=sympy_expressions_equal) ===
def sympy_expressions_equal(expr1, expr2):
    """
    Compare two sympy expressions that are not necessarily expanded.
    :param expr1: a first expression
    :param expr2: a second expression
    :return: True if the expressions are similar, False otherwise
    """
    # the simplified difference is equal to zero: same expressions
    try:
        difference = sympy.simplify(sympy.expand(expr1 - expr2))
    except SympifyError:
        # Doing sympy.simplify(expr1 - expr2) raises an error if expr1 or expr2 is a matrix (for sympy 0.7.2)
        if isinstance(expr1, sympy.Matrix) or isinstance(expr2, sympy.Matrix):
            return _sympy_matrices_equal(expr1, expr2)
        else:
            raise

    # sympy 0.7.4 returns matrix of zeros for equal matrices
    try:
        difference = sum(difference)
    except TypeError:
        pass

    return difference == 0

# === BLOCK 4 (label=human, source_idx=line2215_human, name=get_fit_failed_candidate_model) ===
def get_fit_failed_candidate_model(model_type, formula):
    """ Return a Candidate model that indicates the fitting routine failed.

    Parameters
    ----------
    model_type : :any:`str`
        Model type (e.g., ``'cdd_hdd'``).
    formula : :any:`float`
        The candidate model formula.

    Returns
    -------
    candidate_model : :any:`eemeter.CalTRACKUsagePerDayCandidateModel`
        Candidate model instance with status ``'ERROR'``, and warning with
        traceback.
    """
    warnings = [
        EEMeterWarning(
            qualified_name="eemeter.caltrack_daily.{}.model_results".format(model_type),
            description=(
                "Error encountered in statsmodels.formula.api.ols method. (Empty data?)"
            ),
            data={"traceback": traceback.format_exc()},
        )
    ]
    return CalTRACKUsagePerDayCandidateModel(
        model_type=model_type, formula=formula, status="ERROR", warnings=warnings
    )

# === BLOCK 5 (label=lm, source_idx=line918_lm, name=get_pickup_time_estimates) ===
def get_pickup_time_estimates(self, latitude, longitude, ride_type=None):
        """Get pickup time estimates (ETA) for products at a given location.
        Parameters
            latitude (float)
                The latitude component of a location.
            longitude (float)
                The longitude component of a location.
            ride_type (str)
                Optional specific ride type pickup estimate only.
        Returns
            (Response)
                A Response containing each product's pickup time estimates.
        """
        params = {
            'latitude': latitude,
            'longitude': longitude,
        }
        if ride_type:
            params['ride_type'] = ride_type
        return self.request('GET', 'pickup/time_estimates', params=params)

# === BLOCK 6 (label=human, source_idx=line2515_human, name=resources_to_link) ===
def resources_to_link(self, resources):
        """
        If this API Event Source refers to an explicit API resource, resolve the reference and grab
        necessary data from the explicit API
        """

        rest_api_id = self.RestApiId
        if isinstance(rest_api_id, dict) and "Ref" in rest_api_id:
            rest_api_id = rest_api_id["Ref"]

        # If RestApiId is a resource in the same template, then we try find the StageName by following the reference
        # Otherwise we default to a wildcard. This stage name is solely used to construct the permission to
        # allow this stage to invoke the Lambda function. If we are unable to resolve the stage name, we will
        # simply permit all stages to invoke this Lambda function
        # This hack is necessary because customers could use !ImportValue, !Ref or other intrinsic functions which
        # can be sometimes impossible to resolve (ie. when it has cross-stack references)
        permitted_stage = "*"
        stage_suffix = "AllStages"
        explicit_api = None
        if isinstance(rest_api_id, string_types):

            if rest_api_id in resources \
               and "Properties" in resources[rest_api_id] \
               and "StageName" in resources[rest_api_id]["Properties"]:

                explicit_api = resources[rest_api_id]["Properties"]
                permitted_stage = explicit_api["StageName"]

                # Stage could be a intrinsic, in which case leave the suffix to default value
                if isinstance(permitted_stage, string_types):
                    if not permitted_stage:
                        raise InvalidResourceException(rest_api_id, 'StageName cannot be empty.')
                    stage_suffix = permitted_stage
                else:
                    stage_suffix = "Stage"

            else:
                # RestApiId is a string, not an intrinsic, but we did not find a valid API resource for this ID
                raise InvalidEventException(self.relative_id, "RestApiId property of Api event must reference a valid "
                                                              "resource in the same template.")

        return {
            'explicit_api': explicit_api,
            'explicit_api_stage': {
                'permitted_stage': permitted_stage,
                'suffix': stage_suffix
            }
        }
