# Vendor Submodule Commands

Run these from the SMCC git repository root:

```bash
git submodule add https://github.com/gitroomhq/postiz-app vendor/postiz-app
git submodule add https://github.com/ClimenteA/social-media-posts-scheduler vendor/django-social-scheduler
git submodule add https://github.com/Masterjx9/socialmediascheduler vendor/socialmediascheduler
git submodule add https://github.com/ayrshare/social-media-api vendor/ayrshare-js
git submodule add https://github.com/ayrshare/social-post-api-python vendor/ayrshare-python
git submodule update --init --recursive
git submodule foreach --recursive git pull origin main
```

If a target path already exists locally, do not overwrite it. Keep the folder and run only the remaining missing `git submodule add` commands.
