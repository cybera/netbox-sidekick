# Vendored uPlot

`uPlot.iife.min.js` and `uPlot.min.css` are [uPlot](https://github.com/leeoniya/uPlot)
**v1.6.32**, MIT licensed.

They are vendored rather than loaded from `https://leeoniya.github.io/uPlot/dist/`
so that the traffic graphs on the Network Service, Network Service Group and
Interface pages do not depend on a third-party GitHub Pages site being
reachable from a NetBox client.

The graphs themselves only ever render from sidekick's own graph endpoints
(`/plugins/sidekick/...`); uPlot is purely the client-side charting library.

## Updating

```sh
cd sidekick/static/sidekick/uplot
curl -fsSLO https://leeoniya.github.io/uPlot/dist/uPlot.iife.min.js
curl -fsSLO https://leeoniya.github.io/uPlot/dist/uPlot.min.css
```

Then update the version in this file and in
`sidekick/templates/sidekick/template_content/_graph_assets.html`.

Verify the version from the banner comment on the first line of
`uPlot.iife.min.js`.
