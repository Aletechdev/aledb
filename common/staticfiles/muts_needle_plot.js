/**
 * Created by dgosting on 6/24/16.
 */
var NEEDLE_PLOT = NEEDLE_PLOT || (function () {
       var _args = {};
        return {
            init : function (Args) {
                _args = Args;
            },
            create_muts_needle_plot : function () {
                (function () {
                    var yourDiv = document.getElementById('plot');
                    var mutneedles = require("muts-needle-plot");
                    var colorMap = {};
                    var legends = {
                        x: "Position",
                        y: "Number of Recorded Mutations"
                    };
                    var plotConfig = {
                        maxCoord: 5000000,
                        minCoord: 0,
                        targetElement: yourDiv,
                        mutationData: _args[0],
                        colorMap: colorMap,
                        legends: legends
                    };
                    var instance = new mutneedles(plotConfig);
                })();
            }
        }
}());

