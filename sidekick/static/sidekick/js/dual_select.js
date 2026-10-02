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
 * Selection state invariant: an option's selected state always matches which
 * box it is in. Anything in the named (selected) box is selected, anything
 * in the available box is not. This is enforced at init, on every move, and
 * on form submit, because a multi-select only posts its *selected* options:
 * relying on DOM state left by clicks (a click on a selected option toggles
 * it off) or browser form restoration would silently drop or remove values
 * on save. Reported and fixed after production use: prefixes moved with
 * Add/double-click were not saved, and unselected options were lost.
 *
 * Double-clicking an option moves it. Idempotent init, so duplicate script
 * tags from multiple widget instances are harmless.
 */
(function () {
    'use strict';

    function syncState(root) {
        Array.prototype.forEach.call(
            root.querySelectorAll('.sk-dual-from option'),
            function (opt) { opt.selected = false; });
        Array.prototype.forEach.call(
            root.querySelectorAll('.sk-dual-to option'),
            function (opt) { opt.selected = true; });
    }

    function move(from, to, selectOnArrival) {
        Array.prototype.slice.call(from.selectedOptions).forEach(function (opt) {
            opt.hidden = false;
            opt.selected = selectOnArrival;
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

            add.addEventListener('click', function () { move(fromSel, toSel, true); });
            remove.addEventListener('click', function () { move(toSel, fromSel, false); });
            fromSel.addEventListener('dblclick', function () { move(fromSel, toSel, true); });
            toSel.addEventListener('dblclick', function () { move(toSel, fromSel, false); });

            if (search) {
                search.addEventListener('input', function () {
                    var q = this.value.toLowerCase();
                    Array.prototype.forEach.call(fromSel.options, function (opt) {
                        opt.hidden = q !== '' && opt.text.toLowerCase().indexOf(q) === -1;
                    });
                });
            }

            syncState(root);
            var form = root.closest('form');
            if (form) {
                form.addEventListener('submit', function () { syncState(root); });
            }
        });
    }

    if (document.readyState !== 'loading') {
        init();
    } else {
        document.addEventListener('DOMContentLoaded', init);
    }
})();
