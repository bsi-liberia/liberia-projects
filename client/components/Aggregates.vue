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
        <b-col md="9">
          <h1>{{ aggregate.name }}</h1>
        </b-col>
        <b-col md="3" class="text-center" v-if="type=='sectors'">
          <template v-if="preparingSectorBriefFile">
            <b-btn variant="secondary" class="float-md-right" id="download_excel" style="margin-top:4px;" @click="getSectorBriefFile">
              <b-spinner label="Preparing" small></b-spinner> Preparing file...
            </b-btn>
          </template>
          <template v-else>
            <b-btn variant="secondary" class="float-md-right" id="download_excel" href="#" style="margin-top:4px;" @click="getSectorBriefFile">
              <font-awesome-icon :icon="['fas', 'download']" /> Sector Brief
            </b-btn>
          </template>
        </b-col>
      </b-row>
      <hr />
      <b-row>
        <b-col>
          <h2>Planned and Actual Disbursement by {{ dimensionLabel }}</h2>
          <b-row>
            <b-col md="6">
              <b-form-group
                label="Fiscal year"
                label-align="right"
                label-cols-sm="3">
                <b-select v-model="selectedFY"
                :options="fyOptions"></b-select>
              </b-form-group>
            </b-col>
          </b-row>
          <client-only>
            <aggregates-bar-chart
              :selected-fy="selectedFY"
              :dimension="dimension"
              :agg-filter="aggFilter"
              :agg-filter-value="aggFilterValue"></aggregates-bar-chart>
          </client-only>
        </b-col>
      </b-row>
      <hr />
      <b-row>
        <b-col>
          <h2>Projected / Actual Disbursements by {{ dimensionLabel }}, over time</h2>
          <b-row class="mb-2">
            <b-col md="6" class="mt-1">
              <b-form-radio-group
                v-model="selectedPlannedActualDisbursements"
                :options="plannedActualDisbursementOptions"
                button-variant="outline-primary"
                buttons
                size="sm"
              ></b-form-radio-group>
            </b-col>
            <b-col md="6" class="text-md-right mt-1">
              <b-form-radio-group
                v-model="plannedActualDisbursementsStacked"
                :options="plannedActualDisbursementsStackedOptions"
                button-variant="outline-secondary"
                buttons
                size="sm"
              ></b-form-radio-group>
            </b-col>
          </b-row>
          <client-only>
            <aggregates-line-chart
              :value-field="selectedPlannedActualDisbursements"
              :fy-options="fyOptions"
              :stacked="plannedActualDisbursementsStacked"
              :dimension="dimension"
              :agg-filter="aggFilter"
              :agg-filter-value="aggFilterValue"></aggregates-line-chart>
          </client-only>
        </b-col>
      </b-row>
      <hr />
      <b-row class="mb-3">
        <b-col md="9">
          <b-button block href="#"
          :class="{'btn-danger': displayResetFilters}"
          v-b-toggle.sidebar-filters>Show filters <font-awesome-icon :icon="['fas', 'filter']" /></b-button>
          <b-sidebar id="sidebar-filters" title="Filter activities" width="500px" right shadow no-close-on-route-change>
            <div class="px-3 py-2">
              <form class="form-activity-filters">
                <b-button id="filtersAppliedLabel"
                  v-if="displayResetFilters" variant="danger" class="float-right"
                  size="sm"
                  @click="resetFilters">Reset filters</b-button>
                <p class="lead">Find projects matching all of the following conditions. Results automatically update.</p>
                <b-form-group
                  :label="filter.label"
                  :label-for="filter.name" v-for="filter in filters" v-bind:key="filter.name">
                  <b-select class="form-control filter-select" :name="filter.name"
                    :options="filter.codes" value-field="id" text-field="name"
                    v-model="selectedFilters[filter.name]" size="sm"
                    :state="(selectedFilters[filter.name] != 'all') ? true : null">
                    <template v-slot:first>
                      <option value="all">Select all</option>
                    </template>
                  </b-select>
                </b-form-group>
                <b-form-group
                  label="Date Range"
                  label-for="date-range">
                  <b-row class="mt-2 mb-5">
                    <b-col cols="1"></b-col>
                    <b-col>
                      <client-only>
                        <vue-slider v-model="sliderDates"
                          :enable-cross="false"
                          :min="sliderMinMax.min"
                          :max="sliderMinMax.max"
                          height="6px"
                          :tooltip="'always'"
                          :tooltip-placement="['bottom', 'bottom']"
                          :tooltip-formatter="dateFormatter">
                        </vue-slider>
                      </client-only>
                    </b-col>
                    <b-col cols="1"></b-col>
                  </b-row>
                  <p class="text-muted">Matches projects containing any activity between these dates.</p>
                </b-form-group>
              </form>
            </div>
          </b-sidebar>
        </b-col>
        <div class="col-md-3 text-center">
          <template v-if="preparingFile">
            <b-btn variant="secondary" class="float-md-right" id="download_excel" style="margin-top:4px;" @click="getActivitiesFile">
              <b-spinner label="Preparing" small></b-spinner> Preparing file...
            </b-btn>
          </template>
          <template v-else>
            <b-btn variant="primary" class="float-md-right" id="download_excel" href="#" style="margin-top:4px;" @click="getActivitiesFile">
              <font-awesome-icon :icon="['fas', 'download']" /> Export projects to Excel
            </b-btn>
          </template>
        </div>
      </b-row>
      <b-row>
        <b-col>
          <h2>{{ projects.length }} Projects</h2>
        </b-col>
      </b-row>
      <div class="row">
        <div class="col-md-12">
          <div id="projects-data">
            <b-table id="projectsList" :busy="isBusy"
              :fields="fields" :items="projects" show-empty
              :per-page="perPage"
              :current-page="currentPage"
              :filter="filterTitle"
              :filterIncludedFields="filterIncludedFields"
              sort-by="updated_date"
              :sort-desc="true"
              @filtered="onFiltered"
              responsive>

              <template v-slot:table-busy>
                <div class="text-center my-2">
                  <b-spinner class="align-middle" label="Loading..."></b-spinner>
                  <strong>Loading...</strong>
                </div>
              </template>

              <template v-slot:cell(title)="data">
                <nuxt-link :to="{ name: 'activities-id', params: { id: data.item.id}}">
                  {{ data.item.title }}
                </nuxt-link>
              </template>

              <template v-slot:cell(edit)="data">
                <nuxt-link :to="{ name: 'activities-id-edit', params: { id: data.item.id}}" v-if="data.item.permissions.edit">
                  <font-awesome-icon :icon="['fas', 'edit']" />
                </nuxt-link>
              </template>

              <template v-slot:cell(delete)="data">
                <b-link href="#" variant="link" class="text-danger"
                  @click="confirmDelete(data.item.id, data)"
                  v-if="data.item.permissions.edit">
                  <font-awesome-icon :icon="['fa', 'trash-alt']" />
                </b-link>
              </template>
            </b-table>
            <b-row>
              <b-col>
                <b-pagination
                  v-model="currentPage"
                  :total-rows="totalRows"
                  :per-page="perPage"
                  aria-controls="projectsList"
                ></b-pagination>
              </b-col>
              <b-col>
                <b-form-group
                  id="fieldset-1"
                  label="Projects per page"
                  label-cols-md="4"
                  label-align-md="right"
                  label-for="per-page">
                  <b-select v-model="perPage" :options="[20,50,100,500,1000]" id="per-page"></b-select>
                </b-form-group>
              </b-col>
            </b-row>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
<script>
// import component
import VueSlider from 'vue-slider-component/dist-css/vue-slider-component.umd.min.js'
import 'vue-slider-component/dist-css/vue-slider-component.css'
// import theme
import 'vue-slider-component/theme/default.css'
import { debounce } from 'vue-debounce'
import { mapGetters } from 'vuex'
import { saveAs } from 'file-saver'
import AggregatesBarChart from '~/components/Aggregates/BarChart.vue'
import AggregatesLineChart from '~/components/Aggregates/LineChart.vue'
// We use saveAs because we have token-based authentication so a normal
// link won't work.
export default {
  components: {
    VueSlider,
    AggregatesBarChart,
    AggregatesLineChart
  },
  props: ['type', 'label'],
  head() {
    return {
      title: this.aggregate.name ? `${this.label}: ${this.aggregate.name} | ${this.$config.title}` : `${this.label} | ${this.$config.title}`
    }
  },
  data() {
    return {
      aggregate: {
        name: null
      },
      selectedFY: '2020',
      fyOptions: [],
      slider: null,
      isBusy: true,
      perPage: 20,
      currentPage: 1,
      totalRows: 1,
      filters: [],
      filterTitle: null,
      filterIncludedFields: [],
      defaultFilters: {
      },
      selectedFilters: {
      },
      projects: [],
      fields: [],
      preparingFile: false,
      preparingSectorBriefFile: false,
      selectedPlannedActualDisbursements: 'Disbursements',
      plannedActualDisbursementsStacked: true,
      plannedActualDisbursementsStackedOptions: [
        {
          'value': true,
          'text': 'Area chart'
        },
        {
          'value': false,
          'text': 'Line chart'
        }
      ],
      plannedActualDisbursementOptions: [
        {
          'value': 'Disbursement Projection',
          'text': 'Projected Disbursements'
        },
        {
          'value': 'Disbursements',
          'text': 'Actual Disbursements'
        }
      ]
    }
  },
  mounted: function() {
    this.setupData()
  },
  watch: {
    sectorID: {
      handler() {
        this.getSector()
      }
    },
    selectedFilters: {
      deep: true,
      handler(oldValue, newValue) {
        if (this.isBusy == true) { return }
        this.updateRouter()
        this.queryProjectsData()
      }
    }
  },
  methods: {
    async setupData() {
      this.getFYs()
      this.setupFilters()
      this.setFiltersFromQuery()
      if (this.type == 'sectors') {
        this.getSector()
      } else if (this.type == 'donors') {
        this.getDonor()
      }
      this.queryProjectsData()
    },
    getFYs() {
      this.$axios
      .get(`filters/available_fys.json`)
      .then(response => {
        this.fyOptions = [{'value': null, 'text': 'All Fiscal Years'}].concat(response.data.fys)
        this.selectedFY = response.data.current_fy
      });
    },
    async getDonor() {
      await this.$axios
      .get(`codelists/organisations/donors/${this.aggFilterValue}.json`)
      .then(response => {
        this.aggregate = response.data.organisation
        this.selectedFilters['reporting_org_id'] = this.aggregate.id
        this.defaultFilters['reporting_org_id'] = this.aggregate.id
        this.selectedFilters['domestic_external'] = 'external'
        this.defaultFilters['domestic_external'] = 'external'
      })
    },
    async getSector() {
      await this.$axios
      .get(`codelists/mtef-sector/${this.sectorID}.json`)
      .then(response => {
        this.aggregate = response.data.code
        this.selectedFilters['mtef-sector'] = this.aggregate.id
        this.defaultFilters['mtef-sector'] = this.aggregate.id
        this.selectedFilters['domestic_external'] = 'external'
        this.defaultFilters['domestic_external'] = 'external'
      })
    },
    async getSectorBriefFile() {
      this.preparingSectorBriefFile = true
      await this.$axios({url: `sector-brief/${this.sectorID}.docx`,
        method: 'GET',
        responseType: 'blob'}).then(response => {
        if (response.status === 200) {
          saveAs(
            new Blob([response.data]),
            `${this.aggregate.name} Sector Brief.docx`
          )
        } else if (response.status === 500) {
          alert(
            'Sorry, there was an error, and your file could not be downloaded.'
          )
        }
      })
      this.preparingSectorBriefFile = false
    },
    async getActivitiesFile() {
      this.preparingFile = true
      await this.$axios({url: this.downloadURL,
        method: 'GET',
        responseType: 'blob'}).then(response => {
        if (response.status === 200) {
          saveAs(
            new Blob([response.data]),
            `export.xlsx`
          )
        } else if (response.status === 500) {
          alert(
            'Sorry, there was an error, and your file could not be downloaded.'
          )
        }
      })
      this.preparingFile = false
    },
    dateFormatter(value) {
      return new Date(value).toISOString().split("T")[0]
    },
    makeFields: function(projects) {
      var _fields = [
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
          sortable: true,
          tdClass: 'text-nowrap'
        }]

      var edit_permissions = projects.map(
          item =>  {
            return item.permissions.edit
          })

      if (edit_permissions.includes(true)) {
        _fields.push({
            key: 'edit',
            sortable: false
          })
        _fields.push({
            key: 'delete',
            sortable: false
          })
      }
      return _fields


    },
    confirmDelete(activity_id, data) {
      this.$bvModal.msgBoxConfirm('Are you sure you want to delete this activity? This action cannot be undone!', {
        title: 'Confirm delete',
        okVariant: 'danger',
        okTitle: 'Confirm delete',
        hideHeaderClose: false,
        centered: true
      })
      .then(value => {
        if (value) {
          this.$axios.post(`activities/${activity_id}/delete/`)
          .then(response => {
            /* Not quite sure why this is necessary... */
            const getIndex = (project => {
              return project.id == data.item.id
            })
            const index = this.projects.findIndex(getIndex)
            this.$delete(this.projects, index)
            this.$bvToast.toast('Your activity was successfully deleted.', {
              title: 'Deleted',
              autoHideDelay: 5000,
              variant: 'success',
              solid: true,
              appendToast: true
            })
          })
          .catch(error => {
            this.$bvToast.toast('Sorry, there was an error, and your activity could not be deleted.', {
              title: 'Error',
              autoHideDelay: 5000,
              variant: 'danger',
              solid: true,
              appendToast: true
            })
          })
        }
      })
    },
    setFiltersFromQuery() {
      if (Object.keys(this.$route.query).length == 0) { return }
      Object.entries(this.$route.query).forEach((k) => {
        if (['earliest_date', 'latest_date'].includes(k[0])) {
          this.$set(this.selectedFilters, k[0], new Date(k[1]))
        } else {
          this.$set(this.selectedFilters, k[0], k[1])
        }
      })
    },
    resetFilters: function() {
      Object.entries(this.selectedFilters).map(
        item =>  {
          if (item[0] != this.defaultFilters[item[0]]) {
            this.$set(this.selectedFilters, item[0], this.defaultFilters[item[0]])
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
    updateRouter() {
      if (this.type == 'sectors') {
        this.$router.push({ name: 'sectors-id', params: {id: this.sectorID}, query: this.nonDefaultFilters })
      } else if (this.type == 'donors') {
        this.$router.push({ name: 'donors-id', params: {id: this.aggFilterValue}, query: this.nonDefaultFilters })
      }
    },
    setupFilters() {
      this.$axios
        .get('activities/filters.json')
        .then(response => {
          response.data.filters.reduce(
            (obj, item) => {
              this.$set(this.defaultFilters, item.name, "all")
              if (!(item.name in this.selectedFilters)) {
                this.$set(this.selectedFilters, item.name, "all")
              }
            },
            {})
          this.filters = response.data.filters
          this.$set(this.defaultFilters, 'earliest_date', new Date(response.data.activity_dates.earliest))
          this.$set(this.defaultFilters, 'latest_date', new Date(response.data.activity_dates.latest))
          this.$set(this.selectedFilters, 'earliest_date', new Date(response.data.activity_dates.earliest))
          this.$set(this.selectedFilters, 'latest_date', new Date(response.data.activity_dates.latest))
        });
      },
    queryProjectsData: debounce(function (e) {
      this.$axios
        .get('activities/', {
          params: this.nonDefaultFilters
        })
        .then(response => {
          this.fields = this.makeFields(response.data.activities)
          this.projects = response.data.activities
          this.isBusy = false
          this.totalRows = this.projects.length
        })
    }, 500)
  },
  computed: {
    dimension() {
      if (this.type == 'sectors') {
        return 'reporting-org'
      } else if (this.type == 'donors') {
        return 'mtef-sector'
      }
    },
    dimensionLabel() {
      if (this.type == 'sectors') {
        return 'Donor'
      } else if (this.type == 'donors') {
        return 'Sector'
      }
    },
    aggFilter() {
      if (this.type == 'sectors') {
        return 'mtef-sector'
      } else if (this.type == 'donors') {
        return 'reporting-org'
      }
    },
    aggFilterValue() {
      return this.$route.params.id
    },
    sectorID() {
      return this.$route.params.id
    },
    downloadURL() {
      return `exports/activities_filtered.xlsx${this.filtersHash}`
    },
    earliestDateReadable() {
      return this.selectedFilters.earliest_date.toISOString().split("T")[0]
    },
    latestDateReadable() {
      return this.selectedFilters.latest_date.toISOString().split("T")[0]
    },
    activity_base_url() {
      return ''
    },
    sliderMinMax() {
      return {
        min: Number(this.defaultFilters.earliest_date),
        max: Number(this.defaultFilters.latest_date)
      }
    },
    sliderDates: {
     // getter
      get: function () {
        return [
          Number(this.selectedFilters.earliest_date),
          Number(this.selectedFilters.latest_date)
        ]
      },
      // setter
      set: function (newValue) {
        this.$set(this.selectedFilters, 'earliest_date', new Date(newValue[0]))
        this.$set(this.selectedFilters, 'latest_date', new Date(newValue[1]))
      }
    },
    nonDefaultFilters() {
      return Object.entries(this.selectedFilters).reduce(
        (obj, item, index) => {
          if (String(item[1]) != String(this.defaultFilters[item[0]])) {
            obj[item[0]] = item[1]
            if (['earliest_date', 'latest_date'].includes(item[0])) {
              obj[item[0]] = item[1].toISOString().split("T")[0]
            }
          }
          return obj
        },
      {})
    },
    displayResetFilters() {
      return Object.keys(this.nonDefaultFilters).length > 0
    },
    filtersHash() {
      const entries = Object.entries(this.nonDefaultFilters).reduce(
            (obj, item, index) => {
              obj.push(`${item[0]}=${item[1]}`)
              return obj
            },
        [])
      if (entries.length > 0) {
        return `?${entries.join("&")}`
      } else {
        return ``
      }
    },
    ...mapGetters(['isAuthenticated', 'loggedInUser'])
  }
}
</script>
