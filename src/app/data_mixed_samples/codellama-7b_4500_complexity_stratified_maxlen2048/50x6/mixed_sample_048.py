# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line468_human, name=_from_pointer) ===
def _from_pointer(pointer, incref):
        """Wrap an existing :c:type:`cairo_scaled_font_t *` cdata pointer.

        :type incref: bool
        :param incref:
            Whether increase the :ref:`reference count <refcounting>` now.
        :return: A new :class:`ScaledFont` instance.

        """
        if pointer == ffi.NULL:
            raise ValueError('Null pointer')
        if incref:
            cairo.cairo_scaled_font_reference(pointer)
        self = object.__new__(ScaledFont)
        ScaledFont._init_pointer(self, pointer)
        return self

# === BLOCK 2 (label=human, source_idx=line4911_human, name=validate_busy) ===
def validate_busy(func, *args, **kwargs):
    """
    A decorator that raises an exception if the specified target is busy.

    Expects the target ID to be either the 'target_id' param in kwargs,
    or the first positional parameter.

    Raises a TargetBusyException if the target does not exist.
    """
    def inner(self, *args, **kwargs):
        # find the target param
        target_id = None
        if 'target_id' in kwargs and kwargs['target_id'] != None:
            target_id = kwargs['target_id']
        else:
            target_id = 0

        # if there was a target specified, ensure it's not busy
        if self.target_is_busy(target_id):
            raise TargetBusyException()

        # call the function
        return func(self, *args, **kwargs)
    return inner

# === BLOCK 3 (label=human, source_idx=line3753_human, name=Compile) ===
def Compile(self, filter_implementation):
    """Compile the binary expression into a filter object."""
    operator = self.operator.lower()
    if operator in ('and', '&&'):
      method = 'AndFilter'
    elif operator in ('or', '||'):
      method = 'OrFilter'
    else:
      raise errors.ParseError(
          'Invalid binary operator {0:s}.'.format(operator))

    args = [x.Compile(filter_implementation) for x in self.args]
    return filter_implementation.FILTERS[method](arguments=args)

# === BLOCK 4 (label=lm, source_idx=line8896_lm, name=save_config) ===
def save_config(
        self,
        cmd="copy running-configuration startup-configuration",
        confirm=False,
        confirm_response="",
    ):
        """Saves Config"""
        return self.device.send_config_set(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )

# === BLOCK 5 (label=lm, source_idx=line5555_lm, name=description) ===
def description(self, force_refresh=False):
        """Call ``DescribeHyperParameterTuningJob`` for the hyperparameter tuning job.

        Args:
            force_refresh (bool): Set to True to fetch the latest data from SageMaker API.

        Returns:
            dict: The Amazon SageMaker response for ``DescribeHyperParameterTuningJob``.
        """
        if force_refresh or not self._description:
            self._description = self._sagemaker_session.sagemaker_client.describe_hyper_parameter_tuning_job(
                HyperParameterTuningJobName=self.name
            )
        return self._description

# === BLOCK 6 (label=lm, source_idx=line6846_lm, name=ip_registrant_monitor) ===
def ip_registrant_monitor(self, query, days_back=0, search_type="all", server=None, country=None, org=None, page=1,
                              include_total_count=False, **kwargs):
        """Query based on free text query terms"""
        params = {
            "query": query,
            "days_back": days_back,
            "search_type": search_type,
            "page": page,
            "include_total_count": include_total_count
        }
        if server:
            params["server"] = server
        if country:
            params["country"] = country
        if org:
            params["org"] = org
        return self._get("ip/registrant/monitor", params=params, **kwargs)
