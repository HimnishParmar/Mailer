const puppeteer = require('puppeteer');

async function scrapePage(url) {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: 'networkidle0' });

  // Wait for the DOM to be fully loaded
  await page.waitForSelector('body');

  // Extract and embed CSS content
  const cssContent = await page.evaluate(() => {
    return Array.from(document.styleSheets)
      .map(sheet => {
        try {
          return Array.from(sheet.cssRules).map(rule => rule.cssText).join('\n');
        } catch (e) {
          console.log('Error accessing stylesheet:', e);
          return '';
        }
      })
      .join('\n');
  });

  // Extract and embed JS content
  const jsContent = await page.evaluate(() => {
    return Array.from(document.scripts)
      .map(script => script.src ? `// Source: ${script.src}\n${script.innerHTML}` : script.innerHTML)
      .join('\n\n');
  });

  // Get the HTML content and convert relative URLs to absolute
  const htmlContent = await page.evaluate((cssContent, jsContent) => {
    const baseUrl = document.baseURI;
    let html = document.documentElement.outerHTML;
    
    // Convert relative URLs to absolute
    html = html.replace(/(href|src)=["'](?!http:\/\/|https:\/\/|\/\/)([^"']+)["']/gi, (match, attr, url) => {
      return `${attr}="${new URL(url, baseUrl)}"`;
    });

    // Remove existing style and script tags
    html = html.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '');
    html = html.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '');

    // Inject CSS and JS into the HTML
    const headEnd = html.indexOf('</head>');
    html = html.slice(0, headEnd) + 
           `<style>${cssContent}</style>` +
           `<script>${jsContent}</script>` +
           html.slice(headEnd);

    return html;
  }, cssContent, jsContent);

  await browser.close();

  return htmlContent;
}

const url = process.argv[2];

scrapePage(url).then(result => {
  console.log(JSON.stringify(result));
}).catch(error => {
  console.error('Error:', error);
});

module.exports = { scrapePage };
