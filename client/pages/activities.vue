<template>
  <div>
    <template v-if="isBusy">
      <div class="text-center my-2">
        <b-spinner class="align-middle" label="Loading..." variant="secondary"></b-spinner>
        <strong>Loading...</strong>
      </div>
    </template>
    <template v-else>
      <div class="row">
        <div class="col-md-10">
          <h1>Activities: <span id="activities_loading" v-if="isBusy">loading...</span><span id="activities_count" v-else>{{ projects.length }} found</span></h1>
        </div>
        <div class="col-md-2 text-center">
          <template v-if="loggedInUser.permissions_dict.edit != 'none' || loggedInUser.roles_list.contains('desk-officer')">
            <a class="btn btn-success btn-large float-md-right" :to="{name: 'activity_new'}">
              <font-awesome-icon :icon="['fas', 'plus']" />
              New activity
            </a>
          </template>
        </div>
      </div>
      <hr />
      <div class="row">
        <div class="col-md-9">
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
                  <b-select class="form-control filter-select" name="filter.name"
                    id="filter.name" :options="filter.codes" value-field="id" text-field="name"
                    v-model="selectedFilters[filter.name]" size="sm">
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
                      <vue-slider v-model="sliderDates"
                        :enable-cross="false"
                        :min="sliderMinMax.min"
                        :max="sliderMinMax.max"
                        height="6px"
                        :tooltip="'always'"
                        :tooltip-placement="['bottom', 'bottom']"
                        :tooltip-formatter="dateFormatter">
                      </vue-slider>
                    </b-col>
                    <b-col cols="1"></b-col>
                  </b-row>
                  <p class="text-muted">Matches projects containing any activity between these dates.</p>
                </b-form-group>
              </form>
            </div>
          </b-sidebar>
        </div>
        <div class="col-md-3 text-center">
          <a class="btn btn-primary float-md-right" id="download_excel" :to="'exports_all_activities_xlsx_filtered' + filtersHash" style="margin-top:4px;">
            <font-awesome-icon :icon="['fas', 'download']" /> Export selection to Excel
          </a>
        </div>
      </div>
      <div class="row mt-2 mb-3">
        <div class="col-md-9">
          <b-form-input type="search" placeholder="Type to search by project title..." v-model="filterTitle"></b-form-input>
        </div>
      </div>
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
                <a :href="activity_base_url + data.item.id + '/'">
                  {{ data.item.title }}
                </a>
              </template>

              <template v-slot:cell(edit)="data">
                <a :href="activity_base_url + data.item.id + '/edit/'" v-if="data.item.permissions.edit">
                  <font-awesome-icon :icon="['fas', 'edit']" /></a>
              </template>

              <template v-slot:cell(delete)="data">
                <a href="#" class="text-danger"
                  @click.prevent="confirmDelete(activity_base_url + data.item.id + '/delete/')"
                  v-if="data.item.permissions.edit">
                  <font-awesome-icon :icon="['fa', 'trash-alt']" />
                </a>
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
import Vue from 'vue'
// import component
import VueSlider from 'vue-slider-component/dist-css/vue-slider-component.umd.min.js'
import 'vue-slider-component/dist-css/vue-slider-component.css'
// import theme
import 'vue-slider-component/theme/default.css'
import { debounce } from 'vue-debounce'

import { mapGetters } from 'vuex'
import config from '../nuxt.config'

export default {
  components: {
    VueSlider
  },
  data() {
    return {
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
      fields: []
    }
  },
  mounted: function() {
    this.setupFilters()
    this.setFiltersFromQuery()
    this.queryProjectsData()
  },
  watch: {
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
    confirmDelete: function(delete_url) {
        this.$bvModal.msgBoxConfirm('Are you sure you want to delete this activity? This action cannot be undone!', {
          title: 'Confirm delete',
          okVariant: 'danger',
          okTitle: 'Confirm delete',
          hideHeaderClose: false,
          centered: true
        })
          .then(value => {
            if (value) {
              window.location = delete_url;
            }
          })
          .catch(err => {
            alert("Sorry, there was an error, and that activity couldn't be deleted.")
          })
    },
    setFiltersFromQuery() {
      if (Object.keys(this.$route.query).length == 0) { return }
      Object.entries(this.$route.query).forEach((k) => {
        if (['earliest_date', 'latest_date'].includes(k[0])) {
          Vue.set(this.selectedFilters, k[0], new Date(k[1]))
        } else {
          Vue.set(this.selectedFilters, k[0], k[1])
        }
      })
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
    updateRouter() {
      this.$router.push({ name: 'activities', query: this.nonDefaultFilters })
    },
    setupFilters() {
      this.$axios
        .get('activities/filters.json')
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
          Vue.set(this.defaultFilters, 'earliest_date', new Date(response.data.activity_dates.earliest))
          Vue.set(this.defaultFilters, 'latest_date', new Date(response.data.activity_dates.latest))
          Vue.set(this.selectedFilters, 'earliest_date', new Date(response.data.activity_dates.earliest))
          Vue.set(this.selectedFilters, 'latest_date', new Date(response.data.activity_dates.latest))
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
        Vue.set(this.selectedFilters, 'earliest_date', new Date(newValue[0]))
        Vue.set(this.selectedFilters, 'latest_date', new Date(newValue[1]))
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
      return Object.entries(this.nonDefaultFilters).reduce(
            (obj, item, index) => {
              if (index > 0) { obj += "&"}
              obj += `${item[0]}=${item[1]}`
              return obj
            },
        "?")
    },
    ...mapGetters(['isAuthenticated', 'loggedInUser'])
  }
}
</script>
