# SayInky.com

The website for **Inky**, the kids' colouring-page app: home page, help, privacy policy and terms, in English, German and French. Hosted on GitHub Pages.

## Editing

1. Change files in `src/` or `static/`. Don't edit `docs/` directly: it's rebuilt every time.
2. Run `python3 build.py` (no dependencies needed).
3. Look at it locally: `python3 -m http.server 8000 -d docs`, then open http://localhost:8000.
4. Commit both `src/` and `docs/`.

| Path | What |
| --- | --- |
| `src/site.json` | Domain, support email, company details, App Store link and app ID |
| `src/strings.json` | Menu, footer and button wording in each language |
| `src/pages/<lang>/` | One HTML fragment per page: `index`, `support`, `privacy`, `terms` |
| `static/` | Styles, icons and example pages, copied into `docs/` as they are |
| `docs/` | The built site that GitHub Pages serves |

`{{email}}`, `{{company}}` and the other keys in `site.json` can be used in any page. A new page must exist in every language, or the build stops.

When the app is live, put the App Store link in `app_store_url` and the numeric app ID in `apple_app_id` in `src/site.json`. The "Coming soon" label then becomes a download button, and iPhone visitors see Apple's Smart App Banner.

When you change the privacy policy or terms, update the date at the top of the page in all three languages.

## Hosting

GitHub Pages serves the `docs/` folder of the `main` branch (Settings › Pages › Build and deployment › Deploy from a branch › `main` / `docs`). `docs/CNAME` holds the custom domain.

DNS at Hostinger:

| Type | Name | Value |
| --- | --- | --- |
| A | @ | 185.199.108.153 |
| A | @ | 185.199.109.153 |
| A | @ | 185.199.110.153 |
| A | @ | 185.199.111.153 |
| CNAME | www | `<github-username>.github.io` |

Delete Hostinger's default parking A record (and any CDN record) for `@`. Then, in GitHub, verify the domain (account Settings › Pages) and tick **Enforce HTTPS** once the certificate is ready.
