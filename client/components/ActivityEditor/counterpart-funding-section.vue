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
      <b-table
        :items="counterpartFundingBreakdownItems"
        :fields="counterpartFundingBreakdownFields"
        >
        <template v-slot:[slotData[0]]="data" v-for="slotData in counterpartFundingYearSlots">
          <finances-input
            :transaction="data"
            type="number"
            :name="slotData[1]"
            placeholder="e.g. 1,000,000"
            currency="USD"
            :value.sync="data.item.values[slotData[1]]">
          </finances-input>
        </template>
      </b-table>
      <b-alert variant="warning" show>Want to provide a breakdown by
      type of counterpart funding or by year?<br />
        <b-btn variant="warning" @click="configureCounterpartFunding"
          size="sm">
          <font-awesome-icon :icon="['fa', 'cog']" />
          Configure this form
        </b-btn>
      </b-alert>
      <b-modal
        id="configure-counterpart-funding"
        title="Configure counterpart funding form"
        size="lg">
        <b-row>
          <b-col>
            <h4>Show fiscal years</h4>
            <b-form-group
              label="Fiscal Year">
              <b-form-checkbox-group
                v-model="selectedYears"
                :options="years"
                stacked>
              </b-form-checkbox-group>
            </b-form-group>
          </b-col>
          <b-col>
            <h4>Show breakdown</h4>
            <b-form-group
              label="Type of counterpart funding">
              <b-form-checkbox-group
                v-model="selectedCounterpartFundingTypes"
                :options="counterpartFundingTypes"
                stacked>
              </b-form-checkbox-group>
            </b-form-group>
          </b-col>
        </b-row>
      </b-modal>
    </template>
  </div>
</template>
<style scoped>
.input-group-text {
  padding: 0.375rem 0.25rem;
}
</style>
<script>
import FinancesSelect from './subcomponents/finances-select.vue'
import FinancesInput from './subcomponents/finances-input.vue'
import FinancesCheckbox from './subcomponents/finances-checkbox.vue'
export default {
  data() {
    return {
      isBusy: true,
      fields: [
        {'key': 'amount', 'label': 'Total Amount'}
      ],
      selectedYears: [],
      years: [],
      counterpartFunding: [],
      selectedCounterpartFundingTypes: [],
      counterpartFundingTypes: [
        {
          'value': 'rap',
          'text': 'RAP'
        },
        {
          'value': 'bank-charges',
          'text': 'Bank Charges'
        },
        {
          'value': 'reimbursement',
          'text': 'Reimbursement'
        },
        {
          'value': 'in-kind',
          'text': 'In Kind'
        },
        {
          'value': 'other',
          'text': 'Other'
        }
      ]
    }
  },
  components: {
    FinancesSelect,
    FinancesInput,
    FinancesCheckbox
  },
  props: ["api_routes"],
  mounted: function() {
    this.setupCounterpartFunding()
  },
  provide: function () {
    return {
      updateFinances: this.updateCounterpartFunding
    }
  },
  computed: {
    counterpartFundingDataObject() {
      return this.counterpartFunding.reduce((summary, item) => {
        if (!(item.year in summary)) {
          summary[item.year] = {}
        }
        summary[item.year][item.type] = item.required_value
        return summary
      }, {})
    },
    counterpartFundingTypesObject() {
      return this.counterpartFundingTypes.reduce((summary, item) => {
        summary[item.value] = item.text
        return summary
      }, {})
    },
    counterpartFundingBreakdownItems() {
      const rows = this.selectedCounterpartFundingTypes.reduce((summary, type) => {
        summary.push({
          field: this.counterpartFundingTypesObject[type],
          type: type
        })
        return summary
        },
        [{
          field: 'Total',
          type: 'total',
        }]
      )
      const getRowTotalValue = row => {
        if (this.counterpartFundingDataObject['total'] && this.counterpartFundingDataObject['total'][row.type]) {
          return this.counterpartFundingDataObject['total'][row.type]
        } else {
          return 0.0
        }
      }
      return rows.map(row => {
        row.values = this.selectedYears.reduce((summary, year) => {
          if (this.counterpartFundingDataObject[year] && this.counterpartFundingDataObject[year][row.type]) {
            summary[year] = this.counterpartFundingDataObject[year][row.type]
          } else {
            summary[year] = 0.0
          }
          return summary
          }, {
          total: getRowTotalValue(row)
        })
        return row
      })
    },
    counterpartFundingBreakdownFields() {
      return [
        {
          'key': 'field',
          'label': ''
        },
        {
          'key': 'total',
          'label': 'Total (all years)'
        },...this.selectedYears
      ]
    },
    counterpartFundingYearSlots() {
      return this.selectedYears.reduce((summary, item) => {
        summary.push([`cell(${item})`, item])
        return summary
        },
        [['cell(total)', 'total']]
      )
    }
  },
  methods: {
    configureCounterpartFunding() {
      this.$bvModal.show('configure-counterpart-funding')
    },
    setupCounterpartFunding(data) {
      this.$axios.get(this.api_routes.counterpart_funding)
        .then(res => {
          this.counterpartFunding = res.data.counterpart_funding
          this.counterpartFunding.forEach(item => {
            if (!this.selectedYears.includes(item.year)) {
              if (item.year != 'total') {
                this.selectedYears.push(item.year)
              }
            }
            if (!this.selectedCounterpartFundingTypes.includes(item.type)) {
              if (item.type != 'total') {
                this.selectedCounterpartFundingTypes.push(item.type)
              }
            }
          })
          this.years = res.data.fiscal_years.map(fy => {
            return {
              'id': fy,
              'name': fy,
              'value': fy,
              'text': fy
            }
          })
          this.isBusy = false
      });
    },
    addCounterpartFunding() {
      var required_value = 0.0
      var available_fys = this.counterpartFunding.map(cF => {
        return cF.required_fy
      })
      if (available_fys.length > 0) {
        var required_fy = Math.max.apply(Math, available_fys)+1
      } else {
        var required_fy = (new Date).getFullYear();
      }
      this.$axios.post(this.api_routes.counterpart_funding, {
        "required_value": required_value,
        "required_fy": required_fy,
        "action": "add"
      })
      .then(response => {
        this.counterpartFunding.push(response.data.counterpart_funding)
      })
    },
    deleteCounterpartFunding(yearType, deletedItems) {
      if (deletedItems.length > 0) {
        this.$bvModal.msgBoxConfirm(`Are you sure you want to delete counterpart funding data for the ${yearType} ${deletedItems.join()}? This action cannot be undone.`, {
          title: 'Confirm delete',
          okVariant: 'danger',
          okTitle: 'Confirm delete',
          hideHeaderClose: false,
          centered: true
        })
          .then(value => {
            if (value) {
              if (yearType == 'year') {
                this.$axios.post(this.api_routes.counterpart_funding, {
                  "year": deletedItems[0],
                  "action": "delete"
                })
                this.counterpartFunding.forEach((item, index) => {
                  if (item.year == deletedItems[0]) {
                    this.$delete(this.counterpartFunding, index)
                  }
                })
              } else if (yearType == 'type') {
                this.$axios.post(this.api_routes.counterpart_funding, {
                  "type": deletedItems[0],
                  "action": "delete"
                })
                this.counterpartFunding.forEach((item, index) => {
                  if (item.type == deletedItems[0]) {
                    this.$delete(this.counterpartFunding, index)
                  }
                })
              }
            } else {
              if (yearType == 'year') {
                deletedItems.forEach(item => {
                  this.selectedYears.push(item)
                })
              } else if (yearType == 'type') {
                deletedItems.forEach(item => {
                  this.selectedCounterpartFundingTypes.push(item)
                })
              }
            }
          })
          .catch(err => {
            alert("Sorry, there was an error, and that counterpart funding entry couldn't be deleted.")
          })
      }
    },
    updateCounterpartFunding(_this, data, year, value, oldValue) {
      var postdata = {
        type: data.item.type,
        year: year,
        value: value,
        action: 'update'
      }
      this.$axios.post(this.api_routes.counterpart_funding, postdata)
      .then(response => {
        _this.validation = true
      })
      .catch(error => {
        _this.validation = false
      })
    }
  },
  watch: {
    selectedYears(newValue, oldValue) {
      const deletedItems = oldValue.filter(item => { return !newValue.includes(item) })
      this.deleteCounterpartFunding('year', deletedItems)
    },
    selectedCounterpartFundingTypes(newValue, oldValue) {
      const deletedItems = oldValue.filter(item => { return !newValue.includes(item) })
      this.deleteCounterpartFunding('type', deletedItems)
    }
  }
}
</script>