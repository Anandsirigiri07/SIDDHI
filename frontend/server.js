const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.X_ZOHO_CATALYST_LISTEN_PORT || 9000;
const DIST_DIR = path.join(__dirname, 'dist');

const MIME_TYPES = {
  '.html': 'text/html',
  '.css': 'text/css',
  '.js': 'text/javascript',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon'
};

const server = http.createServer((req, res) => {
  // Normalize path and remove query params
  const parsedUrl = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  let pathname = parsedUrl.pathname;
  
  let filePath = path.join(DIST_DIR, pathname === '/' ? 'index.html' : pathname);
  
  // Safe directory traversal check
  const relative = path.relative(DIST_DIR, filePath);
  const isSafe = relative && !relative.startsWith('..') && !path.isAbsolute(relative);
  
  if (!isSafe && pathname !== '/') {
    res.writeHead(403);
    res.end('Forbidden');
    return;
  }

  // Fallback to index.html for Single Page Application (SPA) routing
  if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
    filePath = path.join(DIST_DIR, 'index.html');
  }

  const ext = path.extname(filePath).toLowerCase();
  const contentType = MIME_TYPES[ext] || 'application/octet-stream';

  fs.readFile(filePath, (err, content) => {
    if (err) {
      res.writeHead(500);
      res.end('Internal Server Error');
    } else {
      res.writeHead(200, { 
        'Content-Type': contentType,
        'Cache-Control': ext === '.html' ? 'no-cache, no-store, must-revalidate' : 'public, max-age=31536000'
      });
      res.end(content, 'utf-8');
    }
  });
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`Frontend server running on port ${PORT}`);
});
