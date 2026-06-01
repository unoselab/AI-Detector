# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line3031_lm, name=paste) ===
def paste(self, other):
        """Return a new Image with the given image pasted on top.

        This image will show through transparent areas of the given image.

        """
        new_image = Image.new(mode="RGBA", size=self.size)
        new_image.paste(self, (0, 0))
        new_image.paste(other, (0, 0), mask=other)
        return new_image

# === BLOCK 2 (label=human, source_idx=line2635_human, name=__args_check) ===
def __args_check(self, valid, args=None, kwargs=None):
        """
        valid is a dicts: {'args': [...], 'kwargs': {...}} or a list of such dicts.
        """
        if not isinstance(valid, list):
            valid = [valid]
        for cond in valid:
            if not isinstance(cond, dict):
                # Invalid argument
                continue
            # whitelist args, kwargs
            cond_args = cond.get('args', [])
            good = True
            for i, cond_arg in enumerate(cond_args):
                if args is None or len(args) <= i:
                    good = False
                    break
                if cond_arg is None:  # None == '.*' i.e. allow any
                    continue
                if not self.match_check(cond_arg, six.text_type(args[i])):
                    good = False
                    break
            if not good:
                continue
            # Check kwargs
            cond_kwargs = cond.get('kwargs', {})
            for k, v in six.iteritems(cond_kwargs):
                if kwargs is None or k not in kwargs:
                    good = False
                    break
                if v is None:  # None == '.*' i.e. allow any
                    continue
                if not self.match_check(v, six.text_type(kwargs[k])):
                    good = False
                    break
            if good:
                return True
        return False

# === BLOCK 3 (label=lm, source_idx=line3969_lm, name=timer) ===
def timer(name, count):
    """Time this block."""
    start_time = time.time()
    for _ in range(count):
        pass
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Time taken for {name} with count {count}: {elapsed_time} seconds")

# === BLOCK 4 (label=human, source_idx=line1606_human, name=mcmc_CH) ===
def mcmc_CH(self, walkerRatio, n_run, n_burn, mean_start, sigma_start, threadCount=1, init_pos=None, mpi=False):
        """
        runs mcmc on the parameter space given parameter bounds with CosmoHammerSampler
        returns the chain
        """
        lowerLimit, upperLimit = self.lower_limit, self.upper_limit

        mean_start = np.maximum(lowerLimit, mean_start)
        mean_start = np.minimum(upperLimit, mean_start)

        low_start = mean_start - sigma_start
        high_start = mean_start + sigma_start
        low_start = np.maximum(lowerLimit, low_start)
        high_start = np.minimum(upperLimit, high_start)
        sigma_start = (high_start - low_start) / 2
        mean_start = (high_start + low_start) / 2
        params = np.array([mean_start, lowerLimit, upperLimit, sigma_start]).T

        chain = LikelihoodComputationChain(
            min=lowerLimit,
            max=upperLimit)

        temp_dir = tempfile.mkdtemp("Hammer")
        file_prefix = os.path.join(temp_dir, "logs")
        #file_prefix = "./lenstronomy_debug"
        # chain.addCoreModule(CambCoreModule())
        chain.addLikelihoodModule(self.chain)
        chain.setup()

        store = InMemoryStorageUtil()
        #store = None
        if mpi is True:
            sampler = MpiCosmoHammerSampler(
            params=params,
            likelihoodComputationChain=chain,
            filePrefix=file_prefix,
            walkersRatio=walkerRatio,
            burninIterations=n_burn,
            sampleIterations=n_run,
            threadCount=1,
            initPositionGenerator=init_pos,
            storageUtil=store)
        else:
            sampler = CosmoHammerSampler(
                params=params,
                likelihoodComputationChain=chain,
                filePrefix=file_prefix,
                walkersRatio=walkerRatio,
                burninIterations=n_burn,
                sampleIterations=n_run,
                threadCount=threadCount,
                initPositionGenerator=init_pos,
                storageUtil=store)
        time_start = time.time()
        if sampler.isMaster():
            print('Computing the MCMC...')
            print('Number of walkers = ', len(mean_start)*walkerRatio)
            print('Burn-in iterations: ', n_burn)
            print('Sampling iterations:', n_run)
        sampler.startSampling()
        if sampler.isMaster():
            time_end = time.time()
            print(time_end - time_start, 'time taken for MCMC sampling')
        # if sampler._sampler.pool is not None:
        #     sampler._sampler.pool.close()
        try:
            shutil.rmtree(temp_dir)
        except Exception as ex:
            print(ex, 'shutil.rmtree did not work')
            pass
        #samples = np.loadtxt(file_prefix+".out")
        #prob = np.loadtxt(file_prefix+"prob.out")
        return store.samples, store.prob

# === BLOCK 5 (label=human, source_idx=line3452_human, name=undeclared_query_parameters) ===
def undeclared_query_parameters(self):
        """Return undeclared query parameters from job statistics, if present.

        See:
        https://cloud.google.com/bigquery/docs/reference/rest/v2/jobs#statistics.query.undeclaredQueryParameters

        :rtype:
            list of
            :class:`~google.cloud.bigquery.ArrayQueryParameter`,
            :class:`~google.cloud.bigquery.ScalarQueryParameter`, or
            :class:`~google.cloud.bigquery.StructQueryParameter`
        :returns: undeclared parameters, or an empty list if the query has
                  not yet completed.
        """
        parameters = []
        undeclared = self._job_statistics().get("undeclaredQueryParameters", ())

        for parameter in undeclared:
            p_type = parameter["parameterType"]

            if "arrayType" in p_type:
                klass = ArrayQueryParameter
            elif "structTypes" in p_type:
                klass = StructQueryParameter
            else:
                klass = ScalarQueryParameter

            parameters.append(klass.from_api_repr(parameter))

        return parameters

# === BLOCK 6 (label=lm, source_idx=line2085_lm, name=resource_path) ===
def resource_path(relative):
    """Adjust path for executable use in executable file"""
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, relative)
