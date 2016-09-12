/**
 * Created by dgosting on 9/6/16.
 */
var number_of_columns = null;

$(document).ready(function () {


    var non_sortable_columns = [0, 1];

    if(sorted_column == 3) {
        non_sortable_columns = [0, 1, 2];
    }

    number_of_columns = document.getElementById('data').rows[0].cells.length - 1;

    var oTable = $("#data").dataTable({
        "bPaginate": true,
        "bAutoWidth": false,
        "iDisplayLength": 15,
        "sPaginationType": "full_numbers",
        "aoColumnDefs": [ {
            "aTargets": non_sortable_columns,
            "bSortable": false
            } ]
    }).fnSort([[sorted_column, 'asc']]);
    $("tr td:first-child").each(function () {
        $(this).hover(
                function () {
                    $(this).children(".shut").css("display", "block");
                },
                function () {
                    $(this).children(".shut").css("display", "none");
                }
        );
    });
    var filter_offset = $("#data_filter").offset();
    $(window).resize(function () {
        filter_offset = $("#data_filter").offset();
    });
    var ui_offset = [];
    $(".ui").each(function () {
        ui_offset.push($(this).offset().left);
    });
    $(window).scroll(function () {
        var scrollLeft = $(window).scrollLeft();
        $("#data_filter").offset({left: filter_offset.left + scrollLeft});
        i = 0;
        var sidebar_offset = 0;
        if (sidebar_hidden == true) {
            sidebar_offset = 240;
        }
        $(".ui").each(function () {
            $(this).offset({left: ui_offset[i++] + scrollLeft - sidebar_offset});
        });
    });
    var hidden_cols = document.getElementById('hidden_columns').value.split(',');
    if(hidden_cols[0] == "") {
        hidden_cols = [sorted_column + 4, sorted_column + 5, sorted_column + 6, sorted_column + 7]
    }
    for (var i = 0, len = hidden_cols.length; i < len; i++) {
        if(hidden_cols[i] == "") {
            continue
        }
        fnShowHide(parseInt(hidden_cols[i]))
    }
});

function column_sort_from_right() {
    var sorting_array = [];

    for (var i = number_of_columns; i > sorted_column + 8; i--) {
        sorting_array.push([i, 'desc'])
    }

    var table = $("#data").dataTable();
    table.fnSort(sorting_array)
}

function fnShowHide( iCol ) {
    var oTable = $('#data').dataTable();

    var bVis = oTable.fnSettings().aoColumns[iCol].bVisible;
    if(bVis == true) {
        oTable.fnSetColumnVis( iCol, false );
        if(!document.getElementById('hidden_columns').value.includes(iCol)) {
            document.getElementById('hidden_columns').value = document.getElementById('hidden_columns').value + "," + iCol;
        }
    } else {
        oTable.fnSetColumnVis( iCol, true );
        if(document.getElementById('hidden_columns').value.includes(iCol)) {
            document.getElementById('hidden_columns').value = document.getElementById('hidden_columns').value.replace(iCol, "");
        }
    }
}

var deleteRow = function () {
    var row = $(this).closest("tr").get(0);
    $('.dataTable').dataTable().fnDeleteRow(row);
};

var filterSample = function (filter_type) {
    var url = location.href.split("&remove=")[0].split("&show=")[0];
    checked_samples = [];
    $("tr td").children(".cb").each(function () {
        if (this.checked) {
            checked_samples.push(this.name);
        }
    });
    var removed_sample_ids, kept_sample_ids;
    location.href.split("&").forEach(function (s) {
        if (s.indexOf("remove") >= 0) {
            removed_sample_ids = s.split("=")[1];
        }
        else if (s.indexOf("show") >= 0) {
            kept_sample_ids = s.split("=")[1];
        }
    });
    if (filter_type == "remove") {
        query_string = typeof kept_sample_ids != "undefined" ? "&show=" + kept_sample_ids : "";
        query_string += typeof removed_sample_ids != "undefined" ? "&remove=" + removed_sample_ids.replace("}", "") : "&remove={";
    }
    else if (filter_type == "show") {
        query_string = "&show={";
    }
    checked_samples.forEach(function (id) {
        query_string += id + ",";
    });
    query_string += "}";
    window.location.replace(url + query_string);
}

function filter_dups() {
    if ($('#show_dups').is(":checked")) {
        $('.dataTable').dataTable().fnFilter('');
    } else {
        $('.dataTable').dataTable().fnFilter("^(.(?!DUP))*$", null, true, false);
    }
}

function save_to_global_filter(mutation_id) {
    $.ajax({
        type: "POST",
        url: "",
        data: { mut_id: mutation_id,
                save_method: "global"
        }
    })
}

function save_to_experiment_filter(ale_experiment_id, mutation_id) {
    $.ajax({
        type: "POST",
        url: "",
        data: { mut_id: mutation_id,
                save_method: "experiment"
        }
    })
}

function expand_collapse_gene_entry(sign) {

    if(sign.className.includes('plus')) {
        sign.className = sign.className.replace('plus', 'minus');
        $($($(sign).parent()).children()[1]).hide();
    } else {
        sign.className = sign.className.replace('minus', 'plus');
        $($($(sign).parent()).children()[1]).show()
    }
}