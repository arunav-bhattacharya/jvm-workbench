# Deploy to Cloudflare

The site is a static Cloudflare Worker: `wrangler.jsonc` tells Cloudflare to serve the `web/` folder. There is no server code and no sign-in. `web/` is committed, so Cloudflare needs no build step.

The live site is https://jvm-workbench.ai-arunav.workers.dev.

## How it is connected now

The `jvm-workbench` Worker is connected to this GitHub repo in the Cloudflare dashboard (Workers Builds), with deploy command `npx wrangler deploy` on branch `main`.

Pushes to `main` have not been starting builds on their own. Until that is fixed, start a build by hand after a push:

1. Open https://dash.cloudflare.com and go to **Workers & Pages**, then **jvm-workbench**.
2. Open the **Deployments** tab (or **Settings**, then **Build**) and start a new build of `main`.

To make pushes deploy on their own, check two things:

- In Cloudflare, **jvm-workbench → Settings → Build** shows the GitHub repo connected and automatic builds for the `main` branch turned on.
- In GitHub, **Settings → Applications** (or the repo's **Settings → GitHub Apps**) shows the **Cloudflare Workers and Pages** app with access to `jvm-workbench`.

## Set it up from scratch (if the Worker is ever deleted)

1. Sign in at https://dash.cloudflare.com.
2. Open **Workers & Pages**, click **Create**, then **Import a repository**. Connect GitHub if asked, and give Cloudflare access to `arunav-bhattacharya/jvm-workbench`.
3. Fill in:

   | Setting | Value |
   |---|---|
   | Project name | `jvm-workbench` (must match `"name"` in `wrangler.jsonc`) |
   | Production branch | `main` |
   | Build command | leave empty |
   | Deploy command | `npx wrangler deploy` |
   | Root directory | `/` |
   | API token | any token with Workers edit rights in this account, or **Create new token** |

4. Click **Create and deploy**.

## Deploy from your laptop instead

You need Node.js 18 or newer.

```bash
git clone https://github.com/arunav-bhattacharya/jvm-workbench.git
cd jvm-workbench
npx wrangler login
npx wrangler deploy
```

## Check that it works

1. Open the URL. The home page shows "JVM Workbench", the plate of week dots and "Today".
2. Open a finished lesson from the sidebar. It should load in about a second. Lessons are fetched from `web/lessons/<id>.json`, so if one stays on "Loading", the `web/lessons` folder was not uploaded.
3. Switch the theme and the Java / Kotlin / Both switch, then reload. Both choices stick.

## Progress and devices

Progress is saved in each browser. To move it to another device, open **Plan and progress**, click **Copy my progress**, then paste it on the other device and click **Import pasted progress**. Importing merges, so nothing is lost on either side. A new domain starts with empty storage too, so copy your progress over the same way if you add a custom domain.

## Optional: your own domain

If the domain is on Cloudflare: open the Worker, then **Settings**, **Domains & Routes**, **Add**, **Custom domain**, and enter something like `jvm.yourdomain.com`.

## Updating the site

```bash
python3 site/validate.py --all   # every lesson passes the brief
python3 site/build.py            # rebuilds web/
git add -A && git commit -m "Update lessons" && git push
```

Then start a build in Cloudflare if pushes are not deploying on their own (see above).
