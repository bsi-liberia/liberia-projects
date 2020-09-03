<template>
  <div>
    <b-table :fields="fields" :items="counterpartFunding">
      <template v-slot:cell(amount)="data">
        <finances-input
          :transaction="data"
          type="number"
          name="required_value"
          placeholder="e.g. 1,000,000"
          :value.sync="data.item.required_value">
          </finances-input>
      </template>
      <template v-slot:cell(fy)="data">
        <finances-select
          :transaction="data"
          name="required_fy"
          :options="years"
          :value.sync="data.item.required_fy">
        </finances-select>
      </template>
      <template v-slot:cell(budgeted)="data">
        <finances-checkbox
          :transaction="data"
          name="budgeted"
          label="Budgeted"
          :value.sync="data.item.budgeted">
        </finances-checkbox>
      </template>
      <template v-slot:cell(allotted)="data">
        <finances-checkbox
          :transaction="data"
          name="allotted"
          label="Allotted"
          :value.sync="data.item.allotted">
        </finances-checkbox>
      </template>
      <template v-slot:cell(disbursed)="data">
        <finances-checkbox
          :transaction="data"
          name="disbursed"
          label="Disbursed"
          :value.sync="data.item.disbursed">
        </finances-checkbox>
      </template>
      <template v-slot:cell(delete)="data">
        <b-form-group>
          <b-button variant="link" class="text-danger"
            size="sm" @click="deleteCounterpartFunding(data)">
            <font-awesome-icon :icon="['fa', 'trash-alt']" />
          </b-button>
        </b-form-group>
      </template>
    </b-table>
    <b-btn variant="primary" @click="addCounterpartFunding">
      <font-awesome-icon :icon="['fa', 'plus']" />
      Add counterpart funding
    </b-btn>
  </div>
</template>
<script>
import FinancesSelect from './subcomponents/finances-select.vue'
import FinancesInput from './subcomponents/finances-input.vue'
import FinancesCheckbox from './subcomponents/finances-checkbox.vue'
export default {
  data() {
    return {
      fields: [
        {'key': 'amount', 'label': 'Amount'},
        {'key': 'fy', 'label': 'For FY'},
        {'key': 'budgeted', 'label': 'Budgeted'},
        {'key': 'allotted', 'label': 'Allotted'},
        {'key': 'disbursed', 'label': 'Disbursed'},
        {'key': 'delete', 'label': 'Delete'}
      ],
      years: [],
      counterpartFunding: []
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
  methods: {
    setupCounterpartFunding(data) {
      this.$axios.get(this.api_routes.counterpart_funding)
        .then(res => {
          this.counterpartFunding = res.data.counterpart_funding
          this.years = res.data.fiscal_years.map(fy => {
            return {'id': fy, 'name': `FY${fy}/${parseInt(fy)+1}`}
          })
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
    deleteCounterpartFunding(data) {
      this.$bvModal.msgBoxConfirm('Are you sure you want to delete this counterpart funding entry? This action cannot be undone!', {
        title: 'Confirm delete',
        okVariant: 'danger',
        okTitle: 'Confirm delete',
        hideHeaderClose: false,
        centered: true
      })
        .then(value => {
          if (value) {
            this.$axios.post(this.api_routes.counterpart_funding, {
              "id": data.item.id,
              "action": "delete"
            })
            .then(response => {
              this.$delete(this.counterpartFunding, data.index)
            })
          }
        })
        .catch(err => {
          alert("Sorry, there was an error, and that counterpart funding entry couldn't be deleted.")
        })
    },
    updateCounterpartFunding(_this, data, attr, value, oldValue) {
      var postdata = {
        id: data.item.id,
        attr: attr,
        value: value,
        action: 'update'
      }
      this.$axios.post(this.api_routes.counterpart_funding, postdata)
      .then(response => {
        _this.validation = true
        var _cf = this.counterpartFunding[data.index]
        _cf[attr] = value
        this.$set(this.counterpartFunding, data.index, _cf)
      })
      .catch(error => {
        _this.validation = false
      })
    }
  }
}
</script>