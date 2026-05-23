# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line2790_lm, name=markov_blanket) ===
def markov_blanket(y, mean, scale, shape, skewness):
        """ Markov blanket for each likelihood term

        Parameters
        ----------
        y : np.ndarray
            univariate time series

        mean : np.ndarray
            array of location parameters for the Skew t distribution

        scale : float
            scale parameter for the Skew t distribution

        shape : float
            tail thickness parameter for the Skew t distribution

        skewness : float
            skewness parameter for the Skew t distribution

        Returns
        ----------
        - Markov blanket of the Skew t family
        """
        mean_mb = y + scale + shape + skewness
        scale_mb = y + mean + shape + skewness
        shape_mb = y + mean + scale + skewness
        skewness_mb = y + mean + scale + shape
        return mean_mb, scale_mb, shape_mb, skewness_mb

# === BLOCK 2 (label=human, source_idx=line1420_human, name=find_synonymous) ===
def find_synonymous(input_file, work_dir):
    """Run yn00 to find the synonymous subsitution rate for the alignment.
    """
    cwd = os.getcwd()
    os.chdir(work_dir)
    # create the .ctl file
    ctl_file = "yn-input.ctl"
    output_file = "nuc-subs.yn"
    ctl_h = open(ctl_file, "w")
    ctl_h.write("seqfile = %s\noutfile = %s\nverbose = 0\n" %
                (op.basename(input_file), output_file))
    ctl_h.write("icode = 0\nweighting = 0\ncommonf3x4 = 0\n")
    ctl_h.close()

    cl = YnCommandline(ctl_file)
    print("\tyn00:", cl, file=sys.stderr)
    r, e = cl.run()
    ds_value_yn = None
    ds_value_ng = None
    dn_value_yn = None
    dn_value_ng = None

    # Nei-Gojobori
    output_h = open(output_file)
    row = output_h.readline()
    while row:
        if row.find("Nei & Gojobori") >=0:
            for x in xrange(5):
                row = next(output_h)
            dn_value_ng, ds_value_ng = row.split('(')[1].split(')')[0].split()
            break
        row = output_h.readline()
    output_h.close()

    # Yang
    output_h = open(output_file)
    for line in output_h:
        if line.find("+-") >= 0 and line.find("dS") == -1:
            parts = line.split(" +-")
            ds_value_yn = extract_subs_value(parts[1])
            dn_value_yn = extract_subs_value(parts[0])

    if ds_value_yn is None or ds_value_ng is None:
        h = open(output_file)
        print("yn00 didn't work: \n%s" % h.read(), file=sys.stderr)

    os.chdir(cwd)
    return ds_value_yn, dn_value_yn, ds_value_ng, dn_value_ng

# === BLOCK 3 (label=human, source_idx=line2387_human, name=precip_master_station) ===
def precip_master_station(precip_daily,
                          master_precip_hourly,
                          zerodiv):
    """Disaggregate precipitation based on the patterns of a master station

    Parameters
    -----------
    precip_daily : pd.Series
        daily data
    master_precip_hourly :  pd.Series
        observed hourly data of the master station
    zerodiv : str
        method to deal with zero division by key "uniform" --> uniform
        distribution
    """

    precip_hourly = pd.Series(index=melodist.util.hourly_index(precip_daily.index))

    # set some parameters for cosine function
    for index_d, precip in precip_daily.iteritems():

        # get hourly data of the day
        index = index_d.date().isoformat()
        precip_h = master_precip_hourly[index]

        # calc rel values and multiply by daily sums
        # check for zero division
        if precip_h.sum() != 0 and precip_h.sum() != np.isnan(precip_h.sum()):
            precip_h_rel = (precip_h / precip_h.sum()) * precip

        else:
            # uniform option will preserve daily data by uniform distr
            if zerodiv == 'uniform':
                precip_h_rel = (1/24) * precip

            else:
                precip_h_rel = 0

        # write the disaggregated day to data
        precip_hourly[index] = precip_h_rel

    return precip_hourly

# === BLOCK 4 (label=human, source_idx=line342_human, name=movie) ===
def movie(args):
    """
    %prog movie test.tour test.clm ref.contigs.last

    Plot optimization history.
    """
    p = OptionParser(movie.__doc__)
    p.add_option("--frames", default=500, type="int",
                 help="Only plot every N frames")
    p.add_option("--engine", default="ffmpeg", choices=("ffmpeg", "gifsicle"),
                 help="Movie engine, output MP4 or GIF")
    p.set_beds()
    opts, args, iopts = p.set_image_options(args, figsize="16x8",
                                            style="white", cmap="coolwarm",
                                            format="png", dpi=300)

    if len(args) != 3:
        sys.exit(not p.print_help())

    tourfile, clmfile, lastfile = args
    tourfile = op.abspath(tourfile)
    clmfile = op.abspath(clmfile)
    lastfile = op.abspath(lastfile)
    cwd = os.getcwd()
    odir = op.basename(tourfile).rsplit(".", 1)[0] + "-movie"
    anchorsfile, qbedfile, contig_to_beds = \
        prepare_synteny(tourfile, lastfile, odir, p, opts)

    args = []
    for i, label, tour, tour_o in iter_tours(tourfile, frames=opts.frames):
        padi = "{:06d}".format(i)
        # Make sure the anchorsfile and bedfile has the serial number in,
        # otherwise parallelization may fail
        a, b = op.basename(anchorsfile).split(".", 1)
        ianchorsfile = a + "_" + padi + "." + b
        symlink(anchorsfile, ianchorsfile)

        # Make BED file with new order
        qb = Bed()
        for contig, o in zip(tour, tour_o):
            if contig not in contig_to_beds:
                continue
            bedlines = contig_to_beds[contig][:]
            if o == '-':
                bedlines.reverse()
            for x in bedlines:
                qb.append(x)

        a, b = op.basename(qbedfile).split(".", 1)
        ibedfile = a + "_" + padi + "." + b
        qb.print_to_file(ibedfile)
        # Plot dot plot, but do not sort contigs by name (otherwise losing
        # order)
        image_name = padi + "." + iopts.format

        tour = ",".join(tour)
        args.append([[tour, clmfile, ianchorsfile,
                    "--outfile", image_name, "--label", label]])

    Jobs(movieframe, args).run()

    os.chdir(cwd)
    make_movie(odir, odir, engine=opts.engine, format=iopts.format)

# === BLOCK 5 (label=lm, source_idx=line2591_lm, name=get_api_key) ===
def get_api_key(self, api_key_id):
        """Get API key details for key registered in organisation.

        :param str api_key_id: The ID of the API key to be updated (Required)
        :returns: API key object
        :rtype: ApiKey
        """
        api_key = self.api_keys.get(api_key_id)
        if api_key:
            return api_key
        else:
            raise ValueError(f"API key with ID {api_key_id} not found.")

# === BLOCK 6 (label=lm, source_idx=line386_lm, name=interm_fluent_ordering) ===
def interm_fluent_ordering(self) -> List[str]:
        """The list of intermediate-fluent names in canonical order.

        Returns:
            List[str]: A list of fluent names.
        """
        self.interm_fluents.sort()
        return [interm_fluent.name for interm_fluent in self.interm_fluents]
