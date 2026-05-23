# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line2215_lm, name=get_fit_failed_candidate_model) ===
def get_fit_failed_candidate_model(model_type, formula):
    """ Return a Candidate model that indicates the fitting routine failed.

    Parameters
    ----------
    model_type : :any:`str`
        Model type (e.g., ``'cdd_hdd'``).
    formula : :any:`float`
        The candidate model formula.

    Returns
    -------
    candidate_model : :any:`eemeter.CalTRACKUsagePerDayCandidateModel`
        Candidate model instance with status ``'ERROR'``, and warning with
        traceback.
    """
    def get_fit_failed_candidate_model(model_type, formula):
        candidate_model = CalTRACKUsagePerDayCandidateModel(
            model_type=model_type,
            formula=formula,
            status="ERROR",
            warning="Fitting routine failed.",
        )
        return candidate_model

# === BLOCK 2 (label=human, source_idx=line188_human, name=save) ===
def save(self, request, connect=False):
        """
        Saves a new account. Note that while the account is new,
        the user may be an existing one (when connecting accounts)
        """
        assert not self.is_existing
        user = self.user
        user.save()
        self.account.user = user
        self.account.save()
        if app_settings.STORE_TOKENS and self.token:
            self.token.account = self.account
            self.token.save()
        if connect:
            # TODO: Add any new email addresses automatically?
            pass
        else:
            setup_user_email(request, user, self.email_addresses)

# === BLOCK 3 (label=lm, source_idx=line1528_lm, name=to_shcoeffs) ===
def to_shcoeffs(self, itaper, normalization='4pi', csphase=1):
        """
        Return the spherical harmonic coefficients of taper i as a SHCoeffs
        class instance.

        Usage
        -----
        clm = x.to_shcoeffs(itaper, [normalization, csphase])

        Returns
        -------
        clm : SHCoeffs class instance

        Parameters
        ----------
        itaper : int
            Taper number, where itaper=0 is the best concentrated.
        normalization : str, optional, default = '4pi'
            Normalization of the output class: '4pi', 'ortho' or 'schmidt' for
            geodesy 4pi-normalized, orthonormalized, or Schmidt semi-normalized
            coefficients, respectively.
        csphase : int, optional, default = 1
            Condon-Shortley phase convention: 1 to exclude the phase factor,
            or -1 to include it.
        """
        def to_shcoeffs(self, itaper, normalization='4pi', csphase=1):
            if itaper < 0 or itaper >= self.ntapers:
                raise ValueError('itaper must be between 0 and self.ntapers-1')
            if normalization not in ['4pi', 'ortho','schmidt']:
                raise ValueError("normalization must be '4pi', 'ortho', or'schmidt'")
            if csphase not in [1, -1]:
                raise ValueError('csphase must be either 1 or -1')
            clm = SHCoeffs.from_array(self.tapers[itaper], normalization=normalization, csphase=csphase)

            return clm

# === BLOCK 4 (label=lm, source_idx=line188_lm, name=save) ===
def save(self, request, connect=False):
        """
        Saves a new account. Note that while the account is new,
        the user may be an existing one (when connecting accounts)
        """
        if connect:
            user = User.objects.get(pk=request.user.id)
        else:
            user = User.objects.create(username=request.data['username'], password=request.data['password'])
        account = Account.objects.create(user=user, name=request.data['name'], balance=request.data['balance'])
        return account

# === BLOCK 5 (label=human, source_idx=line1863_human, name=remove_selected_classification) ===
def remove_selected_classification(self):
        """Remove selected item on hazard class form."""
        removed_classes = self.hazard_class_form.selectedItems()
        current_item = self.hazard_class_form.currentItem()
        removed_index = self.hazard_class_form.indexFromItem(current_item)
        del self.classification[removed_index.row()]
        for item in removed_classes:
            self.hazard_class_form.takeItem(
                self.hazard_class_form.row(item))

# === BLOCK 6 (label=human, source_idx=line2718_human, name=start_dag) ===
def start_dag(self, dag, *, data=None):
        """ Schedule the execution of a dag by sending a signal to the workflow.

        Args:
            dag (Dag, str): The dag object or the name of the dag that should be started.
            data (MultiTaskData): The data that should be passed on to the new dag.

        Returns:
            str: The name of the successfully started dag.
        """
        return self._client.send(
            Request(
                action='start_dag',
                payload={'name': dag.name if isinstance(dag, Dag) else dag,
                         'data': data if isinstance(data, MultiTaskData) else None}
            )
        ).payload['dag_name']
