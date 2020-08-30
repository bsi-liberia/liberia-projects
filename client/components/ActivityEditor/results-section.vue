<template>
  <div>
    <b-table
    responsive
    :fields="resultsFields"
    :items="results">
      <template v-slot:cell(title)="data">
        {{ data.item.indicator_title }}
        <span v-if="data.item.measurement_unit_type">
          ({{ data.item.measurement_unit_type }})
        </span>
      </template>
      <template v-slot:cell(from)="data">
        {{ data.item.period_start }}
      </template>
      <template v-slot:cell(to)="data">
        {{ data.item.period_end }}
      </template>
      <template v-slot:cell(target)="data">
        {{ data.item.target_value }}
      </template>
      <template v-slot:cell(actual)="data">
        {{ data.item.actual_value }}
      </template>
      <template v-slot:cell(%)="data">
        <b-progress
          :value="data.item.percent_complete" max="100"
          :variant="data.item.percent_complete_category"
          show-progress
          v-if="data.item.percent_complete">
        </b-progress>
      </template>
    </b-table>
  </div>
</template>
<script>
import Vue from 'vue'
export default {
  data() {
    return {
      resultsFields: [
        {'key': 'title', 'label': 'Title'},
        {'key': 'from', 'label': 'From'},
        {'key': 'to', 'label': 'To'},
        {'key': 'target', 'label': 'Target'},
        {'key': 'actual', 'label': 'Actual'},
        {'key': '%', 'label': '%', 'thStyle': 'width: 30%'}
      ],
      results: []
    }
  },
  props: ["api_routes"],
  mounted: function() {
    this.setupResults()
  },
  methods: {
    async setupResults() {
      this.$axios
        .get(this.api_routes.results)
        .then((response) => {
          this.results = response.data.results.reduce((results, result) => {
            result.periods.forEach(period => {
              results.push({...period, ...result})
            })
            return results
          }, [])
        })
    }
  }
}
</script>