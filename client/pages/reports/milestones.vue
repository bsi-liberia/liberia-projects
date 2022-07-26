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
        <b-col lg="9">
          <h1>Project Development and Appraisal Tracking</h1>
          <p class="lead">The indicators show progress through the project development and appraisal process for {{ activities.length }} PSIP activities.</p>
          <p class="lead">Appropriations, allotment and actual disbursement columns are restricted to amounts in {{ fiscalYear }} only, and are generated automatically based on the latest available financial data.</p>
        </b-col>
        <b-col lg="3">
          <b-form-group label="Select fiscal year"
            label-class="font-weight-bold">
            <b-form-select :options="fiscalYears"
            v-model="fiscalYear">
            </b-form-select>
          </b-form-group>
        </b-col>
      </b-row>
      <b-table class="table" id="milestones" sort-by="Final Proposal"
          :items="activities" :fields="fields" :busy="isBusy" responsive>
        <template v-slot:table-busy>
          <div class="text-center">
            <b-spinner class="align-middle" label="Loading..."></b-spinner>
            <strong>Loading...</strong>
          </div>
        </template>
        <template v-slot:cell(title)="data">
          <nuxt-link :to="{ name: 'activities-id', params: { id: data.item.id}}">{{ data.item.title }}</nuxt-link>
        </template>
        <template v-slot:[`cell(${milestone})`]="data" v-for="(milestone, milestone_data) in milestones">
          <span :class="`text-${data.item[milestone].colour}`">
            <font-awesome-icon :icon="['fas', data.item[milestone].icon]" />
            <span class="sr-only">{{ data.item[milestone].status }}</span>
          </span>
        </template>
        <template v-slot:cell(appropriation)="data">
          <span v-if="data.item.sum_appropriations > 0" class="text-success">
            <font-awesome-icon :icon="['fas', 'check-circle']" />
            <span class="sr-only">True</span>
          </span>
          <span class="text-warning" v-else>
            <font-awesome-icon :icon="['fas', 'times-circle']" />
            <span class="sr-only">False</span>
          </span>
        </template>
        <template v-slot:cell(allotment)="data">
          <span class="text-success" v-if="data.item.sum_allotments > 0">
            <font-awesome-icon :icon="['fas', 'check-circle']" />
            <span class="sr-only">True</span>
          </span>
          <span class="text-warning" v-else>
            <font-awesome-icon :icon="['fas', 'times-circle']" />
            <span class="sr-only">False</span>
          </span>
        </template>
        <template v-slot:cell(disbursement)="data">
          <span class="text-success" v-if="data.item.sum_disbursements > 0">
            <font-awesome-icon :icon="['fas', 'check-circle']" />
              <span class="sr-only">True</span>
          </span>
          <span class="text-warning" v-else>
            <font-awesome-icon :icon="['fas', 'times-circle']" />
            <span class="sr-only">False</span>
          </span>
        </template>
      </b-table>
    </template>
  </div>
</template>
<script>
export default {
  data() {
    return {
      fields: [],
      activities: [],
      isBusy: true,
      fiscalYear: null,
      fiscalYears: [],
      milestones: []
    }
  },
  head() {
    return {
      title: `Project Development and Appraisal Tracking | ${this.$config.title}`,
      meta: [
        { hid: 'twitter:title', name: 'twitter:title', content: `Project Development and Appraisal Tracking | ${this.$config.title}` },
        { hid: 'og:title', name: 'og:title', content: `Project Development and Appraisal Tracking | ${this.$config.title}` },
      ]
    }
  },
  mounted: function() {
    this.getReportData()
  },
  watch: {
    fiscalYear: function() {
      this.getReportData()
    }
  },
  methods: {
    numberFormatter(value) {
      if (value == null) { return "" }
      return "$" + value.toLocaleString(undefined, {maximumFractionDigits: 0})
    },
    getReportData: function() {
      this.$axios
        .get(`reports/project-development-tracking/`, {
          params: { fiscal_year: this.fiscalYear }
        })
        .then((response) => {
          this.activities = response.data.activities
          this.milestones = response.data.milestones
          this.fields = [ "title", "implementer"].map(item=>
            { return { key: item, sortable: true }
            }).concat(
                ["First Draft", "Revised Draft Submitted",
            "Final Proposal"].map(item=>
            { return { key: item, sortable: true, variant: "light", class: "text-center" }
            })).concat(
                [{
                  'key': 'appropriation', 'label': 'Appropriation Made',
                  sortable: true, class: 'text-center'
                },
                {
                  'key': 'allotment', 'label': 'Allotment Made',
                  sortable: true, class: 'text-center'},
                {
                  'key': 'disbursement', 'label': 'Disbursement Made',
                  sortable: true, class: 'text-center'
                }])
          this.fiscalYears = response.data.fiscalYears
          this.isBusy = false
          this.fiscalYear = response.data.fiscalYear
        });
    }
  }
}
</script>