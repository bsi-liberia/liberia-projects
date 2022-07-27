<template>
  <div>
    <template v-if="isBusy">
      <b-row style="margin-bottom: 20px;">
        <b-col md="12" class="text-center">
          <b-spinner class="align-middle" label="Loading..."></b-spinner>
          <strong>Loading...</strong>
        </b-col>
      </b-row>
    </template>
    <template v-else>
      <b-row>
        <b-col md="6">
          <b-form-group
            label="Fiscal year"
            label-size="sm"
            label-align-sm="right"
            label-cols-sm="4">
            <b-select
              v-model="selectedFY"
              size="sm"
              :options="fyOptions"></b-select>
          </b-form-group>
        </b-col>
        <b-col md="6" class="text-md-right ml-auto">
          <b-form-group>
            <b-form-radio-group
              v-model="showChart"
              :options="showChartOptions"
              button-variant="outline-secondary"
              size="sm"
              class="w-100"
              name="radio-btn-outline"
              buttons></b-form-radio-group>
          </b-form-group>
        </b-col>
      </b-row>
      <client-only>
        <template v-if="showData">
          <template v-if="showChart">
            <BarChart
              :data="chartData"
              :options="barChartOptions"
              class="bar-chart"
              ></BarChart>
          </template>
          <template v-else>
            <b-table
              responsive
              :fields="dataFields"
              :items="summaryData" />
          </template>
        </template>
        <template v-else>
          <b-alert show variant="secondary" class="text-center">No data.</b-alert>
        </template>
      </client-only>
    </template>
  </div>
</template>
<style scoped>
.bar-chart {
  width: 100%;
  height: 400px;
}
#locationMap {
  height: 400px;
}
</style>
<script>
import BarChart from '~/components/charts/bar-chart'

export default {
  data() {
    return {
      isBusy: true,
      data: [],
      valueField: "Actual Disbursements",
      valueLabel: "Amount (USD mn)",
      showChart: true,
      showChartOptions: [
        {'text': 'Chart', value: true},
        {'text': 'Table', value: false}
      ]
    }
  },
  props: ['selected-fy', 'fy-options', 'dimension', 'dimension-label', 'agg-filter', 'agg-filter-value'],
  components: {
    BarChart
  },
  mounted: function() {
    this.loadData()
  },
  watch: {
  },
  computed: {
    selectedFY: {
      get() {
        return this.selectedFy
      },
      set(newValue) {
        this.$emit('update:selectedFy', newValue)
      }
    },
    showData() {
      return this.summaryData.length>0 && (this.totalDisbursements > 0 || this.totalDisbursementProjections > 0)
    },
    barChartOptions(){
      return {
        maintainAspectRatio: false,
        tooltips: {
          callbacks: {
            title: ((tooltipItem, data) => {
              return this.chartData.labels[tooltipItem[0].index]
            }),
            label: ((tooltipItem, data) => {
              var label = this.valueLabel || '';

              if (label) {
                  label += ': ';
              }
              label += tooltipItem.yLabel.toLocaleString(undefined, {
                maximumFractionDigits: 1,
                minimumFractionDigits: 1
              })
              return label;
            })
          }
        },
        scales: {
          yAxes: [
            {
              ticks: {
                beginAtZero: true,
                callback: function(tick) {
                  return tick.toLocaleString(undefined, {
                    maximumFractionDigits: 0,
                    minimumFractionDigits: 0
                  })
                }
              },
              scaleLabel: {
                display: true,
                labelString: this.valueLabel
              }
            }
          ],
          xAxes: [
            {
              ticks: {
                callback: function(tick) {
                  const characterLimit = 20
                  if (tick == undefined) { return "UNDEFINED" }
                  if (tick.length >= characterLimit) {
                    return (
                      tick
                        .slice(0, tick.length)
                        .substring(0, characterLimit - 1)
                        .trim() + '...'
                    )
                  }
                  return tick
                }
              }
            }
          ]
        }
      }
    },
    filteredData() {
      if (this.selectedFy == null) {
        return this.data
      }
      return this.data.filter(item => {
        return item.fy == this.selectedFy
      })
    },
    totalDisbursements() {
      return this.summaryData.reduce((summary, item)=> {
        summary += item['Actual Disbursements']
        return summary
      }, 0.00)
    },
    totalDisbursementProjections() {
      return this.summaryData.reduce((summary, item)=> {
        summary += item['Planned Disbursements']
        return summary
      }, 0.00)
    },
    dataFields(){
      return [
        {
          key: this.dimensionLabel,
          sortable: true
        },
        {
          key: 'Planned Disbursements',
          label: 'Planned Disbursements (USDm)',
          class: "number",
          sortable: true,
          formatter: value => {
            return value.toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2
            })
          }
        },
        {
          key: 'Actual Disbursements',
          label: 'Actual Disbursements (USDm)',
          class: "number",
          sortable: true,
          formatter: value => {
            return value.toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2
            })
          }
        }
      ]
    },
    summaryData() {
      return Object.values(this.filteredData.reduce((summary, item) => {
        if (!(summary[item.name])) {
          summary[item.name] = {
            'Actual Disbursements': 0.0,
            'Planned Disbursements': 0.0
          }
          summary[item.name][this.dimensionLabel] = item.name
        }
        summary[item.name]['Actual Disbursements'] += (item.Disbursements / 1000000)
        summary[item.name]['Planned Disbursements'] += (item['Disbursement Projection'] / 1000000)
        return summary
      }, {}))
      .sort((a,b) => a[this.dimensionLabel] > b[this.dimensionLabel] ? 1 : -1)
    },
    chartData() {
      const colours = [
        "#6e40aa", "#6849b9", "#6153c7", "#585fd2", "#4e6cda", "#4479df", "#3988e1", "#2f96e0", "#26a5db", "#1fb3d3", "#1bc1c8", "#19cdbb", "#1bd9ac", "#20e29d", "#28ea8d", "#34f07e", "#44f470", "#56f665", "#6bf75c", "#81f558",
        "#98f357", "#aff05b"
      ]
      const filterOutZero = this.summaryData.filter((ds) => {
        return ((ds['Planned Disbursements'] > 0 ) || (ds['Actual Disbursements'] > 0))
      })
      return {
        datasets: [{
          label: 'Planned Disbursements',
          fill: true,
          data: filterOutZero.map((ds) => { return ds['Planned Disbursements'] }),
          backgroundColor: colours[10]
        },
        {
          label: 'Actual Disbursements',
          fill: true,
          data: filterOutZero.map((ds) => { return ds['Actual Disbursements'] }),
          backgroundColor: colours[0]
        }],
        labels: filterOutZero.map((ds) => { return ds[this.dimensionLabel] }),
      }
    }
  },
  methods: {
    async loadData() {
      var apiURL = `aggregates.json?dimension=${this.dimension}`
      if (this.aggFilterValue != null) {
        apiURL += `&filter=${this.aggFilter}&filter_value=${this.aggFilterValue}`
      }
      await this.$axios.get(apiURL)
      .then(response => {
        this.data = response.data.entries
      })
      .finally(f=> {
        this.isBusy = false
      })
    }
  }
}
</script>