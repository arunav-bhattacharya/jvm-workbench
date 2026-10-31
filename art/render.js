// node art/render.js : renders art/build/plate-*.html to PNG at 1x
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 2400, height: 1500 }, deviceScaleFactor: 1 });
  for (const m of ['dark', 'light']) {
    await p.goto('file://' + path.resolve(__dirname, `build/plate-${m}.html`));
    await p.waitForTimeout(400);
    await p.screenshot({ path: path.resolve(__dirname, `plate-${m}.png`) });
  }
  await b.close();
})();
