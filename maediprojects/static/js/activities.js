Vue.config.devtools = true
new Vue({
  el: "#app",
  delimiters: ["[[", "]]"],
  data() {
    return {
      slider: null,
      transaction_dates: {
        min_earliest_date: new Date(activity_dates['earliest']),
        max_latest_date: new Date(activity_dates['latest'])
      },
      isBusy: true,
      perPage: 20,
      currentPage: 1,
      totalRows: 1,
      filters: [],
      filterTitle: null,
      filterIncludedFields: [],
      defaultFilters: {
        'earliest_date': new Date(activity_dates['earliest']).toISOString().split("T")[0],
        'latest_date': new Date(activity_dates['latest']).toISOString().split("T")[0]
      },
      selectedFilters: {
        'earliest_date': new Date(activity_dates['earliest']).toISOString().split("T")[0],
        'latest_date': new Date(activity_dates['latest']).toISOString().split("T")[0]
      },
      projects: [],
      fields: [
        {
          key: 'title',
          sortable: true
        },
        {
          key: 'reporting_org',
          label: "Organisation",
          sortable: true
        },
        {
          key: 'total_commitments',
          label: 'Commitments',
          sortable: true,
          class: "number",
          formatter: value => {
            return "$" + value.toLocaleString(undefined, {minimumFractionDigits: 2})
          }
        },
        {
          key: 'total_disbursements',
          label: 'Disbursements',
          sortable: true,
          class: "number",
          formatter: value => {
            return "$" + value.toLocaleString(undefined, {minimumFractionDigits: 2})
          }
        },
        {
          key: 'updated_date',
          label: "Last updated",
          sortable: true
        },
        {
          key: 'edit',
          sortable: false
        },
        {
          key: 'delete',
          sortable: false
        }]
    }
  },
  mounted: function() {
    this.setupDates()
    this.setupFilters()
    // this.queryProjectsData()
    this.$refs.slider.noUiSlider.on('update',(values, handle) => {
      this.selectedFilters[handle ? 'latest_date' : 'earliest_date'] = values[handle];
    });
    window.addEventListener('hashchange', () => {
      this.setupHashFilters()
    }, false);
  },
  watch: {
    selectedFilters: {
      deep: true,
      handler() {
        window.location.hash = this.filtersHash
        this.queryProjectsData()
        this.updateSlider()
      }
    }
  },
  methods: {
    confirmDelete: function(delete_url) {
        this.$bvModal.msgBoxConfirm('Are you sure you want to delete this activity? This action cannot be undone!', {
          title: 'Confirm delete',
          okVariant: 'danger',
          okTitle: 'Confirm delete',
          hideHeaderClose: false,
          centered: true
        })
          .then(value => {
            window.location = delete_url;
          })
          .catch(err => {
            alert("Sorry, there was an erorr, and that activity couldn't be deleted.")
          })
    },
    updateSlider: function() {
      if ((this.selectedFilters.earliest_date != null) && (this.selectedFilters.latest_date != null)) {
        this.$refs.slider.noUiSlider.set([new Date(this.selectedFilters.earliest_date), new Date(this.selectedFilters.latest_date)])
      }
    },
    resetFilters: function() {
      Object.entries(this.selectedFilters).map(
        item =>  {
          if (item[0] != this.defaultFilters[item[0]]) {
            Vue.set(this.selectedFilters, item[0], this.defaultFilters[item[0]])
          }
        })
    },
    formatDate: function ( date ) {
      return date.toISOString().split("T")[0];
    },
    toFormat: function ( v ) {
      return this.formatDate(new Date(v));
    },
    fromFormat: function( v ) {
      var newdate = v.split("-")
      return new Date(v).getTime()
    },
    onFiltered(filteredItems) {
      // Trigger pagination to update the number of buttons/pages due to filtering
      this.totalRows = filteredItems.length
      this.currentPage = 1
    },
    setupDates: function() {
      this.dateSlider = noUiSlider.create(this.$refs.slider, {
        id: 'slider2',
        connect: true,
        animate: false,
        range: {
          min: this.transaction_dates.min_earliest_date.getTime(),
          max: this.transaction_dates.max_latest_date.getTime()
        },
        start: [this.transaction_dates.min_earliest_date.getTime(),this.transaction_dates.max_latest_date.getTime()],
        tooltips: true,
        format: { to: this.toFormat, from: Number }
      });
    },
    setupHashFilters() {
      if (window.location.hash) {
        params = window.location.hash.split("?")[1].split("&");
        var hashFilters = params.reduce(
            (obj, item) => {
              var _item = item.split("=")
              obj[_item[0]]= _item[1]
              return obj
            },
            {})
        Object.keys(hashFilters).forEach(key => {
          if (hashFilters[key] != undefined) {
            Vue.set(this.selectedFilters, key, hashFilters[key])
          }
        })
        Object.keys(this.defaultFilters).forEach(key => {
          if (!(key in hashFilters)) {
            Vue.set(this.selectedFilters, key, this.defaultFilters[key])
          }
        })
      } else {
        this.selectedFilters = this.defaultFilters
      }
    },
    setupFilters() {
      this.setupHashFilters()
      axios
        .get(activities_filters_url)
        .then(response => {
          response.data.filters.reduce(
            (obj, item) => {
              Vue.set(this.defaultFilters, item.name, "all")
              if (!(item.name in this.selectedFilters)) {
                Vue.set(this.selectedFilters, item.name, "all")
              }
            },
            {})
          this.filters = response.data.filters
        });
      },
    queryProjectsData:  _.debounce(function (e) {
      axios
        .get(activity_api_url, {
          params: this.nonDefaultFilters
        })
        .then(response => {
          this.projects = response.data.activities
          this.isBusy = false
          this.totalRows = this.projects.length
        });
    }, 500)
  },
  computed: {
    nonDefaultFilters() {
      return Object.entries(this.selectedFilters).reduce(
        (obj, item, index) => {
          if (item[1] != this.defaultFilters[item[0]]) {
            obj[item[0]] = item[1]
          }
          return obj
        },
      {})
    },
    displayResetFilters() {
      theset = new Set(Object.entries(this.selectedFilters).map(
          item =>  {
            if ((item[0] == "earliest_date") && (this.transaction_dates.min_earliest_date.toISOString().split("T")[0] == item[1])) {
              return "all"
            } else if ((item[0] == "latest_date") && (this.transaction_dates.max_latest_date.toISOString().split("T")[0] == item[1])) {
              return "all"
            } else {
              return item[1]
            }
          }))
      return (theset.size > 1)
    },
    filtersHash() {
      return Object.entries(this.nonDefaultFilters).reduce(
            (obj, item, index) => {
              if (index > 0) { obj += "&"}
              obj += `${item[0]}=${item[1]}`
              return obj
            },
        "?")
    }
  }
})