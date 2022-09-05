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
        <b-col md="3" class="text-center" v-if="(aggFilter=='mtef-sector') && isAuthenticated">
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
      <AggregatesTop :dimension="dimension" :dimension-label="dimensionLabel" :agg-filter="aggFilter" :agg-filter-value="aggFilterValue" />
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
                  :label-for="filter.name"
                  v-for="filter in filters"
                  v-bind:key="filter.name"
                  v-if="filter.name!=aggFilter">
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

import AggregatesTop from '~/components/AggregatesTop.vue'
import VueSlider from 'vue-slider-component/dist-css/vue-slider-component.umd.min.js'
import 'vue-slider-component/dist-css/vue-slider-component.css'
// import theme
import 'vue-slider-component/theme/default.css'
import { debounce } from 'vue-debounce'
import { mapGetters } from 'vuex'
import { saveAs } from 'file-saver'
// We use saveAs because we have token-based authentication so a normal
// link won't work.
export default {
  components: {
    VueSlider,
    AggregatesTop
  },
  props: ['aggFilter', 'label', 'aggFilterValue'],
  head() {
    return {
      title: this.title,
      meta: [
        { hid: 'twitter:title', name: 'twitter:title', content: this.title },
        { hid: 'og:title', name: 'og:title', content: this.title },
      ]
    }
  },
  data() {
    return {
      aggregate: {
        name: null
      },
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
      aggDefaultFilters: {
      },
      projects: [],
      fields: [],
      preparingFile: false,
      preparingSectorBriefFile: false,
    }
  },
  mounted: function() {
    this.setupData()
  },
  watch: {
    aggFilterValue: {
      handler() {
        this.getAggData()
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
      this.setupFilters()
      this.setFiltersFromQuery()
      await this.getAggData()
      this.queryProjectsData()
    },
    async getAggData() {
      if (this.aggFilter == 'mtef-sector') {
        await this.getSector()
        this.setAggDefaultFilters('mtef-sector')
      } else if (this.aggFilter == 'sdg-goals') {
        await this.getSector()
        this.setAggDefaultFilters('sdg-goals')
      } else if (this.aggFilter == 'papd-pillar') {
        await this.getSector()
        this.setAggDefaultFilters('papd-pillar')
      } else if (this.aggFilter == 'reporting-org') {
        await this.getDonor()
        this.setAggDefaultFilters('reporting_org_id')
      }
    },
    setAggDefaultFilters(_filter) {
      this.$set(this.selectedFilters, _filter, this.aggregate.id)
      this.$set(this.aggDefaultFilters, _filter, this.aggregate.id)
      this.$set(this.selectedFilters, 'domestic_external', 'external')
      this.$set(this.aggDefaultFilters, 'domestic_external', 'external')
    },
    async getDonor() {
      return await this.$axios
      .get(`codelists/organisations/donors/${this.aggFilterValue}.json`)
      .then(response => {
        this.aggregate = response.data.organisation
      })
    },
    async getSector() {
      return await this.$axios
      .get(`codelists/${this.aggFilter}/${this.aggFilterValue}.json`)
      .then(response => {
        this.aggregate = response.data.code
      })
    },
    async getSectorBriefFile() {
      this.preparingSectorBriefFile = true
      await this.$axios({url: `sector-brief/${this.aggFilterValue}.docx`,
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
    makeFields(projects) {
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
      }
      return _fields
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
      if (this.aggFilter == 'mtef-sector') {
        this.$router.push({ name: 'sectors-id', params: {id: this.aggFilterValue}, query: this.nonDefaultFilters })
      } else if (this.aggFilter == 'sdg-goals') {
        this.$router.push({ name: 'sdgs-id', params: {id: this.aggFilterValue}, query: this.nonDefaultFilters })
      } else if (this.aggFilter == 'reporting-org') {
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
    title() {
      return this.aggregate.name ? `${this.label}: ${this.aggregate.name} | ${this.$config.title}` : `${this.label} | ${this.$config.title}`
    },
    dimension() {
      if (this.aggFilter == 'reporting-org') {
        return 'mtef-sector'
      } else {
        return 'reporting-org'
      }
    },
    dimensionLabel() {
      if (this.aggFilter == 'reporting-org') {
        return 'Sector'
      } else {
        return 'Donor'
      }
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
