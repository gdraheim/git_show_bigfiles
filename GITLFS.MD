https://confluence.atlassian.com/bbkb/how-to-check-your-repository-s-size-and-identify-large-files-1178867192.html
https://www.inovex.de/de/blog/migrate-binary-bloat-git-repository/
https://github.com/git-lfs/git-lfs/wiki/Tutorial#migrating-existing-repository-data-to-lfs
https://chrisshort.net/permanently-remove-any-record-of-a-file-from-git/

https://stackoverflow.com/questions/38856833/svn-to-git-migration-with-git-lfs
https://support.atlassian.com/bitbucket-cloud/docs/use-bfg-to-migrate-a-repo-to-git-lfs/

https://stackoverflow.com/questions/6119956/how-to-determine-if-git-handles-a-file-as-binary-or-as-text

https://gist.github.com/mhl/498447
https://www.enricozini.org/blog/2019/debian/gitpython-list-all-files-in-a-git-commit/
https://dev.to/serhatteker/list-files-tracked-by-git-5gcb

https://www.codethink.co.uk/articles/2023/gitlfsfastimport/

# git binary detection

There is a file ".gitattributes" that says which files should be automatically tracked by LFS.
And there is a warning "ncountered n files that should have been pointers, but weren’t" based on it. (https://docs.gitlab.com/ee/topics/git/lfs/troubleshooting.html)

https://github.com/git-lfs/git-lfs/issues/5071
open issue to "Auto-Detection of Binary Files #5071"

https://rehansaeed.com/gitattributes-best-practices/

https://stackoverflow.com/questions/37576604/find-and-remove-too-large-of-files-to-push-in-git-lfs
https://stackoverflow.com/questions/75227161/is-there-a-good-way-to-determine-if-a-file-is-stored-using-git-lfs

# bfg
https://rtyley.github.io/bfg-repo-cleaner/
https://www.theguardian.com/info/developer-blog/2013/apr/29/rewrite-git-history-with-the-bfg
https://stackoverflow.com/questions/58898712/how-can-i-remove-all-files-larger-than-some-given-size-from-all-my-unpushed-git?noredirect=1&lq=1
https://stackoverflow.com/questions/20989885/removing-file-from-commit-due-to-file-size-on-the-github?rq=3

# warning support
https://stackoverflow.com/questions/25765447/how-can-i-automatically-detect-that-a-file-of-a-given-type-has-changed-in-git
https://stackoverflow.com/questions/54451856/how-can-i-tell-if-a-file-will-be-uploaded-to-git-lfs-correctly
https://stackoverflow.com/questions/53690327/prevent-large-text-file-from-being-added-to-commit-when-using-github
https://stackoverflow.com/questions/39576257/how-to-limit-file-size-on-commit/39578014#39578014
https://stackoverflow.com/questions/7147699/limiting-file-size-in-git-repository
https://stackoverflow.com/questions/32953238/how-can-i-ignore-big-files-and-push-to-git-repo?noredirect=1&lq=1
https://stackoverflow.com/questions/858278/rejecting-large-files-in-git?noredirect=1&lq=1
https://stackoverflow.com/questions/53690327/prevent-large-text-file-from-being-added-to-commit-when-using-github?noredirect=1&lq=1

# git lfs locking support
https://stackoverflow.com/questions/42597408/git-lfs-what-is-locking-support-and-should-i-enable-it
https://medal.ctb.upm.es/internal/gitlab/help/administration/lfs/manage_large_binaries_with_git_lfs.md



