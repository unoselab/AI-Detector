# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line20_human, name=clean) ===
def clean(self, value, initial=None):
        """
        Most part of this method is a copy of
        django.forms.MultiValueField.clean, with the exception of initial
        value handling (this need for correct processing FileField's).
        All original comments saved.
        """
        if initial is None:
            initial = [None for x in range(0, len(value))]
        else:
            if not isinstance(initial, list):
                initial = self.widget.decompress(initial)

        clean_data = []
        errors = []
        if not value or isinstance(value, (list, tuple)):
            if (not value or not [v for v in value if
                                  v not in self.empty_values]) \
                    and (not initial or not [v for v in initial if
                                             v not in self.empty_values]):
                if self.required:
                    raise ValidationError(self.error_messages['required'],
                                          code='required')
        else:
            raise ValidationError(self.error_messages['invalid'],
                                  code='invalid')
        for i, field in enumerate(self.fields):
            try:
                field_value = value[i]
            except IndexError:
                field_value = None
            try:
                field_initial = initial[i]
            except IndexError:
                field_initial = None

            if field_value in self.empty_values and \
                    field_initial in self.empty_values:
                if self.require_all_fields:
                    # Raise a 'required' error if the MultiValueField is
                    # required and any field is empty.
                    if self.required:
                        raise ValidationError(self.error_messages['required'],
                                              code='required')
                elif field.required:
                    # Otherwise, add an 'incomplete' error to the list of
                    # collected errors and skip field cleaning, if a required
                    # field is empty.
                    if field.error_messages['incomplete'] not in errors:
                        errors.append(field.error_messages['incomplete'])
                    continue
            try:
                clean_data.append(field.clean(field_value, field_initial))
            except ValidationError as e:
                # Collect all validation errors in a single list, which we'll
                # raise at the end of clean(), rather than raising a single
                # exception for the first error we encounter. Skip duplicates.
                errors.extend(m for m in e.error_list if m not in errors)
        if errors:
            raise ValidationError(errors)

        out = self.compress(clean_data)
        self.validate(out)
        self.run_validators(out)
        return out

# === BLOCK 2 (label=human, source_idx=line264_human, name=methodcaller) ===
def methodcaller(name, *args):
    """
    Upstream bug in python:
    https://bugs.python.org/issue26822
    """
    func = operator.methodcaller(name, *args)
    return lambda obj, **kwargs: func(obj)

# === BLOCK 3 (label=lm, source_idx=line5574_lm, name=get_months_of_year) ===
def get_months_of_year(year):
    """
    Returns the number of months that have already passed in the given year.

    This is useful for calculating averages on the year view. For past years,
    we should divide by 12, but for the current year, we should divide by
    the current month.

    """
    if year == datetime.now().year:
        return datetime.now().month
    else:
        return 12

# === BLOCK 4 (label=lm, source_idx=line4993_lm, name=scalarmult_B) ===
def scalarmult_B(e):
    """
    Implements scalarmult(B, e) more efficiently.
    """
    if e == 0:
        return 0
    elif e == 1:
        return B
    else:
        return scalarmult_B(e // 2) * scalarmult_B(e // 2) * (B if e % 2 == 1 else 1)

# === BLOCK 5 (label=lm, source_idx=line2806_lm, name=search_files) ===
def search_files(self, search):
        """
        Search for :class:`meteorpi_model.FileRecord` entities

        :param search:
            an instance of :class:`meteorpi_model.FileRecordSearch` used to constrain the observations returned from
            the DB
        :return:
            a structure of {count:int total rows of an unrestricted search, observations:list of
            :class:`meteorpi_model.FileRecord`}
        """
        if not isinstance(search, FileRecordSearch):
            raise TypeError("search must be an instance of FileRecordSearch")

        # TODO: implement this
        return None

# === BLOCK 6 (label=human, source_idx=line3169_human, name=find_version) ===
def find_version(file_path):
    """
    Scrape version information from specified file path.

    """
    with open(file_path, 'r') as f:
        file_contents = f.read()
    version_match = re.search(r"^__version__\s*=\s*['\"]([^'\"]*)['\"]",
                              file_contents, re.M)
    if version_match:
        return version_match.group(1)
    else:
        raise RuntimeError("unable to find version string")
