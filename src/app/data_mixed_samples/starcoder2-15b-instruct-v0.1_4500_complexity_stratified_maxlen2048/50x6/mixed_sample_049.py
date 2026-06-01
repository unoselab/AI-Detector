# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line4681_human, name=tax_for_order) ===
def tax_for_order(self, order_deets):
        """Shows the sales tax that should be collected for a given order."""
        request = self._post('taxes', order_deets)
        return self.responder(request)

# === BLOCK 2 (label=lm, source_idx=line1784_lm, name=_prepare_init_params_from_job_description) ===
def _prepare_init_params_from_job_description(cls, job_details, model_channel_name=None):
        """Convert the job description to init params that can be handled by the class constructor

        Args:
            job_details: the returned job details from a describe_training_job API call.
            model_channel_name (str): Name of the channel where pre-trained model data will be downloaded.

        Returns:
             dictionary: The transformed init_params

        """
        init_params = {
            "image_uri": job_details.get("AlgorithmSpecification", {}).get("TrainingImage"),
            "model_uri": job_details.get("ModelArtifacts", {}).get("S3ModelArtifacts"),
            "instance_type": job_details.get("ResourceConfig", {}).get("InstanceType"),
            "instance_count": job_details.get("ResourceConfig", {}).get("InstanceCount"),
            "role": job_details.get("RoleArn"),
            "hyperparameters": job_details.get("HyperParameters"),
            "input_data_config": job_details.get("InputDataConfig"),
            "output_data_config": job_details.get("OutputDataConfig"),
            "stopping_condition": job_details.get("StoppingCondition"),
            "enable_network_isolation": job_details.get("EnableNetworkIsolation"),
            "vpc_config": job_details.get("VpcConfig"),
            "tags": job_details.get("Tags"),
            "model_channel_name": model_channel_name,
        }
        return init_params

# === BLOCK 3 (label=human, source_idx=line4990_human, name=index_by) ===
def index_by(self, field):
        """
        Returns a dict with a key for each value of `field` and the first record with that value as value.
        :param field: Name of the field to index by.
        :type field: string.
        """
        values = self[field].unique()
        results = {}
        for value in values:
            results[value] = self.model_class(**self[self[field] == value].iloc[0])
        return results

# === BLOCK 4 (label=human, source_idx=line2184_human, name=ip_to_array) ===
def ip_to_array(ipaddress):
    """Convert a string representing an IPv4 address to 4 bytes."""
    res = []
    for i in ipaddress.split("."):
        res.append(int(i))

    assert len(res) == 4
    return res

# === BLOCK 5 (label=lm, source_idx=line3343_lm, name=get_resource_data) ===
def get_resource_data(ref_key, ref_id, scenario_id, type_id=None, expunge_session=True, **kwargs):
    """
        Get all the resource scenarios for a given resource
        in a given scenario. If type_id is specified, only
        return the resource scenarios for the attributes
        within the type.
    """
    resource_scenarios = []
    for resource_scenario in resource_scenarios:
        if type_id is not None and resource_scenario.type_id!= type_id:
            continue
        resource_scenarios.append(resource_scenario)
    return resource_scenarios

# === BLOCK 6 (label=lm, source_idx=line526_lm, name=_get_id2obj_high) ===
def _get_id2obj_high(self, id2obj_user, id_sources, fnc_fill):
        """Get id2obj containing: id_srcs and parents."""
        id2obj = dict(id2obj_user)
        for id_src in id_sources:
            if id_src not in id2obj:
                id2obj[id_src] = fnc_fill(id_src)
        return id2obj
