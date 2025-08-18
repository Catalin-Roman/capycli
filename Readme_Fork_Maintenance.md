# Maintaining this Fork in sync with upstream

[[_TOC_]]

# 1. Required variables
The synchronization of this fork with the upstream prject requires the following variables:

| Name | Details | Default value |
|------|---------|---------------|
| GIT_AUTOMATION_NAME | Used to configure Git user.name | git-automation-name|
| GIT_AUTOMATION_EMAIL | Used to configure Git user.email | git-automation-email |
| GIT_AUTOMATION_TOKEN |  - Used as the token for Git commands (e.g. git push) and Gitlab API (e.g. create Merge Request) <br/> - It's a Personal Access Token, see [Troubleshooting](https://docs.gitlab.com/18.1/user/profile/account/two_factor_authentication_troubleshooting/#error-http-basic-access-denied-if-a-password-was-provided-for-git-authentication-) <br/> - Required scopes: api, read_repository, write_repository| |

# 2. How it works

1. There is a pipeline scheduled once per week
2. The weekly pipeline does the following:
    1. Merge the "upstream/main" into "upstream_main" (goal: keep an exact copy of the upstream main branch)(Note: without tags from upstream - would clober existing tags)
    2. Create a branch named "sync-with-upstream" from the "upstream_main" branch
    3. Rebase "sync-with-upstream" to "origin/fork_main"
    4. Push the "sync-with-upstream" branch to "origin/sync-with-upstream" (regardless of conflicts)(use --force to override if the previous sync was not merged)
    5. Create a Merge Request from "sync-with-upstream" to "fork_main"
    6. If there are conflicts at Step 3 then they should be fixed on "sync-with-upstream"
    7. If the Merge Request looks good, then Merge !

# 3. Links

Link to upstream (on GitHub): [CaPyCLI](https://github.com/sw360/capycli)
