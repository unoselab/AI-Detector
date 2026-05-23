# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line2763_human, name=_can_hold_element) ===
def _can_hold_element(self, element):
        """ require the same dtype as ourselves """
        dtype = self.values.dtype.type
        tipo = maybe_infer_dtype_type(element)
        if tipo is not None:
            return issubclass(tipo.type, dtype)
        return isinstance(element, dtype)

# === BLOCK 2 (label=lm, source_idx=line1619_lm, name=bind) ===
def bind(self, name, filterset):
        """ attach filter to filterset

        gives a name to use to extract arguments from querydict
        """
        self.filters[name] = filterset

# === BLOCK 3 (label=lm, source_idx=line2868_lm, name=insert_index) ===
def insert_index(self, table, name, url, std=""):
        """callback to insert index"""
        sql = "INSERT INTO %s (name, url, std) VALUES (?,?,?)" % table
        self.execute(sql, (name, url, std))
        self.commit()

# === BLOCK 4 (label=lm, source_idx=line971_lm, name=synonyms) ===
def synonyms(self):
        """A ranked list of all the names associated with this Compound.

        Requires an extra request. Result is cached.
        """
        if not hasattr(self, '_synonyms'):
            self._synonyms = self.client.compound_synonyms(self.id)
        return self._synonyms

# === BLOCK 5 (label=human, source_idx=line467_human, name=log) ===
def log(self, name, val, **tags):
        """Log metric name with value val. You must include at least one tag as a kwarg"""
        global _last_timestamp, _last_metrics

        # do not allow .log after closing
        assert not self.done.is_set(), "worker thread has been closed"
        # check if valid metric name
        assert all(c in _valid_metric_chars for c in name), "invalid metric name " + name

        val = float(val)  #Duck type to float/int, if possible.
        if int(val) == val:
            val = int(val)

        if self.host_tag and 'host' not in tags:
            tags['host'] = self.host_tag

        # get timestamp from system time, unless it's supplied as a tag
        timestamp = int(tags.pop('timestamp', time.time()))

        assert not self.done.is_set(), "tsdb object has been closed"
        assert tags != {}, "Need at least one tag"

        tagvals = ' '.join(['%s=%s' % (k, v) for k, v in tags.items()])

        # OpenTSDB has major problems if you insert a data point with the same
        # metric, timestamp and tags. So we keep a temporary set of what points
        # we have sent for the last timestamp value. If we encounter a duplicate,
        # it is dropped.
        unique_str = "%s, %s, %s, %s, %s" % (name, timestamp, tagvals, self.host, self.port)
        if timestamp == _last_timestamp or _last_timestamp == None:
            if unique_str in _last_metrics:
                return  # discard duplicate metrics
            else:
                _last_metrics.add(unique_str)
        else:
            _last_timestamp = timestamp
            _last_metrics.clear()

        line = "put %s %d %s %s\n" % (name, timestamp, val, tagvals)

        try:
            self.q.put(line, False)
            self.queued += 1
        except queue.Full:
            print("potsdb - Warning: dropping oldest metric because Queue is full. Size: %s" % self.q.qsize(), file=sys.stderr)
            self.q.get()  #Drop the oldest metric to make room
            self.q.put(line, False)
        return line

# === BLOCK 6 (label=human, source_idx=line2276_human, name=_add_single_session_to_to_ordered_dict) ===
def _add_single_session_to_to_ordered_dict(self, d, dataset_index, recommended_only):
        """
        Save a single session to an ordered dictionary.
        """
        for model_index, model in enumerate(self.models):
            # determine if model should be presented, or if a null-model should
            # be presented (if no model is recommended.)
            show_null = False
            if recommended_only:
                if self.recommendation_enabled:
                    if self.recommended_model is None:
                        if model_index == 0:
                            show_null = True
                        else:
                            continue
                    elif self.recommended_model == model:
                        pass
                    else:
                        continue
                else:
                    if model_index == 0:
                        show_null = True
                    else:
                        continue

            d["dataset_index"].append(dataset_index)
            d["doses_dropped"].append(self.doses_dropped)
            model._to_df(d, model_index, show_null)
