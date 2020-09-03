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
      <b-form @submit.stop.prevent="saveResultsSubmitCheck" style="margin-bottom: 10px">
        <b-row lg="9">
          <b-col>
            <p class="lead">This interface allows you to provide results
              data for your activities. The indicators should be consistent
              with your project results framework.</p>
          </b-col>
          <b-col lg="3" class="text-right">
            <b-button type="submit" variant="primary" :disabled="saveDisabled"
              @click="save">
              <font-awesome-icon :icon="['fa', 'save']" /> Save
            </b-button>
            <b-button type="submit" variant="success" :disabled="saveDisabled"
              @click="saveSubmit">
              <font-awesome-icon :icon="['fa', 'lock']" /> Save and submit
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
                  <template>
                    {{ result.result_title }}
                  <b-badge>{{ result.result_type }}</b-badge>
                  </template>
                </h3>
              </template>
              <b-row>
                <b-col>
                  <b-row>
                    <b-col cols="2">
                      <b>Indicator title</b>
                    </b-col>
                    <b-col cols="8">
                      {{ result.indicator_title }}
                    </b-col>
                  </b-row>
                </b-col>
              </b-row>
              <b-row>
                <b-col lg="6">
                  <b-row>
                    <b-col cols="4">
                      <b>Measurement type</b>
                    </b-col>
                    <b-col cols="8">
                      {{ result.measurement_type }}
                    </b-col>
                  </b-row>
                </b-col>
                <b-col lg="6" v-if="result.measurement_type=='Number' && result.measurement_unit_type">
                  <b-row>
                    <b-col cols="4">
                      <b>Unit of measure</b>
                    </b-col>
                    <b-col cols="8">
                      {{ result.measurement_unit_type }}
                    </b-col>
                  </b-row>
                </b-col>
              </b-row>
              <b-row>
                <b-col lg="6">
                  <b-row>
                    <b-col cols="4">
                      <b>Baseline year</b>
                    </b-col>
                    <b-col cols="8">
                      {{ result.baseline_year }}
                    </b-col>
                  </b-row>
                </b-col>
                <b-col lg="6">
                  <b-row>
                    <b-col cols="4">
                      <b>Baseline value</b>
                    </b-col>
                    <b-col cols="8">
                      {{ result.baseline_value }}
                      <template v-if="result.measurement_type=='Percentage'">
                        %
                      </template>
                      <template v-else if="result.measurement_unit_type">
                        {{ result.measurement_unit_type }}
                      </template>
                    </b-col>
                  </b-row>
                </b-col>
              </b-row>
              <b-col>
                <hr />
              </b-col>
              <b-row>
                <b-col>
                  <h5>Reporting periods</h5>
                  <b-table :fields="periodFields"
                    :items="result.periods" responsive>
                    <template v-slot:cell(period_start)="data">
                        {{ data.item.period_start }}
                    </template>
                    <template v-slot:cell(period_end)="data">
                        {{ data.item.period_end }}
                    </template>
                    <template v-slot:cell(target_value)="data">
                      {{ data.item.target_value }}
                      <template v-if="result.measurement_type=='Percentage'">
                        %
                      </template>
                      <template v-else if="result.measurement_unit_type">
                        {{ result.measurement_unit_type }}
                      </template>
                    </template>
                    <template v-slot:cell(actual_value)="data">
                      <template v-if="data.item.status==4">
                        {{ data.item.actual_value }}
                        <template v-if="result.measurement_type=='Percentage'">
                          %
                        </template>
                        <template v-else if="result.measurement_unit_type">
                          {{ result.measurement_unit_type }}
                        </template>
                      </template>
                      <template v-else>
                        <b-input-group v-if="result.measurement_type == 'Number'" :append="result.measurement_unit_type">
                          <b-form-input type="number" class="form-control" :required="submitResults"
                            step="0.000001"
                            placeholder="Actual value" name="actual_value"
                            v-model="data.item.actual_value"
                            :disabled="data.item.open==false || data.item.status==4">
                          </b-form-input>
                        </b-input-group>
                        <b-input-group v-if="result.measurement_type == 'Percentage'" append="%">
                          <b-form-input type="number" class="form-control" required="submitResults"
                            step="0.000001"
                            placeholder="Actual value" name="actual_value"
                            v-model="data.item.actual_value"
                            :disabled="data.item.open==false || data.item.status==4">
                          </b-form-input>
                        </b-input-group>
                        <b-input-group v-if="result.measurement_type == 'Qualitative'">
                          <b-form-input type="text" class="form-control" required="submitResults"
                            placeholder="Actual value" name="actual_value"
                            v-model="data.item.actual_value"
                            :disabled="data.item.open==false || data.item.status==4">
                          </b-form-input>
                        </b-input-group>
                        <b-input-group v-if="result.measurement_type == 'Yes/No'">
                          <b-form-select :options="['Yes', 'No']" required="submitResults"
                            v-model="data.item.actual_value"
                            :disabled="data.item.open==false || data.item.status==4">
                          </b-form-select>
                        </b-input-group>
                      </template>
                    </template>
                    <template v-slot:cell(open)="data">
                      <template v-if="data.item.open==false && data.item.status==4">
                        <b-btn size="sm" variant="outline-success" disabled>
                          <font-awesome-icon :icon="['fa', 'lock']" /> Submitted
                        </b-btn>
                      </template>
                      <template v-else-if="data.item.open==false">
                        <b-btn size="sm" variant="outline-secondary" disabled>
                          <font-awesome-icon :icon="['fa', 'lock']" /> Not yet open
                        </b-btn>
                      </template>
                      <template v-else>
                        <b-form-group>
                          <b-form-radio-group
                            id="btn-radios-2"
                            v-model="data.item.status"
                            buttons
                            button-variant="outline-primary"
                            size="sm"
                            name="radio-btn-outline"
                            @change="checkRequiredField(result_index, data.index)"
                          >
                            <b-form-radio value="3">
                              <font-awesome-icon :icon="['fa', 'lock-open']" />
                              Draft
                            </b-form-radio>
                            <b-form-radio value="4">
                              <font-awesome-icon :icon="['fa', 'lock']" />
                              Submit
                            </b-form-radio>
                          </b-form-radio-group>
                        </b-form-group>
                      </template>
                    </template>
                  </b-table>
                </b-col>
              </b-row>
            </b-card>
          </template>
        </template>
      </b-form>
      <b-modal id="confirm-submit-modal" title="Confirm submit">
        <p>Would you like to submit all your results, or only
          those you have selected for submission?</p>
        <template v-slot:modal-footer="{ ok, cancel }">
          <!-- Emulate built in modal footer ok and cancel button actions -->
          <b-button variant="outline-success" @click="confirmSubmitAllResults">
            Submit all
          </b-button>
          <b-button variant="success" @click="confirmSubmitSelectedResults">
            Submit only selected
          </b-button>
          <b-button @click="cancel()">
            Cancel
          </b-button>
        </template>
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
      submitResults: false,
      activity_title: null,
      activity_id: this.$route.params.id,
      periodFields: []
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
    save() {
      this.submitResults = false;
    },
    saveSubmit() {
      this.submitResults = true
    },
    loadResults() {
      this.$axios
        .get(`activities/${this.activity_id}/results/data-entry.json`
          ).then(response => {
            this.results = response.data.results
            this.activity_title = response.data.activity_title
            this.periodFields = ['period_start', 'period_end', 'target_value', 'actual_value']
            this.periodFields.push({
              key: 'open',
              label: 'Submission Status'
            })
            this.isBusy = false
            this.saveDisabled = false
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
    checkRequiredField(result_id, period_id) {
      if (
          (this.results[result_id].periods[period_id].open == true) &&
          (this.results[result_id].periods[period_id].status == 4) &&
          (this.results[result_id].periods[period_id].actual_value==null)) {
        this.$bvModal.msgBoxOk('You have not entered a value for this field. Please enter a value.', {
            title: 'Warning',
            okVariant: 'danger',
        })
      }
    },
    saveResultsSubmitCheck() {
      if (this.submitResults == true) {
        this.$bvModal.show('confirm-submit-modal')
      } else {
        this.saveResults('save')
      }
      this.submitResults = false
    },
    confirmSubmitSelectedResults() {
      this.$bvModal.hide('confirm-submit-modal')
      this.saveResults('submitSelected')
    },
    confirmSubmitAllResults() {
      this.saveResults('submitAll')
      this.$bvModal.hide('confirm-submit-modal')
    },
    saveResults(saveType) {
      this.$axios
        .post(`activities/${this.activity_id}/results/data-entry.json`, {
            results: this.results,
            saveType: saveType
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
    }
  }
}
</script>