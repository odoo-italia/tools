import os
import json
from subprocess import check_output

REPO_FILE = (
    ".. FILE AUTOMATICALLY GENERATED. DO NOT EDIT\n"
    "\n"
    ":banner: banners/%s.jpg\n"
    "\n"
    "%s\n"
    "%s\n"
    "%s\n"
    "\n"
    "%s\n"
    "\n"
    "------\n"
    "Moduli\n"
    "------\n"
    "\n"
    "|\n"
    "\n"
    ".. toctree::\n"
    "   :titlesonly:\n"
    "\n"
)

SECTION_FILE = (
    ".. FILE AUTOMATICALLY GENERATED. DO NOT EDIT\n"
    "\n"
    "%s\n"
    "%s\n"
    "%s\n"
    "\n"
    ".. toctree::\n"
    "   :titlesonly:\n"
    "\n"
)

def reset_git_repo(path, branch):
    os.chdir(path)
    check_output(['git', 'checkout', '-f'])
    check_output(['git', 'clean', '-df'])
    check_output(["git", "fetch", "origin"])
    check_output(["git", "checkout", branch])
    check_output(['git', 'reset', '--hard', 'origin/%s' % branch])


def get_all_versions(data):
    versions = []
    for oca_section in data['oca_sections']:
        for oca_repo in data['oca_sections'][oca_section]['oca_repositories']:
            for version in data['oca_sections'][oca_section]['oca_repositories'][oca_repo]['versions']:
                if version not in versions:
                    versions.append(version)
    return versions


def push_if_needed(path):
    os.chdir(path)
    check_output(['git', 'add', '.'])
    diff = check_output(['git', 'diff', '--cached'])
    if diff:
        check_output(['git', 'commit', '-m', 'Automatic push of OCA README'])
        check_output(['git', 'push'])
    check_output(['make', 'html', 'SPHINXBUILD=/var/www/documentazione/venv/bin/sphinx-build'])


def build_modules_rst(local_doc_path_oca_repo, repo_title, repo_descr):
    repo_oca_dir, repo_name = os.path.split(local_doc_path_oca_repo)
    title_separator = "=" * len(repo_title)
    repo_file_content = REPO_FILE % (repo_name, title_separator, repo_title, title_separator, repo_descr)
    repo_rst_file = "%s/%s.rst" % (repo_oca_dir, repo_name)
    for module_rst in os.listdir(local_doc_path_oca_repo):
        repo_file_content += "   %s/%s\n" % (repo_name, module_rst.replace(".rst", ""))
    with open(repo_rst_file, "w") as output:
        output.write(repo_file_content)


def build_repo_oca_rst(local_doc_path_oca_section, section_title):
    root_dir, section_name = os.path.split(local_doc_path_oca_section)
    title_separator = "=" * len(section_title)
    section_file_content = SECTION_FILE % (title_separator, section_title, title_separator)
    for repo_dir in os.listdir(local_doc_path_oca_section):
        if os.path.isdir("%s/%s" % (local_doc_path_oca_section, repo_dir)):
            section_file_content += "   %s/%s\n" % (section_name, repo_dir)
    with open("%s.rst" % (local_doc_path_oca_section), "w") as output:
        output.write(section_file_content)



with open('%s/config.json' % os.path.dirname(__file__)) as config_file:
    data = json.load(config_file)
local_oca_repo_path = data['local_oca_repo_path']
local_doc_path = data['local_doc_path']
versions = get_all_versions(data)
for version in versions:
    reset_git_repo("%s/%s" % (local_doc_path, version), version)
for oca_section in data['oca_sections']:
    section_title = data['oca_sections'][oca_section]['title']
    for oca_repo in data['oca_sections'][oca_section]['oca_repositories']:
        oca_repo_local_path = "%s/%s" % (local_oca_repo_path, oca_repo)
        if not os.path.isdir(oca_repo_local_path):
            check_output(["git", "clone", "https://github.com/OCA/%s.git" % oca_repo, oca_repo_local_path])
        for version in data['oca_sections'][oca_section]['oca_repositories'][oca_repo]['versions']:
            repo_title = data['oca_sections'][oca_section]['oca_repositories'][oca_repo]['title']
            repo_descr = data['oca_sections'][oca_section]['oca_repositories'][oca_repo]['description']
            reset_git_repo(oca_repo_local_path, version)
            section_oca_dir = "%s/%s" % (local_doc_path, version)
            local_doc_path_oca_section = "%s/%s" % (section_oca_dir, oca_section)
            if not os.path.isdir(local_doc_path_oca_section):
                check_output(["mkdir", local_doc_path_oca_section])
            local_doc_path_oca_repo = "%s/%s" % (local_doc_path_oca_section, oca_repo)
            if not os.path.isdir(local_doc_path_oca_repo):
                check_output(["mkdir", local_doc_path_oca_repo])
            for module_name in os.listdir(oca_repo_local_path):
                module_path = "%s/%s" % (oca_repo_local_path, module_name)
                if os.path.isdir(module_path):
                    readme_path = "%s/README.rst" % module_path
                    if os.path.isfile(readme_path):
                        check_output([
                            "cp", readme_path,
                            "%s/%s.rst" % (local_doc_path_oca_repo, module_name)])
            build_modules_rst(local_doc_path_oca_repo, repo_title, repo_descr)
            build_repo_oca_rst(local_doc_path_oca_section, section_title)

for version in versions:
    push_if_needed("%s/%s" % (local_doc_path, version))
