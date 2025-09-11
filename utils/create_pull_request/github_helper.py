from argparse import Namespace
from typing import Any
import requests
import logging

logger = logging.getLogger(__name__)


class GitHubRepo:
    """Class representing a GitHub repository."""

    def __init__(self, username: str, repo_name: str, default_branch: str = "main") -> None:
        self.username = username
        self.repo_name = repo_name
        self.default_branch = default_branch

        self.short_name = f"{self.username}/{self.repo_name}"
        self.url_for_api = f"https://api.github.com/repos/{self.short_name}"


class GitHubHelper:
    """Helper class for managing GitHub API interactions."""

    def __init__(self, args: Namespace) -> None:
        self.github_content_token = args.github_content_token
        self.github_pull_request_token = args.github_pull_request_token

        self.pull_request_branch = args.pull_request_branch
        self.pull_request_title = args.pull_request_title
        self.pull_request_body = args.pull_request_body

        self.fork = GitHubRepo(args.github_username, args.github_upstream_repo)
        self.upstream = GitHubRepo(args.github_upstream_username, args.github_upstream_repo)

        self.content_headers = {
            "Authorization": f"Bearer {self.github_content_token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        self.pull_request_headers = {
            "Authorization": f"Bearer {self.github_pull_request_token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def check_fork_exists(self) -> bool:
        """
        Checks if the specified GitHub repository exists and is a fork of the expected upstream repository.
        Returns:
            bool: True if the repository exists and is a fork of the expected upstream repository, False otherwise.
        """

        logger.info(f"Checking if GitHub repo: {self.fork.url_for_api} exists and "
                    f"is a fork of: {self.upstream.short_name}")
        response = requests.get(self.fork.url_for_api, headers=self.content_headers)

        if response.ok:
            try:
                response_json = response.json()
            except requests.JSONDecodeError as e:
                logger.error(e)
                return False

            if response_json.get("fork"):
                fork_parent = response_json.get("parent", {}).get("full_name")
                if fork_parent == self.upstream.short_name:
                    logger.info(f"The {self.fork.short_name} repository "
                                f"is a fork of: {fork_parent}")
                    return True
                else:
                    logger.warning(f"The {self.fork.short_name} repository "
                                   f"is a fork of: {fork_parent}, "
                                   f"but not of the expected parent: {self.upstream.short_name}")
                    return False
            else:
                logger.warning(f"The {self.fork.short_name} repository is not a fork.")
                return False
        else:
            logger.error(f"The request to check for fork existence failed with status code: {response.status_code}")
            return False

    def create_fork(self) -> bool:
        """
        Creates a fork of the upstream GitHub repository for the authenticated user.
        The fork will be created under the authenticated user's account with the specified repository name.
        Only the default branch will be forked.
        Returns:
            bool: True if the fork was created successfully, False otherwise.
        """

        url = f"{self.upstream.url_for_api}/forks"

        data = {
            "name": f"{self.upstream.repo_name}",
            "default_branch_only": True
        }

        logger.info(f"Creating fork FROM: {self.upstream.short_name} "
                    f"TO {self.fork.short_name}")
        response = requests.post(url, headers=self.content_headers, json=data)

        if response.ok:
            logger.info(f"Successfully created fork: {self.fork.short_name}")
            return True
        else:
            logger.error(f"Unable to create the fork. Response status code: {response.status_code}")
            return False

    def create_pull_request(self) -> None:
        """
        Creates a draft pull request on GitHub for the specified repository, targeting the 'main' branch of the
        upstream repository.
        """

        # Define the upstream URL
        url = f"{self.upstream.url_for_api}/pulls"

        data = {
            "title": self.pull_request_title,
            "head": f"{self.fork.username}:{self.pull_request_branch}",
            "base": f"{self.upstream.default_branch}",
            "body": self.pull_request_body,
            "draft": True
        }

        logger.info(f"Creating Pull Request to: {url}")
        logger.debug(f"Pull Request data: {data}")
        response = requests.post(url, headers=self.pull_request_headers, json=data)
        if response.ok:
            response_json = response.json()
            logger.info(f"Successfully created Pull Request: {response_json.get('html_url')}")
        else:
            logger.error(f"Unable to create Pull Request. Response status code: {response.status_code}")

    def get_existing_pull_requests(self) -> list[dict[str, Any]]:
        """
        Retrieves a list of existing pull requests in the upstream repository.
        Returns:
            list[dict]: A list of pull request objects.
        """
        url = f"{self.upstream.url_for_api}/pulls"
        logger.info(f"Fetching existing Pull Requests from: {url}")
        response = requests.get(url, headers=self.pull_request_headers)

        if response.ok:
            response_json = response.json()
            logger.info("Successfully fetched existing Pull Requests.")
            return response_json
        else:
            logger.error(f"Unable to fetch Pull Requests. Response status code: {response.status_code}")
            return []

    def pull_request_exists(self) -> bool:
        """
        Checks if an open pull request exists from the current user's pull request branch
        to the 'main' branch of the upstream repository.
        Returns:
            bool: True if an open pull request exists, False otherwise.
        """

        for pr in self.get_existing_pull_requests():
            if (pr.get("state") == "open" and
                    pr.get("head", {}).get("ref") == self.pull_request_branch and
                    pr.get("base", {}).get("ref") == "main"):

                logger.info(f"An OPEN Pull Request from: {self.fork.username}/{self.pull_request_branch} "
                            f"to the '{self.upstream.default_branch}' branch "
                            f"of the upstream repo: {self.upstream.short_name} already exists: "
                            f"{pr.get('html_url')}")
                return True

        logger.info(f"No existing OPEN Pull Request from: {self.fork.username}/{self.pull_request_branch} "
                    f"to the '{self.upstream.default_branch}' branch "
                    f"of the upstream repo: {self.upstream.short_name} found.")
        return False
