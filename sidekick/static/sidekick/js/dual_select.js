/*
 * Two-box prefix selector for sidekick (replacement for the Django admin's
 * FilteredSelectMultiple, whose machinery left with the admin in NetBox 4).
 *
 * Markup produced by sidekick/widgets/dual_select.html:
 *   .sk-dual
 *     .sk-dual-search   filter input over the available list
 *     .sk-dual-from     multi-select of unselected options (no name -- posts nothing)
 *     .sk-dual-add      move selected options from -> to
 *     .sk-dual-remove   move selected options to -> from
 *     .sk-dual-to       multi-select named field holding the selected options
 *
 * The real <select> stays named, so a save without any JS still posts the
 * selected values. Double-clicking an option moves it. Idempotent init, so
 * duplicate script tags from multiple widget instances are harmless.
 */
(function () {
    'use strict';

    function move(from, to) {
        Array.prototype.slice.call(from.selectedOptions).forEach(function (opt) {
            opt.selected = false;
            opt.hidden = false;
            to.appendChild(opt);
        });
    }

    function init() {
        var roots = document.querySelectorAll('.sk-dual:not([data-ready])');
        Array.prototype.forEach.call(roots, function (root) {
            var fromSel = root.querySelector('.sk-dual-from');
            var toSel = root.querySelector('.sk-dual-to');
            var search = root.querySelector('.sk-dual-search');
            var add = root.querySelector('.sk-dual-add');
            var remove = root.querySelector('.sk-dual-remove');
            if (!fromSel || !toSel || !add || !remove) {
                return;
            }
            root.dataset.ready = '1';

            add.addEventListener('click', function () { move(fromSel, toSel); });
            remove.addEventListener('click', function () { move(toSel, fromSel); });
            fromSel.addEventListener('dblclick', function () { move(fromSel, toSel); });
            toSel.addEventListener('dblclick', function () { move(toSel, fromSel); });

            if (search) {
                search.addEventListener('input', function () {
                    var q = this.value.toLowerCase();
                    Array.prototype.forEach.call(fromSel.options, function (opt) {
                        opt.hidden = q !== '' && opt.text.toLowerCase().indexOf(q) === -1;
                    });
                });
            }
        });
    }

    if (document.readyState !== 'loading') {
        init();
    } else {
        document.addEventListener('DOMContentLoaded', init);
    }
})();
