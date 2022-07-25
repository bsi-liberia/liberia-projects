<template>
  <div>
    <b-row>
      <b-col>
        <h2>Planned and Actual Disbursement by {{ dimensionLabel }}</h2>
        <client-only>
          <aggregates-bar-chart
            :selected-fy.sync="selectedFY"
            :fy-options="fyOptions"
            :dimension="dimension"
            :dimension-label="dimensionLabel"
            :agg-filter="aggFilter"
            :agg-filter-value="aggFilterValue"></aggregates-bar-chart>
        </client-only>
      </b-col>
    </b-row>
    <hr />
    <b-row>
      <b-col>
        <h2>Planned / Actual Disbursements by {{ dimensionLabel }}, over time</h2>
        <client-only>
          <aggregates-line-chart
            :fy-options="fyOptions"
            :dimension="dimension"
            :dimension-label="dimensionLabel"
            :agg-filter="aggFilter"
            :agg-filter-value="aggFilterValue"></aggregates-line-chart>
        </client-only>
      </b-col>
    </b-row>
  </div>
</template>
<script>
import AggregatesBarChart from '~/components/Aggregates/BarChart.vue'
import AggregatesLineChart from '~/components/Aggregates/LineChart.vue'
export default {
  components: {
    AggregatesBarChart,
    AggregatesLineChart
  },
  props: ['dimension', 'dimensionLabel', 'aggFilter', 'aggFilterValue'],
  data() {
    return {
      selectedFY: '2020',
      fyOptions: []
    }
  },
  mounted: function() {
    this.getFYs()
  },
  methods: {
    getFYs() {
      this.$axios
      .get(`filters/available_fys.json`)
      .then(response => {
        this.fyOptions = [{'value': null, 'text': 'All Fiscal Years'}].concat(response.data.fys)
        this.selectedFY = response.data.current_fy
      });
    },
  }
}
</script>