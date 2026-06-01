# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line3533_human, name=_set_or_sum_metric) ===
def _set_or_sum_metric(self, metrics, metric_path, value):
        """If we already have a datapoint for this metric, lets add
        the value. This is used when the logstash mode is enabled."""
        if metric_path in metrics:
            metrics[metric_path] += value
        else:
            metrics[metric_path] = value

# === BLOCK 2 (label=lm, source_idx=line787_lm, name=update) ===
def update(self, payload):
        """Updates the queried record with `payload` and returns the updated record after validating the response

        :param payload: Payload to update the record with
        :raise:
            :NoResults: if query returned no results
            :MultipleResults: if query returned more than one result (currently not supported)
        :return:
            - The updated record
        """
        self.validate_query_result()
        self.validate_payload(payload)
        self.validate_update_payload(payload)
        return self.client.update(self.query_result, payload)

# === BLOCK 3 (label=human, source_idx=line3392_human, name=encrypt) ===
def encrypt(self, plaintext):
        """Return ciphertext for given plaintext."""

        # String to bytes.
        plainbytes = plaintext.encode('utf8')

        # Compress plaintext bytes.
        compressed = zlib.compress(plainbytes)

        # Construct AES-GCM cipher, with 96-bit nonce.
        cipher = AES.new(self.cipher_key, AES.MODE_GCM, nonce=random_bytes(12))

        # Encrypt and digest.
        encrypted, tag = cipher.encrypt_and_digest(compressed)

        # Combine with nonce.
        combined = cipher.nonce + tag + encrypted

        # Encode as Base64.
        cipherbytes = base64.b64encode(combined)

        # Bytes to string.
        ciphertext = cipherbytes.decode('utf8')

        # Return ciphertext.
        return ciphertext

# === BLOCK 4 (label=human, source_idx=line5071_human, name=acquire_metadata) ===
def acquire_metadata(self):
        """
        Handles the acquisition of metadata for both collection mode and single
        mode, uses the metadata methods belonging to the article's publisher
        attribute.
        """
        #For space economy
        publisher = self.article.publisher

        if self.collection:  # collection mode metadata gathering
            pass
        else:  # single mode metadata gathering
            self.pub_id = publisher.package_identifier()
            self.title = publisher.package_title()
            for date in publisher.package_date():
                self.dates.add(date)

        #Common metadata gathering
        for lang in publisher.package_language():
            self.languages.add(lang)  # languages
        for contributor in publisher.package_contributors():  # contributors
            self.contributors.add(contributor)
        self.publishers.add(publisher.package_publisher())  # publisher names
        desc = publisher.package_description()
        if desc is not None:
            self.descriptions.add(desc)
        for subj in publisher.package_subject():
            self.subjects.add(subj)  # subjects
        #Rights
        art_rights = publisher.package_rights()
        self.rights.add(art_rights)
        if art_rights not in self.rights_associations:
            self.rights_associations[art_rights] = [self.article.doi]
        else:
            self.rights_associations[art_rights].append(self.article.doi)

# === BLOCK 5 (label=lm, source_idx=line4868_lm, name=load_clients) ===
def load_clients(self, path=None, apis=[]):
        """Generate client libraries for the given apis, without starting an
        api server"""
        if path is None:
            path = os.path.join(self.root_dir, 'clients')
        if not os.path.exists(path):
            os.makedirs(path)
        for api in apis:
            self.generate_client(api, path)

# === BLOCK 6 (label=lm, source_idx=line5989_lm, name=_iterate_records) ===
def _iterate_records(self):
        """ iterate over each record
        """
        for record in self.records:
            yield record
