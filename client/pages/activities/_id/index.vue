<template>
  <div>
    <template v-if="isBusy">
      <div class="text-center my-2">
        <b-spinner class="align-middle" label="Loading..." variant="secondary"></b-spinner>
        <strong>Loading...</strong>
      </div>
    </template>
    <template v-else>
      <b-row>
        <b-col>
          <h1>{{ activity.title }}</h1>
        </b-col>
      </b-row>
      <b-row>
        <b-col md="10">
          <p class="lead">{{ activity.description }}</p>
        </b-col>
        <b-col md="2" v-if="activity.permissions.edit" class="text-right">

          <b-btn :to="{ name: 'activities-id-edit', params: {id: activity.id }}" variant="warning">
            <font-awesome-icon :icon="['fas', 'edit']" />
            Edit project
          </b-btn>
        </b-col>
      </b-row>
      <b-row>
        <b-col md="6">
          <b-btn variant="primary" :to="{ name: 'activities-id-results-design', params: {id: activity.id}}"
          v-if="(activity.permissions.edit == true) || (loggedInUser.roles_list.includes('results-data-design'))">
            <font-awesome-icon :icon="['fa', 'magic']" /> Results designer
          </b-btn>
          <b-btn variant="primary" :to="{ name: 'activities-id-results-data-entry', params: {id: activity.id}}"
          v-if="(activity.permissions.edit == true) || (loggedInUser.roles_list.includes('results-data-entry')) || (loggedInUser.roles_list.includes('results-data-design'))">
            <font-awesome-icon :icon="['fa', 'clipboard-list']" /> Results data entry
          </b-btn>
          <h3>Basic data</h3>
          <table class="table table-hover table-sm" responsive>
            <tbody>
              <tr>
                <td><b>Project code</b></td>
                <td>{{ activity.code }}</td>
              </tr>
              <tr>
                <td><b>Project status</b></td>
                <td><!-- codelist_lookups["ActivityStatus"] -->
                  <span class="badge badge-secondary">{{ activity.activity_status }}</span>
                </td>
              </tr>
              <tr>
                <td><b>Funded by</b></td>
                <td>{{ activity.reporting_org.name }}</td>
              </tr>
              <tr>
                <td><b>Implemented by</b></td>
                <td>
                  <b-badge v-for="organisation in activity.implementing_organisations" v-bind:key="organisation.id">{{ organisation.name }}</b-badge>
                </td>
              </tr>
              <tr>
                <td><b>Start date</b></td>
                <td>{{ activity.start_date }}</td>
              </tr>
              <tr>
                <td><b>End date</b></td>
                <td>{{ activity.end_date }}</td>
              </tr>
              <tr>
                <td><b>Last updated</b></td>
                <td>{{ activity.updated_date }}</td>
              </tr>
            </tbody>
          </table>
          <h3>Sectors</h3>
          <table class="table table-hover table-sm" responsive>
            <tbody>
              <tr v-for="(classification, cl_id) in activity.classifications_data" v-bind:key="classification.code">
                <td><b>{{ classification.name }}</b></td>
                <td>
                  <span :class="`badge badge-secondary ${classification.code}`"
                  v-for="entry in classification.entries" v-bind:key="entry.id">{{ entry.codelist_code.name }}</span>
                </td>
              </tr>
              <template v-if="activity.domestic_external == 'external'">
                  <tr>
                    <td><b>Finance Type</b></td>
                    <td>
                      <span v-for="(pct, ft) in activity.disb_finance_types">
                        {{ ft }}: {{ pct }}% <br />
                      </span>
                    </td>
                  </tr>
                  <tr v-if="activity.disb_fund_sources.length > 1">
                    <td><b>Fund Sources</b></td>
                    <td>
                      <span v-for="(data, fs) in activity.disb_fund_sources">
                        {{ fs }} ({{ data.finance_type }}): {{ data.value }}% <br />
                      </span>
                    </td>
                  </tr>
              </template>
            </tbody>
          </table>
          <template v-if="activity.milestones_data">
          <h3>Project Development and Appraisal</h3>
            <table class="table table-hover table-sm" responsive>
              <tbody>
                <tr v-for="milestone in activity.milestones_data" v-bind:key="milestone.id">
                  <td><b>{{milestone.name }}</b></td>
                  <td><span :class="`badge badge-${milestone.achieved.colour}`">
                    <i :class="`fa ${milestone.achieved.icon}`"></i> ${milestone.achieved.name}
                  </span></td>
                </tr>
              </tbody>
            </table>
          </template>
        </b-col>
        <b-col md="6" class="activity-profile-location-map-container">
          <h3 id="locations">Locations</h3>
          <div id="locationMap">
            <client-only>
              <l-map :zoom=7 :center="[6.5,-9.2]" :options="{scrollWheelZoom: false}">
                <l-tile-layer url="https://d.tiles.mapbox.com/v3/markbrough.n3kod47p/{z}/{x}/{y}.png"></l-tile-layer>
                <l-marker :lat-lng="location.latLng" v-for="location in locations" v-bind:key="location.id">
                  <l-popup>{{ location.name }}</l-popup>
                </l-marker>
              </l-map>
           </client-only>
          </div>
        </b-col>
      </b-row>
      <b-row>
        <b-col>
          <LineChart
            :data="financesChartData"
            :height="100"
            class="line-chart"></LineChart>
        </b-col>
      </b-row>
      <b-row>
        <b-col>
          <hr />
        </b-col>
      </b-row>
      <b-row id="financialdata">
        <b-col lg="9">
          <h2>Financial data</h2>
        </b-col>
        <b-col lg="3" v-if="(activity.domestic_external == 'external') && (activity.disb_fund_sources.length > 1)">
          <b-form-group class="text-right"
          label="Display:">
            <b-form-radio-group
              id="btn-radios-1"
              v-model="showFundSource"
              :options="showFundSourceOptions"
              buttons
              button-variant="outline-dark"
            ></b-form-radio-group>
          </b-form-group>
        </b-col>
      </b-row>
      <template v-if="showFundSource">
        <template v-for="finance in financesFundSources">
          <b-row>
            <template v-for="fundSourceData, fundSource in fundSources">
              <b-col v-if="fundSource in finance.data">
                <h3>
                  <template v-if="fundSource != 'null'">{{ fundSource }}</template>
                  <b-badge>{{ fundSourceData.finance_type }}</b-badge>
                  <br />{{ finance.title }}</h3>
                <b-table class="table financial-table table-sm"
                :fields="fiscal_fields" :items="Object.values(finance.data[fundSource])"
                sort-by="period"
                :sort-desc="true"
                :busy="isBusy"
                responsive>
                  <template v-slot:table-busy class="text-center text-muted my-2">
                    <b-spinner class="align-middle"></b-spinner>
                    <strong>Loading...</strong>
                  </template>
                </b-table>
              </b-col>
            </template>
          </b-row>
        </template>
      </template>
      <template v-else>
        <b-row>
          <template v-for="(finance, fkey) in finances">
            <b-col>
              <h3>{{ finance.title }}</h3>
              <b-table class="table financial-table table-sm"
              :id="`${fkey}-table`"
              :fields="fiscal_fields" :items="finance.data"
              sort-by="period"
              :sort-desc="true"
              :busy="isBusy"
              responsive>
              <div slot:table-busy class="text-center text-muted my-2">
                <b-spinner class="align-middle"></b-spinner>
                <strong>Loading...</strong>
              </div>
            </b-table>
            </b-col>
          </template>
        </b-row>
      </template>
      <b-row v-if="results.length > 0">
        <b-col>
          <hr />
        </b-col>
      </b-row>
      <div class="row" id="results" v-if="results.length > 0">
        <div class="col-md-12">
          <h2>Results</h2>
          <b-alert variant="info" :show="activity.domestic_external == 'external'">
            These results were automatically captured from <a :href="`http://d-portal.org/q.html?aid=${activity.code}`">this donor's IATI data</a>.
          </b-alert>
          <b-table
          responsive
          :fields="resultsFields"
          :items="results">
            <template v-slot:cell(title)="data">
              {{ data.item.indicator_title }}
              <span v-if="data.item.measurement_unit_type">
                ({{ data.item.measurement_unit_type }})
              </span>
            </template>
            <template v-slot:cell(from)="data">
              {{ data.item.period_start }}
            </template>
            <template v-slot:cell(to)="data">
              {{ data.item.period_end }}
            </template>
            <template v-slot:cell(target)="data">
              {{ data.item.target_value }}
            </template>
            <template v-slot:cell(actual)="data">
              {{ data.item.actual_value }}
            </template>
            <template v-slot:cell(%)="data">
              <b-progress
                :value="data.item.percent_complete" max="100"
                :variant="data.item.percent_complete_category"
                show-progress
                v-if="data.item.percent_complete">
              </b-progress>
            </template>
          </b-table>
        </div>
      </div>
      <div class="row" v-if="documents.length > 0">
        <div class="col">
          <hr />
        </div>
      </div>
      <div class="row" id="documents" v-if="documents.length > 0">
        <div class="col-md-12">
          <h2>Documents</h2>
          <b-alert variant="info" :show="activity.domestic_external == 'external'">
            These documents were automatically captured from <a :href="`http://d-portal.org/q.html?aid=${activity.code}`">this donor's IATI data</a>.
          </b-alert>
          <b-table responsive fixed
            :fields="['title', 'type', 'date']"
            :items="documents">
            <template v-slot:cell(title)="data">
              <a :href="data.item.url">{{ data.item.title }}</a>
            </template>
            <template v-slot:cell(type)="data">
              <span class="badge badge-secondary"
                  v-for="category in data.item.categories" v-bind:key="category">{{ category }}</span>
            </template>
            <template v-slot:cell(date)="data">
              {{ data.item.document_date || '' }}
            </template>
          </b-table>
        </div>
      </div>
    </template>
  </div>
</template>
<style scoped>
.line-chart {
  width: 100%;
}
#locationMap {
  height: 400px;
}
</style>
<script>
import config from '~/nuxt.config'
import { mapGetters } from 'vuex'
import LineChart from '~/components/charts/line-chart'

export default {
  components: {
    LineChart
  },
  head() {
    return {
      title: this.activity.title ? `${this.activity.title} | ${config.head.title}` : config.head.title
    }
  },
  middleware: 'auth',
  data() {
    return {
      activityID: this.$route.params.id,
      activity: {},
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
      locations: [],
      results: [],
      documents: [],
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
    this.getActivity()
    this.getLocations()
    this.getFinances()
    this.getFinancesFundSources()
    this.getResults()
    this.getDocuments()
    /*
    if (window.location.hash && window.location.hash.split("#").length>0) {
      console.log("scrollto", window.location.hash.split("#")[1])
      VueScrollTo.scrollTo(document.getElementById(window.location.hash.split("#")[1]), 500, {offset:-60})
    }
    */
  },
  computed: {
    isBusy() {
      return Object.keys(this.activity).length == 0
    },
    resultsFields() {
      return ['title', 'from', 'to', 'target', 'actual'].concat({key: '%', thStyle: 'width: 30%'})
    },
    financesChartData() {
      return {
        "labels": this.years,
        "datasets": [
          {
            "label": "Disbursements",
            "data": this.chartData.disbursements || [],
            "borderColor":"rgb(0, 131, 61)",
            "fillColor":"rgb(0, 131, 61)",
            "fill": false,
            "lineTension":0.1
          },
          {
            "label": "Commitments",
            "data": this.chartData.commitments || [],
            "borderColor": "rgb(241, 86, 35)",
            "fillColor": "rgb(241, 86, 35)",
            "fill": false,
            "lineTension":0.1
          }
        ]
      }
    },
    ...mapGetters(['isAuthenticated', 'loggedInUser'])
  },
  methods: {
    getRange: function(start, stop, step = 1) {
      return Array(Math.ceil((stop - start) / step)).fill(start).map((x, y) => x + y * step)
    },
    getChartData: function(finances) {
      var disbursements = Object.values(finances.disbursement.data.reduce((obj, item) => {
        var d = new Date(item.date); var y = d.getFullYear(); obj[y] += item.value; return obj; }, this.years.reduce((obj, item) => {obj[item] = 0; return obj}, {})))
      var commitments = Object.values(finances.commitments.data.reduce((obj, item) => {
        var d = new Date(item.date); var y = d.getFullYear(); obj[y] += item.value; return obj; }, this.years.reduce((obj, item) => {obj[item] = 0; return obj}, {})))
      return {
        disbursements: disbursements.reduce((obj, item, index) => { if (index == 0) { return obj } obj[index] = item + obj[index-1]; return obj }, disbursements),
        commitments: commitments.reduce((obj, item, index) => { if (index == 0) { return obj } obj[index] = item + obj[index-1]; return obj }, commitments),
      }
    },
    async getActivity() {
      await this.$axios
        .get(`activities/${this.activityID}.json`)
        .then((response) => {
          this.activity = response.data.activity
        })
    },
    async getLocations() {
      this.$axios
        .get(`activity_locations/${this.activityID}/`)
        .then((response) => {
          this.locations = response.data.locations.map(l => {
            return {
              id: l.id,
              latLng: [l.locations.latitude, l.locations.longitude],
              name: l.locations.name
            }
          });
        });
    },
    async getResults() {
      this.$axios
        .get(`activities/${this.activityID}/results.json`)
        .then((response) => {
          this.results = response.data.results.reduce((results, result) => {
            result.periods.forEach(period => {
              results.push({...period, ...result})
            })
            return results
          }, [])
        })
    },
    async getDocuments() {
      this.$axios
        .get(`activities/${this.activityID}/documents.json`)
        .then((response) => {
          this.documents = response.data.documents
        })
    },
    async getFinances() {
      await this.$axios
        .get(`activities/${this.activityID}/finances.json`)
        .then((response) => {
          this.finances = response.data.finances
          var disbYears = this.finances.disbursement ? this.finances.disbursement.data.map(item => new Date(item.date).getFullYear()): []
          var commitmentYears = this.finances.commitments ? this.finances.commitments.data.map(item => new Date(item.date).getFullYear()) : []
          var years = [...disbYears, ...commitmentYears]
          if ((disbYears.length === 0) || (commitmentYears.length === 0)) { return false }
          this.years = this.getRange(Math.min.apply(Math, years), new Date().getFullYear()+1) // to this year
          this.chartData = this.getChartData(response.data.finances)
        });
    },
    async getFinancesFundSources() {
      await this.$axios
        .get(`activities/${this.activityID}/finances/fund_sources.json`)
        .then((response) => {
          this.financesFundSources = response.data.finances
          this.fundSources = response.data.fund_sources
        });
    }
  }
}
</script>
