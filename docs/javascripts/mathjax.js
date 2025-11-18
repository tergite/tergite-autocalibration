window.MathJax = {
    loader: { load: ['[tex]/physics', '[tex]/ams'] },
    tex: {
        packages: { '[+]': ['physics', 'ams'] },
        inlineMath: [["\\(", "\\)"]],
        displayMath: [["\\[", "\\]"]],
        processEscapes: true,
        processEnvironments: true,
        tags: 'ams'  // Enable equation numbering and referencing
    },
    options: {
        ignoreHtmlClass: ".*|",
        processHtmlClass: "arithmatex"
    }
};

document$.subscribe(() => {
    MathJax.startup.output.clearCache()
    MathJax.typesetClear()
    MathJax.texReset()
    MathJax.typesetPromise()
})