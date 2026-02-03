// Select All / Deselect All for batch review
document.addEventListener("DOMContentLoaded", function () {
    var checkAll = document.getElementById("checkAll");
    var selectAllBtn = document.getElementById("selectAll");
    var deselectAllBtn = document.getElementById("deselectAll");

    function getRowChecks() {
        return document.querySelectorAll(".row-check");
    }

    if (checkAll) {
        checkAll.addEventListener("change", function () {
            getRowChecks().forEach(function (cb) {
                cb.checked = checkAll.checked;
            });
        });
    }

    if (selectAllBtn) {
        selectAllBtn.addEventListener("click", function () {
            getRowChecks().forEach(function (cb) { cb.checked = true; });
            if (checkAll) checkAll.checked = true;
        });
    }

    if (deselectAllBtn) {
        deselectAllBtn.addEventListener("click", function () {
            getRowChecks().forEach(function (cb) { cb.checked = false; });
            if (checkAll) checkAll.checked = false;
        });
    }
});

// Toggle edit mode for admin printer rows
function toggleEdit(index) {
    document.querySelectorAll(".printer-display-" + index).forEach(function (el) {
        el.classList.toggle("d-none");
    });
    document.querySelectorAll(".printer-edit-" + index).forEach(function (el) {
        el.classList.toggle("d-none");
    });
}
