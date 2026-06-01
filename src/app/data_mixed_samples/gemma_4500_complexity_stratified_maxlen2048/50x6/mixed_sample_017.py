# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line2166_lm, name=__erase_primes) ===
def __erase_primes(self):
        """Erase all prime markings"""
        for i in range(len(self.primes)):
            self.primes[i] = False

# === BLOCK 2 (label=lm, source_idx=line4974_lm, name=load_containers) ===
def load_containers(self, service, configs, use_cache):
        """
        :param service_name:
        :return None:
        """
        if use_cache and hasattr(self, '_container_cache'):
            cached = self._container_cache.get(service)
            if cached:
                return cached

        containers = []
        for config in configs:
            container = self.create_container(service, config)
            containers.append(container)

        if use_cache and hasattr(self, '_container_cache'):
            self._container_cache[service] = containers

        return containers

# === BLOCK 3 (label=lm, source_idx=line1261_lm, name=_process_response) ===
def _process_response(self, response: Response):
        """Handle the response and update the internal state."""
        if response.status_code == 200:
            self.last_response = response.json()
            self.status = "success"
        elif response.status_code == 404:
            self.status = "not_found"
        else:
            self.status = "error"
            self.error_message = response.text

        self.update_timestamp()

# === BLOCK 4 (label=human, source_idx=line711_human, name=interstore) ===
def interstore(self, dest, *others):
        """
        Store the intersection of the current set and one or more
        others in a new key.

        :param dest: the name of the key to store intersection
        :param others: One or more :py:class:`Set` instances
        :returns: A :py:class:`Set` referencing ``dest``.
        """
        keys = [self.key]
        keys.extend([other.key for other in others])
        self.database.sinterstore(dest, keys)
        return self.database.Set(dest)

# === BLOCK 5 (label=human, source_idx=line4295_human, name=init_vq_bottleneck) ===
def init_vq_bottleneck(bottleneck_size, hidden_size):
  """Get lookup table for VQ bottleneck."""
  means = tf.get_variable(
      name="means",
      shape=[bottleneck_size, hidden_size],
      initializer=tf.uniform_unit_scaling_initializer())
  ema_count = tf.get_variable(
      name="ema_count",
      shape=[bottleneck_size],
      initializer=tf.constant_initializer(0),
      trainable=False)
  with tf.colocate_with(means):
    ema_means = tf.get_variable(
        name="ema_means",
        initializer=means.initialized_value(),
        trainable=False)

  return means, ema_means, ema_count

# === BLOCK 6 (label=human, source_idx=line5929_human, name=delete_trigger) ===
def delete_trigger(self, trigger):
        """
        Deletes from the Alert API the trigger record identified by the ID of the provided
        `pyowm.alertapi30.trigger.Trigger`, along with all related alerts

        :param trigger: the `pyowm.alertapi30.trigger.Trigger` object to be deleted
        :type trigger: `pyowm.alertapi30.trigger.Trigger`
        :returns: `None` if deletion is successful, an exception otherwise
        """
        assert trigger is not None
        assert isinstance(trigger.id, str), "Value must be a string"
        status, _ = self.http_client.delete(
            NAMED_TRIGGER_URI % trigger.id,
            params={'appid': self.API_key},
            headers={'Content-Type': 'application/json'})
