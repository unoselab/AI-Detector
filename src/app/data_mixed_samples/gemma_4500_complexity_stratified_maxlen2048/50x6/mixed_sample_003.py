# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line7034_human, name=get) ===
def get(self, floating_ip_id):
        """Fetches the floating IP.

        :returns: FloatingIp object corresponding to floating_ip_id
        """
        fip = self.client.show_floatingip(floating_ip_id).get('floatingip')
        self._set_instance_info(fip)
        return FloatingIp(fip)

# === BLOCK 2 (label=lm, source_idx=line3173_lm, name=_get_fwl_billing_item) ===
def _get_fwl_billing_item(self, firewall_id, dedicated=False):
        """Retrieves the billing item of the firewall.

        :param int firewall_id: Firewall ID to get the billing item for
        :param bool dedicated: whether the firewall is dedicated or standard
        :returns: A dictionary of the firewall billing item.
        """
        billing_item = self.billing_service.get_firewall_billing_item(
            firewall_id=firewall_id,
            dedicated=dedicated
        )
        return billing_item

# === BLOCK 3 (label=human, source_idx=line7566_human, name=read_namespace_status) ===
def read_namespace_status(self, name, **kwargs):  # noqa: E501
        """read_namespace_status  # noqa: E501

        read status of the specified Namespace  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.read_namespace_status(name, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param str name: name of the Namespace (required)
        :param str pretty: If 'true', then the output is pretty printed.
        :return: V1Namespace
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        if kwargs.get('async_req'):
            return self.read_namespace_status_with_http_info(name, **kwargs)  # noqa: E501
        else:
            (data) = self.read_namespace_status_with_http_info(name, **kwargs)  # noqa: E501
            return data

# === BLOCK 4 (label=human, source_idx=line7501_human, name=ensure) ===
def ensure(cond, *args, **kwds):
    """
    Return if a condition is true, otherwise raise a caller-configurable
    :py:class:`Exception`
    :param bool cond: the condition to be checked
    :param sequence args: the arguments to be passed to the exception's
                          constructor
    The only accepted named parameter is `raising` used to configure the
    exception to be raised if `cond` is not `True`
    """
    _CHK_UNEXP = 'check_condition() got an unexpected keyword argument {0}'

    raising = kwds.pop('raising', AssertionError)
    if kwds:
        raise TypeError(_CHK_UNEXP.format(repr(kwds.popitem()[0])))

    if cond is True:
        return
    raise raising(*args)

# === BLOCK 5 (label=lm, source_idx=line5103_lm, name=get_service_by_name) ===
def get_service_by_name(self, service_name):
		"""Get a specific service by name."""
		for service in self.services:
		    if service.name == service_name:
		        return service
		return None

# === BLOCK 6 (label=lm, source_idx=line6044_lm, name=happybirthday) ===
def happybirthday(person):
    """
    Sing Happy Birthday
    """
    for i in range(4):
        if i == 2:
            print(f"Happy Birthday dear {person}!")
        else:
            print("Happy Birthday to you!")
