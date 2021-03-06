from __future__ import print_function

import os
import subprocess
import sys


def info(*args):
    print(*args, file=sys.stderr)


def turingarena_cli():
    ssh_command = (
        [
            "ssh",
            "-o", "BatchMode=yes",
            "-o", "LogLevel=error",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "StrictHostKeyChecking=no",
            "-p", "20122",
        ]
    )

    working_dir = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"],
        universal_newlines=True,
    ).strip()

    current_dir = os.path.relpath(os.curdir, working_dir)
    info("Sending work dir: {working_dir} (current dir: {current_dir})...".format(
        working_dir=working_dir,
        current_dir=current_dir,
    ))

    git_dir = os.path.join(os.path.expanduser("~"), ".turingarena", "db.git")
    git_env = {
        "GIT_WORK_TREE": working_dir,
        "GIT_DIR": git_dir,
        "GIT_SSH_COMMAND": " ".join("'" + c + "'" for c in ssh_command),
    }

    git_popen_args = dict(env=git_env, universal_newlines=True)

    subprocess.check_call(["git", "init", "--quiet", "--bare", git_dir])
    subprocess.check_call(["git", "add", "-A", "."], **git_popen_args)

    tree_id = subprocess.check_output(["git", "write-tree"], **git_popen_args).strip()

    commit_message = "Turingarena payload."
    commit_id = subprocess.check_output(
        ["git", "commit-tree", tree_id, "-m", commit_message],
        **git_popen_args
    ).strip()

    subprocess.check_call(ssh_command + [
        "turingarena@localhost",
        "git init --bare --quiet db.git",
    ])

    subprocess.check_call([
        "git", "push", "-q",
        "turingarena@localhost:db.git",
        "{commit_id}:refs/heads/sha-{commit_id}".format(commit_id=commit_id),
    ], **git_popen_args)

    # remove the remove branch (we only need the tree object)
    subprocess.check_call([
        "git", "push", "-q",
        "turingarena@localhost:db.git",
        ":refs/heads/sha-{commit_id}".format(commit_id=commit_id),
    ], **git_popen_args)

    info("Work dir sent. Running command...")

    subprocess.call(ssh_command + [
        "-t",
        "turingarena@localhost",
        "TURINGARENA_TREE_ID=" + tree_id,
        "TURINGARENA_CURRENT_DIR=" + current_dir,
        "/usr/local/bin/python", "-m", "turingarena_impl",
    ] + sys.argv[1:])


if __name__ == '__main__':
    turingarena_cli()
