# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line580_lm, name=removeIndexOnAttribute) ===
def removeIndexOnAttribute(self, attributeName):
        """
            removeIndexOnAttribute - Remove an attribute from indexing (for getElementsByAttr function) and remove indexed data.

        @param attributeName <lowercase str> - An attribute name. Will be lowercased. "name" and "id" will have no effect.
        """
        attributeName = attributeName.lower()
        if attributeName in self.indexedAttributes:
            del self.indexedAttributes[attributeName]
        if attributeName == "name" or attributeName == "id":
            return
        for element in self.elements:
            if attributeName in element.attributes:
                del element.attributes[attributeName]

# === BLOCK 2 (label=human, source_idx=line908_human, name=generate_veq) ===
def generate_veq(R=1.3, dR=0.1, Prot=6, dProt=0.1,nsamples=1e4,plot=False,
                 R_samples=None,Prot_samples=None):
    """ Returns the mean and std equatorial velocity given R,dR,Prot,dProt

    Assumes all distributions are normal.  This will be used mainly for
    testing purposes; I can use MC-generated v_eq distributions when we go for real.
    """
    if R_samples is None:
        R_samples = R*(1 + rand.normal(size=nsamples)*dR)
    else:
        inds = rand.randint(len(R_samples),size=nsamples)
        R_samples = R_samples[inds]

    if Prot_samples is None:
        Prot_samples = Prot*(1 + rand.normal(size=nsamples)*dProt)
    else:
        inds = rand.randint(len(Prot_samples),size=nsamples)
        Prot_samples = Prot_samples[inds]

    veq_samples = 2*np.pi*R_samples*RSUN/(Prot_samples*DAY)/1e5

    if plot:
        plt.hist(veq_samples,histtype='step',color='k',bins=50,normed=True)
        d = stats.norm(scale=veq_samples.std(),loc=veq_samples.mean())
        vs = np.linspace(veq_samples.min(),veq_samples.max(),1e4)
        plt.plot(vs,d.pdf(vs),'r')

    return veq_samples.mean(),veq_samples.std()

# === BLOCK 3 (label=human, source_idx=line1412_human, name=adev) ===
def adev(self, tau0, tau):
        """ return predicted ADEV of noise-type at given tau

        """
        prefactor = self.adev_from_qd(tau0=tau0, tau=tau)
        c = self.c_avar()
        avar = pow(prefactor, 2)*pow(tau, c)
        return np.sqrt(avar)

# === BLOCK 4 (label=lm, source_idx=line631_lm, name=get_output) ===
def get_output(self, idx=-1):
        """
      Return an additional output of the instruction

        :rtype: string

        """
        if idx < 0 or idx >= len(self.outputs):
            raise IndexError("Index out of range")
        return self.outputs[idx]

# === BLOCK 5 (label=lm, source_idx=line527_lm, name=split_denovos) ===
def split_denovos(denovo_path, temp_dir):
    """ split de novos from an input file into files, one for each gene
    """
    with open(denovo_path) as denovo_file:
        for line in denovo_file:
            gene = line.split()[0]
            gene_file_path = f"{temp_dir}/{gene}.txt"
            with open(gene_file_path, "a") as gene_file:
                gene_file.write(line)

# === BLOCK 6 (label=human, source_idx=line3870_human, name=get_title) ===
def get_title(src_name, src_type=None):
    """Normalizes a source name as a string to be used for viewer's title."""
    if src_type == 'tcp':
        return '{0}:{1}'.format(*src_name)
    return os.path.basename(src_name)
