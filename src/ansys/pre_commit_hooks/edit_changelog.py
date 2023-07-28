"""Use towncrier to determine if fragments are available & merge fragments into changelog."""
import os
import subprocess

import git


def check_branch():
    """Get current branch."""
    git_repo = git.Repo(os.getcwd(), search_parent_directories=True)
    current_branch = str(git_repo.active_branch)

    root_dir = current_branch.split("/")[0]
    print(root_dir)
    # if root_dir != "release":
    #     run_towncrier_hook()
    check_towncrier_fragments()


def check_towncrier_fragments():
    """Determine if there are towncrier fragments in the repository."""
    check = subprocess.run(["towncrier", "check"], stdout=subprocess.PIPE)
    if "news file changes detected" in check.stdout.decode():
        print("News file changes detected")
        towncrier_build()


def towncrier_build():
    """Add fragments to CHANGELOG.md."""
    # removes the news files with git rm and appends the build news to
    # file specified in pyproject.toml (CHANGELOG.md) with git add.
    # The user has to commit this change

    print("run the towncrier command")
    build = subprocess.run(
        ["towncrier", "build", "--keep", "--version=0.1.0"], stdout=subprocess.PIPE
    )
    # add --keep to keep the news fragments in changelog.d
    # Remove --version=<number> once the __version__ variable is set up for automatic versioning
    print(build.stdout.decode())

    # Return 1 since fragments were found and towncrier build was run
    return 1


# When PR is merged, create newsfile on branch
# towncrier create -c <title of PR> <issuenumber>.<tool.towncrier.type>.md
#     refer to pyproject.toml for different tool.towncrier.type sections
# for example: towncrier create -c "Fixed bug issue" 7.fix.md


def main():
    """Update CHANGELOG.md if fragments exist."""
    check_branch()


if __name__ == "__main__":
    main()
