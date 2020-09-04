<template>
  <div>
    <b-row class="nopadding">
      <b-col class="intro-message text-center">
        <h1>Tracking development<br />
          across Liberia</h1>
      </b-col>
    </b-row>
    <b-container>
      <b-row class="mt-5">
        <b-col>
          <h2>Activity locations</h2>
          <client-only>
            <home-map id="locationMap"></home-map>
          </client-only>
        </b-col>
      </b-row>
      <b-row class="mt-3 mb-3">
        <b-col><hr />
        </b-col>
      </b-row>
      <b-row>
        <b-col>
          <h2>Planned and Actual Disbursements by Sector</h2>
          <b-row>
            <b-col md="6">
              <b-form-group
                label="Fiscal year"
                label-align="right"
                label-cols-sm="3">
                <b-select v-model="selectedFY"
                :options="fyOptions"></b-select>
              </b-form-group>
            </b-col>
          </b-row>
          <client-only>
            <home-bar-chart :selected-fy="selectedFY"></home-bar-chart>
          </client-only>
        </b-col>
      </b-row>
      <b-row class="mt-3 mb-3">
        <b-col><hr />
        </b-col>
      </b-row>
      <b-row>
        <b-col>
          <h2>Planned / Actual Disbursements by Sector, over time</h2>
          <b-row class="mb-2">
            <b-col md="6" class="mt-1">
              <b-form-radio-group
                v-model="selectedPlannedActualDisbursements"
                :options="plannedActualDisbursementOptions"
                button-variant="outline-primary"
                buttons
                size="sm"
              ></b-form-radio-group>
            </b-col>
            <b-col md="6" class="text-md-right mt-1">
              <b-form-radio-group
                v-model="plannedActualDisbursementsStacked"
                :options="plannedActualDisbursementsStackedOptions"
                button-variant="outline-secondary"
                buttons
                size="sm"
              ></b-form-radio-group>
            </b-col>
          </b-row>
          <client-only>
            <home-line-chart
              :value-field="selectedPlannedActualDisbursements"
              :fy-options="fyOptions" :stacked="plannedActualDisbursementsStacked"></home-line-chart>
          </client-only>
        </b-col>
      </b-row>
    </b-container>
  </div>
</template>
<style scoped>
.nopadding {
  margin-right: 0px;
}
.nopadding .col {
  padding-right: 0px;
}
.intro-message {
  background: #313578;
    background: -moz-linear-gradient(45deg,#313578 0%,#666666 100%);
    background: -webkit-gradient(linear,left bottom,right top,color-stop(0%,#313578),color-stop(100%,#666666));
    background: -webkit-linear-gradient(45deg,#313578 0%,#666666 100%);
    background: -o-linear-gradient(45deg,#313578 0%,#666666 100%);
    background: -ms-linear-gradient(45deg,#313578 0%,#666666 100%);
    background: linear-gradient(45deg, #313578 0%, #666666 100%) repeat scroll 0 0 transparent;
    filter: progid:DXImageTransform.Microsoft.gradient(startColorstr='#313578',endColorstr='#666666',GradientType=1);
    -webkit-box-shadow: inset 0 3px 7px rgba(0,0,0,.2),inset 0 -3px 7px rgba(0,0,0,.2);
    -moz-box-shadow: inset 0 3px 7px rgba(0,0,0,.2),inset 0 -3px 7px rgba(0,0,0,.2);
    box-shadow: inset 0 3px 7px rgba(0,0,0,.2),inset 0 -3px 7px rgba(0,0,0,.2);
    padding: 80px 0 60px;
    margin-top: none;
    color: #ffffff;
}
.intro-message h1 {
    color: #ffffff;
    font-size: 50px;
    text-shadow: 1px 1px 2px #333333;
}
.intro #locationMap {
  width: 100%;
  height: 400px;
}
</style>
<script>
import HomeMap from '~/components/Home/Map.vue'
import HomeBarChart from '~/components/Home/BarChart.vue'
import HomeLineChart from '~/components/Home/LineChart.vue'
export default {
  data() {
    return {
      isBusy: true,
      selectedFY: '2019',
      fyOptions: [],
      selectedPlannedActualDisbursements: 'Disbursements',
      plannedActualDisbursementsStacked: true,
      plannedActualDisbursementsStackedOptions: [
        {
          'value': true,
          'text': 'Area chart'
        },
        {
          'value': false,
          'text': 'Line chart'
        }
      ],
      plannedActualDisbursementOptions: [
        {
          'value': 'Disbursements',
          'text': 'Actual Disbursements'
        },
        {
          'value': 'Disbursement Projection',
          'text': 'Planned Disbursements'
        }
      ]
    }
  },
  components: {
    HomeMap,
    HomeBarChart,
    HomeLineChart
  },
  mounted: function() {
    this.getFYs()
  },
  watch: {
  },
  methods: {
    getFYs() {
      this.$axios
      .get(`filters/available_fys.json`)
      .then(response => {
        this.fyOptions = [{'value': null, 'text': 'All Fiscal Years'}].concat(response.data.fys)
        this.selectedFY = response.data.current_fy
      });
    }
  }
}
</script>