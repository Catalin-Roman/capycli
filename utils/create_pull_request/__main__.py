import logging
import argparse
import os
from . import git_helper as gh
from . import github_helper as ghh


def print_script_arguments(args: argparse.Namespace) -> None:
    """Prints the script arguments, excluding sensitive information like tokens."""
    script_arguments = "Script was called with these arguments (tokens excluded): \n"

    for arg_name, arg_value in vars(args).items():
        if arg_name not in ['github_pull_request_token', 'github_content_token']:
            script_arguments += f"--{arg_name}: {arg_value}\n"

    logger.info(f"{script_arguments}")


def parse_cli_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a Pull Request to the upstream CaPyCLI repository.")
    parser.add_argument('--github-username',
                        required=True,
                        help=("Your username on GitHub"))
    parser.add_argument('--github-pull-request-token',
                        required=True,
                        help=("GitHub token for creating the Pull Request. "
                              "Required Scopes: Pull requests (Read and write)"))
    parser.add_argument('--github-content-token',
                        required=True,
                        help=("GitHub token for accessing the repository content. "
                              "Required Scopes: Contents (Read and write), "
                              "Workflows (Read and write) only if the intermediate Github repo is empty"))
    parser.add_argument('--pull-request-branch',
                        required=False,
                        default='new-si-gsw-feature',
                        help=("The name of the branch to create the Pull Request from. "
                              "Defaults to 'new-si-gsw-feature' if not specified."))
    parser.add_argument('--pull-request-title',
                        required=False,
                        default='Pull Request from SI GSW R&D',
                        help=("The title of the Pull Request. "
                              "Defaults to 'Pull Request from SI GSW R&D' if not specified."))
    parser.add_argument('--pull-request-body',
                        required=False,
                        default='This is a pull request from the SI GSW R&D team.',
                        help=("The body of the Pull Request. "
                              "Defaults to 'This is a pull request from the SI GSW R&D team.' if not specified."))
    parser.add_argument('--my-github-remote',
                        required=False,
                        default='my_github_remote',
                        help=("The name of the GitHub remote to use for pushing changes. "
                              "Defaults to 'my_github_remote' if not specified."))
    parser.add_argument('--github-upstream-username',
                        required=False,
                        default='sw360',
                        help=("The username of the upstream CaPyCLI repository. "
                              "Defaults to 'sw360' if not specified."))
    parser.add_argument('--github-upstream-repo',
                        required=False,
                        default='capycli',
                        help=("The name of the upstream CaPyCLI repository. "
                              "Defaults to 'capycli' if not specified."))
    parser.add_argument('--reset-files',
                        required=False,
                        nargs='*',
                        default=['.gitignore', 'Readme.md', 'pyproject.toml', 'poetry.lock'],
                        help=("Space-separated list of files to be reset to the upstream version. "
                              "Defaults to '.gitignore', 'Readme.md', 'pyproject.toml', 'poetry.lock' "
                              "if not specified."))
    parser.add_argument('--remove-files',
                        required=False,
                        nargs='*',
                        default=['.gitlab-ci.yml', '.gitlab/merge_request_templates/Merge Request.md',
                                 '.pre-commit-config.yaml', 'CHANGELOG_camelot.md',
                                 'Readme_Fork_Maintenance.md', 'release_info'],
                        help=("Comma-separated list of files to remove from the repository. "
                              "Defaults to '.gitlab-ci.yml', '.gitlab/merge_request_templates/Merge Request.md', "
                              "'.pre-commit-config.yaml', 'CHANGELOG_camelot.md', 'Readme_Fork_Maintenance.md', "
                              "'release_info' if not specified."))
    parser.add_argument('--fork-upstream-main',
                        required=False,
                        default='upstream_main',
                        help=("The name of the branch inside our fork which is a 1:1 copy of the upstream main branch. "
                              "Defaults to 'upstream_main' if not specified."))

    return parser.parse_args()


def configure_logging() -> logging.Logger:

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Set the console handler level to INFO
    console_handler.setFormatter(formatter)

    # Ensure the logs directory exists
    os.makedirs('logs', exist_ok=True)
    file_handler = logging.FileHandler('logs/create_pull_request.log', mode='w')
    file_handler.setLevel(logging.DEBUG)  # Set the file handler level to DEBUG
    file_handler.setFormatter(formatter)

    logging.basicConfig(level=logging.DEBUG, handlers=[console_handler, file_handler])

    return logging.getLogger(__name__)


logger = configure_logging()


def main() -> None:
    args = parse_cli_arguments()
    print_script_arguments(args)

    logger.info("Start creating the Pull Request")

    github_helper = ghh.GitHubHelper(args)
    logger.info(f"FROM branch: {github_helper.pull_request_branch} ")
    logger.info(f"USING GitHub user: {github_helper.fork.username} ")
    logger.info(f"TO GitHub repo (upstream): {github_helper.upstream.short_name} ")

    git_helper = gh.GitHelper(args, repo_path=os.getcwd())
    logger.info(f"Local branch tracking upstream/main: {args.fork_upstream_main}")

    # Get the latest commit on the upstream_main branch
    # Will be used to reset the files which should remain as in upstream but were modified by us
    latest_commit = git_helper.get_latest_commit(args.fork_upstream_main)
    if latest_commit is None:
        logger.error(f"Unable to continue: Failed to get the latest commit from the {args.fork_upstream_main} branch")
        return

    if not git_helper.reset_files_to_commit(latest_commit):
        logger.error("Unable to continue: Failed to reset files to commit")
        return

    if not git_helper.remove_files():
        logger.error("Unable to continue: Failed to remove files")
        return

    if not github_helper.check_fork_exists():
        if not github_helper.create_fork():
            logger.error("Unable to continue: The expected fork doesn't exist and unable to create a new one")
            return

    if not git_helper.push_branch_to_remote():
        logger.error("Unable to continue: Failed to push the branch to the GitHub remote")
        return

    if not github_helper.pull_request_exists():
        github_helper.create_pull_request()


if __name__ == '__main__':
    main()
