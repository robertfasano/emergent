import git
repo = git.Repo('../')
for remote in repo.remotes:
    remote.fetch()
    
upstream_commits = list(repo.iter_commits('dev..dev@{u}'))