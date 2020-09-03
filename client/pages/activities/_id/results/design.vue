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
      <h1>Results<template v-if="activity_title"> for <nuxt-link :to="{ name: 'activities-id', params: {id: activity_id}}">{{ activity_title }}</nuxt-link></template></h1>
      <b-form @submit.stop.prevent="saveResults" style="margin-bottom: 10px">
        <b-row lg="10">
          <b-col>
            <p class="lead">This interface allows you to design results
              for your activities, copying from your existing results
              framework. For each indicator, depending on your
              results framework, you can optionally also disaggregate by
              reporting period (e.g. by year, by quarter).</p>
          </b-col>
          <b-col lg="2" class="text-right">
            <b-button type="submit" variant="primary" :disabled="saveDisabled">
              <font-awesome-icon :icon="['fa', 'save']" /> Save
            </b-button>
          </b-col>
        </b-row>
        <hr />
        <template v-if="isBusy">
          <b-row>
            <b-col class="text-center text-muted">
              <b-spinner class="align-middle" label="Loading..."></b-spinner>
              <strong>Loading...</strong>
            </b-col>
          </b-row>
        </template>
        <template v-else>
          <template v-for="result, result_index in results">
            <b-card v-bind="result" style="margin-bottom: 10px;">
              <template v-slot:header>
                <h3>
                  <template v-if="result.result_title">
                    {{ result.result_title }}
                  <b-badge>{{ result.result_type }}</b-badge>
                  </template>
                  <template v-else>
                    New result
                  </template>
                  <b-btn variant="danger" class="float-right"
                    size="sm"
                    @click.prevent="deleteResult(result_index)">
                    <font-awesome-icon :icon="['fa', 'trash']" /> Delete result
                  </b-btn>
                </h3>
              </template>
              <b-row>
                <b-col>
                  <b-form-group label="Result title" for="result_title"
                  label-cols="4" label-cols-lg="4" >
                    <b-form-input id="result_title" name="result_title"
                      placeholder="e.g. More health providers"
                      v-model="result.result_title" required>
                    </b-form-input>
                  </b-form-group>
                </b-col>
                <b-col>
                  <b-form-group label="Result type" for="result_type"
                  label-cols="4" label-cols-lg="4" >
                    <b-select class="form-control" id="result_type" required
                      v-model="result.result_type">
                      <option :value="null">Select result type</option>
                      <option value="Output">Output</option>
                      <option value="Outcome">Outcome</option>
                      <option value="Impact">Impact</option>
                    </b-select>
                  </b-form-group>
                </b-col>
              </b-row>
              <b-row>
                <b-col>
                  <b-form-group label="Indicator title" for="indicator_title"
                  label-cols="4" label-cols-lg="4" description="Can be the same as the result title.">
                    <b-form-input id="indicator_title" name="indicator_title"
                      placeholder="e.g. Number of health providers"
                      v-model="result.indicator_title" required>
                    </b-form-input>
                  </b-form-group>
                </b-col>
                <b-col></b-col>
              </b-row>
              <b-row>
                <b-col>
                  <b-form-group label="Measurement type" for="measurement_type"
                  label-cols="4" label-cols-lg="4">
                    <b-select class="form-control" id="measurement_type" required
                      v-model="result.measurement_type">
                      <option :value="null">Select indicator type</option>
                      <option value="Number">Number (or Unit)</option>
                      <option value="Yes/No">Yes/No</option>
                      <option value="Percentage">Percentage</option>
                      <option value="Qualitative">Qualitative</option>
                    </b-select>
                  </b-form-group>
                </b-col>
                <b-col>
                  <b-form-group
                    label="Unit of measure" for="measurement_unit_type" required
                    v-if="result.measurement_type=='Number'"
                    description="Optional"
                    label-cols="4" label-cols-lg="4" >
                    <b-form-input type="text" class="form-control"
                      placeholder="e.g. km" id="measurement_unit_type"
                      v-model="result.measurement_unit_type">
                    </b-form-input>
                  </b-form-group>
                </b-col>
              </b-row>
              <b-row>
                <b-col>
                  <b-form-group label="Baseline year" for="baseline_year"
                  label-cols="4" label-cols-lg="4" >
                    <b-form-input type="number" min="0" step="1"
                      class="form-control"
                      placeholder="e.g. 2018" id="baseline_year"
                      v-model="result.baseline_year">
                    </b-form-input>
                  </b-form-group>
                </b-col>
                <b-col>
                  <b-form-group label="Baseline value" for="baseline_value"
                  label-cols="4" label-cols-lg="4" >
                    <b-input-group v-if="result.measurement_type == 'Number'" :append="result.measurement_unit_type">
                      <b-form-input type="number" class="form-control" step="0.000001"
                        placeholder="e.g. 500" name="result.baseline_value"
                        v-model="result.baseline_value">
                      </b-form-input>
                    </b-input-group>
                    <b-input-group v-if="result.measurement_type == 'Percentage'" append="%">
                      <b-form-input type="number" class="form-control" step="0.000001"
                        placeholder="e.g. 500" name="result.baseline_value"
                        v-model="result.baseline_value">
                      </b-form-input>
                    </b-input-group>
                    <b-input-group v-if="result.measurement_type == 'Qualitative'">
                      <b-form-input type="text" class="form-control"
                        placeholder="e.g. 500" name="result.baseline_value"
                        v-model="result.baseline_value">
                      </b-form-input>
                    </b-input-group>
                    <b-input-group v-if="result.measurement_type == 'Yes/No'">
                      <b-form-select :options="['Yes', 'No']"
                        v-model="result.baseline_value">
                      </b-form-select>
                    </b-input-group>
                  </b-form-group>
                </b-col>
              </b-row>
              <b-col>
                <hr />
              </b-col>
              <b-row>
                <b-col>
                  <h5>Reporting periods</h5>
                  <b-table :fields="['period_start', 'period_end', 'target_value', 'status', 'delete']"
                    :items="result.periods">
                    <template v-slot:cell(period_start)="data">
                      <b-form-input type="date" class="form-control" required
                        placeholder="YYYY-MM-DD" name="period_start" v-model="data.item.period_start">
                      </b-form-input>
                    </template>
                    <template v-slot:cell(period_end)="data">
                      <b-form-input type="date" class="form-control" required
                        placeholder="YYYY-MM-DD" name="period_end" v-model="data.item.period_end">
                      </b-form-input>
                    </template>
                    <template v-slot:cell(target_value)="data">
                      <b-input-group v-if="result.measurement_type == 'Number'" :append="result.measurement_unit_type">
                        <b-form-input type="number" class="form-control" required
                          step="0.000001"
                          placeholder="Target value" name="target_value"
                          v-model="data.item.target_value">
                        </b-form-input>
                      </b-input-group>
                      <b-input-group v-if="result.measurement_type == 'Percentage'" append="%">
                        <b-form-input type="number" class="form-control" required
                          step="0.000001"
                          placeholder="Target value" name="target_value"
                          v-model="data.item.target_value">
                        </b-form-input>
                      </b-input-group>
                      <b-input-group v-if="result.measurement_type == 'Qualitative'">
                        <b-form-input type="text" class="form-control" required
                          placeholder="Target value" name="target_value"
                          v-model="data.item.target_value">
                        </b-form-input>
                      </b-input-group>
                      <b-input-group v-if="result.measurement_type == 'Yes/No'">
                        <b-form-select :options="['Yes', 'No']" required
                          v-model="data.item.target_value">
                        </b-form-select>
                      </b-input-group>
                    </template>
                    <template v-slot:cell(status)="data">
                      <b-form-checkbox switch value="4" unchecked-value="3" required
                        v-model="data.item.status">{{ statusSwitchText(data.item.status) }}</b-form-checkbox>
                    </template>
                    <template v-slot:cell(delete)="data">
                      <b-btn variant="link"
                        @click.prevent="deletePeriod(result_index, data.index)">
                        <span class="text-danger">
                          <font-awesome-icon :icon="['fa', 'trash']" />
                        </span>
                      </b-btn>
                    </template>
                  </b-table>
                  <b-btn @click.prevent="addPeriodRange(result_index)">
                    <font-awesome-icon :icon="['fa', 'plus']" />
                    Add range of reporting periods
                  </b-btn>
                  <b-btn @click.prevent="addPeriod(result_index)">
                    <font-awesome-icon :icon="['fa', 'plus']" />
                    Add reporting period
                  </b-btn>
                </b-col>
              </b-row>
            </b-card>
          </template>
          <b-row>
            <b-col>
              <p>
                <b-btn @click.prevent="addResult" :disabled="saveDisabled">
                  <font-awesome-icon :icon="['fa', 'plus']" />
                  Add result
                </b-btn>
              </p>
            </b-col>
          </b-row>
        </template>
      </b-form>
      <b-modal id="add-period-range-modal"
        title="Add range of reporting periods"
        @ok="processPeriodRange" ok-title="Add reporting periods"
        ok-variant="success" :ok-disabled="newRangeModal.fromDate>=newRangeModal.period_end">
        <b-form-group label="From Date">
          <b-form-input type="date" class="form-control" required
            placeholder="YYYY-MM-DD" name="period_start"
            v-model="newRangeModal.period_start">
          </b-form-input>
        </b-form-group>
        <b-form-group label="To Date">
          <b-form-input type="date" class="form-control" required
            placeholder="YYYY-MM-DD" name="period_end"
            v-model="newRangeModal.period_end">
          </b-form-input>
        </b-form-group>
        <b-form-group label="Frequency of reporting">
          <b-select :options="['Annually']"
            v-model="newRangeModal.frequency">
          </b-select>
        </b-form-group>
      </b-modal>
    </template>
  </div>
</template>
<script>
import config from '~/nuxt.config'
export default {
  data() {
    return {
      results: [],
      newRangeModal: {
        'period_start': '2018-07-01',
        'period_end': '2019-06-30',
        'frequency': 'Annually'
      },
      isBusy: true,
      saveDisabled: true,
      activity_id: this.$route.params.id,
      activity_title: null
    }
  },
  head() {
    return {
      title: this.activity_title ? `Results data entry: ${this.activity_title} | ${config.head.title}` : `Results data entry | ${config.head.title}`
    }
  },
  mounted: function() {
    this.loadResults()
  },
  methods: {
    statusSwitchText(value) {
      return {3: 'Unsubmitted', 4: 'Submitted'}[value]
    },
    loadResults() {
      this.$axios
        .get(`activities/${this.activity_id}/results/design.json`
          ).then(response => {
            this.results = response.data.results
            this.isBusy = false
            this.saveDisabled = false
            this.activity_title = response.data.activity_title
          }).catch(error => {
            if (error.response) {
              var msg = "Sorry, something went wrong with the server, and your results data could not be loaded. Try reloading the page."
            } else {
              var msg = "Sorry, it was not possible to communicate with the server, and your results could not be loaded. Try ensuring your internet connection is working."
            }
            this.$bvToast.toast(`${msg}`, {
              title: "Error",
              variant: "danger",
              solid: true,
              noAutoHide: true
            })
            this.isBusy = false
          })
    },
    saveResults() {
      this.$axios
        .post(`activities/${this.activity_id}/results/design.json`, {
            results: this.results
          }).then(response => {
            this.results = response.data.results
            this.$bvToast.toast(`Your results data has been saved.`, {
              title: "Successfully saved.",
              variant: "success"
            })
          }).catch(response => {
            this.$bvToast.toast(`Sorry, something went wrong, and your results data could not be saved.`, {
              title: "Error.",
              variant: "danger"
            })
          })
    },
    addResult(){
      this.results.push({
        result_title: null,
        result_type: null,
        indicator_title: null,
        baseline_year: null,
        baseline_value: null,
        measurement_type: null,
        measurement_unit_type: null,
        periods: []
      })
    },
    deleteResult(result_index) {
      var actuals = new Set(this.results[result_index].periods.map(item => {
        return item.actual_value
      }))
      if ((actuals.size > 0) && (!(actuals.has(null)) && (!(actuals.has(''))))) {
        console.log(actuals)
        this.$bvModal.msgBoxOk("Actually achieved data has already been entered for this indicator.", {
          title: 'Unable to delete',
          okVariant: 'danger',
          centered: true
        })
      } else {
        this.$bvModal.msgBoxConfirm('Are you sure you want to delete this result? This action cannot be undone!', {
          title: 'Confirm delete',
          okVariant: 'danger',
          okTitle: 'Confirm delete',
          hideHeaderClose: false,
          centered: true
          }
        ).then(value => {
          if (value) {
            this.$delete(this.results, result_index)
          }
        })
      }
    },
    processPeriodRange() {
      period_start = new Date(this.newRangeModal.period_start)
      period_end = new Date(this.newRangeModal.period_end)
      original_period_end = new Date(period_end.getTime()) // copy
      result_index = this.newRangeModal.result_index
      while(period_start.getFullYear() < original_period_end.getFullYear()) {
        var period_period_end = new Date(period_start.getTime())
        period_period_end.setFullYear(period_period_end.getFullYear()+1)
        period_period_end.setDate(period_period_end.getDate()-1)
        this.results[result_index].periods.push({
          'period_start': period_start.toISOString().slice(0,10),
          'period_end': period_period_end.toISOString().slice(0,10)
        })
        period_start.setFullYear(period_start.getFullYear() + 1)
      }
      if (period_start < original_period_end) {
        this.results[result_index].periods.push({
          'period_start': period_start.toISOString().slice(0,10),
          'period_end': original_period_end.toISOString().slice(0,10)
        })
      }
    },
    addPeriodRange(result_index) {
      this.newRangeModal.result_index = result_index
      this.$bvModal.show("add-period-range-modal")
    },
    addPeriod(result_index) {
      this.results[result_index].periods.push({})
    },
    deletePeriod(result_index, period_index) {
      var actuals = this.results[result_index].periods[period_index].actual_value
      if ((actuals != null) && (actuals != '')) {
        this.$bvModal.msgBoxOk("Actually achieved data has already been entered for this data collection period.", {
          title: 'Unable to delete',
          okVariant: 'danger',
          centered: true
        })
      } else {
        this.$bvModal.msgBoxConfirm('Are you sure you want to delete this period? This action cannot be undone!', {
          title: 'Confirm delete',
          okVariant: 'danger',
          okTitle: 'Confirm delete',
          centered: true
          }
        ).then(value => {
          if (value) {
            this.$delete(this.results[result_index].periods, period_index)
          }
        })
      }
    }
  }
}
</script>