/**
 * Created by dgosting on 9/6/16.
 */

$(document).ready(function () {

    var non_sortable_columns = Array.from(Array(sorted_column+1).keys())
    var columns_to_export = [];
    for(var k = refseq_column; k < number_of_columns; k++) {
        columns_to_export.push(k)
    }

    var styling_targets = [];

    for (var l = number_of_columns - 1; l > refseq_column + 10; l--) {
        styling_targets.push(l)
    }
    var hidden_cols = document.getElementById('hidden_columns').value.split(',');
    if(hidden_cols[0] == "") {
        hidden_cols = [refseq_column + 5, refseq_column + 6, refseq_column + 7, refseq_column+8, refseq_column+9]
    }

    var oTable = $("#data").DataTable({
        paging: true,
        pagingType: "full_numbers",
        data: table_data,
        autoWidth: false,
        pageLength: 100,
        lengthMenu: [50, 100, 500, 1000],
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
            {
                extend: 'colvis',
                columns: columns_to_export,
                columnText: function ( dt, idx, title ) {
                    return title.split("Toggle Tag:")[0]
                }
            },
            {
                text: 'Show all samples',
                action: function(e, dt, node, config) {
                    var colcount = dt.columns().header().length
                    for (var i = 14; i<colcount; i++){
                        dt.columns(i).visible(true)
                    }
                }
            },
            {
                text: 'Hide all samples',
                action: function(e, dt, node, config) {
                    var colcount = dt.columns().header().length
                    for (var i = 14; i<colcount; i++){
                        dt.columns(i).visible(false)
                    }
                }
            },
            {
                extend: 'csv',
                text: 'CSV',
                exportOptions: {
                    columns: function (idx, data, node) {
                        var isVisible = oTable.column(idx).visible();
                        var exportable = $.inArray(idx, columns_to_export) !== -1;
                        return isVisible && exportable;
                    },
                    format: {
                        header: function ( data, row, column, node ) {
                            if(data.includes('Toggle')) {
                                var div = document.createElement("div");
                                div.innerHTML = data;
                                return div.innerText.split('Toggle')[0];
                            } else {
                                return data;
                            }
                        }
                    }
                }
            }
        ],
        deferRender: true
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

    $('#sidebarbutton').click(function () {
        oTable.draw( 'page' );
    });

    $(document).on ("click", ".buttons-columnVisibility", function (x) {

        var visible_columns = oTable.columns().visible();

        var table = $('#data').DataTable();

        table.rows().every( function ( index ) {
            var row = table.row( index );

            var data = row.data();

            var has_entry = false;
            for(var l = sorted_column + 9; l < visible_columns.length; l++) {
                if(visible_columns[l] == true) {
                    if(data[l] != '<span class="empty"></span>') {
                        has_entry = true;
                    }
                }
            }
            if(has_entry == false) {
                $(row.node()).addClass('hidden')
            } else {
                $(row.node()).removeClass('hidden')
            }
        } );
    });

    if(localStorage && localStorage['dups'] == 'false') {
        $('#show_dups').bootstrapToggle('off');
        oTable.column(sorted_column + 3).search("^((?!DUP).)*$", true, false).draw();
    }
    $('#show_dups').change(function () {
        filter_dups()
    });

    $('#tag_toggle').change(function() {
        var column = oTable.column(sorted_column - 1);
        var visibility = column.visible();
        column.visible( ! column.visible() );

        [].forEach.call(document.querySelectorAll('.tag_dropdown'), function (el) {
            if(visibility) {
                el.style.display = 'none';
            } else {
                el.style.display = '';
            }
        });
    })
});

function column_sort_from_right() {
    var sorting_array = [];
    var table = $("#data").DataTable();
    var visible_columns = table.columns().visible();

    for (var i = sorted_column + 10; i < number_of_columns; i++) {
        if(visible_columns[i] == true) {
            sorting_array.push([i, 'desc'])
        }
    }
    table.order(sorting_array).draw();
}

var deleteRow = function () {
    var row = $(this).closest("tr").get(0);
    $('#data').DataTable().row(row).remove().draw();
};

function filter_dups() {
    var table = $('#data').DataTable();
    if ($('#show_dups').is(":checked")) {
        table.column(sorted_column + 3).search('').draw();
        localStorage['dups'] = true;
    } else {
        table.column(sorted_column + 3).search("^((?!DUP).)*$", true, false).draw();
        localStorage['dups'] = false;
    }
}


function expand_collapse_gene_entry(sign) {
    if(sign.className.includes('plus')) {
        sign.className = sign.className.replace('plus', 'minus');
    } else {
        sign.className = sign.className.replace('minus', 'plus');
    }
}

function add_tag(tag_type, mutation_id, row) {
    var token = '{{csrf_token}}';
    $.ajax(
        {
            type: 'POST',
            headers: { "X-CSRFToken": token },
            url: '/mutations/toggle-mut-tag/',
            data: {
                mut_id: mutation_id,
                tag_name: tag_type,
            },
            success: function (result) {
                var message = result['content'];
                if (message == 'ok') {
                    // swal("", "Tag updated in database", "success");
                    update_tag_column(tag_type, row)
                }
                else {
                    swal("", message, "info")
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                swal("", "Save tag failed", "error");
            }
        }
    )
}

function update_tag_column(tag_type, row) {
    var row_id = $(row).closest('tr')[0]._DT_RowIndex;
    var cell = $('#data').DataTable().cell(row_id, sorted_column-1);
    var span_html = '<span class="fa-stack">' + tag_list[tag_type] + '<font style="font-size:0px">' + tag_type + '</font></span>';
    if(cell.data().includes(tag_type)) {
        cell.data(cell.data().replace(span_html, ''));
    } else {
        cell.data(cell.data() + span_html);
    }
    cell.invalidate().draw();
}


function filter_tag(tag_type, is_show, tag_text) {

    var row_tag_selector = document.getElementById('row_tag_selector');
    row_tag_selector.textContent = tag_text;

    var tag_column = $('#data').DataTable().column(sorted_column - 1);
    if(tag_type == 'clear') {
        tag_column.search('').draw();
    } else {
        if(is_show) {
            tag_column.search(tag_type).draw();
        } else {
            var regex = '^((?!' + tag_type + ').)*$';
            tag_column.search(regex, true, false).draw();
        }

    }
}

function add_tag_to_replicate(tag_type, replicate_id, header) {
    var token = '{{csrf_token}}';
    $.ajax(
        {
            type: 'POST',
            headers: { "X-CSRFToken": token },
            url: '/mutations/toggle-rep-tag/',
            data: {
                rep_id: replicate_id,
                tag_name: tag_type,
            },
            success: function (result) {
                var message = result['content'];
                if (message == 'ok') {
                    var cell = $(header).closest('th')[0];
                    $('#data').DataTable().columns().every(function () {
                        if(this.header() == cell) {
                            var header_cell = $(this.header());
                            $(header_cell.children()[header_cell.children().length-1]).children().each(function (idx, obj) {
                                if(obj.innerText.includes(tag_type)) {
                                    if(obj.style.display == 'none') {
                                        obj.style.display = ''
                                    } else {
                                        obj.style.display = 'none'
                                    }
                                }
                            });
                        }
                    });
                }
                else {
                    swal("", message, "info")
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                swal("", "Save tag failed", "error");
            }
        }
    )
}

function save_to_global_filter(mutation_id) {
    var token = '{{csrf_token}}';
    $.ajax(
        {
            type: 'POST',
            headers: { "X-CSRFToken": token },
            url: "/mutations/add_to_global_filter",
            data: { mut_id: mutation_id,
                    save_method: "global"
        },
        success: function (result) {
            var message = result['content'];
            if (message == 'ok') {
                swal("", 'Added mutation to global filter', "success");
            }
            else {
                swal("", message, "info")
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            swal("", "Save-tag failed", "error");
        }
    })
}

function save_to_experiment_filter(ale_experiment_id, mutation_id) {
    var token = '{{csrf_token}}';
    $.ajax(
        {
            type: 'POST',
            headers: { "X-CSRFToken": token },
            url: "/mutations/add_to_exp_filter",
            data: {
                mut_id: mutation_id,
                experiment_id: ale_experiment_id,
                save_method: "experiment"
            },
            error: function (xhr, ajaxOptions, thrownError) {
                swal("", "Save-tag failed", "error");
            }
    })
}


