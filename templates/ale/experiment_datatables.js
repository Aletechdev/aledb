    var export_url = "/export?";
    if (project_id !=null) {
        export_url += "project_id=" + project_id + "&";
    }
    $(document).ready(function () {
        var table = $('#exp_table').DataTable({
            scrollY: 600,
            paging: false,
            dom: 'l<<"pull-left"B><"pull-right"f>r>t<<"pull-left"i><"pull-right"p>>',
            buttons: [
                {
                    text: 'Export Mutations',
                    action: function () {
                        var data = table.rows('.selected').data();
                        var myurl = export_url + "mut_type=mut";
                        if (data.length == 0) {
                            if(project_id == null) {
                                alert("No experiment(s) selected!");
                                return;
                            }
                        } else {
                            var exp_ids = '';
                            for (var i = 0; i < data.length; i++) {
                                exp_ids += data[i][1] + ",";
                            }
                            myurl = myurl + "&experiment_ids=" + exp_ids;
                        }
                        window.open(myurl)
                    }
                },
                {
                    text: 'Export Converged Mutations',
                    action: function () {
                        var data = table.rows('.selected').data();
                        var myurl = export_url + "mut_type=converged_mut";
                        if (data.length == 0) {
                            if(project_id == null) {
                                alert("No experiment(s) selected!");
                                return;
                            }
                        } else {
                            var exp_ids = '';
                            for (var i = 0; i < data.length; i++) {
                                exp_ids += data[i][1] + ",";
                            }
                            myurl = myurl + "&experiment_ids=" + exp_ids;
                        }
                        window.open(myurl)
                    }
                },
                {
                    text: 'Export Fixed Mutations',
                    action: function () {
                        var data = table.rows('.selected').data();
                        if (data.length == 0) {
                            if(project_id == null) {
                                alert("No experiment(s) selected!");
                                return;
                            }
                        } else {
                            exp_ids = '';
                            for (var i = 0; i < data.length; i++) {
                                exp_ids += data[i][1] + ",";
                            }
                            var myurl = export_url + "mut_type=fixed_mut&experiment_ids=" + exp_ids
                            window.open(myurl)
                        }
                    }
                },
            ],
            deferRender: true,
            fixedColumns: {
                leftColumns: 2
            },
            columnDefs: [
                {
                    targets: 0,
                    orderable: false,
                    className: 'select-checkbox',
                },
                {
                    "targets": 1,
                    "visible": true,
                }
            ],
            select: {
                style: 'multi',
                selector: 'td:first-child'
            },
            order: [[1, 'asc']]
        });

    });
