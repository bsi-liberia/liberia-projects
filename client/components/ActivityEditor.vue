<template>
  <div>
    <template v-if="isBusy">
      <b-row>
        <b-col class="text-center" v-if="isBusy" style="margin-bottom: 20px;">
          <b-spinner class="align-middle" label="Loading..."></b-spinner>
          <strong>Loading...</strong>
        </b-col>
      </b-row>
    </template>
    <template v-else>
      <b-row>
        <b-col sm="10">
          <h1 v-if="mode=='new'">New Activity<span v-if="activity">: {{ activity.title }}</span></h1>
          <h1 v-else >Edit activity<span v-if="activity">: {{ activity.title }}</span></h1>
        </b-col>
        <b-col sm="2">
          <b-btn variant="success" :to="{ name: 'activities-id', params: {id: activity.id }}" v-if="mode=='edit'">
            <font-awesome-icon :icon="['fa', 'save']" />
            Save and exit project
          </b-btn>
        </b-col>
      </b-row>
      <b-card no-body>
        <b-card-header>
          <b-nav tabs class="card-header-tabs">
            <b-nav-item :to="{query: {}}" :active="!('tab' in $route.query)">
              Basic
            </b-nav-item>
            <b-nav-item :to="{query: {'tab': 'sectors'}}"  :active="$route.query.tab === 'sectors'">
              Sectors
            </b-nav-item>
            <b-nav-item :to="{query: {'tab': 'locations'}}"  :active="$route.query.tab === 'locations'" v-if="mode=='edit'">
              Locations
            </b-nav-item>
            <b-nav-item :to="{query: {'tab': 'finances'}}"  :active="$route.query.tab === 'finances'" v-if="mode=='edit'">
              Finances
            </b-nav-item>
            <b-nav-item :to="{query: {'tab': 'conditions'}}"  :active="$route.query.tab === 'conditions'" v-if="mode=='edit'">
              Conditions
            </b-nav-item>
            <b-nav-item :to="{query: {'tab': 'milestones'}}"  :active="$route.query.tab === 'milestones'" v-if="(mode=='edit') && (activity.domestic_external=='domestic')">
              Milestones
            </b-nav-item>
            <b-nav-item :to="{query: {'tab': 'results'}}"  :active="$route.query.tab === 'results'" v-if="mode=='edit'">
              Results
            </b-nav-item>
            <b-nav-item :to="{query: {'tab': 'documents'}}"  :active="$route.query.tab === 'documents'" v-if="activity.documents">
              Documents
            </b-nav-item>
          </b-nav>
        </b-card-header>
        <div>
          <transition name="fade">
            <b-card-body v-show="!('tab' in $route.query)">
              <b-card-text class="activity-form-save form-horizontal">
                <activity-basic-section
                  :codelists="codelists"
                  :activity="activity"
                  :api_routes="api_routes"
                  :mode="mode"></activity-basic-section>
              </b-card-text>
            </b-card-body>
          </transition>
          <transition name="fade">
            <b-card-body v-show="$route.query.tab === 'sectors'">
              <b-card-text class="activity-form-save form-horizontal" id="sectors">
                <h2>Sectors</h2>
                <sectors-section
                  :codelists="codelists"
                  :activity.sync="activity"
                  :api_routes="api_routes"
                  :mode="mode"></sectors-section>
              </b-card-text>
            </b-card-body>
          </transition>
          <transition name="fade">
            <!-- Location data -->
            <b-card-body v-show="$route.query.tab === 'locations'" @click="showLocations+=1" v-if="mode=='edit'">
              <b-card-text id="location">
                <h2>Location data</h2>
                  <locations-section
                  :api_routes="api_routes"></locations-section>
              </b-card-text>
            </b-card-body>
          </transition>
          <transition name="fade">
            <!-- Financial data -->
            <b-card-body v-show="$route.query.tab === 'finances'" v-if="mode=='edit'">
              <b-card-text id="finances">
                <finances-section
                  :codelists="codelists"
                  :activity="activity"
                  :api_routes="api_routes"></finances-section>
              </b-card-text>
            </b-card-body>
          </transition>
          <transition name="fade">
            <b-card-body v-show="$route.query.tab === 'milestones'" v-if="(mode=='edit') && (activity.domestic_external=='domestic')">
              <b-card-text id="milestones">
                <h2>Milestones</h2>
                <div class="row">
                  <div class="col-md-12">
                    <milestones-section
                      :api_routes="api_routes"></milestones-section>
                  </div>
                </div>
              </b-card-text>
            </b-card-body>
          </transition>
          <template v-if="activity.id">
            <transition name="fade">
              <!-- Conditions data -->
              <b-card-body v-show="$route.query.tab === 'conditions'" v-if="mode=='edit'">
                  <b-card-text id="conditions">
                  <h3>Counterpart funding</h3>
                  <div class="alert alert-info">Enter how much counterpart funding is required for each year.
                  Enter a new row for each fiscal year that counterpart funding is required for.</div>
                  <div class="row">
                    <div class="col-md-12">
                      <counterpart-funding-section
                        :api_routes="api_routes"></counterpart-funding-section>
                    </div>
                  </div>
                </b-card-text>
              </b-card-body>
            </transition>
            <transition name="fade">
              <b-card-body v-show="$route.query.tab === 'documents'" v-if="activity.documents">
                <b-card-text id="documents">
                  <h2>Documents</h2>
                  <div class="alert alert-info">
                    These documents were automatically captured from <a :href="`http://d-portal.org/q.html?aid=${activity.code}`">this donor's IATI data</a>.
                  </div>
                  <documents-section
                    :api_routes="api_routes"></documents-section>
                </b-card-text>
              </b-card-body>
            </transition>
            <transition name="fade">
              <b-card-body v-show="$route.query.tab === 'results'" v-if="mode=='edit'">
                <b-card-text id="results">
                  <h3>Results</h3>
                  <b-btn variant="primary" :to="{ name: 'activities-id-results-design', params: {id: activity.id}}">
                    <font-awesome-icon :icon="['fa', 'magic']" /> Results designer</b-btn>
                  <b-btn variant="primary" :to="{ name: 'activities-id-results-data-entry', params: {id: activity.id}}" v-if="activity.results">
                    <font-awesome-icon :icon="['fa', 'clipboard-list']" /> Results data entry</b-btn>
                  <div class="row">
                    <div class="col-md-12">
                      <results-section
                        :api_routes="api_routes"></results-section>
                    </div>
                  </div>
                </b-card-text>
              </b-card-body>
            </transition>
          </template>
        </div>
      </b-card>
      <template v-if="mode == 'new'">
        <button type="submit" class="btn btn-success" id="add-activity-btn" v-if="mode=='new'" @click="saveNewActivity">
          Add activity; add detailed data &raquo;
        </button>
      </template>
    </template>
  </div>
</template>
<style scoped>
  .table span.form-control-feedback {
    top: 0;
  }
</style>
<script>
import Vue from 'vue'

import ActivityBasicSection from '~/components/ActivityEditor/activity-basic-section.vue'
import SectorsSection from '~/components/ActivityEditor/sectors-section.vue'
import FinancesSection from '~/components/ActivityEditor/finances-section.vue'
import MilestonesSection from '~/components/ActivityEditor/milestones-section.vue'
import LocationsSection from '~/components/ActivityEditor/locations-section.vue'
import CounterpartFundingSection from '~/components/ActivityEditor/counterpart-funding-section.vue'
import ResultsSection from '~/components/ActivityEditor/results-section.vue'
import DocumentsSection from '~/components/ActivityEditor/documents-section.vue'
import config from '~/nuxt.config'

export default {
  components: {
    ActivityBasicSection,
    SectorsSection,
    FinancesSection,
    MilestonesSection,
    LocationsSection,
    CounterpartFundingSection,
    ResultsSection,
    DocumentsSection
  },
  data() {
    return {
      isBusy: true,
      path: this.$route.path,
      showLocations: 0,
      activity: {},
      codelists: {
      }
    }
  },
  head() {
    return {
      title: this.mode == 'new' ? `New Activity | ${config.head.title}` : this.activity.title ? `Edit Activity: ${this.activity.title} | ${config.head.title}` : `Edit Activity | ${config.head.title}`
    }
  },
  mounted: function() {
    this.setupCodelists()
    this.getActivity()
    this.setView()
  },
  watch: {
    $route: {
      immediate: true,
      handler: function(newValue) {
        if (newValue.path === '/locations') {
          this.showLocations +=1
        }
      }
    }
  },
  computed: {
    api_routes() {
      return {
        activity: this.$route.params.id ? `activities/${this.$route.params.id}.json` : `activities/new.json`,
        activity_update: this.$route.params.id ? `activities/${this.$route.params.id}/edit/update_activity/` : `activities/new.json`,
        codelists: "codelists.json",
        milestones: `api_activity_milestones/${this.$route.params.id}/`,
        country_locations: `locations/LR/`,
        locations: `activity_locations/${this.$route.params.id}/`,
        finances: `activity_finances/${this.$route.params.id}/`,
        finances_update: `activity_finances/${this.$route.params.id}/update_finances/`,
        forwardspends: `activity_forwardspends/${this.$route.params.id}/`,
        counterpart_funding: `activity_counterpart_funding/${this.$route.params.id}/`,
        results: `activities/${this.$route.params.id}/results.json`,
        documents: `activities/${this.$route.params.id}/documents.json`,
        iati_search: `iati_search/`,
        iati_fetch_data: `iati_fetch_data/${this.$route.params.id}/`
      }
    },
    mode() {
      return this.$route.params.id ? 'edit' : 'new'
    }
  },
  methods: {
    setView() {
      if ('tab' in this.$route.query) {
        this.$router.push({query: {tab: this.$route.query.tab}})
      } else {
        this.$router.push({query: {}})
      }
    },
    setDocumentTitle: function() {
      if (this.mode == 'new') {
        document.title = "New activity | Liberia Project Dashboard"
      } else {
        document.title = `Edit activity ${this.activity.title} | Liberia Project Dashboard`
      }
    },
    async getActivity() {
      await this.$axios.get(this.api_routes.activity)
        .then(response => {
          this.activity = response.data.activity
          this.isBusy = false
        })
    },
    async setupCodelists() {
      await this.$axios.get(this.api_routes.codelists)
        .then(response => {
          this.codelists = response.data.codelists
          this.codelists.organisation = response.data.organisations
        })
    },
    saveNewActivity: function() {
      var errors = []
      if (["", undefined].includes(this.activity.title)) { errors.push("You must provide a title.") }
      if (this.activity.reporting_org_id == undefined) { errors.push("You must provide a reporting organisation.") }
      if (errors.length > 0) {
        errors.forEach(error => {
          this.$bvToast.toast(error, {
            title: 'Error',
            autoHideDelay: 5000,
            variant: 'danger',
            solid: true,
            appendToast: true
          })
        })
        return false
      }
      this.$axios.post(this.api_routes.activity_update, this.activity)
      .then(response => {
        this.activity = response.data
        this.$router.push({ name: 'activities-id-edit', params: {id: this.activity.id}})
        this.$root.$bvToast.toast(`Your activity was successfully created! You can continue adding more detailed information.`, {
          title: 'Activity created',
          autoHideDelay: 10000,
          solid: true,
          variant: 'success'
        })
      })
      .catch(error => {
        alert(error)
      })
    }
  }
}
</script>
