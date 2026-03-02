#!/bin/bash
rm -rf build/web build/web-cache
pygbag .
perl -pi -e 's|https?://[^"]*browserfs\.min\.js|https://cdnjs.cloudflare.com/ajax/libs/BrowserFS/2.0.0/browserfs.min.js|g' build/web/index.html
echo "Build complete. Now run:"
echo "cd build/web && python -m http.server 8000"
