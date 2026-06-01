# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line3119_human, name=print_scan_summary) ===
def print_scan_summary(json_data, names=None):
    """
    Print a summary of the data returned from a
    CVE scan.
    """
    max_col_width = 50
    min_width = 15

    def _max_width(data):
        max_name = 0
        for name in data:
            max_name = len(data[name]) if len(data[name]) > max_name \
                else max_name
        # If the max name length is less that max_width
        if max_name < min_width:
            max_name = min_width

        # If the man name is greater than the max col leng
        # we wish to use
        if max_name > max_col_width:
            max_name = max_col_width

        return max_name

    clean = True

    if len(names) > 0:
        max_width = _max_width(names)
    else:
        max_width = min_width
    template = "{0:" + str(max_width) + "}   {1:5} {2:5} {3:5} {4:5}"
    sevs = ['critical', 'important', 'moderate', 'low']
    writeOut(template.format("Container/Image", "Cri", "Imp", "Med", "Low"))
    writeOut(template.format("-" * max_width, "---", "---", "---", "---"))
    res_summary = json_data['results_summary']
    for image in res_summary.keys():
        image_res = res_summary[image]
        if 'msg' in image_res.keys():
            tmp_tuple = (image_res['msg'], "", "", "", "")
        else:
            if len(names) < 1:
                image_name = image[:max_width]
            else:
                image_name = names[image][-max_width:]
                if len(image_name) == max_col_width:
                    image_name = '...' + image_name[-(len(image_name) - 3):]

            tmp_tuple = tuple([image_name] +
                              [str(image_res[sev]) for sev in sevs])
            sev_results = [image_res[sev] for sev in
                           sevs if image_res[sev] > 0]
            if len(sev_results) > 0:
                clean = False
        writeOut(template.format(*tmp_tuple))
    writeOut("")
    return clean

# === BLOCK 2 (label=human, source_idx=line6358_human, name=valueAt) ===
def valueAt(self, percent):
        """
        Returns the value at the inputed percent.

        :param     percent | <float>

        :return     <variant>
        """
        values = self.values()
        if percent < 0:
            index = 0
        elif percent > 1:
            index = -1
        else:
            index = percent * (len(values) - 1)

        # allow some floating point errors for the index (30% left or right)
        remain = index % 1
        if remain < 0.3 or 0.7 < remain:
            try:
                return values[int(round(index))]
            except IndexError:
                return None
        return None

# === BLOCK 3 (label=human, source_idx=line1193_human, name=chunks) ===
def chunks(self):
        """ Returns a chunk iterator over the sound. """
        if not hasattr(self, '_it'):
            class ChunkIterator(object):
                def __iter__(iter):
                    return iter

                def __next__(iter):
                    try:
                        chunk = self._next_chunk()
                    except StopIteration:
                        if self.loop:
                            self._init_stretching()
                            return iter.__next__()

                        raise

                    return chunk
                next = __next__

            self._it = ChunkIterator()

        return self._it

# === BLOCK 4 (label=human, source_idx=line5574_human, name=get_months_of_year) ===
def get_months_of_year(year):
    """
    Returns the number of months that have already passed in the given year.

    This is useful for calculating averages on the year view. For past years,
    we should divide by 12, but for the current year, we should divide by
    the current month.

    """
    current_year = now().year
    if year == current_year:
        return now().month
    if year > current_year:
        return 1
    if year < current_year:
        return 12

# === BLOCK 5 (label=human, source_idx=line2868_human, name=make_folder_for_today) ===
def make_folder_for_today(log_dir):
    """Creates the folder log_dir/yyyy/mm/dd in log_dir if it doesn't exist
    and returns the full path of the folder."""
    now = datetime.datetime.now()
    sub_folders_list = ['{0:04d}'.format(now.year),
                        '{0:02d}'.format(now.month),
                        '{0:02d}'.format(now.day)]
    folder = log_dir
    for sf in sub_folders_list:
        folder = os.path.join(folder, sf)
        if not os.path.exists(folder):
            os.makedirs(folder)
    return folder

# === BLOCK 6 (label=human, source_idx=line1886_human, name=_get_countdown_for_next_slice) ===
def _get_countdown_for_next_slice(self, spec):
    """Get countdown for next slice's task.

    When user sets processing rate, we set countdown to delay task execution.

    Args:
      spec: model.MapreduceSpec

    Returns:
      countdown in int.
    """
    countdown = 0
    if self._processing_limit(spec) != -1:
      countdown = max(
          int(parameters.config._SLICE_DURATION_SEC -
              (self._time() - self._start_time)), 0)
    return countdown
