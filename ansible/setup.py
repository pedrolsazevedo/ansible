#!/usr/bin/env python3
"""
Ansible Workstation Setup Manager
Handles installation, testing, and management of development workstation setup.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


class Colors:
    GREEN = '\033[1;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[1;34m'
    RED = '\033[1;31m'
    RESET = '\033[0m'


class WorkstationManager:
    def __init__(self):
        self.script_dir = Path(__file__).parent.absolute()
        self.playbook = self.script_dir / "playbooks" / "site.yml"
        self.requirements = self.script_dir / "requirements.yml"

        self.roles = {
            "system": "System preparation (update cache, essential packages)",
            "dev_tools": "Development tools (vim, wget, git, VS Code, Chrome)",
            "docker": "Docker Engine with user permissions",
            "package_managers": "Package managers (Homebrew, tfenv, pyenv, nvm)",
            "mise": "Mise polyglot runtime manager",
            "azure": "Azure CLI, Storage Explorer, AzCopy",
            "containers": "kubectl, Podman, Helm, kind",
            "rancher": "Rancher Desktop",
            "ssh": "SSH key generation (ed25519)"
        }

    def print_msg(self, msg: str, color: str = Colors.RESET):
        print(f"{color}{msg}{Colors.RESET}")

    def run_command(self, cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run shell command and return result."""
        try:
            return subprocess.run(cmd, check=check, capture_output=False)
        except subprocess.CalledProcessError as e:
            self.print_msg(f"✗ Command failed: {' '.join(cmd)}", Colors.RED)
            sys.exit(e.returncode)

    def check_requirements(self):
        """Check and install required packages."""
        self.print_msg("==> Checking requirements...", Colors.BLUE)

        packages = ["python3", "ansible", "python3-pip"]
        missing = []

        for pkg in packages:
            if subprocess.run(["which", pkg], capture_output=True).returncode != 0:
                missing.append(pkg)

        if missing:
            self.print_msg(f"Installing missing packages: {', '.join(missing)}", Colors.YELLOW)
            self.run_command(["sudo", "apt-get", "update"])
            self.run_command(["sudo", "apt-get", "install", "-y"] + missing)
        else:
            self.print_msg("✓ All requirements installed", Colors.GREEN)

    def install_collections(self):
        """Install Ansible collections."""
        self.print_msg("==> Installing Ansible collections...", Colors.BLUE)
        self.run_command(["ansible-galaxy", "collection", "install", "-r", str(self.requirements)])

    def test_syntax(self):
        """Run syntax check."""
        self.print_msg("==> Running syntax check...", Colors.BLUE)
        self.run_command(["ansible-playbook", str(self.playbook), "--syntax-check"])
        self.print_msg("✓ Syntax check passed", Colors.GREEN)

    def test_local(self):
        """Run local dry-run tests."""
        self.print_msg("==> Running local tests (dry-run)...", Colors.BLUE)

        self.test_syntax()

        # Test each role
        for tag, desc in self.roles.items():
            self.print_msg(f"\n==> Testing: {desc}", Colors.BLUE)
            self.run_command([
                "ansible-playbook", str(self.playbook),
                "--tags", tag, "--check", "-v"
            ])

        self.print_msg("\n✓ All local tests passed!", Colors.GREEN)

    def test_docker(self):
        """Run Docker-based integration tests."""
        self.print_msg("==> Running Docker tests...", Colors.BLUE)

        test_dir = self.script_dir / "tests"
        compose_file = test_dir / "docker-compose.yml"
        test_playbook = test_dir / "test.yml"
        inventory = test_dir / "inventory.yml"

        try:
            # Start container
            self.print_msg("Starting test container...", Colors.BLUE)
            self.run_command(["docker", "compose", "-f", str(compose_file), "up", "-d"])

            # Wait for container
            subprocess.run(["sleep", "5"])

            # Run tests
            self.print_msg("Running playbook...", Colors.BLUE)
            self.run_command(["ansible-playbook", str(test_playbook), "-i", str(inventory)])

            # Idempotence check
            self.print_msg("Testing idempotence...", Colors.BLUE)
            result = subprocess.run(
                ["ansible-playbook", str(test_playbook), "-i", str(inventory)],
                capture_output=True, text=True
            )

            if "changed=0" in result.stdout and "failed=0" in result.stdout:
                self.print_msg("✓ Idempotence test passed", Colors.GREEN)
            else:
                self.print_msg("✗ Idempotence test failed", Colors.RED)
                sys.exit(1)

        finally:
            # Cleanup
            self.print_msg("Cleaning up...", Colors.BLUE)
            self.run_command(["docker", "compose", "-f", str(compose_file), "down", "-v"])

        self.print_msg("✓ Docker tests passed!", Colors.GREEN)

    def select_roles(self) -> List[str]:
        """Interactive role selection."""
        self.print_msg("\n==> Select roles to install:", Colors.BLUE)
        selected = []

        for tag, desc in self.roles.items():
            response = input(f"Install {desc}? [Y/n] ").strip().lower()
            if response in ['', 'y', 'yes']:
                selected.append(tag)

        return selected

    def install(self, tags: Optional[List[str]] = None, interactive: bool = False):
        """Run installation."""
        self.check_requirements()
        self.install_collections()

        cmd = ["ansible-playbook", str(self.playbook), "-K"]

        if interactive:
            tags = self.select_roles()
            if not tags:
                self.print_msg("No roles selected. Exiting.", Colors.YELLOW)
                return

        if tags:
            cmd.extend(["--tags", ",".join(tags)])

        self.print_msg(f"\n==> Running installation... 🚀", Colors.GREEN)
        self.run_command(cmd)
        self.print_msg("\n✓ Installation complete!", Colors.GREEN)

    def list_roles(self):
        """List available roles."""
        self.print_msg("\n==> Available roles:", Colors.BLUE)
        for tag, desc in self.roles.items():
            print(f"  {Colors.GREEN}{tag:20}{Colors.RESET} {desc}")


def main():
    parser = argparse.ArgumentParser(
        description="Ansible Workstation Setup Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s install                    # Interactive installation
  %(prog)s install --all              # Install everything
  %(prog)s install --tags docker,mise # Install specific roles
  %(prog)s test                       # Run local tests
  %(prog)s test --docker              # Run Docker tests
  %(prog)s list                       # List available roles
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Install command
    install_parser = subparsers.add_parser("install", help="Install workstation setup")
    install_parser.add_argument("--all", action="store_true", help="Install all roles")
    install_parser.add_argument("--tags", help="Comma-separated list of role tags")

    # Test command
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("--docker", action="store_true", help="Run Docker-based tests")
    test_parser.add_argument("--syntax", action="store_true", help="Run syntax check only")

    # List command
    subparsers.add_parser("list", help="List available roles")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    manager = WorkstationManager()

    if args.command == "install":
        if args.all:
            manager.install()
        elif args.tags:
            manager.install(tags=args.tags.split(","))
        else:
            manager.install(interactive=True)

    elif args.command == "test":
        if args.syntax:
            manager.test_syntax()
        elif args.docker:
            manager.test_docker()
        else:
            manager.test_local()

    elif args.command == "list":
        manager.list_roles()


if __name__ == "__main__":
    main()
