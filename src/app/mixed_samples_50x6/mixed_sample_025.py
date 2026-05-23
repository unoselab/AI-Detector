# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line120_human, name=get_public_keys) ===
def get_public_keys(vm_):
    """
    Retrieve list of SSH public keys.
    """
    key_filename = config.get_cloud_config_value(
        'ssh_public_key', vm_, __opts__, search_global=False, default=None
    )
    if key_filename is not None:
        key_filename = os.path.expanduser(key_filename)
        if not os.path.isfile(key_filename):
            raise SaltCloudConfigError(
                'The defined ssh_public_key \'{0}\' does not exist'.format(
                    key_filename
                )
            )
        ssh_keys = []
        with salt.utils.files.fopen(key_filename) as rfh:
            for key in rfh.readlines():
                ssh_keys.append(salt.utils.stringutils.to_unicode(key))

        return ssh_keys

# === BLOCK 2 (label=human, source_idx=line1813_human, name=from_dict) ===
def from_dict(cls, copula_dict):
        """Set attributes with provided values."""
        instance = cls()

        instance.fitted = copula_dict['fitted']
        instance.constant_value = copula_dict['constant_value']

        if instance.fitted and not instance.constant_value:
            instance.model = scipy.stats.gaussian_kde([-1, 0, 0])

            for key in ['dataset', 'covariance', 'inv_cov']:
                copula_dict[key] = np.array(copula_dict[key])

            attributes = ['d', 'n', 'dataset', 'covariance', 'factor', 'inv_cov']
            for name in attributes:
                setattr(instance.model, name, copula_dict[name])

        return instance

# === BLOCK 3 (label=lm, source_idx=line1154_lm, name=filter_by_maf) ===
def filter_by_maf(min_maf=0.01):
    """
    return function that filters by maf
    (takes minimum maf, default is 0.01)
    """
    def filter_function(variant):
        return variant['maf'] >= min_maf
    return filter_function

# === BLOCK 4 (label=human, source_idx=line2719_human, name=get_raise_brok) ===
def get_raise_brok(self, host_name, service_name=''):
        """Get a start downtime brok

        :param host_name: host concerned by the downtime
        :type host_name
        :param service_name: service concerned by the downtime
        :type service_name
        :return: brok with wanted data
        :rtype: alignak.brok.Brok
        """
        data = self.serialize()
        data['host'] = host_name
        if service_name != '':
            data['service'] = service_name

        return Brok({'type': 'downtime_raise', 'data': data})

# === BLOCK 5 (label=lm, source_idx=line1757_lm, name=load_lst) ===
def load_lst(self):
        """
        Load the lst file into internal data structures

        """
        with open(self.lst_file, 'r') as f:
            for line in f:
                if line.startswith(';'):
                    continue
                parts = line.split()
                if len(parts)!= 2:
                    continue
                self.lst_data[parts[0]] = parts[1]

# === BLOCK 6 (label=lm, source_idx=line2489_lm, name=conditions) ===
def conditions(self, full_path, environ):
        """Return Etag and Last-Modified values (based on mtime)."""
        stat = os.stat(full_path)
        mtime = stat.st_mtime
        etag = f'"{mtime}"'
        last_modified = email.utils.formatdate(mtime, usegmt=True)
        return etag, last_modified
