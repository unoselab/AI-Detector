# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line3574_human, name=update) ===
def update(self, *args):
        """
        Call the interact function and update the output widget with
        the result of the function call.

        Parameters
        ----------
        *args : ignored
            Required for this method to be used as traitlets callback.
        """
        self.kwargs = {}
        if self.manual:
            self.manual_button.disabled = True
        try:
            show_inline_matplotlib_plots()
            with self.out:
                if self.clear_output:
                    clear_output(wait=True)
                for widget in self.kwargs_widgets:
                    value = widget.get_interact_value()
                    self.kwargs[widget._kwarg] = value
                self.result = self.f(**self.kwargs)
                show_inline_matplotlib_plots()
                if self.auto_display and self.result is not None:
                    display(self.result)
        except Exception as e:
            ip = get_ipython()
            if ip is None:
                self.log.warn("Exception in interact callback: %s", e, exc_info=True)
            else:
                ip.showtraceback()
        finally:
            if self.manual:
                self.manual_button.disabled = False

# === BLOCK 2 (label=human, source_idx=line7782_human, name=get_num_sequenced) ===
def get_num_sequenced(study_id):
    """Return number of sequenced tumors for given study.

    This is useful for calculating mutation statistics in terms of the
    prevalence of certain mutations within a type of cancer.

    Parameters
    ----------
    study_id : str
        The ID of the cBio study.
        Example: 'paad_icgc'

    Returns
    -------
    num_case : int
        The number of sequenced tumors in the given study
    """
    data = {'cmd': 'getCaseLists',
            'cancer_study_id': study_id}
    df = send_request(**data)
    if df.empty:
        return 0
    row_filter = df['case_list_id'].str.contains('sequenced', case=False)
    num_case = len(df[row_filter]['case_ids'].tolist()[0].split(' '))
    return num_case

# === BLOCK 3 (label=human, source_idx=line1300_human, name=log) ===
def log(msg, *args, **kwargs):
    """Log a message to the console.

    Parameters
    ----------
    msg : str
        A string to display on the console. This can contain {}-style
        formatting commands; the remaining positional and keyword arguments
        will be used to fill them in.
    """
    now = datetime.datetime.now()
    module = 'downhill'
    if _detailed_callsite:
        caller = inspect.stack()[1]
        parts = caller.filename.replace('.py', '').split('/')
        module = '{}:{}'.format(
            '.'.join(parts[parts.index('downhill')+1:]), caller.lineno)
    click.echo(' '.join((
        click.style(now.strftime('%Y%m%d'), fg='blue'),
        click.style(now.strftime('%H%M%S'), fg='cyan'),
        click.style(module, fg='magenta'),
        msg.format(*args, **kwargs),
    )))

# === BLOCK 4 (label=human, source_idx=line6805_human, name=get_instance) ===
def get_instance(self, payload):
        """
        Build an instance of ChallengeInstance

        :param dict payload: Payload response from the API

        :returns: twilio.rest.authy.v1.service.entity.factor.challenge.ChallengeInstance
        :rtype: twilio.rest.authy.v1.service.entity.factor.challenge.ChallengeInstance
        """
        return ChallengeInstance(
            self._version,
            payload,
            service_sid=self._solution['service_sid'],
            identity=self._solution['identity'],
            factor_sid=self._solution['factor_sid'],
        )

# === BLOCK 5 (label=human, source_idx=line336_human, name=get_files) ===
def get_files():
    """
    Read all the template's files
    """

    files_root = path.join(path.dirname(__file__), 'files')

    for root, dirs, files in walk(files_root):
        rel_root = path.relpath(root, files_root)

        for file_name in files:
            try:
                f = open(path.join(root, file_name), 'r', encoding='utf-8')
                with f:
                    yield rel_root, file_name, f.read(), True
            except UnicodeError:
                f = open(path.join(root, file_name), 'rb')
                with f:
                    yield rel_root, file_name, f.read(), False

# === BLOCK 6 (label=human, source_idx=line2019_human, name=updateLodState) ===
def updateLodState(self, verbose=None):
        """
        Switch between full graphics details <---> fast rendering mode.

        Returns a success message.

        :param verbose: print more

        :returns: 200: successful operation
        """

        response=api(url=self.___url+'ui/lod', method="PUT", verbose=verbose)
        return response
