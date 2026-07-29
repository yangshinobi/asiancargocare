import { readFileSync } from 'fs';
import { join } from 'path';
import { lookup } from 'mime-types';

const STATIC_DIR = './.vercel/output/static';

export default function handler(req, res) {
  let path = req.url.split('?')[0];
  if (path === '/' || path === '') path = '/index.html';

  // Strip leading slash, resolve file
  const filename = path.startsWith('/') ? path.slice(1) : path;
  let filepath = join(STATIC_DIR, filename);

  try {
    const content = readFileSync(filepath);
    const mime = lookup(filename) || 'application/octet-stream';
    res.setHeader('Content-Type', mime);
    res.status(200).send(content);
  } catch (e) {
    try {
      const fallback = readFileSync(join(STATIC_DIR, 'index.html'));
      res.setHeader('Content-Type', 'text/html');
      res.status(200).send(fallback);
    } catch (e2) {
      res.status(404).send('Not Found');
    }
  }
}
