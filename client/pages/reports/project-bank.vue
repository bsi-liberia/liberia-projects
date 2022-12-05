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
        <b-col lg="12">
          <h1>Project Bank</h1>
          <p class="lead">This site shows projects which have been fully appraised by the Government of Liberia, but which are as yet unfunded.</p>
        </b-col>
      </b-row>
      <b-row>
        <b-col>
          <b-card-group columns>
            <b-card
              v-for="activity in activities"
              v-bind:key="activity.id"
              :title="activity.title">
              <b-card-text>
                <p>{{ activity.description }}</p>
                <b-btn
                  :to="{name: 'activities-id', params: { id: activity.id }}"
                  variant="primary">
                  View Project &raquo;
                </b-btn>
              </b-card-text>
            </b-card>
          </b-card-group>
        </b-col>
      </b-row>
    </template>
  </div>
</template>
<script>
export default {
  data() {
    return {
      activities: [],
      isBusy: true
    }
  },
  head() {
    return {
      title: `PSIP Project Bank | ${this.$config.title}`,
      meta: [
        { hid: 'twitter:title', name: 'twitter:title', content: `PSIP Project Bank | ${this.$config.title}` },
        { hid: 'og:title', name: 'og:title', content: `PSIP Project Bank | ${this.$config.title}` },
      ]
    }
  },
  mounted: function() {
    this.getReportData()
  },
  methods: {
    numberFormatter(value) {
      if (value == null) { return "" }
      return "$" + value.toLocaleString(undefined, {maximumFractionDigits: 0})
    },
    getReportData: function() {
      this.$axios
        .get(`activities/descriptions-objectives/?reporting_org_id=22&activity_status=1&domestic_external=domestic`)
        .then((response) => {
          this.activities = response.data.activities
          this.isBusy = false
        });
    }
  }
}
</script>
