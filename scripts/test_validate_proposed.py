"""Exercise the upgrade gate with representative apt-cache policy output."""

import importlib.util
from pathlib import Path
import unittest


spec = importlib.util.spec_from_file_location(
    "validate_proposed", Path(__file__).with_name("validate-proposed.py")
)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

REPOSITORIES = """ -1 https://archive.ubuntu.com/ubuntu noble-proposed/main amd64 Packages
     release v=24.04,o=Ubuntu,a=noble-proposed,n=noble,l=Ubuntu,c=main,b=amd64
"""
PACKAGES = """linux-generic:
  Installed: 6.8.0-149.149
  Candidate: 6.8.0-150.150
  Version table:
     6.8.0-150.150 990
          1 https://archive.ubuntu.com/ubuntu noble-proposed/main amd64 Packages
 *** 6.8.0-149.149 500
        500 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 Packages
        100 /var/lib/dpkg/status
"""


class ProposedPolicyTests(unittest.TestCase):
    def test_valid_policy(self):
        self.assertIn("1 linux-* packages at 990", validator.validate(
            "noble", "amd64", REPOSITORIES, PACKAGES
        ))

    def test_missing_index(self):
        with self.assertRaisesRegex(ValueError, "Missing loaded"):
            validator.validate("noble", "amd64", "", PACKAGES)

    def test_unrestricted_proposed_index(self):
        with self.assertRaisesRegex(ValueError, "priority -1"):
            validator.validate("noble", "amd64", REPOSITORIES.replace("-1 ", "500 "), PACKAGES)

    def test_wrong_architecture(self):
        with self.assertRaisesRegex(ValueError, "Missing loaded"):
            validator.validate("noble", "arm64", REPOSITORIES, PACKAGES)

    def test_overridden_kernel_pin(self):
        with self.assertRaisesRegex(ValueError, "expected 990"):
            validator.validate("noble", "amd64", REPOSITORIES, PACKAGES.replace("150 990", "150 500"))

    def test_no_proposed_kernels_blocks_upgrade(self):
        with self.assertRaisesRegex(ValueError, "no linux-\\*"):
            validator.validate("noble", "amd64", REPOSITORIES, "linux-generic:\n")

    def test_installed_proposed_and_multiple_origins(self):
        packages = PACKAGES.replace("     6.8.0-150.150 990", " *** 6.8.0-150.150 990")
        packages = packages.replace(
            "          1 https://", "        500 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 Packages\n          1 https://"
        )
        self.assertIn("Validated", validator.validate("noble", "amd64", REPOSITORIES, packages))


if __name__ == "__main__":
    unittest.main()
