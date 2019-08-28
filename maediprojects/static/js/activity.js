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
      ]
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
    getFinances: function() {
      axios
        .get(api_finances_url)
        .then((response) => {
          this.finances = response.data.finances
          this.isBusy = false
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
