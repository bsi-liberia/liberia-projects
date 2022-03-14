<template>
  <div>
    <b-alert variant="info" show v-if="activity.iati_preferences.length == 0">
      <h4>Automatically update data</h4>
      <p>Connect this activity to IATI to automatically keep data up to date.</p>
      <b-btn variant="primary" v-b-modal.iati-modal>Connect &raquo;</b-btn>
    </b-alert>
    <b-alert variant="success" show v-else>
      <h4>Connected to IATI</h4>
      <p>This activity is connected to IATI and will automatically be updated for {{ activity.iati_preferences.join(', ') }}.</p>
      <b-btn variant="success" v-b-modal.iati-modal>Settings &raquo;</b-btn>
    </b-alert>
    <b-modal
      id="iati-modal"
      ref="iati-modal"
      title="Connect to IATI"
      size="xl"
      scrollable>
      <ol class="breadcrumb">
        <li
          v-for="breadcrumb in iatiStepsBreadcrumbs"
          :class="breadcrumb.active ? 'breadcrumb-item active' : 'breadcrumb-item'"
          :key="breadcrumb.text">
          <template v-if="breadcrumb.disabled">
            {{ breadcrumb.text }}
          </template>
          <template v-else>
            <nuxt-link :to="breadcrumb.to">
              {{ breadcrumb.text }}
            </nuxt-link>
          </template>
        </li>
      </ol>
      <template v-if="stepBusy">
        <div class="text-center text-muted my-2">
          <b-spinner class="align-middle"></b-spinner>
          <strong>Loading...</strong>
        </div>
      </template>
      <template v-else>
        <template v-if="iatiStep==1">
          <h4>Search for IATI activity</h4>
          <b-form-group
            label="Donor project code"
            label-cols-md="3"
            description="If you know the donor project code, enter it here.">
            <b-input v-model="iati_identifier" placeholder="e.g. P123456"></b-input>
          </b-form-group>
          <!--
          <b-form-group
            label="Title"
            label-cols-md="3"
            description="If you don't get a match below, you can try adjusting the title and search again.">
            <b-input v-model="title" placeholder="e.g. Mount Coffee"></b-input>
          </b-form-group>
          -->
          <b-btn variant="primary" @click="getIATISearchResults">
            <font-awesome-icon :icon="['fas', 'search']" />
            Search
          </b-btn>
          <template v-if="iatiSearchResults!=false">
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
                <b-form-radio v-model="selectedIATIIdentifier" name="selected-iati-identifier" :value="data.item.iati_identifier" v-if="data.item.country_data">Select activity</b-form-radio>
                <b-badge variant="danger" pill v-else>
                  <font-awesome-icon :icon="['fa', 'times-circle']" /> No financial amounts for Liberia
                </b-badge>
              </template>
            </b-table>
          </template>
          <template v-else>
            <div class="text-center text-muted my-2" v-if="isBusy">
              <b-spinner class="align-middle"></b-spinner>
              <strong>Loading...</strong>
            </div>
          </template>
        </template>
        <template v-if="iatiStep == 2">
          <h4>Merge projects (optional)</h4>
          <b-alert variant="secondary" class="mb-4" show>
            You can optionally choose to combine projects
            reported by <b>{{ activity.reporting_org.name }}</b>
            in the Dashboard. Note that no changes will be made unless
            you choose to import IATI data at the end of this process.
          </b-alert>
          <SelectActivities
            :similar-activities.sync="similarActivities"
            :selected-activities.sync="selectedActivities"
            :activity="activity" />
        </template>
        <template v-if="iatiStep == 2.5">
          <h4>Merge Dashboard data</h4>
          <b-alert variant="secondary" class="mb-4" show>
            You have selected multiple Dashboard projects. There are some
            differences in these projects for the below fields. Please
            confirm which data you would prefer to take for each field.
          </b-alert>
          <SelectMergeActivities
            :selected-activities-fields="selectedActivitiesFields"
            :selected-activities-fields-options="selectedActivitiesFieldsOptions"
          />
        </template>
        <template v-if="iatiStep == 3">
          <h4>Review data before import</h4>
          <p class="lead">
            {{ iatiSelected.title }}
            <code>{{ iatiSelected.iati_identifier }}</code>
          </p>
          <b-alert variant="secondary" class="mb-4" show>
            Review the data below and choose whether you would prefer to take
            data from IATI, or retain the existing data in the Dashboard. When
            you're ready, click Import below and your selected data will be imported.
          </b-alert>
          <h5>IATI</h5>
          <LineChart
            :data="iatiChartData"
            :options="chartOptions"
            class="line-chart"></LineChart>
          <hr />
          <h5>Dashboard</h5>
          <LineChart
            :data="dashboardChartData"
            :options="chartOptions"
            class="line-chart"></LineChart>
          <hr />
          <h5>Commitments</h5>
          <b-row>
            <b-col md="9">
              <LineChart
                :data="commitmentsChartData"
                :options="chartOptions"
                class="line-chart"></LineChart>
            </b-col>
            <b-col md="3">
              <b-form-group label="Select data from:">
                <b-form-radio-group
                  v-model="importOptions.commitments"
                  id="radio-group-commitments"
                  :options="importSelectionOptionsFinances"
                  name="radio-options-commitments"
                  stacked
                ></b-form-radio-group>
              </b-form-group>
            </b-col>
          </b-row>
          <hr />
          <h5>Disbursements</h5>
          <b-row>
            <b-col md="9">
              <LineChart
                :data="disbursementChartData"
                :options="chartOptions"
                class="line-chart"></LineChart>
            </b-col>
            <b-col md="3">
              <b-form-group label="Select data from:">
                <b-form-radio-group
                  v-model="importOptions.disbursement"
                  id="radio-group-disbursement"
                  :options="importSelectionOptionsFinances"
                  name="radio-options-disbursement"
                  stacked
                ></b-form-radio-group>
              </b-form-group>
            </b-col>
          </b-row>
          <hr />
          <h5>MTEF Projections</h5>
          <b-row>
            <b-col md="9">
              <LineChart
                :data="forwardspendChartData"
                :options="chartOptions"
                class="line-chart"></LineChart>
            </b-col>
            <b-col md="3">
              <b-form-group label="Select data from:">
                <b-form-radio-group
                  v-model="importOptions.forwardspend"
                  id="radio-group-forwardspend"
                  :options="importSelectionOptionsFinances"
                  name="radio-options-forwardspend"
                  stacked
                ></b-form-radio-group>
              </b-form-group>
            </b-col>
          </b-row>
        </template>
      </template>
      <template #modal-footer>
        <div class="row">
          <div class="col text-right">
            <b-button
              variant="secondary"
              @click="hideIATIModal"
            >
              Cancel
            </b-button>
            <b-button
              variant="primary"
              :disabled="modalOKDisabled"
              @click="modalOK"
            >
              {{ modalOKTitle }}
            </b-button>
          </div>
        </div>
      </template>
    </b-modal>
  </div>
</template>
<style scoped>
.line-chart {
  width: 100%;
  height: 300px;
}
.breadcrumb .active a {
  font-weight: bold;
}
</style>
<script>
import LineChart from '~/components/charts/line-chart'
import SelectActivities from '~/components/ActivityEditor/MergeActivities/SelectActivities.vue'
import SelectMergeActivities from '~/components/ActivityEditor/MergeActivities/SelectMergeActivities.vue'
export default {
  components: {
    LineChart,
    SelectActivities,
    SelectMergeActivities
  },
  props: ['activity', 'api_routes'],
  data() {
    return {
      isBusy: false,
      stepBusy: false,
      title: null,
      iati_identifier: null,
      selectedIATIIdentifier: null,
      iatiSearchResults: false,
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
          key: 'import',
          label: 'Select activity'
        }
      ],
      iatiSelected: {
        title: null,
        iati_identifier: null,
        finances: {},
        country_data: false
      },
      selectedActivities: [],
      selectedActivitiesFields: [],
      selectedActivitiesFieldsOptions: {},
      selectedActivitiesFinances: [],
      similarActivities: [],
      importOptions: {
        commitments: 'IATI',
        disbursement: 'IATI',
        forwardspend: 'IATI',
      },
      importSelectionOptionsFinances: [
        { text: 'IATI', value: 'IATI' },
        { text: 'Dashboard', value: 'dashboard' },
      ],
      colours: [ '#CF3D1E', '#F15623', '#F68B1F', '#FFC60B', '#DFCE21',
      '#BCD631', '#95C93D', '#48B85C', '#00833D', '#00B48D', '#60C4B1', '#27C4F4',
      '#478DCB', '#3E67B1', '#4251A3', '#59449B', '#6E3F7C', '#6A246D', '#8A4873',
      '#EB0080', '#EF58A0', '#C05A89']
    }
  },
  computed: {
    importSelectionOptions() {
      var options = [{ text: 'IATI', value: 'IATI' }]
      options = options.concat(this.similarActivities.filter(
        activity=> { return this.selectedActivities.includes(activity.id)}).map(
        activity=> { return { text: activity.title, value: activity.id } }))
      return options
    },
    iatiStep: {
      set(value) {
        this.$router.push({query: {'iati-step': value}})
      },
      get() {
        if ('iati-step' in this.$route.query) {
          const step = Number(this.$route.query['iati-step'])
          if ((step > 1) && (this.selectedIATIIdentifier==null)) {
            this.$router.push({query: {'iati-step': 1}})
            return 1
          }
          if ((step > 2) && (this.selectedActivities.length==0)) {
            this.$router.push({query: {'iati-step': 2}})
            return 2
          }
          return step
        } else {
          return 1
        }
      }
    },
    iatiStepsBreadcrumbs() {
      return [
        {
          text: '1. Select activity',
          to: {query: {'iati-step': 1}},
          active: this.iatiStep == 1
        },
        {
          text: '2. Merge projects (optional)',
          disabled: this.iatiStep < 2,
          to: {query: {'iati-step': 2}},
          active: 1 < this.iatiStep < 3
        },
        {
          text: '3. Review',
          disabled: this.iatiStep < 3,
          to: {query: {'iati-step': 3}},
          active: this.iatiStep == 3
        },
        {
          text: '4. Import',
          disabled: true,
          active: false
        }
      ]
    },
    modalOK() {
      if (this.iatiStep == 1) {
        return this.selectMerge
      } else if (this.iatiStep == 2) {
        if (this.selectedActivities.length > 1) {
          return this.selectMerge2
        }
        return this.previewImport
      } else if (this.iatiStep == 2.5) {
        return this.previewImport
      } else if (this.iatiStep == 3) {
        return this.doImport
      }
    },
    modalOKDisabled() {
      if (this.iatiStep == 1) {
        return !this.selectedIATIIdentifier
      }
      return false
    },
    modalOKTitle() {
      if (this.iatiStep == 1) {
        return this.selectedIATIIdentifier ? 'Continue...' : 'Select an activity to continue.'
      } else if (this.iatiStep == 2) {
        return 'Continue with selection...'
      } else if (this.iatiStep == 2.5) {
        return 'Continue with selection...'
      } else {
        return 'Import'
      }
    },
    activityFinances() {
      return this.selectedActivitiesFinances.reduce((summary, item) => {
          Object.entries(item.finances).forEach(_item => {
              summary[_item[0]].data = summary[_item[0]].data.concat(_item[1].data)
          })
          return summary
      }, {
        commitments: { data: [] },
        disbursement: { data: [] },
        forwardspend: { data: [] }
      })
    },
    years() {
      const _years = Object.values(this.iatiSelected.finances).reduce((years, finance) => {
        years = years.concat(finance['data'].map(item => Number(item.fiscal_year)))
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
    iatiChartData() {
      const series = {
        'commitments': {'label': 'Commitments', 'colour': this.colours[12]},
        'disbursement': {'label': 'Disbursements', 'colour': this.colours[3]},
        'forwardspend': {'label': 'MTEF Projections', 'colour': this.colours[6]}
      }
      if (!('commitments' in this.iatiSelected.finances)) { return {} }
      const inputData = this.chartData({
        'commitments': { 'data': this.iatiSelected.finances.commitments ? this.iatiSelected.finances.commitments.data : [] },
        'disbursement': { 'data': this.iatiSelected.finances.disbursement ? this.iatiSelected.finances.disbursement.data : [] },
        'forwardspend': { 'data': this.iatiSelected.finances.forwardspend ? this.iatiSelected.finances.forwardspend.data : [] }
      })
      return this.financesChartData(inputData, series)
    },
    dashboardChartData() {
      const series = {
        'commitments': {'label': 'Commitments', 'colour': this.colours[12]},
        'disbursement': {'label': 'Disbursements', 'colour': this.colours[3]},
        'forwardspend': {'label': 'MTEF Projections', 'colour': this.colours[6]}
      }
      if (this.activityFinances.commitments.length==0) { return {} }
      const inputData = this.chartData({
        'commitments': { 'data': this.activityFinances.commitments ? this.activityFinances.commitments.data : [] },
        'disbursement': { 'data': this.activityFinances.disbursement ? this.activityFinances.disbursement.data : [] },
        'forwardspend': { 'data': this.activityFinances.forwardspend ? this.activityFinances.forwardspend.data : [] }
      })
      return this.financesChartData(inputData, series)
    },
    commitmentsChartData() {
      const series = {
        'iati': {'label': 'IATI', 'colour': '#000000'},
        'dashboard': {'label': 'Dashboard', 'colour': this.colours[12]}
      }
      if (!('commitments' in this.iatiSelected.finances)) { return {} }
      const inputData = this.chartData({
        'dashboard': { 'data': this.activityFinances.commitments ? this.activityFinances.commitments.data : [] },
        'iati': { 'data': this.iatiSelected.finances.commitments ? this.iatiSelected.finances.commitments.data : [] }
      })
      return this.financesChartData(inputData, series)
    },
    disbursementChartData() {
      const series = {
        'iati': {'label': 'IATI', 'colour': '#000000'},
        'dashboard': {'label': 'Dashboard', 'colour': this.colours[3]}
      }
      if (!('disbursement' in this.iatiSelected.finances)) { return {} }
      const inputData = this.chartData({
        'dashboard': { 'data': this.activityFinances.disbursement ? this.activityFinances.disbursement.data : [] },
        'iati': { 'data': this.iatiSelected.finances.disbursement ? this.iatiSelected.finances.disbursement.data : [] }
      })
      return this.financesChartData(inputData, series)
    },
    forwardspendChartData() {
      const series = {
        'iati': {'label': 'IATI', 'colour': '#000000'},
        'dashboard': {'label': 'Dashboard', 'colour': this.colours[6]}
      }
      if (!('forwardspend' in this.iatiSelected.finances)) { return {} }
      const inputData = this.chartData({
        'dashboard': { 'data': this.activityFinances.forwardspend ? this.activityFinances.forwardspend.data : [] },
        'iati': { 'data': this.iatiSelected.finances.forwardspend ? this.iatiSelected.finances.forwardspend.data : [] }
      })
      return this.financesChartData(inputData, series)
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
    financesChartData(chartData, series) {
      if (Object.keys(chartData).length == 0) { return null }
      return {
        "labels": this.years,
        "datasets": Object.entries(chartData).reduce((datasets, item, index) => {
          const key = item[0]; const data = item[1];
          if (!key in series) { return datasets }
          datasets.push({
            label: series[key].label,
            fill: false,
            data: data,
            backgroundColor: series[key].colour,
            borderColor: series[key].colour,
            lineTension: 0.1
          })
          return datasets
        }, [])
      }
    },
    chartData(inputData) {
      const data = Object.keys(inputData).reduce((out, key) => {
        const entries = (key in inputData) ? inputData[key]['data'] : []
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
    getRange: function(start, stop, step = 1) {
      return Array(Math.ceil((stop - start) / step)).fill(start).map((x, y) => x + y * step)
    },
    rowClass(item, type) {
      if (!item || type !== 'row') return
      if (item.iati_identifier === this.selectedIATIIdentifier) return 'table-success'
    },
    rowClassStep2(item, type) {
      if (!item || type !== 'row') return
      if (this.selectedActivities.includes(item.id)) return 'table-success'
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
    async selectMerge() {
      this.stepBusy = true
      await this.$axios.get(`${this.api_routes.similar_activities}`)
      .then(response => {
        this.iatiStep = 2
        this.similarActivities = response.data.activities
        this.selectedActivities = response.data.activities.filter(
          activity => { return activity.selected }).map(
          activity => { return activity.id })
        this.stepBusy = false
      })
      .catch(response => {
        this.stepBusy = false
      })
    },
    async selectMerge2() {
      this.stepBusy = true
      const data = {
        activity_ids: this.selectedActivities
      }
      await this.$axios.post(this.api_routes.activity_summaries, data)
      .then(response => {
        this.iatiStep = 2.5
        this.selectedActivitiesFieldsOptions = Object.keys(response.data.fields).reduce((summary, item) => {
          summary[item] = this.activity.id
          return summary
        }, {})
        this.selectedActivitiesFields = Object.entries(response.data.fields).map(item=> {
          return {'field': item[0], 'alternatives': item[1]}
        })
        this.stepBusy = false
      })
    },
    async previewImport() {
      this.stepBusy = true
      const data = {
        activity_ids: this.selectedActivities
      }
      await this.$axios.post(`${this.api_routes.finances_by_year}`,
        data)
      .then(response => {
        this.selectedActivitiesFinances = response.data.activities
      })
      const search_data = {
        iati_identifier: this.selectedIATIIdentifier
      }
      await this.$axios.post(`${this.api_routes.iati_search_by_identifier}`, search_data)
      .then(response => {
        this.iatiStep = 3
        this.iatiSelected = response.data.activity
        this.stepBusy = false
      })
      .catch(response => {
        this.stepBusy = false
      })
      return false
    },
    async doImport() {
      this.stepBusy = true
      const data = {
        iatiIdentifier: this.selectedIATIIdentifier,
        activityIDs: this.selectedActivities,
        importOptions: this.importOptions,
        activitiesFieldsOptions: this.selectedActivitiesFieldsOptions
      }
      await this.$axios.post(this.api_routes.iati_import, data)
      .then(response => {
          this.$root.$bvToast.toast(`Successfully imported data from IATI.`, {
          title: 'Imported from IATI',
          autoHideDelay: 10000,
          solid: true,
          variant: 'success'
        })
        this.$router.go()
      })
      .catch(response => {
        this.stepBusy = false
      })
      return true
    },
    hideIATIModal() {
      this.$refs['iati-modal'].hide()
    }
  },
  mounted() {
    this.$root.$on('bv::modal::show', (bvEvent, modalId) => {
      if (modalId == 'iati-modal') {
        if (this.activity.iati_preferences.length > 0) {
          this.selectedIATIIdentifier = this.activity.iati_identifier
          this.selectedActivities = [this.activity.id]
          this.importOptions = {
            commitments: this.activity.iati_preferences.includes('commitments') ? 'IATI' : 'dashboard',
            disbursement: this.activity.iati_preferences.includes('disbursement') ? 'IATI' : 'dashboard',
            forwardspend: this.activity.iati_preferences.includes('forwardspend') ? 'IATI' : 'dashboard',
          }
          this.previewImport()
        } else if (!(this.iatiSearchResults.length > 0)) {
          this.title = this.activity.title
          this.iati_identifier = this.activity.iati_identifier
        }
      }
    })
  }
}
</script>