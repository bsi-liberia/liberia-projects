<template>
  <b-card no-body class="mb-1">
    <b-card-header header-tag="header" role="tab">
      <b v-b-toggle="'collapse-'+transactionType">{{ title }}</b>
    </b-card-header>
    <b-collapse :id="'collapse-'+transactionType" visible role="tabpanel">
      <b-card-body>
        <b-card-text>
          <div class="row">
            <div class="col-sm-12">
              <b-table
                :fields="financesFields"
                :items="finances[transactionTypeLong]">
                <template v-slot:cell(transaction_date)="data">
                  <finances-input
                    :transaction="data"
                    type="date"
                    name="transaction_date"
                    placeholder="yyyy-mm-dd"
                    :value.sync="data.item.transaction_date">
                  </finances-input>
                </template>
                <template v-slot:cell(transaction_value_original)="data">
                  <finances-input-currency-append
                    :transaction="data"
                    type="number"
                    name="transaction_value_original"
                    :value.sync="data.item.transaction_value_original"
                    :currency="data.item.currency"></finances-input-currency-append>
                </template>
                <template v-slot:cell(transaction_value)="data">
                  <b-form-group>
                    <b-input type="text" plaintext
                      name="transaction_value_original"
                      :value="(data.item.transaction_value_original * data.item.currency_rate).toLocaleString(undefined, {maximumFractionDigits:2, minimumFractionDigits: 2})"></b-input>
                  </b-form-group>
                </template>
                <template v-slot:cell(transaction_description)="data">
                  <finances-input
                    :transaction="data"
                    type="text"
                    name="transaction_description"
                    placeholder="optional"
                    :value.sync="data.item.transaction_description"
                    size="30">
                  </finances-input>
                </template>
                <template v-slot:cell(provider_org_id)="data">
                  <finances-select
                    :transaction="data"
                    name="provider_org_id"
                    :options="codelists.organisation"
                    :value.sync="data.item.provider_org_id">
                  </finances-select>
                </template>
                <template v-slot:cell(receiver_org_id)="data">
                  <finances-select
                    :transaction="data"
                    name="receiver_org_id"
                    :options="codelists.organisation"
                    :value.sync="data.item.receiver_org_id">
                  </finances-select>
                </template>
                <template v-slot:cell(aid_type)="data">
                  <finances-select
                    :transaction="data"
                    name="aid_type"
                    :options="codelists.AidType"
                    :value.sync="data.item.aid_type">
                  </finances-select>
                </template>
                <template v-slot:cell(finance_type)="data">
                  <finances-select
                    :transaction="data"
                    name="finance_type"
                    :options="codelists.FinanceType"
                    :value.sync="data.item.finance_type">
                  </finances-select>
                </template>
                <template v-slot:cell(mtef_sector)="data">
                  <finances-select
                    :transaction="data"
                    name="mtef_sector"
                    :options="codelists['mtef-sector']"
                    :value.sync="data.item.mtef_sector">
                  </finances-select>
                </template>
                <template v-slot:cell(fund_source_id)="data">
                  <b-input-group class="nowrap no-margin">
                    <finances-select
                      :transaction="data"
                      name="fund_source_id"
                      :options="fundSources"
                      :value.sync="data.item.fund_source_id">
                    </finances-select>
                    <b-input-group-append>
                      <b-btn size="sm" @click="addFundSource(transactionTypeLong, data.index)">
                        <font-awesome-icon :icon="['fa', 'plus']" />
                      </b-btn>
                    </b-input-group-append>
                  </b-input-group>
                </template>
                <template v-slot:cell(delete)="data">
                  <b-button variant="link" class="text-danger"
                    size="sm" @click="deleteFinances(transactionType, data)">
                    <font-awesome-icon :icon="['fa', 'trash-alt']" />
                  </b-button>
                </template>
              </b-table>
            </div>
          </div>
          <div class="row">
            <div class="col-sm-12 text-center">
              <b-btn variant="primary" @click="addFinances(transactionType)"
              class="addFinancial">
                <font-awesome-icon :icon="['fa', 'plus']" />
                {{ addLabel }}
              </b-btn>
            </div>
          </div>
        </b-card-text>
      </b-card-body>
    </b-collapse>
  </b-card>
</template>
<style scoped>
.nowrap div.input-group {
    flex-wrap: nowrap;
}
.no-margin .form-group {
  margin-bottom: 0px;
}
</style>
<script>
import FinancesSelect from './subcomponents/finances-select.vue'
import FinancesInput from './subcomponents/finances-input.vue'
import FinancesInputCurrencyAppend from './subcomponents/finances-input-currency-append.vue'
export default {
  data() {
    return { validation: null }
  },
  components: {
    FinancesSelect,
    FinancesInput,
    FinancesInputCurrencyAppend
  },
  props: ["transactionType", "transactionTypeLong", "title", "addLabel",
    "financesFields", "fundSources", "api_routes", "codelists"],
  inject: ['finances', 'addFinances',
    'updateFinances', 'deleteFinances',
    'currencyDetailPopup', 'addFundSource'],
  provide: function () {
    return {
      updateFinances: this.updateFinances,
      currencyDetailPopup: this.currencyDetailPopup,
      codelists: this.codelists
    }
  }
}
</script>