/**
 * Created by dgosting on 9/6/16.
 */

$(document).ready(function () {

    var non_sortable_columns = [0, 1];

    if(sorted_column == 3) {
        non_sortable_columns = [0, 1, 2];
    }

    var columns_to_export = [];

    for(var k = sorted_column; k < number_of_columns; k++) {
        columns_to_export.push(k)
    }

    var styling_targets = [];

    for (var l = number_of_columns - 1; l > sorted_column + 8; l--) {
        styling_targets.push(l)
    }
    var hidden_cols = document.getElementById('hidden_columns').value.split(',');
    if(hidden_cols[0] == "") {
        hidden_cols = [sorted_column + 4, sorted_column + 5, sorted_column + 6, sorted_column + 7]
    }

    var oTable = $("#data").DataTable({
        paging: true,
        pagingType: "full_numbers",
        data: table_data,
        autoWidth: false,
        pageLength: 10,
        language: ',',
        columns: table_heads,
        columnDefs: [ {
                targets: non_sortable_columns,
                sortable: false
            },{
                targets: hidden_cols,
                visible: false
            }, {
                className: 'exportable', 'targets': columns_to_export
            }, {
                "targets": styling_targets,
                "createdCell": function (td, cellData, rowData, row, col) {
                    if(cellData.includes('class="true"')) {
                        $(td).css('background-color', 'rgba(0, 255, 0, 0.1)')
                    } else {
                        $(td).css('background-color', 'rgba(255, 0, 0, 0.1)')
                    }
                }
            }
        ],
        order: [[sorted_column, 'asc']],
        dom: 'l<<"pull-left"B><"pull-right"f>r>t<<"pull-left"i><"pull-right"p>>',
        buttons: [
            'colvis', {
                extend: 'csv',
                text: 'CSV',
                exportOptions: {
                    columns: columns_to_export
                }
            }
        ],
        deferRender: true,
        scrollX: true
    });

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
});

function column_sort_from_right() {

    var sorting_array = [];

    for (var i = number_of_columns - 1; i > sorted_column + 8; i--) {
        sorting_array.push([i, 'desc'])
    }
    var table = $("#data").DataTable();
    table.order(sorting_array).draw();
}

var deleteRow = function () {
    var row = $(this).closest("tr").get(0);
    $('#data').DataTable().row(row).remove().draw();
};

function filter_dups() {

    var table = $('#data').DataTable();

    if ($('#show_dups').is(":checked")) {
        table.column(sorted_column + 1).search('').draw();
    } else {
        table.column(sorted_column + 1).search("^((?!DUP).)*$", true, false).draw();
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
    } else {
        sign.className = sign.className.replace('minus', 'plus');
    }
}
