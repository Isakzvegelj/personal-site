# Safe site workflow

The repository instructions in `AGENTS.md` make this workflow apply to future
Codex sessions working on the personal site as well.

The production site is deployed from `main`. Keep unfinished work off `main`
and verify it locally before promoting it.

## Start a working version

From this directory:

```sh
git switch -c staging
./preview.sh
```

Open <http://localhost:8877/>. The preview includes the home page and blog.
If a preview is already running, `preview.sh` reuses it instead of opening a
second server. To use another port, run `SITE_PREVIEW_PORT=9000 ./preview.sh`.

## Blog drafts

Run `bash blog/start.sh`, choose **Save draft locally (recommended)**, and
preview the result. This writes `blog/posts.js` only; it does not commit or
push anything.

## Promote a confirmed version

After checking the preview on desktop and mobile:

```sh
git diff --check
git add -A
git commit -m "Describe the approved update"
git push -u origin staging
```

If everything is correct, merge the staging branch into production:

```sh
git switch main
git pull --ff-only origin main
git merge --no-ff staging -m "Promote approved site update"
git push origin main
```

Only the final push to `main` updates the live site. The blog tool also keeps
its **Publish live to main** option available for an intentionally immediate
blog release, but local draft mode is the default.
