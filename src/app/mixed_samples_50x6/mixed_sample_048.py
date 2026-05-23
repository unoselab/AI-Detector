# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line889_human, name=extract_field) ===
def extract_field(self, field):
        """ extract value from requests.Response.
        """
        if not isinstance(field, basestring):
            err_msg = u"Invalid extractor! => {}\n".format(field)
            logger.log_error(err_msg)
            raise exceptions.ParamsError(err_msg)

        msg = "extract: {}".format(field)

        if text_extractor_regexp_compile.match(field):
            value = self._extract_field_with_regex(field)
        else:
            value = self._extract_field_with_delimiter(field)

        if is_py2 and isinstance(value, unicode):
            value = value.encode("utf-8")

        msg += "\t=> {}".format(value)
        logger.log_debug(msg)

        return value

# === BLOCK 2 (label=lm, source_idx=line467_lm, name=log) ===
def log(self, name, val, **tags):
        """Log metric name with value val. You must include at least one tag as a kwarg"""
        if not tags:
            raise ValueError("At least one tag is required")
        self.metrics[name] = {**tags, "value": val}

# === BLOCK 3 (label=human, source_idx=line1806_human, name=get_grade_entries) ===
def get_grade_entries(self):
        """Gets the package list resulting from the search.

        return: (osid.grading.GradeEntryList) - the grade entry list
        raise:  IllegalState - list already retrieved
        *compliance: mandatory -- This method must be implemented.*

        """
        if self.retrieved:
            raise errors.IllegalState('List has already been retrieved.')
        self.retrieved = True
        return objects.GradeEntryList(self._results, runtime=self._runtime)

# === BLOCK 4 (label=lm, source_idx=line125_lm, name=main) ===
def main():
    """
    Starts the Application.

    :return: Definition success.
    :rtype: bool
    """
    return True

# === BLOCK 5 (label=lm, source_idx=line1215_lm, name=read_config) ===
def read_config(filename):
    """Reads and flattens a configuration file into a single
    dictionary for ease of use. Works with both ``.config`` and
    ``.yaml`` files. Files should look like this::

        search_rules:
            from-date: 2017-06-01
            to-date: 2017-09-01 01:01
            pt-rule: kanye

        search_params:
            results-per-call: 500
            max-results: 500

        output_params:
            save_file: True
            filename_prefix: kanye
            results_per_file: 10000000

    or::


        [search_rules]
        from_date = 2017-06-01
        to_date = 2017-09-01
        pt_rule = beyonce has:geo

        [search_params]
        results_per_call = 500
        max_results = 500

        [output_params]
        save_file = True
        filename_prefix = beyonce
        results_per_file = 10000000

    Args:
        filename (str): location of file with extension ('.config' or '.yaml')

    Returns:
        dict: parsed configuration dictionary.
    """
    def read_config(filename):
        if filename.endswith('.config'):
            parser = configparser.ConfigParser()
            parser.read(filename)
            config = {}
            for section in parser.sections():
                for key, value in parser.items(section):
                    config[key] = value
        elif filename.endswith('.yaml'):
            with open(filename) as f:
                config = yaml.load(f, Loader=yaml.FullLoader)
        else:
            raise ValueError("Invalid file extension. Must be '.config' or '.yaml'.")

        return config

# === BLOCK 6 (label=human, source_idx=line287_human, name=download_financialzip) ===
def download_financialzip():
    """
    会创建一个download/文件夹
    """
    result = get_filename()
    res = []
    for item, md5 in result:
        if item in os.listdir(download_path) and md5==QA_util_file_md5('{}{}{}'.format(download_path,os.sep,item)):

            print('FILE {} is already in {}'.format(item, download_path))
        else:
            print('CURRENTLY GET/UPDATE {}'.format(item[0:12]))
            r = requests.get('http://down.tdx.com.cn:8001/fin/{}'.format(item))

            file = '{}{}{}'.format(download_path, os.sep, item)

            with open(file, "wb") as code:
                code.write(r.content)
            res.append(item)
    return res
