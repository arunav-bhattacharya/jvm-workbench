# Deploy to Cloudflare

The site is a static Cloudflare Worker: `wrangler.jsonc` points Cloudflare at the `web/` folder, and there is no server code. `web/` is committed, so Cloudflare needs no build step.

Pick one of the three ways below. The first is the easiest, and after it every push to `main` deploys on its own.

## Option 1: connect the GitHub repo in the dashboard (recommended)

1. Sign in at https://dash.cloudflare.com.
2. In the left menu, open **Workers & Pages** (under Compute), then click **Create**.
3. Choose **Import a repository**. If asked, connect your GitHub account and give Cloudflare access to `arunav-bhattacharya/jvm-workbench`.
4. Select the `jvm-workbench` repository.
5. Fill in the settings:

   | Setting | Value |
   |---|---|
   | Project name | `jvm-workbench` (must match `"name"` in `wrangler.jsonc`) |
   | Production branch | `main` |
   | Build command | leave empty |
   | Deploy command | `npx wrangler deploy` |
   | Root directory | `/` |

6. Click **Create and deploy** (the button may say **Save and Deploy**). The first deploy takes a minute or two.
7. When it finishes, Cloudflare shows the URL. With your account it should be `https://jvm-workbench.ai-arunav.workers.dev`.

From now on, every push to `main` deploys a new version. You can watch each build under the Worker's **Deployments** tab.

## Option 2: deploy once from your laptop

You need Node.js 18 or newer.

```bash
git clone https://github.com/arunav-bhattacharya/jvm-workbench.git
cd jvm-workbench
npx wrangler login      # opens the browser to sign in to Cloudflare
npx wrangler deploy     # uploads web/ and prints the URL
```

Run `npx wrangler deploy` again whenever you want to publish changes.

## Option 3: deploy from GitHub Actions

The `ci` workflow already has a deploy job. It runs after the content and lab checks pass on `main`, and it skips itself until the secrets below exist.

1. Create an API token: in the Cloudflare dashboard, open **My Profile**, then **API Tokens**, then **Create Token**, and use the **Edit Cloudflare Workers** template. Copy the token.
2. Find your account ID: open **Workers & Pages**; the account ID is shown on the right side of the overview page. Copy it.
3. In GitHub, open the repo, then **Settings**, **Secrets and variables**, **Actions**, and add two repository secrets:
   - `CLOUDFLARE_API_TOKEN`: the token from step 1
   - `CLOUDFLARE_ACCOUNT_ID`: the ID from step 2
4. Push to `main` (or re-run the latest `ci` workflow). The deploy job publishes the site.

Use Option 1 or Option 3, not both, or each push deploys twice.

## Check that it works

1. Open the URL. The home page shows the cover plate and "Today".
2. Open any finished lesson from the sidebar. It should load in about a second. Lessons are fetched from `web/lessons/<id>.json`, so if a lesson stays on "Loading", the `web/lessons` folder was not uploaded.
3. Switch the theme and the Java / Kotlin / Both switch, then reload. Both choices should stick.

## Optional: your own domain

If the domain is on Cloudflare: open the Worker, then **Settings**, **Domains & Routes**, **Add**, **Custom domain**, and enter something like `jvm.yourdomain.com`. Cloudflare creates the DNS record and the certificate.

Progress lives in each browser's local storage, and every domain has its own storage. If you move from the `workers.dev` URL to a custom domain, copy your progress first (Plan and progress, then Copy my progress) and import it on the new domain.

## Updating the site

```bash
python3 site/validate.py --all   # every lesson passes the brief
python3 site/build.py            # rebuilds web/
git add -A && git commit -m "Update lessons" && git push
```

With Option 1 or 3, the push is the deploy.
