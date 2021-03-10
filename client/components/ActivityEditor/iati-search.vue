<template>
  <div>
    <b-alert variant="info" show>
      <h4>Automatically update data</h4>
      <p>Connect this activity to IATI to automatically keep data up to date.</p>
      <b-btn variant="primary" v-b-modal.iati-modal>Connect &raquo;</b-btn>
    </b-alert>
    <b-overlay
      :show="isBusy"
      rounded="sm">
      <b-modal
        id="iati-modal"
        title="Connect to IATI"
        size="lg"
        scrollable
        :ok-disabled="!selectedIATIIdentifier"
        :ok-title="selectedIATIIdentifier ? 'Continue...' : 'Select an activity to continue.'"
        @ok="previewImport">
        <h4>Search for IATI activity</h4>
        <b-form-group
          label="Donor project code"
          label-cols-md="3"
          description="If you know the donor project code, enter it here. You are most likely to get a match using the donor project code.">
          <b-input v-model="iati_identifier" placeholder="e.g. P123456"></b-input>
        </b-form-group>
        <b-form-group
          label="Title"
          label-cols-md="3"
          description="If you don't get a match below, you can try adjusting the title and search again.">
          <b-input v-model="title" placeholder="e.g. Mount Coffee"></b-input>
        </b-form-group>
        <b-btn variant="secondary" @click="getIATISearchResults" size="sm">Search again...</b-btn>
        <hr />
        <h4>Search results</h4>
        <p v-if="iatiSearchResults.length>0">Select an activity below to begin import.</p>
        <b-table
          :items="iatiSearchResults"
          :fields="iatiSearchResultsFields"
          :busy="isBusy"
          :tbody-tr-class="rowClass"
          show-empty>
          <template #empty="scope">
            <div class="text-muted text-center">
              No activities found. Try adjusting the title above.
            </div>
          </template>
          <template #table-busy>
            <div class="text-center text-muted my-2">
              <b-spinner class="align-middle"></b-spinner>
              <strong>Loading...</strong>
            </div>
          </template>
          <template #cell(import)="data">
            <b-form-radio v-model="selectedIATIIdentifier" name="selected-iati-identifier" :value="data.item.iati_identifier">Select activity</b-form-radio>
          </template>
        </b-table>
      </b-modal>
      <b-modal
        id="iati-preview-modal"
        title="Review data before import"
        size="lg"
        scrollable
        ok-title="Import">
        <h4>{{ iatiSelected.title }}</h4>
        <LineChart
          :data="financesChartData"
          :options="chartOptions"
          class="line-chart"></LineChart>
      </b-modal>
    </b-overlay>
  </div>
</template>
<style scoped>
.line-chart {
  width: 100%;
  height: 300px;
}
</style>
<script>
import LineChart from '~/components/charts/line-chart'
export default {
  components: {
    LineChart
  },
  props: ['activity', 'api_routes'],
  data() {
    return {
      isBusy: false,
      title: null,
      iati_identifier: null,
      selectedIATIIdentifier: null,
      iatiSearchResults: [],
      iatiSearchResultsFields: [
        {
          key: 'iati_identifier',
          label: 'IATI Identifier'
        },
        {
          key: 'title',
          label: 'Title'
        },
        {
          key: 'description',
          label: 'Description'
        },
        {
          key: 'import',
          label: 'Select activity'
        }
      ],
      iatiSelected: {
        title: null,
        iati_identifier: null,
        transactions: {}
      }
    }
  },
  computed: {
    years() {
      const _years = Object.values(this.iatiSelected.transactions).reduce((years, finance) => {
        years = years.concat(finance.map(item => Number(item.fiscal_year)))
        return years
      }, [])
      if (_years.length == 0) { return [] }
      if (this.activity.start_date) {
        _years.push(new Date(this.activity.start_date).getFullYear())
      }
      _years.push(new Date(this.activity.end_date).getFullYear()+1)
      if (this.activity.end_date) {
        _years.push(new Date(this.activity.end_date).getFullYear())
      }
      return this.getRange(Math.min.apply(Math, _years), Math.max.apply(Math, _years)+1)
    },
    chartData() {
      const data = Object.keys(this.iatiSelected.transactions).reduce((out, key) => {
        const entries = (key in this.iatiSelected.transactions) ? this.iatiSelected.transactions[key] : []
        out[key] = Object.entries(entries.reduce((keyItems, entry) => {
          /* For each allowed year, add the value for this entry */
          if (Number(entry.fiscal_year) in keyItems) {
            keyItems[Number(entry.fiscal_year)] += entry.value
          }
          return keyItems
        }, /* Pass in list of available years with default amount 0.0 */
          this.years.reduce((yearObj, year) => {
            yearObj[year] = 0.0; return yearObj
          }, {}))
        ).reduce((_keyItems, entry, index) => {
          /* Cumulative: add previous year's amount to current year's */
          if (index == 0) { _keyItems.push(entry[1]) }
          else { _keyItems.push(entry[1] + _keyItems[index-1]) }
          return _keyItems
        }, [])
        return out
      }, {})
      return data
    },
    financesChartData() {
      const colours = [ '#CF3D1E', '#F15623', '#F68B1F', '#FFC60B', '#DFCE21',
      '#BCD631', '#95C93D', '#48B85C', '#00833D', '#00B48D', '#60C4B1', '#27C4F4',
      '#478DCB', '#3E67B1', '#4251A3', '#59449B', '#6E3F7C', '#6A246D', '#8A4873',
      '#EB0080', '#EF58A0', '#C05A89']
      const transactionTypes = {
        3: {'label': 'Disbursements', 'colour': colours[3]},
        2: {'label': 'Commitments', 'colour': colours[12]},
        'budget': {'label': 'MTEF Projections', 'colour': colours[6]},
      }
      if (Object.keys(this.chartData).length == 0) { return null }
      return {
        "labels": this.years,
        "datasets": Object.entries(this.chartData).reduce((datasets, item, index) => {
          const key = item[0]; const data = item[1];
          if (!key in transactionTypes) { return datasets }
          datasets.push({
            label: transactionTypes[key].label,
            fill: false,
            data: data,
            backgroundColor: transactionTypes[key].colour,
            borderColor: transactionTypes[key].colour,
            lineTension: 0.1
          })
          return datasets
        }, [])
      }
    },
    chartOptions() {
      return {
        maintainAspectRatio: false,
        tooltips: {
          callbacks: {
            label: ((tooltipItem, data) => {
              const datasetLabel = data.datasets[tooltipItem.datasetIndex].label
              const value = tooltipItem.yLabel.toLocaleString(undefined, {
                maximumFractionDigits: 0,
                minimumFractionDigits: 0
              })
              return `${datasetLabel}: USD ${value}`;
            })
          }
        },
        scales: {
          yAxes: [
            {
              ticks: {
                beginAtZero: true,
                callback: function(tick) {
                  return tick.toLocaleString(undefined, {
                    maximumFractionDigits: 0,
                    minimumFractionDigits: 0
                  })
                }
              },
              scaleLabel: {
                display: true,
                labelString: 'Amount (USD)'
              }
            }
          ],
          xAxes: [
            {
              ticks: {
                callback: function(tick) {
                  return `${tick}`
                }
              },
              scaleLabel: {
                display: true,
                labelString: 'Calendar Year'
              }
            }
          ]
        }
      }
    },
  },
  methods: {
    getRange: function(start, stop, step = 1) {
      return Array(Math.ceil((stop - start) / step)).fill(start).map((x, y) => x + y * step)
    },
    rowClass(item, type) {
      if (!item || type !== 'row') return
      if (item.iati_identifier === this.selectedIATIIdentifier) return 'table-success'
    },
    async getIATISearchResults() {
      const data = {
        title: this.title,
        iati_identifier: this.iati_identifier,
        reporting_org_code: this.activity.reporting_org.code
      }
      this.isBusy = true
      await this.$axios.post(this.api_routes.iati_search, data)
      .then(response => {
        this.iatiSearchResults = response.data.results
      })
      this.isBusy = false
    },
    async previewImport() {
      this.isBusy = true
      await this.$axios.post(`${this.api_routes.iati_search}${this.selectedIATIIdentifier}/`)
      .then(response => {
        this.$bvModal.hide('iati-modal')
        this.iatiSelected = response.data.activity
        this.$bvModal.show('iati-preview-modal')
        this.isBusy = false
      })
      .catch(response => {
        this.isBusy = false
      })
    }
  },
  mounted() {
    this.$root.$on('bv::modal::show', (bvEvent, modalId) => {
      if (modalId == 'iati-modal') {
        this.title = this.activity.title
        this.iati_identifier = this.activity.iati_identifier
        this.getIATISearchResults()
      }
    })
  }
}
</script>