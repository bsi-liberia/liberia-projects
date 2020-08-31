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
      <h1>Management Overview</h1>
      <p class="lead">This section provides a simple overview of activity on the Liberia Project Dashboard.
        It can be used to better understand data gaps and progress in data collection.</p>
      <b-row>
        <b-col>
          <h2>Data collection for the last four quarters</h2>
          <template v-if="isBusy">
            <b-spinner class="align-middle" label="Loading..."></b-spinner>
            <strong>Loading...</strong>
          </template>
          <template v-for="(quarter, key) in quarters" v-else>
            <h5>Disbursements data reported for {{ quarter }}</h5>
            <p>
              <b-progress :max="items[key].Total" show-value>
                <b-progress-bar :value="items[key].True">
                  {{ items[key].True }} out of {{ items[key].Total }}
                </b-progress-bar>
              </b-progress>
            </p>
          </template>
          <p class="text-muted">"Reported" is defined as any value reported within the relevant quarter. A total of 39 organisations are registered in the system to provide data.</p>
          <p>
            <b-btn variant="warning"
              :to="{ name: 'management-dataquality'}">
              <font-awesome-icon :icon="['fa', 'clipboard-list']" />
                See detailed breakdown by organisation
            </b-btn>
          </p>
        </b-col>
      </b-row>
    </template>
  </div>
</template>
<script>
export default {
  data() {
    return {
      items: [],
      quarters: [],
      isBusy: true,
    }
  },
  mounted: function() {
    this.getDataQualitySummary()
  },
  methods: {
    getDataQualitySummary: function() {
      this.$axios
        .get(`reporting_orgs/summary.json`)
        .then((response) => {
          this.quarters = response.data.list_of_quarters
          console.log(this.quarters)
          this.items = response.data.summary;
          console.log(this.items)
          this.isBusy = false
        });
    }
  }
}
</script>
