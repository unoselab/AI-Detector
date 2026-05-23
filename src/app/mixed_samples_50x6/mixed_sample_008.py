# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line76_human, name=_validate_json_for_regular_workflow) ===
def _validate_json_for_regular_workflow(json_spec, args):
    """
    Validates fields used only for building a regular, project-based workflow.
    """
    validated = {}
    override_project_id, override_folder, override_workflow_name = \
        dxpy.executable_builder.get_parsed_destination(args.destination)
    validated['project'] = _get_destination_project(json_spec, args, override_project_id)
    validated['folder'] = _get_destination_folder(json_spec, override_folder)

    workflow_name = _get_workflow_name(json_spec, override_workflow_name)
    if not workflow_name:
        print('Warning: workflow name is not specified')
    else:
        validated['name'] = workflow_name
    return validated

# === BLOCK 2 (label=lm, source_idx=line2015_lm, name=invite) ===
def invite(self, email, roles=None):
        """
        Send invitation to email with a list of roles
        :param email:
        :param roles: None or "ALL" or list of role_names
        :return:
        """
        if not isinstance(email, str):
            raise TypeError("Email must be a string")
        if not isinstance(roles, (type(None), list)) and roles!= "ALL":
            raise TypeError("Roles must be a list or the string 'ALL'")
        if isinstance(roles, list) and not all(isinstance(role, str) for role in roles):
            raise TypeError("Roles must be a list of strings")
        if roles == "ALL":
            roles = self.role_names
        for role in roles:
            if role not in self.role_names:
                raise ValueError(f"Role {role} does not exist")
        invitation = Invitation(email=email, roles=roles)
        self.invitations.append(invitation)
        return invitation

# === BLOCK 3 (label=human, source_idx=line2568_human, name=main) ===
def main():
   """
   Simple command-line program for powering on virtual machines on a system.
   """

   args = GetArgs()
   if args.password:
      password = args.password
   else:
      password = getpass.getpass(prompt='Enter password for host %s and user %s: ' % (args.host,args.user))

   try:
      vmnames = args.vmname
      if not len(vmnames):
         print("No virtual machine specified for poweron")
         sys.exit()

      context = None
      if hasattr(ssl, '_create_unverified_context'):
         context = ssl._create_unverified_context()
      si = SmartConnect(host=args.host,
                        user=args.user,
                        pwd=password,
                        port=int(args.port),
                        sslContext=context)
      if not si:
         print("Cannot connect to specified host using specified username and password")
         sys.exit()

      atexit.register(Disconnect, si)

      # Retreive the list of Virtual Machines from the inventory objects
      # under the rootFolder
      content = si.content
      objView = content.viewManager.CreateContainerView(content.rootFolder,
                                                        [vim.VirtualMachine],
                                                        True)
      vmList = objView.view
      objView.Destroy()

      # Find the vm and power it on
      tasks = [vm.PowerOn() for vm in vmList if vm.name in vmnames]

      # Wait for power on to complete
      WaitForTasks(tasks, si)

      print("Virtual Machine(s) have been powered on successfully")
   except vmodl.MethodFault as e:
      print("Caught vmodl fault : " + e.msg)
   except Exception as e:
      print("Caught Exception : " + str(e))

# === BLOCK 4 (label=human, source_idx=line1094_human, name=become_slave) ===
def become_slave(self, broker):
        """
        Run as part of the handshake.
        @param broker: Remote reference to the broker object
        """
        self._set_state(BrokerRole.slave)
        self._master = broker
        d = defer.succeed(None)
        if callable(self.on_slave_cb):
            d.addCallback(defer.drop_param, self.on_slave_cb)

        d.addCallback(defer.drop_param, self._master.callRemote,
                      'handshake', self, self.agency, self.agency.agency_id,
                      self.is_standalone())
        d.addCallback(defer.inject_param, 1, self.update_state,
                      'reset_locally')

        for medium in self.agency.iter_agents():
            d.addCallback(defer.drop_param, self.register_agent, medium)

        return d

# === BLOCK 5 (label=lm, source_idx=line959_lm, name=in_region) ===
def in_region(rname, rstart, target_chr, target_start, target_end):
    """
    Quick check if a point is within the target region.
    """
    if target_chr == rname and target_start >= rstart:
        return True
    else:
        return False

# === BLOCK 6 (label=lm, source_idx=line148_lm, name=determineLength) ===
def determineLength(length):
        """
        Given first read byte, determine how many more bytes
        needs to be known in order to get fully encoded length.

        :param length: First read byte.
        :return: How many bytes to read.
        """
        if length < 128:
            return 0
        else:
            num_bytes = length & 7
            return num_bytes
