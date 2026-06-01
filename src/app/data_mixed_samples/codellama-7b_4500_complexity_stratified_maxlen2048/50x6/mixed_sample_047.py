# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line6676_lm, name=run) ===
def run(self):
        """Run self on provided screen"""
        self.screen.fill(self.color)
        self.screen.blit(self.image, self.rect)

# === BLOCK 2 (label=human, source_idx=line8318_human, name=build_image_from_inherited_image) ===
def build_image_from_inherited_image(self, image_name: str, image_tag: str,
                                         repo_path: Path,
                                         requirements_option: RequirementsOptions):
        """
        Builds a image with installed requirements from the inherited image. (Or just tags the image
        if there are no requirements.)

        See :meth:`build_image` for parameters descriptions.

        :rtype: docker.models.images.Image
        """

        base_name, base_tag = self.get_inherit_image()

        if requirements_option == RequirementsOptions.no_requirements:
            image = self.get_image(base_name, base_tag)
            image.tag(image_name, image_tag)  # so ``build_image`` doesn't have to be called next time

            return image

        dockerfile = self.get_install_requirements_dockerfile(base_name, base_tag, repo_path, requirements_option)

        self.get_or_build_image(image_name, image_tag, dockerfile, build_context=repo_path.parent, pull=False)

        return self.get_image(image_name, image_tag)

# === BLOCK 3 (label=human, source_idx=line2656_human, name=expand_region) ===
def expand_region(tuple_of_s, a, b, start=0, stop=None):
    """Apply expend_slice on a tuple of slices"""
    return tuple(expand_slice(s, a, b, start=start, stop=stop)
                 for s in tuple_of_s)

# === BLOCK 4 (label=human, source_idx=line3444_human, name=_md5_compare) ===
def _md5_compare(self, file_path, checksum, block_size=2 ** 13):
        """Compare a given MD5 checksum with one calculated from a file."""
        with closing(self._tqdm(desc="MD5 checksumming", total=getsize(file_path), unit="B",
                                unit_scale=True)) as progress:
            md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                while True:
                    block_data = f.read(block_size)
                    if not block_data:
                        break
                    md5.update(block_data)
                    progress.update(len(block_data))
            return md5.hexdigest().lower() == checksum.lower()

# === BLOCK 5 (label=lm, source_idx=line3702_lm, name=is_valid_preview) ===
def is_valid_preview(preview):
  """ Verifies that the preview is a valid filetype """

# === BLOCK 6 (label=lm, source_idx=line6196_lm, name=_validated) ===
def _validated(self, value):
        """Format the value or raise a :exc:`ValidationError` if an error occurs."""
        try:
            return self.validate(value)
        except ValidationError as e:
            raise ValidationError(
                self.error_messages['invalid'],
                code='invalid',
                params={'value': value},
            ) from e
