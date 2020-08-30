<template>
  <div>
    <b-row>
      <b-col sm="9">
        <h2>Financial data</h2>
      </b-col>
      <b-col sm="3" class="text-right">
        <b-dropdown id="dropdown-form" text="Show/hide columns" ref="dropdown" right size="sm">
          <b-dropdown-form>
            <b-form-group label="Display the following columns">
              <b-form-checkbox-group
                :options="optionalSelectableFields"
                v-model="optionalSelectedFields"
              ></b-form-checkbox-group>
            </b-form-group>
          </b-dropdown-form>
        </b-dropdown>
      </b-col>
    </b-row>
    <div role="tablist">
      <finances-subsection
        :finances-fields="financesFields"
        transaction-type="C"
        transaction-type-long="commitments"
        :title="commitmentsOrAppropriations"
        :add-label="'Add ' + commitmentsOrAppropriations"
        :fund-sources="fundSources"
        :api_routes="api_routes"
        :codelists="codelists"
      ></finances-subsection>
      <finances-subsection
        v-if="activity.domestic_external=='domestic'"
        :finances-fields="financesFields"
        transaction-type="99-A"
        transaction-type-long="allotments"
        title="Allotments"
        add-label="Add allotment"
        :fund-sources="fundSources"
        :api_routes="api_routes"
        :codelists="codelists"
      ></finances-subsection>
      <finances-subsection
        :finances-fields="financesFields"
        transaction-type="D"
        transaction-type-long="disbursements"
        title="Disbursements"
        add-label="Add disbursement"
        :fund-sources="fundSources"
        :api_routes="api_routes"
        :codelists="codelists"
      ></finances-subsection>
      <b-card no-body class="mb-1">
        <b-card-header header-tag="header" role="tab">
          <b v-b-toggle.collapse-forwardspends>Forward spending plans</b>
        </b-card-header>
        <b-collapse id="collapse-forwardspends" visible role="tabpanel">
          <b-card-body>
            <b-card-text>
              <div class="row">
                <div class="col-sm-12">
                  <p class="lead">This project starts on <em>{{ activity.start_date }}</em>
                  and ends on <em>{{ activity.end_date }}</em>. Please provide
                  forward spend projections by quarter for the lifetime of this project.</p>
                  <p class="lead">To provide forward spend projections for earlier or later dates,
                  adjust the project start and end dates and new rows will automatically be created below.</p>
                  <p class="lead">Currency: <b>USD</b></p>
                  <b-table :fields="forwardspendFields" :items="forwardspends">
                    <template v-slot:cell(year)="data">
                      <b-form-group>
                        <b-input plaintext :value="data.item.year"></b-input>
                      </b-form-group>
                    </template>
                    <template v-slot:cell(Q1)="data">
                      <forwardspends-quarter
                        quarter="Q1" :data="data"
                        :api_routes="api_routes">
                      </forwardspends-quarter>
                    </template>
                    <template v-slot:cell(Q2)="data">
                      <forwardspends-quarter
                        quarter="Q2" :data="data"
                        :api_routes="api_routes">
                      </forwardspends-quarter>
                    </template>
                    <template v-slot:cell(Q3)="data">
                      <forwardspends-quarter
                        quarter="Q3" :data="data"
                        :api_routes="api_routes">
                      </forwardspends-quarter>
                    </template>
                    <template v-slot:cell(Q4)="data">
                      <forwardspends-quarter
                        quarter="Q4" :data="data"
                        :api_routes="api_routes">
                      </forwardspends-quarter>
                    </template>
                    <!--
                    <template v-slot:cell(total)="data">
                      <forwardspends-total :data="data"></forwardspends-total>
                    </template>
                    -->
                  </b-table>
                </div>
              </div>
            </b-card-text>
          </b-card-body>
        </b-collapse>
      </b-card>
    </div>
    <b-modal
      id="adjust-currency"
      title="Currency conversion settings"
      v-if="financesDetail">
      <form class="form-horizontal">
        <b-form-group
          label="Currency"
          label-cols-sm="4"
          for="currency">
          <finances-select
            :transaction="financesDetail"
            name="currency"
            :options="codelists.currency"
            :value.sync="financesDetail.item.currency">
          </finances-select>
        </b-form-group>
        <b-form-group
          label="Set conversion rate"
          label-cols-sm="4"
          for="currency_automatic">
          <finances-radio-group
            :transaction="financesDetail"
            :finances="financesDetail.item.id"
            :value.sync="financesDetail.item.currency_automatic"
            :options="currencyAutomaticOptions"
            name="currency_automatic"
          ></finances-radio-group>
        </b-form-group>
        <b-form-group
          label="Source"
          label-cols-sm="4"
          for="currency_source">
          <finances-input
            :transaction="financesDetail"
            name="currency_source"
            type="text"
            placeholder="e.g. OECD"
            :value.sync="financesDetail.item.currency_source"
            :disabled="financesDetail.item.currency_automatic">
          </finances-input>
        </b-form-group>
        <b-form-group
          label="Rate to USD"
          label-cols-sm="4"
          for="currency_rate">
          <finances-input
            :transaction="financesDetail"
            name="currency_rate"
            type="text"
            placeholder="e.g. 1"
            :value.sync="financesDetail.item.currency_rate"
            :disabled="financesDetail.item.currency_automatic">
          </finances-input>
        </b-form-group>
        <b-form-group
          label="Value date"
          label-cols-sm="4"
          for="currency_value_date">
          <finances-input
            :transaction="financesDetail"
            name="currency_value_date"
            type="date"
            :disabled="financesDetail.item.currency_automatic"
            :value.sync="financesDetail.item.currency_value_date">
          </finances-input>
        </b-form-group>
      </form>
    </b-modal>
    <b-modal
      id="add-fund-source"
      title="Add Fund Source"
      v-if="codelists"
      @ok="handleAddFundSource"
      ok-title="Add new fund source">
      <b-alert :show="newFundSource.validationErrors" variant="danger">
        All fields are required.
      </b-alert>
      <b-form-group
        label="Code"
        label-cols-sm="4"
        for="code"
        description="The code for this fund source">
        <b-input
          name="code"
          v-model="newFundSource.code"
          placeholder="e.g. TF1045"
          required>
        </b-input>
      </b-form-group>
      <b-form-group
        label="Name"
        label-cols-sm="4"
        for="name"
        description="A human-readable name for this fund source (or just repeat the code)">
        <b-input
          name="name"
          v-model="newFundSource.name"
          placeholder="e.g. Fragile States Facility, or TF1045"
          required>
        </b-input>
      </b-form-group>
      <b-form-group
        label="Finance Type"
        label-cols-sm="4"
        for="finance_type"
        description="The type of finance of this fund source (grant or loan)">
        <b-select
          :options="codelists.FinanceType"
          value-field="id" text-field="name"
          v-model="newFundSource.finance_type"
          name="finance_type"
          required>
        </b-select>
      </b-form-group>
    </b-modal>
  </div>
</template>
<script>
import Vue from 'vue'
import FinancesSubsection from './finances-subsection.vue'
import FinancesSelect from './subcomponents/finances-select.vue'
import FinancesInput from './subcomponents/finances-input.vue'
import FinancesRadioGroup from './subcomponents/finances-radio-group.vue'
import ForwardspendsQuarter from './subcomponents/forwardspends-quarter.vue'
import ForwardspendsTotal from './subcomponents/forwardspends-total.vue'
export default {
  props: ["activity", "codelists", "api_routes"],
  components: {
    FinancesSubsection,
    FinancesSelect,
    FinancesInput,
    FinancesRadioGroup,
    ForwardspendsQuarter,
    ForwardspendsTotal
  },
  data() {
    return {
      finances: {
        'commitments': [],
        'allotments': [],
        'disbursements': []
      },
      financesDetail: {
        'index': null,
        'item': {
          'transaction_id': null,
          'currency': null,
          'currency_automatic': null,
          'currency_source': null,
          'currency_rate': null,
          'currency_value_date': null
        }
      },
      forwardspends: [],
      forwardspendFields: [],
      availableFields:
        {
          'transaction_date': {'key': 'transaction_date', 'label': 'Date'},
          'transaction_value_original': {'key': 'transaction_value_original', 'label': 'Value', 'tdClass': 'nowrap'},
          'transaction_value': {'key': 'transaction_value', 'label': 'Value (USD)', 'tdClass': 'number', 'thClass': 'number'},
          'transaction_description': {'key': 'transaction_description', 'label': 'Description'},
          'provider_org_id': {'key': 'provider_org_id', 'label': 'Funder'},
          'receiver_org_id': {'key': 'receiver_org_id', 'label': 'Implementer'},
          'aid_type': {'key': 'aid_type', 'label': 'Aid Type'},
          'finance_type': {'key': 'finance_type', 'label': 'Finance Type'},
          'mtef_sector': {'key': 'mtef_sector', 'label': 'MTEF Sector'},
          'fund_source_id': {'key': 'fund_source_id', 'label': 'Fund Source', 'tdClass': 'nowrap'},
          'delete': {'key': 'delete', 'label': ''}
      },
      transaction_types: {'C': 'commitments', 'D': 'disbursements', '99-A': 'allotments'},
      defaultFields: ['transaction_date', 'transaction_value_original', 'transaction_value',
      'transaction_description', 'delete'],
      optionalSelectedFields: [],
      currencyAutomaticOptions: [
        { text: 'Automatically (recommended)', value: true },
        { text: 'Manually', value: false }
      ],
      fundSources: [],
      newFundSource: {
        code: null,
        name: null,
        finance_type: null,
        validationErrors: null
      }
    }
  },
  mounted: function() {
    this.setupFinances()
    this.setupForwardSpends()
  },
  methods: {
    currencyDetailPopup(data) {
      this.financesDetail = data
      this.$bvModal.show('adjust-currency')
    },
    setupFinances: function() {
      this.$axios.get(this.api_routes.finances)
        .then(res => {
          this.finances.commitments = res.data.finances.commitments
          this.finances.allotments = res.data.finances.allotments
          this.finances.disbursements = res.data.finances.disbursements
          this.fundSources = res.data.fund_sources
          var availableFundSources = this.finances.disbursements.reduce((obj, item) => {
            if (!obj.includes(item.fund_source_id)) {
              obj.push(item.fund_source_id)
            }
            return obj
          }, [])
          if (availableFundSources.length >1) {
            this.defaultFields.push('fund_source_id')
          }
      });
    },
    setupForwardSpends: function() {
      this.$axios.get(this.api_routes.forwardspends)
      .then(response => {
          this.forwardspends = response.data.forwardspends
          this.forwardspendFields = [{
              'key': 'year', 'label': 'Year'
            }].concat(response.data.quarters.map(quarter => {
            return {
              'key': quarter.quarter_name,
              'label': `${quarter.quarter_name} (${quarter.quarter_months})`
            }
          })) /*
            For now, don't show total, as it's not yet
            updating each year.

            .concat([{
              'key': 'total', 'label': 'Total'
            }])
            */
      });
    },
    addFinances: function(transaction_type) {
      var last_transaction = this.finances[this.transaction_types[transaction_type]].slice(-1)[0]
      const currency = (last_transaction == undefined) ? "USD" : last_transaction.currency
      var transaction_date = this.last_quarter_transaction_date();
      var data = {
        "transaction_type": transaction_type,
        "transaction_date": transaction_date,
        "transaction_value": "0.00",
        "currency": currency,
        "action": "add"
      }
      if (last_transaction) {
        data["fund_source_id"] = last_transaction.fund_source_id
      }
      this.$axios.post(this.api_routes.finances, data)
        .then(response => {
          if (response.data == 'False'){
              alert("There was an error updating that financial data.");
          } else {
            data = response.data;
            this.finances[this.transaction_types[transaction_type]].push(data)
          }
        }
      );
    },
    deleteFinances(transaction_type, transaction) {
      this.$bvModal.msgBoxConfirm('Are you sure you want to delete this transaction? This action cannot be undone!', {
        title: 'Confirm delete',
        okVariant: 'danger',
        okTitle: 'Confirm delete',
        hideHeaderClose: false,
        centered: true
      })
        .then(value => {
          if (value) {
            var data = {
              "transaction_id": transaction.item.id,
              "action": "delete"
            }
            this.$axios.post(this.api_routes.finances, data)
            .then(returndata => {
              Vue.delete(this.finances[this.transaction_types[transaction_type]], transaction.index)
            });
          }
        })
        .catch(err => {
          alert("Sorry, there was an error, and that transaction couldn't be deleted.")
        })
    },
    updateFinances(_this, transaction, attr, value, oldValue) {
      var data = {
        'finances_id': transaction.item.id,
        'attr': attr,
        'value': value,
      }
      this.$axios.post(this.api_routes.finances_update, data)
      .then(response => {
        var data = response.data
        // Because there can be a delay in getting data back
        // from the API, we only want to update `finances` for
        // certain fields.
        // If it's automatic and date or currency changed
        // or if automatic is set to true
        var updateFields = ['transaction_date', 'currency']
        if (
            ((updateFields.includes(attr)) && (transaction.item.currency_automatic == true)) ||
            ((attr=='currency_automatic') && (value = true))
           ) {
          var finances_long_name = this.transaction_types[transaction.item.transaction_type]
          var copyData = this.finances[this.transaction_types[transaction.item.transaction_type]][transaction.index]
          copyData.currency_rate = data.currency_rate
          copyData.currency_source = data.currency_source
          copyData.currency_value_date = data.currency_value_date
          Vue.set(this.finances[finances_long_name], transaction.index, copyData)
        }
        _this.validation = true
      }).catch(error => {
        console.log(`Error trying to update attribute ${attr} with value ${value}, the error was: ${ error }`)
        _this.validation = false
      }
      )
    },
    last_quarter_transaction_date() {
      const months_quarters = {
        0: 1, 1: 1, 2: 1,
        3: 2, 4: 2, 5: 2,
        6: 3, 7: 3, 8: 3,
        9: 4, 10: 4, 11: 4
      }
      const quarters = {
        1: {date: '03-31', year: 0},
        2: {date: '06-30', year: 0},
        3: {date: '09-30', year: 0},
        4: {date: '12-31', year: -1}
      }
      const today = new Date
      const year = today.getFullYear()
      const month = today.getMonth()
      const quarter = months_quarters[month]
      const previous_quarter = quarters[quarter-1] || quarter[4]
      const correct_year = year + previous_quarter.year
      return `${correct_year}-${previous_quarter.date}`
    },
    addFundSource: function(transaction_type, finance_index) {
      this.$bvModal.show('add-fund-source')
      this.newFundSource.transaction_type = transaction_type
      this.newFundSource.finance_index = finance_index
    },
    handleAddFundSource(bvModalEvt) {
      bvModalEvt.preventDefault()
      if (this.newFundSource.code && this.newFundSource.name && this.newFundSource.finance_type) {
        this.newFundSource.validationErrors = false
        this.$axios.post(this.api_routes.codelists,
        {
          'method': 'add',
          'codelist': 'fund-source',
          'code': this.newFundSource.code,
          'name': this.newFundSource.name,
          'finance_type': this.newFundSource.finance_type
        })
        .then(response => {
          // Add to list of available fund sources
          this.fundSources.push({'id': response.data.id, 'name': this.newFundSource.name})
          // Change that row to use this new fund source
          var ft = this.finances[this.newFundSource.transaction_type][this.newFundSource.finance_index]
          ft.fund_source_id = response.data.id
          Vue.set(this.finances[this.newFundSource.transaction_type], this.newFundSource.finance_index, ft)
          this.$bvModal.hide('add-fund-source')
        })
        .catch(error => {
          alert(`There was an error adding that fund source. Please check this fund source doesn't already exist and try again.`)
          console.log('Error adding fund source', error)
        })
      } else {
        this.newFundSource.validationErrors = true
      }
    }
  },
  computed: {
    commitmentsOrAppropriations() {
      if (this.activity.domestic_external == 'domestic') {
        return 'Appropriations'
      } else {
        return 'Commitments'
      }
    },
    optionalSelectableFields() {
      return Object.values(this.availableFields).reduce((fields, field) => {
        if (!(this.defaultFields.includes(field.key))) {
          fields.push({'value': field.key, 'text': field.label})
        }
        return fields
      }, [])
    },
    financesFields() {
      // Displayed fields are determined by default fields
      // plus any that are optionally selected.
      // We do it this way so that they are displayed in the order
      // listed in this.availableFields.
      return Object.values(this.availableFields).reduce((fields, field) => {
        if (this.defaultFields.concat(this.optionalSelectedFields).includes(field.key)) {
          fields.push(field)
        }
        return fields
      }, [])
    }
  },
  provide: function () {
    return {
      addFinances: this.addFinances,
      updateFinances: this.updateFinances,
      deleteFinances: this.deleteFinances,
      finances: this.finances,
      currencyDetailPopup: this.currencyDetailPopup,
      addFundSource: this.addFundSource
    }
  }
}
</script>