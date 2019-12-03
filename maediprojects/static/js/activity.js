// LOCATIONS

axios
  .get(api_activity_locations_url)
  .then((response) => {
    var locationsMap = new MAEDImap("locationMap");
    var data = response.data;
    existingLocations = data;
    for (i in data["locations"]) {
      var l = data["locations"][i]["locations"];
      var toggle = locationsMap.toggleLocation(l);
    }
    locationsMap.resize();
    locationsMap.fitBounds([
        [4.3833, -11.3242],
        [8.37583, -7.56658]
    ]);
  });

// ACTIVITIES APP
Vue.config.devtools = true
new Vue({
  el: "#app",
  delimiters: ["[[", "]]"],
  data() {
    return {
      fiscal_fields: [
        {
          key: 'period',
          sortable: true
        },
        {
          key: 'value',
          sortable: true,
          class: "number",
          formatter: value => {
            return value.toLocaleString(undefined, {minimumFractionDigits: 2})
          }}],
      isBusy: true,
      finances: {},
      financesFundSources: {},
      showFundSource: false,
      fundSources: [],
      showFundSourceOptions: [{
          'value': false,
          'text': 'Summary'
        },
        {
          'value': true,
          'text': 'By Fund Source'
        },
      ],
      years: this.getRange(2008, 2020),
      chartData: []
    }
  },
  mounted: function() {
    this.getFinances()
    this.getFinancesFundSources()
    if (window.location.hash && window.location.hash.split("#").length>0) {
      console.log("scrollto", window.location.hash.split("#")[1])
      VueScrollTo.scrollTo(document.getElementById(window.location.hash.split("#")[1]), 500, {offset:-60})
    }

  },
  methods: {
    getRange: function(start, stop, step = 1) {
      return Array(Math.ceil((stop - start) / step)).fill(start).map((x, y) => x + y * step)
    },
    getChartData: function(finances) {
      var disbursements = Object.values(finances.disbursement.data.reduce((obj, item) => { d = new Date(item.date); y = d.getFullYear(); obj[y] += item.value; return obj; }, this.years.reduce((obj, item) => {obj[item] = 0; return obj}, {})))
      var commitments = Object.values(finances.commitments.data.reduce((obj, item) => { d = new Date(item.date); y = d.getFullYear(); obj[y] += item.value; return obj; }, this.years.reduce((obj, item) => {obj[item] = 0; return obj}, {})))
      var v = {
        disbursements: disbursements.reduce((obj, item, index) => { if (index == 0) { return obj } obj[index] = item + obj[index-1]; return obj }, disbursements),
        commitments: commitments.reduce((obj, item, index) => { if (index == 0) { return obj } obj[index] = item + obj[index-1]; return obj }, commitments),
      }
      console.log(v)
      return v
    },
    setupChart: function() {
      var ctx = document.getElementById('chartArea');
      var data = [{
          x: 10,
          y: 20
      }, {
          x: 15,
          y: 10
      }]
      var stackedLine = new Chart(ctx, {
        "type":"line","data":
          {
            "labels": this.years,
            "datasets": [
              {
                "label": "Disbursements",
                "data": this.chartData.disbursements,
                "borderColor":"rgb(0, 131, 61)",
                "fillColor":"rgb(0, 131, 61)",
                "fill": false,
                "lineTension":0.1
              },
              {
                "label": "Commitments",
                "data": this.chartData.commitments,
                "borderColor": "rgb(241, 86, 35)",
                "fillColor": "rgb(241, 86, 35)",
                "fill": false,
                "lineTension":0.1
              }
            ]
          }
        });
    },
    getFinances: function() {
      axios
        .get(api_finances_url)
        .then((response) => {
          this.finances = response.data.finances
          this.isBusy = false
          var disbYears = this.finances.disbursement ? this.finances.disbursement.data.map(item => new Date(item.date).getFullYear()): []
          var commitmentYears = this.finances.commitments ? this.finances.commitments.data.map(item => new Date(item.date).getFullYear()) : []
          var years = [...disbYears, ...commitmentYears]
          console.log('finances', this.finances)
          if ((disbYears.length === 0) || (commitmentYears.length === 0)) { return false }
          this.years = this.getRange(Math.min.apply(Math, years), new Date().getFullYear()+1) // to this year
          this.chartData = this.getChartData(response.data.finances)
          this.setupChart()
        });
    },
    getFinancesFundSources: function() {
      axios
        .get(api_finances_fund_sources_url)
        .then((response) => {
          this.financesFundSources = response.data.finances
          this.fundSources = response.data.fund_sources
          this.isBusy = false
        });
    }
  }
})
