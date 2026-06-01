# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line4293_human, name=getPerfInfo) ===
def getPerfInfo(rh, useridlist):
    """
    Get the performance information for a userid

    Input:
       Request Handle
       Userid to query <- may change this to a list later.

    Output:
       Dictionary containing the following:
          overallRC - overall return code, 0: success, non-zero: failure
          rc        - RC returned from SMCLI if overallRC = 0.
          rs        - RS returned from SMCLI if overallRC = 0.
          errno     - Errno returned from SMCLI if overallRC = 0.
          response  - Stripped and reformatted output of the SMCLI command.
    """
    rh.printSysLog("Enter vmUtils.getPerfInfo, userid: " + useridlist)
    parms = ["-T", rh.userid,
             "-c", "1"]
    results = invokeSMCLI(rh, "Image_Performance_Query", parms)
    if results['overallRC'] != 0:
        # SMCLI failed.
        rh.printLn("ES", results['response'])
        rh.printSysLog("Exit vmUtils.getPerfInfo, rc: " +
                       str(results['overallRC']))
        return results

    lines = results['response'].split("\n")
    usedTime = 0
    totalCpu = 0
    totalMem = 0
    usedMem = 0
    try:
        for line in lines:
            if "Used CPU time:" in line:
                usedTime = line.split()[3].strip('"')
                # Value is in us, need make it seconds
                usedTime = int(usedTime) / 1000000
            if "Guest CPUs:" in line:
                totalCpu = line.split()[2].strip('"')
            if "Max memory:" in line:
                totalMem = line.split()[2].strip('"')
                # Value is in Kb, need to make it Mb
                totalMem = int(totalMem) / 1024
            if "Used memory:" in line:
                usedMem = line.split()[2].strip('"')
                usedMem = int(usedMem) / 1024
    except Exception as e:
        msg = msgs.msg['0412'][1] % (modId, type(e).__name__,
            str(e), results['response'])
        rh.printLn("ES", msg)
        results['overallRC'] = 4
        results['rc'] = 4
        results['rs'] = 412

    if results['overallRC'] == 0:
        memstr = "Total Memory: %iM\n" % totalMem
        usedmemstr = "Used Memory: %iM\n" % usedMem
        procstr = "Processors: %s\n" % totalCpu
        timestr = "CPU Used Time: %i sec\n" % usedTime
        results['response'] = memstr + usedmemstr + procstr + timestr
    rh.printSysLog("Exit vmUtils.getPerfInfo, rc: " +
                   str(results['rc']))
    return results

# === BLOCK 2 (label=lm, source_idx=line3594_lm, name=solve_limited) ===
def solve_limited(self, assumptions=[]):
        """
            Solve internal formula using given budgets for conflicts and
            propagations.
        """
        result = self.solve(assumptions=assumptions, 
                             conflict_limit=self.conflict_limit, 
                             propagation_limit=self.propagation_limit)
        return result

# === BLOCK 3 (label=human, source_idx=line8924_human, name=_update_mappings) ===
def _update_mappings(self):
        """Update the mappings for the current index."""
        headers = {'Content-Type': 'application/json', 'DB-Method': 'PUT'}
        url = '/v2/exchange/db/{}/{}/_mappings'.format(self.domain, self.data_type)
        r = self.tcex.session.post(url, json=self.mapping, headers=headers)
        self.tcex.log.debug(
            'update mapping. status_code: {}, response: "{}".'.format(r.status_code, r.text)
        )

# === BLOCK 4 (label=lm, source_idx=line86_lm, name=export_ruptures_csv) ===
def export_ruptures_csv(ekey, dstore):
    """
    :param ekey: export key, i.e. a pair (datastore key, fmt)
    :param dstore: datastore object
    """
    ds_key, fmt = ekey
    data = dstore.get(ds_key)
    import csv
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(data)
    return output.getvalue(), fmt

# === BLOCK 5 (label=lm, source_idx=line6720_lm, name=get_overlays) ===
def get_overlays(self, **kw):
        """
        See Overlay.match() for arguments.
        """
        overlays = []
        for overlay in self.overlays:
            if overlay.match(**kw):
                overlays.append(overlay)
        return overlays

# === BLOCK 6 (label=human, source_idx=line4395_human, name=contents) ===
def contents(self):
        """Return the list of contained directory entries, loading them
        if not already loaded."""
        if not self.contents_read:
            self.contents_read = True
            base = self.path
            for entry in os.listdir(self.source_path):
                source_path = os.path.join(self.source_path, entry)
                target_path = os.path.join(base, entry)
                if os.path.isdir(source_path):
                    self.filesystem.add_real_directory(
                        source_path, self.read_only, target_path=target_path)
                else:
                    self.filesystem.add_real_file(
                        source_path, self.read_only, target_path=target_path)
        return self.byte_contents
