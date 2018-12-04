
// Load the data
queue()
    .defer(d3.csv, "static/c.csv")
    .defer(d3.csv, "static/s.csv")
    .await(compileData);


function compileData(error, categoryData, scoreData) {
    // Make sure no error loading data
    if (error){
        return console.log(error);
    }

    console.log(categoryData);
    console.log(scoreData);

    // Create map between category ID and the name
    let categoryMap = {};
    categoryData.forEach(function(categoryObj) {
        categoryMap[categoryObj.categoryID] = categoryObj.category;
    });

    console.log(categoryMap)

    var getscores = [];
    for (var i=0; i < scoreData.length ; i++)
        getscores.push(scoreData[i]["score"]);

    console.log("Scores", getscores);

    // Sort the data in ascending order
    getscores.sort(function(a,b) {
       return a - b;
    });

    // // Splicing the array for display convenience. Not really necessary
    // getscores.splice(0, 180);

    // Now that the data has laoded, we can make the visualization
    createVis("chart-display-col", getscores, categoryMap, scoreData);
}

function createVis(parentElement, countData, categoryMap, scoreData) {
    // Configure margins
    let margin = { top: 20, right: 20, bottom: 90, left: 30 };

    console.log($("#" + parentElement).width())

    // Cofigure height and width of the visualization
    let width = $("#" + parentElement).width() - margin.left - margin.right,
        height = $("#" + parentElement).height() - margin.top - margin.bottom;

    console.log($("#" + parentElement).height())

    // SVG drawing area
    let svg = d3.select("#" + parentElement).append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // Create scales
    // Use ordinal scale since the x axis isn't numerical
    let xOrdinalScale = d3.scaleBand()
        .rangeRound([0, width])
        .padding(.5)
        .domain(d3.map(countData, function(datum){return categoryMap[datum.key]}).keys());

    let yScale = d3.scaleLinear()
        .range([height - margin.bottom, margin.top]) // we could also set this to height and 0, but would need to translate axis
        .domain([0, d3.max(countData, function(datum){ return datum.value})]);

    // Now set up the axis
    let barYAxis = d3.axisLeft()
        .scale(yScale);

    let barXAxis = d3.axisBottom()
        .scale(xOrdinalScale);

    // Append the axes to the svg
    let barYAxisGroup = svg.append("g")
        .attr("class", "axis bar-y-axis")
        .call(barYAxis);

    let barXAxisGroup = svg.append("g")
        .attr("class", "axis bar-x-axis")
        .attr("transform", "translate(0," + (height - margin.bottom) + ")")
        .call(barXAxis)
        .selectAll("text")
        .attr("y", 0)
        .attr("x", 9)
        .attr("dy", ".35em")
        .attr("transform", "rotate(75)") // allows us to rotate the text
        .style("text-anchor", "start");;

    // Draw the bars
    let bars = svg.selectAll("rect")
        .data(countData)
        .enter()
        .append("rect")
        .attr("class","count-bar")
        .attr("fill", "red")
        .attr("width", xOrdinalScale.bandwidth())
        .attr("height", function(datum) {
            return yScale(0) - yScale(datum.value);
        })
        .attr("y", function(datum){
            return yScale(datum.value);
        })
        .attr("x", function(datum){
            return xOrdinalScale(categoryMap[datum.key]);
        })
        .on("click", function(datum){
            getCategoryInfo(categoryMap[datum.key], datum.key, scoreData);
        });

}

function getScoreInfo(categoryName, categoryID, scoreData){
    // Get category name
    document.querySelector("#category-span").innerHTML = category;

    // Construct list of scores for that category
    let ul_list = "<ul>";
    scoreData.forEach(function(score){
        if (score.categoryID === categoryID) {
            ul_list += "<li>" + score.score + "</li>";
        }
    })
    ul_list += "</ul>";

    // Put that html string into the dom
    document.querySelector("#scores").innerHTML = ul_list;

}



