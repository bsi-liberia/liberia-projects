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
          <h1>Counterpart funding</h1>
          <p class="lead">Activities with counterpart funding requirements for {{ fy_text }}. Only shows activities with planned expenditure or GoL counterpart funding requirements.</p>
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
      <b-row>
        <b-col md="12">
          <b-table
            :fields="fields"
            :items="activities"
            sort-by="gol_requested" :sort-desc="true">
            <template v-slot:thead-top="data">
              <b-tr>
                <b-th colspan="6" class="text-center">Financial reporting for {{ fy_text }} only</b-th>
              </b-tr>
            </template>
            <template v-slot:cell(title)="data">
              <template v-if="data.item.id">
                <nuxt-link :to="{ name: 'activities-id', params: { id: data.item.id}}">{{ data.item.title }}</nuxt-link>
              </template>
              <template v-else>
                {{ data.item.title }}
              </template>
            </template>
          </b-table>
        </b-col>
      </b-row>
    </template>
  </div>
</template>
<script>
export default {
  data() {
    return {
      fields: [
        {
          key: 'title',
          label: 'Title',
          sortable: true
        },
        {
          key: 'reporting_org_name',
          label: 'Donor',
          sortable: true
        },
        {
          key: 'ministry_name',
          label: 'Ministry',
          sortable: true
        },
        {
          key: 'sector_name',
          label: 'Sector',
          sortable: true
        },
        {
          key: 'gol_requested',
          label: 'GoL (requested)',
          class: 'number',
          sortable: true,
          formatter: this.numberFormatter
        },
        {
          key: 'donor_planned',
          label: 'Donor (planned)',
          class: 'number',
          sortable: true,
          formatter: this.numberFormatter
        }
      ],
      activities: [],
      isBusy: true,
      fiscalYear: null,
      fiscalYears: []
    }
  },
  head() {
    return {
      title: `Counterpart funding | ${this.$config.title}`
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
        .get(`reports/counterpart-funding/`, {
          params: { fiscal_year: this.fiscalYear }
        })
        .then((response) => {
          this.activities = response.data.activities
          this.fiscalYears = response.data.fiscalYears
          this.fiscalYear = response.data.fiscalYear
          this.isBusy = false
        });
    }
  }
}
</script>