# Maintaining this Fork in sync with upstream

[[_TOC_]]

# 1. Required variables
The synchronization of this fork with the upstream prject requires the following variables:

| Name | Details | Default value |
|------|---------|---------------|
| GIT_AUTOMATION_NAME | Used to configure Git user.name | git-automation-name|
| GIT_AUTOMATION_EMAIL | Used to configure Git user.email | git-automation-email |
| GIT_AUTOMATION_TOKEN |  - Used as the token for Git commands (e.g. git push) and Gitlab API (e.g. create Merge Request) <br/> - It's a Personal Access Token, see [Troubleshooting](https://docs.gitlab.com/18.1/user/profile/account/two_factor_authentication_troubleshooting/#error-http-basic-access-denied-if-a-password-was-provided-for-git-authentication-) <br/> - Required scopes: api, read_repository, write_repository| |

# 2. Relevant branches

The following branches are relevant:

| Name | Details |
|------|---------|
| fork_main | The default branch of the fork repo (this repo) |
| upstream_main | Contains only the upstream code (no upstream tags, no changes done by us) |
| pull-from-upstream | Created from upstream_main and rebased on fork_main; used as source for the Merge Request (and for fixing conflicts) |

# 3. How it works

1. There is a pipeline scheduled once per week
2. The weekly pipeline does the following:
    1. Merge the "upstream/main" into "upstream_main" (goal: keep an exact copy of the upstream main branch)(Note: without tags from upstream - would clober existing tags)
    2. Create a branch named "pull-from-upstream" from the "upstream_main" branch
    3. Rebase "pull-from-upstream" to "origin/fork_main"
    4. Push the "pull-from-upstream" branch to "origin/pull-from-upstream" (regardless of conflicts)(use --force to override if the previous sync was not merged)
    5. Create a Merge Request from "pull-from-upstream" to "fork_main"
    6. If there are conflicts at Step 3 then they should be fixed on the "pull-from-upstream" branch
    7. If the Merge Request looks good, then Merge !

# 3. Links

Link to upstream (on GitHub): [CaPyCLI](https://github.com/sw360/capycli)
