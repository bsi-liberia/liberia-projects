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
      <BarChart
        :data="chartData"
        :options="barChartOptions"
        class="bar-chart"
        v-if="isBusy==false"
        ></BarChart>
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
      valueField: "Disbursements",
      labelField: "Sector",
      valueLabel: "Amount (USD mn)"
    }
  },
  props: ['selectedFY'],
  components: {
    BarChart
  },
  mounted: function() {
    this.loadData()
  },
  watch: {
  },
  computed: {
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
      if (this.selectedFY == null) {
        return this.data
      }
      return this.data.filter(item => {
        return item.fy == this.selectedFY
      })
    },
    summaryData() {
      return Object.values(this.filteredData.reduce((summary, item) => {
        if (!(summary[item.name])) {
          summary[item.name] = {
            'Sector': item.name,
            'Disbursements': 0.0,
            'Disbursement Projection': 0.0
          }
        }
        summary[item.name].Disbursements += (item.Disbursements / 1000000)
        summary[item.name]['Disbursement Projection'] += (item['Disbursement Projection'] / 1000000)
        return summary
      }, {}))
      .sort((a,b) => a[this.labelField] > b[this.labelField] ? 1 : -1)
    },
    chartData() {
      const colours = [
        "#6e40aa", "#6849b9", "#6153c7", "#585fd2", "#4e6cda", "#4479df", "#3988e1", "#2f96e0", "#26a5db", "#1fb3d3", "#1bc1c8", "#19cdbb", "#1bd9ac", "#20e29d", "#28ea8d", "#34f07e", "#44f470", "#56f665", "#6bf75c", "#81f558",
        "#98f357", "#aff05b"
      ]
      return {
        datasets: [{
          label: 'Planned Disbursements',
          fill: true,
          data: this.summaryData.map((ds) => { return ds['Disbursement Projection'] }).slice(0,20),
          backgroundColor: colours[10]
        },
        {
          label: 'Actual Disbursements',
          fill: true,
          data: this.summaryData.map((ds) => { return ds['Disbursements'] }).slice(0,20),
          backgroundColor: colours[0]
        }],
        labels: this.summaryData.map((ds) => { return ds[this.labelField] }).slice(0,20),
      }
    }
  },
  methods: {
    async loadData() {
      await this.$axios.get(`sectors_C_D.json`)
      .then(response => {
        this.data = response.data.sectors
      })
      .finally(f=> {
        this.isBusy = false
      })
    }
  }
}
</script>