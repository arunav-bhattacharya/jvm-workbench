# Deploy to Cloudflare

The site runs as a Cloudflare Worker (`worker/index.js`) in front of the `web/` folder. Every page needs a Google sign-in, and only the Gmail addresses in `ALLOWED_EMAILS` (in `wrangler.jsonc`) get in. Progress syncs to Cloudflare KV under each learner's Google account, so phone and laptop match. `web/` is committed, so Cloudflare needs no build step.

## Before the first deploy: sign-in setup (once)

The Worker reuses the Google sign-in client and the KV namespace of AI Engineer from Zero, so there is nothing new to create. Two settings outside this repo need one change each:

1. **Allow this site in Google sign-in.** Open https://console.cloud.google.com, pick the project that holds the AI Engineer from Zero sign-in, then **APIs & Services**, **Credentials**, and open the OAuth client whose ID starts with `213282967449-`. Under **Authorized JavaScript origins**, add `https://jvm-workbench.ai-arunav.workers.dev` (and any custom domain you add later). Save. Google can take a few minutes to a few hours to apply it.
2. **Enroll learners.** Put every allowed Gmail address in `ALLOWED_EMAILS` in `wrangler.jsonc`, comma-separated, then push. If the Google consent screen (**APIs & Services**, **OAuth consent screen**, or **Audience**) is in Testing mode, also add the same addresses as **Test users** there, or Google won't let them sign in.

To remove someone, take their address out of `ALLOWED_EMAILS` and push. They are signed out on their next request.

KV keys for this course all start with `jvmwb:`, so they never mix with the other course's data. To give this course its own namespace instead, run `npx wrangler kv namespace create jvm-workbench`, put the printed ID in `kv_namespaces` in `wrangler.jsonc`, and push.

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

6. **API token**: the existing AI Engineer from Zero token works, since it belongs to the same account and already covers Workers and KV. Or pick **Create new token** to give this project its own.
7. Click **Create and deploy** (the button may say **Save and Deploy**). The first deploy takes a minute or two.
8. When it finishes, Cloudflare shows the URL. With your account it should be `https://jvm-workbench.ai-arunav.workers.dev`.

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

1. Open the URL. You land on the sign-in page. Sign in with an enrolled Gmail address.
2. The home page shows the cover plate, "Today", and your Google picture at the top right. The sidebar says "Progress syncs to this account."
3. Sign in with a Gmail address that is not enrolled (or ask someone to). It should say the account is not enrolled.
4. Open any finished lesson from the sidebar. It should load in about a second. Lessons are fetched from `web/lessons/<id>.json`, so if a lesson stays on "Loading", the `web/lessons` folder was not uploaded.
5. Mark a lesson done, then open the site on your phone and sign in. The lesson shows as done there too.

If the Google button never appears and the page says sign-in did not load, the site's address is not yet in the OAuth client's authorized JavaScript origins (step 1 above), or Google has not applied it yet.

## Optional: your own domain

If the domain is on Cloudflare: open the Worker, then **Settings**, **Domains & Routes**, **Add**, **Custom domain**, and enter something like `jvm.yourdomain.com`. Cloudflare creates the DNS record and the certificate.

Add the custom domain to the Google OAuth client's authorized JavaScript origins too. Progress is stored per Google account, so it follows you to the new domain.

## Updating the site

```bash
python3 site/validate.py --all   # every lesson passes the brief
python3 site/build.py            # rebuilds web/
git add -A && git commit -m "Update lessons" && git push
```

With Option 1 or 3, the push is the deploy.
