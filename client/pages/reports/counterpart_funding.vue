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
                <b-th colspan="5" class="text-center">Financial reporting for {{ fy_text }} only</b-th>
              </b-tr>
            </template>
            <template v-slot:cell(title)="data">
              <nuxt-link :to="{ name: 'activities-id', params: { id: data.item.id}}">{{ data.item.title }}</nuxt-link>
            </template>
          </b-table>
          <!--
            <th style="width:25%;" rowspan="2">Title</th>
            <th rowspan="2">Donor</th>
            <th rowspan="2">Ministry</th>
            <th colspan="2">Requested and planned expenditure for {{ fy }} only (USD)</th>
          -->
          <!--
          <table class="table" id="milestones">
            <thead>
              <tr>
                <th style="width:25%;" rowspan="2">Title</th>
                <th rowspan="2">Donor</th>
                <th rowspan="2">Ministry</th>
                <th colspan="2">Requested and planned expenditure for {{ fy }} only (USD)</th>
              </tr>
              <tr>
                <th class="number">GoL (requested)</th>
                <th class="number">Donor (planned)</th>
              </tr>
            </thead>
            <tbody>
              {% for activity in activities %}
              <tr>
                <td><a href="{{ url_for('activities.activity', activity_id=activity.id) }}">{{ activity.title }}</a></td>
                <td>{{ activity.reporting_org.name }}</td>
                <td>{% for ministry in activity.classification_data.get('aligned-ministry-agency', {}).get('entries', []) %}
                  {{ ministry.codelist_code.name }}
                {% endfor %}</td>
                <td class="number">{{ "{:,.2f}".format(activity._fy_counterpart_funding) }}</td>
                <td class="number">{{ "{:,.2f}".format(activity._fy_forwardspends) }}</td>
              </tr>
              {% endfor %}
            </tbody>
          </table>
          -->
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
          key: 'gol_requested',
          label: 'GoL (requested)',
          class: 'number',
          sortable: true
        },
        {
          key: 'donor_planned',
          label: 'Donor (planned)',
          class: 'number',
          sortable: true
        }
      ],
      activities: [],
      isBusy: true,
      fiscalYear: null,
      fiscalYears: []
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