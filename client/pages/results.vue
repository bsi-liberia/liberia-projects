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
      <p class="lead">Please enter results data for the following activities.</p>
      <b-table class="table" :busy="isBusy" :fields="fields" :items="activities" sort-by="pct"
      :sort-desc="true" responsive>
        <template v-slot:table-busy>
          <div class="text-center">
            <b-spinner class="align-middle" label="Loading..."></b-spinner>
            <strong>Loading...</strong>
          </div>
        </template>
        <template v-slot:cell(title)="data">
            <nuxt-link :to="{ name: 'activities-id', params: { id: data.item.id}}">{{ data.item.title }}</nuxt-link>
        </template>
        <template v-slot:cell(url)="data">
          <b-btn variant="primary" :to="{ name: 'activities-id-results-design', params: { id: data.item.id}}"
            style="margin-bottom: 5px;"
            size="sm" v-if="data.item.permissions.data_design">
            <font-awesome-icon :icon="['fa', 'magic']" /> Design results
          </b-btn>
          <b-btn variant="primary" :to="{ name: 'activities-id-results-data-entry', params: { id: data.item.id}}"
            style="margin-bottom: 5px;"
            size="sm" v-if="data.item.permissions.data_entry">
            <font-awesome-icon :icon="['fa', 'clipboard-list']" /> Enter results
          </b-btn>
        </template>
        <template v-slot:cell(results_average)="data">
          <b-progress :max="100" show-value>
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
export default {
  data() {
    return {
      fields: [
        {
          key: 'title',
          label: 'Title',
          sortable: true,
          thStyle: "width: 40%;"
        },
        {
          key: 'funding_org',
          label: 'Funded by',
          sortable: true,
          thStyle: "width: 20%;"
        },
        {
          key: 'results_average',
          label: 'Progress',
          sortable: true,
          thStyle: "width: 20%;"
        },
        {
          key: 'url',
          label: 'Enter data',
          sortable: true,
          thStyle: "width: 20%;",
          tdClass: "number",
          thClass: "number"
        }
      ],
      activities: [],
      isBusy: true
    }
  },
  head() {
    return {
      title: `Results | ${this.$config.title}`
    }
  },
  mounted: function() {
    this.getResultsData()
  },
  methods: {
    getResultsData: function() {
      this.$axios
        .get(`user-results/`)
        .then((response) => {
          this.activities = response.data.activities
          this.isBusy = false
        });
    }
  }
}
</script>
