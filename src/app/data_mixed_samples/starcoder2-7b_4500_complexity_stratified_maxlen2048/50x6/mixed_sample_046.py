# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1835_human, name=K) ===
def K(self,X,X2,target):
        """Compute the covariance matrix between X and X2."""
        AX = np.dot(X,self.transform)
        if X2 is None:
            X2 = X
            AX2 = AX
        else:
            AX2 = np.dot(X2, self.transform)
        self.k.K(X,X2,target)
        self.k.K(AX,X2,target)
        self.k.K(X,AX2,target)
        self.k.K(AX,AX2,target)

# === BLOCK 2 (label=lm, source_idx=line4359_lm, name=_pruneMMD) ===
def _pruneMMD(self, minimum_solid_angle):
        """
        Remove regions of magnitude-magnitude space where the unmasked solid angle is
        statistically insufficient to estimate the background.

        INPUTS:
            solid_angle[1]: minimum solid angle (deg^2)
        """
        # get the unmasked solid angle
        unmasked_solid_angle = self.get_unmasked_solid_angle()

        # if the unmasked solid angle is less than the minimum solid angle, then
        # we need to remove the region from the magnitude-magnitude space
        if unmasked_solid_angle < minimum_solid_angle:
            # get the magnitude-magnitude space
            mags = self.get_magnitudes()
            mags = np.array(mags)

            # get the indices of the magnitude-magnitude space
            indices = np.where(mags[0] > 0)

            # get the magnitude-magnitude space
            mags = mags[:, indices]

            # get the unmasked solid angle
            unmasked_solid_angle = self.get_unmasked_solid_angle(mags)

            # if the unmasked solid angle is less than the minimum solid angle, then
            # we need to remove the region from the magnitude-magnitude space
            if unmasked_solid_angle < minimum_solid_angle:
                # get the indices of the magnitude-magnitude space
                indices = np.where(mags[0] > 0)

                # get the magnitude-magnitude space
                mags = mags[:, indices]

                # get the unmasked solid angle
                unmasked_solid_angle = self.get_unmasked_solid_angle(mags)

                # if the unmasked solid angle is less than the minimum solid angle, then
                # we need to remove the region from the magnitude-magnitude space
                if unmasked_solid_angle < minimum_solid_angle:
                    # get the indices of the magnitude-magnitude space
                    indices = np.where(mags[0] > 0)

                    # get the magnitude-magnitude space
                    mags = mags[:, indices]

                    # get the unmasked solid angle
                    unmasked_solid_angle = self.get_unmasked_solid_angle(mags)

                    # if the unmasked solid angle is less than the minimum solid angle, then
                    # we need to remove the region from the magnitude-magnitude space
                    if unmasked_solid_angle < minimum_solid_angle:
                        # get the indices of the magnitude-magnitude space
                        indices = np.where(mags[0] > 0)

                        # get the magnitude-magnitude space
                        mags = mags[:, indices]

                        # get the un

# === BLOCK 3 (label=human, source_idx=line437_human, name=from_object) ===
def from_object(cls, o, base_uri):
        """Returns a new ``Link`` based on a JSON object or array.

        Arguments:

        - ``o``: a dictionary holding the deserializated JSON for the new
                 ``Link``, or a ``list`` of such documents.
        - ``base_uri``: optional URL used as the basis when expanding
                               relative URLs in the link.

        """
        if isinstance(o, list):
            if len(o) == 1:
                return cls.from_object(o[0], base_uri)

            return [cls.from_object(x, base_uri) for x in o]

        return cls(o, base_uri)

# === BLOCK 4 (label=lm, source_idx=line629_lm, name=_strptime) ===
def _strptime(expr, date_format):
    """
    Return datetimes specified by date_format,
    which supports the same string format as the python standard library.
    Details of the string format can be found in python string format doc

    :param expr:
    :param date_format: date format string (e.g. “%Y-%m-%d”)
    :type date_format: str
    :return:
    """
    return datetime.strptime(expr, date_format)

# === BLOCK 5 (label=lm, source_idx=line2612_lm, name=process_signal) ===
def process_signal(self, signum):
        """Invoked whenever a signal is added to the stack.

        :param int signum: The signal that was added

        """
        self.signals.append(signum)

# === BLOCK 6 (label=human, source_idx=line4196_human, name=as_version) ===
def as_version(self, version=Version.latest):
        """Returns a dict that has been modified based on versioning
        in order to be represented in JSON properly

        A class should overload as_version(self, version)
        implementation in order to tailor a more specific representation

        :param version: the relevant version. This allows for variance
         between versions
        :type version: str | unicode

        """
        if not isinstance(self, list):
            result = {}
            for k, v in self.iteritems() if isinstance(self, dict) else vars(self).iteritems():
                k = self._props_corrected.get(k, k)
                if isinstance(v, SerializableBase):
                    result[k] = v.as_version(version)
                elif isinstance(v, list):
                    result[k] = []
                    for val in v:
                        if isinstance(val, SerializableBase):
                            result[k].append(val.as_version(version))
                        else:
                            result[k].append(val)
                elif isinstance(v, uuid.UUID):
                    result[k] = unicode(v)
                elif isinstance(v, datetime.timedelta):
                    result[k] = jsonify_timedelta(v)
                elif isinstance(v, datetime.datetime):
                    result[k] = jsonify_datetime(v)
                else:
                    result[k] = v
            result = self._filter_none(result)
        else:
            result = []
            for v in self:
                if isinstance(v, SerializableBase):
                    result.append(v.as_version(version))
                else:
                    result.append(v)
        return result
