$(function () {
    var myChart = echarts.init(document.getElementById('blog-graph'));

// 指定图表的配置项和数据

    myChart.showLoading();
    $.get('/assets/data/graph.gexf', function (xml) {
        myChart.hideLoading();

        var graph = echarts.dataTool.gexf.parse(xml);
        var categories = [];
        for (var i = 0; i < 9; i++) {
            categories[i] = {
                name: '类目' + i
            };
        }
        graph.nodes.forEach(function (node) {
            node.itemStyle = null;
            // node.symbolSize = 10;
            node.value = node.symbolSize/7;
            node.symbolSize = node.symbolSize+10;

            node.category = node.attributes.modularity_class;
            // Use random x, y
            node.x = node.y = null;
            node.draggable = true;
        });
        option = {
            tooltip: {},
            // legend: [{
            //     // selectedMode: 'single',
            //     data: categories.map(function (a) {
            //         return a.name;
            //     })
            // }],
            animation: false,
            series : [
                {
                    // name: 'Les Miserables',
                    type: 'graph',
                    layout: 'force',
                    data: graph.nodes,
                    links: graph.links,
                    categories: categories,
                    roam: true,
                    label: {
                        normal: {
                            position: 'right'
                        }
                    },
                    force: {
                        repulsion: 200
                    }
                }
            ]
        };

        myChart.setOption(option);
    }, 'xml');
});
