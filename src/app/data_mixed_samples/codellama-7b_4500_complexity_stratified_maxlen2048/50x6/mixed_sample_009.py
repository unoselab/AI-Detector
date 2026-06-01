# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line7720_lm, name=_format_lines) ===
def _format_lines(self, tokensource):
        """
        Just format the tokens, without any wrapping tags.
        Yield individual lines.
        """
        for ttype, value in tokensource:
            if ttype is None:
                continue
            yield value

# === BLOCK 2 (label=lm, source_idx=line3753_lm, name=Compile) ===
def Compile(self, filter_implementation):
    """Compile the binary expression into a filter object."""
    if filter_implementation == 'python':
      return self._CompilePython(filter_implementation)
    elif filter_implementation == 'native':
      return self._CompileNative(filter_implementation)
    else:
      raise ValueError('Unknown filter implementation: %s' %
                       filter_implementation)

# === BLOCK 3 (label=human, source_idx=line2565_human, name=get_field_analysis) ===
def get_field_analysis(self, field):
        """
        Get the FieldAnalysis for a given fieldname

        :param field: TODO
        :return: :class:`FieldClassAnalysis`
        """
        class_analysis = self.get_class_analysis(field.get_class_name())
        if class_analysis:
            return class_analysis.get_field_analysis(field)
        return None

# === BLOCK 4 (label=human, source_idx=line4590_human, name=get_visible_items) ===
def get_visible_items(self):
        """Return a list of all visible items in the treewidget."""
        items = []
        iterator = QTreeWidgetItemIterator(self)
        while iterator.value():
            item = iterator.value()
            if not item.isHidden():
                if item.parent():
                    if item.parent().isExpanded():
                        items.append(item)
                else:
                    items.append(item)
            iterator += 1
        return items

# === BLOCK 5 (label=human, source_idx=line5555_human, name=description) ===
def description(self, force_refresh=False):
        """Call ``DescribeHyperParameterTuningJob`` for the hyperparameter tuning job.

        Args:
            force_refresh (bool): Set to True to fetch the latest data from SageMaker API.

        Returns:
            dict: The Amazon SageMaker response for ``DescribeHyperParameterTuningJob``.
        """
        if force_refresh:
            self.clear_cache()
        if not self._tuning_job_describe_result:
            self._tuning_job_describe_result = self._sage_client.describe_hyper_parameter_tuning_job(
                HyperParameterTuningJobName=self.name
            )
        return self._tuning_job_describe_result

# === BLOCK 6 (label=lm, source_idx=line7279_lm, name=enable_logging) ===
def enable_logging(self):
        """Enable logging to the global debug log.  This adds a run_id to the log,
        in case of muliple processes on the same machine.

        Currently no way to disable logging after it's enabled.
        """
        self.log = logging.getLogger('{}.{}'.format(self.log.name, self.run_id))
        self.log.setLevel(logging.DEBUG)
        self.log.addHandler(logging.StreamHandler())
