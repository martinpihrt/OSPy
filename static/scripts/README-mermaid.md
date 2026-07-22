# Mermaid browser bundle

OSPy includes `mermaid-10.9.6.min.js` for the read-only flow diagrams in
Diagnostics. The file is served locally so diagrams remain available when the
controller has no Internet connection.

- Upstream: https://github.com/mermaid-js/mermaid
- Package: `mermaid@10.9.6/dist/mermaid.min.js`
- Download source: https://cdn.jsdelivr.net/npm/mermaid@10.9.6/dist/mermaid.min.js
- SHA-256: `EDA3A0AD572BBE69A318C1BE0163E8233DD824F3F12939E5168FEBA207767151`
- License: MIT; see `mermaid-LICENSE.txt`

The renderer uses Mermaid's `strict` security level. Diagram structures are
shipped with OSPy and are not accepted from users or remote services.
