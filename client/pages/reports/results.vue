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
      <h1>Results</h1>
      <p class="lead">Showing {{ activities.length }} donor-funded activities with results data.</p>
      <b-alert show>Note: this page is a pilot, with limited data currently included. The results data for external projects is sourced from international sources.</b-alert>
      <b-table
        :fields="fields"
        :items="activities">
        <template v-slot:cell(title)="data">
          <nuxt-link :to="{ name: 'activities-id', params: { id: data.item.id}}">{{ data.item.title }}</nuxt-link>
        </template>
        <template v-slot:cell(reporting_org_name)="data">
          {{ data.item.reporting_org_name }}
        </template>
        <template v-slot:cell(results_average)="data">
          <b-progress :max="100" v-if="data.item.results_average">
            <b-progress-bar :value="data.item.results_average">
                {{ data.item.results_average }}%
            </b-progress-bar>
          </b-progress>
        </template>
      </b-table>
    </template>
  </div>
</template>
<script>
import config from '~/nuxt.config'
export default {
  data() {
    return {
      fields: [
        {
          key: 'title',
          label: 'Title',
          sortable: true,
          thStyle: 'width: 25%'
        },
        {
          key: 'reporting_org_name',
          label: 'Donor',
          sortable: true
        },
        {
          key: 'implementer_name',
          label: 'Implemented by',
          sortable: true
        },
        {
          key: 'results_average',
          label: 'Results (average)',
          thStyle: 'width: 25%'
        }
      ],
      activities: [],
      isBusy: true
    }
  },
  head() {
    return {
      title: `Results | ${config.head.title}`
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
  computed: {
    fy_text() {
      return `FY${this.fiscalYear.slice(-2)}`
    }
  },
  methods: {
    rowClass(item, type) {
      if (!item) return
      if (item.isTime) { return 'table-warning' }
    },
    numberFormatter(value) {
      if (value == null) { return "" }
      return "$" + value.toLocaleString(undefined, {maximumFractionDigits: 0})
    },
    getReportData: function() {
      this.$axios
        .get(`reports/results/`)
        .then((response) => {
          this.activities = response.data.activities
          this.isBusy = false
        });
    }
  }
}
</script>