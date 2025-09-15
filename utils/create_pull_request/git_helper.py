from git import Repo, Commit
from git.exc import InvalidGitRepositoryError, NoSuchPathError, GitCommandError
from argparse import Namespace
from pathlib import Path
import logging
import os

logger = logging.getLogger(__name__)


class GitHelper:
    """Helper class for managing git operations."""

    def __init__(self, args: Namespace, repo_path: str) -> None:
        try:
            logger.debug(f"Initializing git repository at path: {repo_path}")
            self.repo = Repo(repo_path)

            logger.debug("Available remotes:")
            for remote in self.repo.remotes:
                logger.debug(f" - {remote.name} ({remote.url})")

            logger.debug("Fetching branches for origin...")
            self.repo.remotes.origin.fetch()
            logger.debug(f"Available branches: {self.repo.branches}")

            # Git command interface
            self.git_cmd = self.repo.git
        except (InvalidGitRepositoryError, NoSuchPathError) as e:
            logger.error(e)
            return
        except Exception as e:
            logger.error(f"Unexpected error while initializing git repository: {e}")
            return

        self.reset_files: list[str] = args.reset_files
        self.files_to_remove: list[str] = args.remove_files
        self.my_github_remote: str = args.my_github_remote
        self.pull_request_branch: str = args.pull_request_branch
        self.fork_upstream_main: str = args.fork_upstream_main

        self.github_username = args.github_username
        self.github_content_token = args.github_content_token

        self.github_upstream_username: str = args.github_upstream_username
        self.github_upstream_repo: str = args.github_upstream_repo
        self.remote_short_name: str = f"{self.github_username}/{self.github_upstream_repo}"

    def get_latest_commit(self, branch_name: str) -> str | None:
        """
        Returns the latest commit hash for the specified branch.
        Args:
            branch_name (str): The name of the branch to retrieve the latest commit from.
        Returns:
            str: The hash of the latest commit on the given branch.
            None: If the branch does not exist or an error occurs.
        """
        result = None

        # Checkout the branch which tracks upstream/main
        try:
            logger.info(f"Checking out branch: {branch_name}")
            tracking_branch = self.repo.heads[branch_name]
            tracking_branch.checkout()
        except (IndexError, GitCommandError) as e:
            logger.error(e)
            return None

        commit: Commit = self.repo.commit(branch_name)
        result = commit.hexsha
        logger.info(f"Got latest commit: {result} for branch: {branch_name}")

        return result

    def reset_files_to_commit(self, commit_sha: str) -> bool:
        """
        Resets specified files in the current branch to their state in the given commit SHA,
        stages them, and commits the changes while skipping certain pre-commit hooks.
        Finally, rebases the branch onto the upstream main branch.
        Args:
            commit_sha (str): The SHA of the commit to reset the files to.
        Returns:
            bool: True if the operation was successful, False otherwise.
        Steps:
            1. Checks out the pull request branch.
            2. Resets the specified files to their state in the given commit.
            3. Stages the reset files.
            4. Commits the changes, skipping specific pre-commit checks.
            5. Rebases the branch onto the upstream_main branch.
        Logs errors and returns False if any step fails.
        """

        # Checkout the branch that will be the source in the Pull Request
        try:
            logger.info(f"Checking out branch: {self.pull_request_branch}")
            pull_request_branch = self.repo.heads[self.pull_request_branch]
            pull_request_branch.checkout()
        except (IndexError, GitCommandError) as e:
            logger.error(e)
            return False

        # Reset the file to the latest commit on upstream_main
        try:
            logger.info(f"Resetting files: {self.reset_files} to commit: {commit_sha}")
            self.git_cmd.checkout(commit_sha, "--", self.reset_files)
        except GitCommandError as e:
            logger.error(e)
            return False

        # Add the reseted files the the staging area
        try:
            logger.info("Adding reset files to staging area")
            self.git_cmd.add(self.reset_files)
        except GitCommandError as e:
            logger.error(e)
            return False

        # The repo has pre-commit configured and the upstream files are not compliant ->
        # we need to skip the pre-commit checks for this commit
        os.environ["SKIP"] = "trailing-whitespace, end-of-file-fixer"

        # Allow committing without a pre-commit config file
        # (might have been deleted by a previous execution of the script, which is OK)
        os.environ["PRE_COMMIT_ALLOW_NO_CONFIG"] = "1"

        # Commit the reseted files only if there's something to commit
        # (the files might have been reset by a previous execution of the script, which is OK)
        if self.repo.is_dirty(untracked_files=True):
            try:
                logger.info("Committing reset files")
                self.git_cmd.commit("-m", f"chore: auto reset to {commit_sha}")
            except GitCommandError as e:
                logger.error(e)
                return False
        else:
            logger.info("No changes to commit while resetting files.")

        # Rebase
        try:
            logger.info(f"Rebasing onto: {self.fork_upstream_main}")
            self.git_cmd.rebase(self.fork_upstream_main)
        except GitCommandError as e:
            logger.error(e)
            return False

        logger.info(f"Successfully reset files and rebased onto: {self.fork_upstream_main}")
        return True

    def remove_files(self) -> bool:
        """
        Removes specified files from the pull request branch, commits the changes,
        and rebases the branch onto the upstream_main branch.
        Steps performed:
            1. Checks out the pull request branch.
            2. Removes each file or directory.
            3. Sets the environment variable to allow committing without a pre-commit config file.
            4. Commits the file removals.
            5. Rebases the branch onto upstream_main.
        Returns:
            bool: True if all operations succeed, False if any step fails.
        Logs errors and returns False if any git operation fails.
        """

        logger.info(f"Removing files: {self.files_to_remove} from branch: {self.pull_request_branch}")

        # Checkout the branch that will be the source in the Pull Request
        try:
            logger.info(f"Checking out branch: {self.pull_request_branch}")
            pull_request_branch = self.repo.heads[self.pull_request_branch]
            pull_request_branch.checkout()
        except (IndexError, GitCommandError) as e:
            logger.error(e)
            return False

        for file in self.files_to_remove:
            if file.endswith("/*"):
                dir_path = file[:-2]  # Remove the '/*' to get the directory path
                if not Path(dir_path).is_dir():
                    logger.info(f"Directory: {dir_path} does not exist. Skipping removal.")
                    continue

                try:
                    logger.info(f"Removing all files in directory: {dir_path}")
                    self.git_cmd.rm("-r", dir_path)
                except GitCommandError as e:
                    logger.error(e)
                    return False
                continue

            if not Path(file).exists():
                logger.info(f"File: {file} does not exist. Skipping removal.")
                continue

            try:
                logger.info(f"Removing file: {file}")
                self.git_cmd.rm(file)
            except GitCommandError as e:
                logger.error(e)
                return False

        # Required in case the .pre-commit-config.yaml was deleted
        os.environ["PRE_COMMIT_ALLOW_NO_CONFIG"] = "1"

        # Commit the removed files only if there's something to commit
        # (the files might have been removed by a previous execution of the script, which is OK)
        if self.repo.is_dirty(untracked_files=True):
            try:
                logger.info("Committing removed files")
                self.git_cmd.commit("-m", "chore: auto removed files")
            except GitCommandError as e:
                logger.error(e)
                return False
        else:
            logger.info("No changes to commit while removing files.")

        # Rebase
        try:
            logger.info(f"Rebasing onto: {self.fork_upstream_main}")
            self.git_cmd.rebase(self.fork_upstream_main)
        except GitCommandError as e:
            logger.error(e)
            return False

        logger.info(f"Successfully removed files and rebased onto: {self.fork_upstream_main}")
        return True

    def push_branch_to_remote(self) -> bool:
        # Create a new remote if it doesn't exist
        # (enables pushing the development branch to GitHub)
        if self.my_github_remote not in [remote.name for remote in self.repo.remotes]:
            try:
                remote_url = (f"https://{self.github_username}:{self.github_content_token}"
                              f"@github.com/{self.remote_short_name}.git")
                logger.info(f"Creating new remote: {self.my_github_remote} for user: {self.github_username} "
                            f"to repo: {remote_url.split('@')[1]}")
                created_remote = self.repo.create_remote(self.my_github_remote, url=remote_url)
            except GitCommandError as e:
                logger.error(e)
                return False

            logger.info(f"Successfullly created new remote: {created_remote.name}. "
                        f"All remotes: {[remote.name for remote in self.repo.remotes]}")
        else:
            logger.error(f"The remote: {self.my_github_remote} already exists with URL: "
                         f"{self.repo.remote(name=self.my_github_remote).url}. "
                         f"Will NOT continue to avoid pushing to an undesired remote!")
            return False

        # Check if the branch exists in the local repository
        if self.pull_request_branch not in self.repo.heads:
            logger.error(f"The branch: {self.pull_request_branch} does not exist "
                         f"in the local repository: {self.repo.working_dir}")
            return False

        # Checkout the branch that will be the source in the Pull Request
        try:
            logger.info(f"Checking out branch: {self.pull_request_branch}")
            pull_request_branch = self.repo.heads[self.pull_request_branch]
            pull_request_branch.checkout()
        except (IndexError, GitCommandError) as e:
            logger.error(e)
            return False

        # Push the branch to the remote (use the same name for the branch on the remote)
        try:
            # Handle [rejected] (fetch first)
            logger.info(f"Fetching remote: {created_remote.name} before pushing")
            created_remote.fetch()

            # Handle [rejected] (non-fast-forward)
            # Why: we are doing a couple of commits (reset files, remove files) to achieve a clean Pull Request
            # so we need to rebase on top of the remote branch (same content, different commit history)
            # only if the branch exists in the remote
            if self.branch_exists(self.pull_request_branch, created_remote.name):
                logger.info(f"Rebasing onto: {self.my_github_remote}/{self.pull_request_branch}")
                self.git_cmd.rebase(f"{self.my_github_remote}/{self.pull_request_branch}")

            logger.info(f"Pushing branch: {self.pull_request_branch} to remote: {created_remote.name}")
            push_result = created_remote.push(refspec=f"{self.pull_request_branch}:{self.pull_request_branch}")

            if len(push_result) == 0:
                logger.error("The push operation failed completely")
                return False

            for push_info in push_result:
                if push_info.flags & push_info.ERROR:
                    logger.error(f"Error while pushing branch: {push_info.summary}")
                    return False
                else:
                    logger.debug(f"Push summary: {push_info.summary}")
                    logger.info(f"Successfully pushed branch: {self.pull_request_branch} "
                                f"to remote: {created_remote.name}")
                    return True
        except GitCommandError as e:
            logger.error(e)
            return False
        except Exception as e:
            logger.error(f"Unexpected error occurred while pushing branch: {e}")
            return False
        finally:
            # Clean up by removing the temporary remote
            deleted_remote = self.repo.delete_remote(created_remote)
            logger.info(f"Successfully deleted temporary remote: {deleted_remote}")

        return True

    def branch_exists(self, branch_name: str, remote_name: str) -> bool:
        """
        Checks if the given branch exists in the given remote.
        Args:
            branch_name (str): The name of the branch to check.
            remote (str): The name of the remote to check against.
        """
        try:
            logger.info(f"Checking if branch: {branch_name} exists in remote: {remote_name}")
            remote_refs = self.repo.remote(name=remote_name).refs
            target_branch = f"{remote_name}/{branch_name}"

            return any(ref.name == target_branch for ref in remote_refs)
        except ValueError as e:
            logger.error(e)
            return False
