"""
Scans local Maven and Gradle projects using the JFrog CLI and filters Log4Shell results
"""
import json
import os
from distutils.version import LooseVersion
from shutil import which
from subprocess import DEVNULL, CalledProcessError, check_output
from typing import Dict, List, Optional, Set

import colorama
import easyargs

RED = colorama.Fore.RED
GREEN = colorama.Fore.GREEN
YELLOW = colorama.Fore.YELLOW

LOG4SHELL_CVES = {
    "CVE-2021-44228",
    "CVE-2021-45046",
    "CVE-2021-45105",
}


JFROG_CLI = which("jfrog") or which("jf")
JFROG_CLI_MIN_VERSION = LooseVersion("2.6.2")

g_verbose = False


class ChangeDir:
    """ ctxmgr to handle a directory change """
    def __init__(self, newdir):
        self.olddir = os.getcwd()
        self.newdir = newdir

    def __enter__(self):
        os.chdir(self.newdir)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        os.chdir(self.olddir)


def check_xray_results_for_cves(xray_results: Dict, target_cves: Set[str]) -> List[str]:
    detected_cves = []
    for res in xray_results:
        for vuln in res.get("vulnerabilities", []):
            for cve in vuln.get("cves", []):
                cve_str = cve.get("cve", "")
                if cve_str in target_cves:
                    detected_cves.append(cve_str)
    return detected_cves


def run_jfrog_cli(args: List[str]) -> Optional[Dict]:
    # Set stderr redirection according to verbosity
    if g_verbose:
        stderr = None
    else:
        stderr = DEVNULL

    # Run the CLI
    base_args = [JFROG_CLI]
    post_args = ["--format", "json"]
    json_str = check_output(base_args + args + post_args, stderr=stderr)

    return json.loads(json_str)


def check_project(root_dir: str, audit_command: str) -> List[str]:
    with ChangeDir(root_dir):
        xray_results = run_jfrog_cli([audit_command])
        if not xray_results:
            return []
    return check_xray_results_for_cves(xray_results, LOG4SHELL_CVES)


def check_gradle_project(root_dir: str) -> List[str]:
    print(f'Handling Gradle project at "{root_dir}"...')
    return check_project(root_dir, "audit-gradle")


def check_maven_project(root_dir: str) -> List[str]:
    print(f'Handling Maven project at "{root_dir}"...')
    return check_project(root_dir, "audit-mvn")


# Handlers for supported project types
SUPPORTED_PROJECT_TYPES = {
    "pom.xml": check_maven_project,
    "build.gradle": check_gradle_project
}


def check_single_directory(target_dir: str) -> bool:
    """
    Prints the detected CVEs
    returns True iff target_dir contains a supported project
    """
    dirfiles = os.listdir(target_dir)
    for indicator_file, project_handler in SUPPORTED_PROJECT_TYPES.items():
        if indicator_file in dirfiles:
            # Matched the directory to a supported project
            break
    else:
        return False

    try:
        detected_cves = project_handler(target_dir)
    except CalledProcessError:
        print(f'{YELLOW} Failed running JFrog CLI on "{target_dir}"')
        if not g_verbose:
            print(f'{YELLOW} Run with "--verbose" for more details')
        return True
    if detected_cves:
        for cve in detected_cves:
            print(f'{RED} Xray detected {cve}')
    else:
        print(f'{GREEN} Xray did not detect Log4Shell CVEs')

    return True


def check_directory_tree(root_dir) -> bool:
    """
    Prints the detected CVEs (recursive descent)
    returns True iff root_dir tree contains a supported project under it
    """
    # Check the root dir itself
    found_supported_project = check_single_directory(root_dir)

    # Check all dirs under the root dir
    for root, dirs, _ in os.walk(root_dir):
        for dir in dirs:
            found_supported_project |= check_single_directory(os.path.join(root, dir))

    return found_supported_project


def jfrog_config_get_values(jfrog_config: bytes, target_key: str) -> List[str]:
    """ Search Xray configuration for target_key and return matching values """
    values = []
    for line in jfrog_config.splitlines():
        try:
            line = line.decode("UTF-8")
        except UnicodeDecodeError:
            continue
        if not line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if key == target_key:
            values.append(value)

    return values


def jfrog_config_get_default_server() -> Optional[str]:
    jfrog_all_servers = check_output([JFROG_CLI, "config", "show"])
    servers = jfrog_config_get_values(jfrog_all_servers, "Server ID")
    defaults = jfrog_config_get_values(jfrog_all_servers, "Default")
    if not servers or not defaults:
        return None
    default_server_idx = [i for i, val in enumerate(defaults) if val == "true"]
    if not default_server_idx:
        return None
    return servers[default_server_idx[0]]


def check_default_xray_configured() -> bool:
    """ Checks that Xray URL is configured in the default Server ID used by JFrog CLI """
    # Get the default server
    jfrog_default_server = jfrog_config_get_default_server()
    if not jfrog_default_server:
        # No default server is configured
        return False

    # Query the default server for Xray URL
    jfrog_default_config = check_output([JFROG_CLI, "config", "show", jfrog_default_server])
    return bool(jfrog_config_get_values(jfrog_default_config, "Xray URL"))


def check_jfrog_cli_version() -> bool:
    version_output = check_output([JFROG_CLI, "--version"]).decode("UTF-8")
    version_str = version_output.split()[-1]  # Last word should be the version
    return LooseVersion(version_str) >= JFROG_CLI_MIN_VERSION


def check_prerequisites() -> bool:
    if not any(which(tool) for tool in ["mvn", "gradle"]):
        print('ERROR: Either "mvn" or "gradle" must be available')
        return False

    if not JFROG_CLI:
        print('ERROR: JFrog CLI must be available')
        return False

    if not check_jfrog_cli_version():
        print('ERROR: JFrog CLI version must be 2.6.2 or later')
        return False

    if not check_default_xray_configured():
        print('ERROR: JFrog CLI default server has no Xray URL configured')
        print('Visit https://www.jfrog.com/confluence/display/CLI/JFrog+CLI#JFrogCLI-AddingandEditingConfiguredServers for more details')
        return False

    return True


@easyargs
def main(target_dir, recurse=False, verbose=False):
    """
     :param target_dir: The directory to start searching from
     :param recurse: Search `target_dir` recursively for projects
     :param verbose: Output JFrog CLI STDERR to console
    """
    colorama.init(autoreset=True)

    global g_verbose
    g_verbose = verbose

    if not check_prerequisites():
        return

    if recurse:
        if not check_directory_tree(target_dir):
            print(f'{YELLOW} "{target_dir}" tree does not contain a supported project')
    else:
        if not check_single_directory(target_dir):
            print(f'{YELLOW} "{target_dir}" does not contain a supported project')


if __name__ == "__main__":
    main()
