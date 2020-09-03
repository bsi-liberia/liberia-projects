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
          <h1>PSIP disbursement tracking</h1>
          <p class="lead">Showing {{ activities.length }} PSIP activities with appropriations over
          USD 0 million. Appropriations and actual disbursements are restricted to amounts in {{ fy_text }} only.</p>
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
      <b-table class="table" :busy="isBusy" :fields="fields" :items="activities" sort-by="pct" :sort-desc="true" :tbody-tr-class="rowClass" responsive>
        <template v-slot:table-busy>
          <div class="text-center">
            <b-spinner class="align-middle" label="Loading..."></b-spinner>
            <strong>Loading...</strong>
          </div>
        </template>
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
        <template v-slot:cell(sum_appropriations)="data">
          {{ numberFormatter(data.item.sum_appropriations) }}
        </template>
        <template v-slot:cell(sum_allotments)="data">
          {{ numberFormatter(data.item.sum_allotments) }}
        </template>
        <template v-slot:cell(sum_disbursements)="data">
          {{ numberFormatter(data.item.sum_disbursements) }}
        </template>
        <template v-slot:cell(pct)="data">
          <template v-if="data.item.isTime">
            <b-progress :max="100" show-value variant="warning">
              <b-progress-bar :value="data.item.pct">
                {{ data.item.pct }}%
              </b-progress-bar>
            </b-progress>
          </template>
          <template v-else>
            <b-progress :max="100" show-value v-if="data.item.pct">
              <b-progress-bar :value="data.item.pct">
                {{ data.item.pct }}%
              </b-progress-bar>
            </b-progress>
          </template>
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
          sortable: true
        },
        {
          key: 'reporting_org_name',
          label: 'Reported by',
          sortable: true
        },
        {
          key: 'sum_appropriations',
          label: 'Appropriations',
          class: 'number',
          sortable: true
        },
        {
          key: 'sum_allotments',
          label: 'Allotments',
          class: 'number',
          sortable: true
        },
        {
          key: 'sum_disbursements',
          label: 'Actual Disbursements',
          class: 'number',
          sortable: true
        },
        {
          key: 'pct',
          label: '% Disbursed',
          class: 'number width-25pct',
          sortable: true
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
      title: `PSIP Disbursements | ${config.head.title}`
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
        .get(`disbursements/psip/`, {
          params: { fiscal_year: this.fiscalYear }
        })
        .then((response) => {
          var timeActivity = {
            title: `Rough expected disbursement, given ${response.data.days_since_fy_began} days since start of the fiscal year`,
            pct: response.data.progress_time,
            isTime: true
          }
          this.activities = response.data.activities
          this.activities.push(timeActivity)
          this.fiscalYears = response.data.fiscalYears
          this.fiscalYear = response.data.fiscalYear
          this.isBusy = false
        });
    }
  }
}
</script>
