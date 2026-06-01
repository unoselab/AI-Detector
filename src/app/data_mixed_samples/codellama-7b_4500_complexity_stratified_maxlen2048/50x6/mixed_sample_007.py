# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1961_lm, name=_execute_callback) ===
def _execute_callback(self, callback, data):
        """Execute the callback in another thread. Wait for and return the results."""
        if callback is None:
            return None

        if not isinstance(callback, Callback):
            raise TypeError("callback must be a Callback")

        if not isinstance(data, dict):
            raise TypeError("data must be a dict")

        if self.thread_pool is None:
            self.thread_pool = ThreadPool(self.thread_pool_size)

        future = self.thread_pool.submit(callback.execute, data)
        return future.result()

# === BLOCK 2 (label=human, source_idx=line3760_human, name=get_translation) ===
def get_translation(self, lang, field):
        """
        Return the translation string of an specific field in a Translatable
        istance

        @type lang: string
        @param lang: a string with the name of the language

        @type field: string
        @param field: a string with the name that we try to get

        @rtype: string
        @return: Returns a translation string
        """
        # Read from cache
        key = self._get_translation_cache_key(lang, field)
        trans = cache.get(key, '')

        if not trans:
            trans_obj = self.get_translation_obj(lang, field)
            trans = getattr(trans_obj, 'translation', '')
            # if there's no translation text fall back to the model field
            if not trans:
                trans = getattr(self, field, '')
            # update cache
            cache.set(key, trans)
        return trans

# === BLOCK 3 (label=human, source_idx=line8366_human, name=_drop_diagonal) ===
def _drop_diagonal(self):
        """
        Drops self-contacts from the network dataframe.
        """
        self.network = self.network.where(
            self.network['i'] != self.network['j']).dropna()
        self.network.reset_index(inplace=True, drop=True)

# === BLOCK 4 (label=lm, source_idx=line4568_lm, name=update) ===
def update(self, pbar):
        """
        Handle progress bar updates
        @type   pbar:   ProgressBar
        @rtype: str
        """
        if self.total is None:
            pbar.update(self.current)
        else:
            pbar.update(self.current, self.total)

# === BLOCK 5 (label=lm, source_idx=line3361_lm, name=Write) ===
def Write(self, grr_message):
    """Write the message into the transaction log.

    Args:
      grr_message: A GrrMessage instance.
    """
    self.messages.append(grr_message)

# === BLOCK 6 (label=human, source_idx=line1729_human, name=destroy) ===
def destroy(name, call=None):
    """
    destroy a machine by name

    :param name: name given to the machine
    :param call: call value in this case is 'action'
    :return: array of booleans , true if successfully stopped and true if
             successfully removed

    CLI Example:

    .. code-block:: bash

        salt-cloud -d vm_name

    """
    if call == 'function':
        raise SaltCloudSystemExit(
            'The destroy action must be called with -d, --destroy, '
            '-a or --action.'
        )

    __utils__['cloud.fire_event'](
        'event',
        'destroying instance',
        'salt/cloud/{0}/destroying'.format(name),
        args={'name': name},
        sock_dir=__opts__['sock_dir'],
        transport=__opts__['transport']
    )

    node = get_node(name)
    ret = query(command='my/machines/{0}'.format(node['id']),
                location=node['location'], method='DELETE')

    __utils__['cloud.fire_event'](
        'event',
        'destroyed instance',
        'salt/cloud/{0}/destroyed'.format(name),
        args={'name': name},
        sock_dir=__opts__['sock_dir'],
        transport=__opts__['transport']
    )

    if __opts__.get('update_cachedir', False) is True:
        __utils__['cloud.delete_minion_cachedir'](name, __active_provider_name__.split(':')[0], __opts__)

    return ret[0] in VALID_RESPONSE_CODES
