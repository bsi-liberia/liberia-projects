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
      <template v-if="Object.entries(summaryData).length>0">
        <LineChart
          :data="chartData"
          :options="lineChartOptions"
          class="line-chart"
          v-if="isBusy==false"
          ></LineChart>
      </template>
      <template v-else>
        <b-alert show variant="secondary" class="text-center">No data.</b-alert>
      </template>
    </template>
  </div>
</template>
<style scoped>
.line-chart {
  width: 100%;
  height: 400px;
}
#locationMap {
  height: 400px;
}
</style>
<script>
import LineChart from '~/components/charts/line-chart'

export default {
  data() {
    return {
      isBusy: true,
      data: [],
      labelField: "Sector",
      valueLabel: "Amount (USD mn)"
    }
  },
  props: ['fyOptions', 'valueField', 'stacked', 'dimension', 'agg-filter', 'agg-filter-value'],
  components: {
    LineChart
  },
  mounted: function() {
    this.loadData()
  },
  watch: {
  },
  computed: {
    lineChartOptions() {
      return {
        maintainAspectRatio: false,
        tooltips: {
          callbacks: {
            title: ((tooltipItem, data) => {
              return data.datasets[tooltipItem[0].datasetIndex].label
            }),
            footer: ((tooltipItem, data) => {
              return this.chartData.labels[tooltipItem[0].index]
            }),
            label: ((tooltipItem, data) => {
              var label = this.valueLabel + ': ' || '';
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
              stacked: this.stacked,
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
    years() {
      return this.fyOptions.filter(option => {
        return option.value != null
      }).map(option => {
        return String(option.value)
      })
    },
    yearsLabels() {
      return this.fyOptions.filter(option => {
        return option.value != null
      }).map(option => {
        return option.text
      })
    },
    summaryData() {
      /* Roll up by sector, with a list of years */
      const obj = this.data.reduce((summary, item) => {
        if (!(item.name in summary)) {
          summary[item.name] = this.years.reduce((yearsObj, year) => {
            yearsObj[year] = 0.0
            return yearsObj
          }, {})
        }
        /* We add the amount to the sector list */
        if (this.years.includes(item.fy)) {
          summary[item.name][item.fy] += item[this.valueField] / 1000000
        }
        return summary
      }, {})
      /* Sort by name of sector */
      return Object.keys(obj).sort().reduce((out, key) => {
        out[key] = obj[key]
        return out
      }, {})
    },
    chartData() {
      const colours = [ '#CF3D1E', '#F15623', '#F68B1F', '#FFC60B', '#DFCE21',
      '#BCD631', '#95C93D', '#48B85C', '#00833D', '#00B48D', '#60C4B1', '#27C4F4',
      '#478DCB', '#3E67B1', '#4251A3', '#59449B', '#6E3F7C', '#6A246D', '#8A4873',
      '#EB0080', '#EF58A0', '#C05A89']
      return {
        datasets: Object.entries(this.summaryData).map((sector, i) => {
          return {
            label: sector[0],
            fill: this.stacked,
            data: Object.values(sector[1]).map((ds) => { return ds }),
            backgroundColor: colours[i],
            borderColor: colours[i]
          }
        }),
        labels: this.yearsLabels,
      }
    }
  },
  methods: {
    async loadData() {
      const apiURL = `aggregates.json?dimension=${this.dimension}&filter=${this.aggFilter}&filter_value=${this.aggFilterValue}`
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