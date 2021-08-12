<template>
  <div>
    <h1>Manage Fiscal Years</h1>
    <b-alert :show="invalid.length>0" variant="danger" dismissible>
      Your fiscal year entries below are invalid.
      <ul>
        <li v-if="invalid.includes('overlapping')">
          They must not be overlapping.
        </li>
        <li v-if="invalid.includes('gaps')">
          There must be no gaps between them.
        </li>
        <li v-if="invalid.includes('calendarQuarters')">
          Fiscal years must start and end at the start/end of calendar quarters.
        </li>
      </ul>
    </b-alert>
    <b-table :items="fiscalYearItems" :fields="fiscalYearFields" :busy="isBusy">

      <template #table-busy>
        <div class="text-center text-muted my-2">
          <b-spinner class="align-middle"></b-spinner>
          <strong>Loading...</strong>
        </div>
      </template>
      <template #cell(from)="data">
        <finances-input
          :disabled="data.index == 0"
          :transaction="data"
          type="date"
          name="from"
          :placeholder="data.item.from ? 'yyyy-mm-dd' : ''"
          :value.sync="data.item.from">
        </finances-input>
      </template>
      <template #cell(to)="data">
        <finances-input
          :disabled="data.index == fiscalYearItems.length-1"
          :transaction="data"
          type="date"
          name="to"
          :placeholder="data.item.to != null ? 'yyyy-mm-dd' : ''"
          :value.sync="data.item.to">
        </finances-input>
      </template>
      <template #cell(fyStart)="data">
        <b-input
          plaintext
          :value="fyStartOptions[data.item.from.slice(5,10)]">
        </b-input>
      </template>
      <template #cell(fyEnd)="data">
        <b-input
          plaintext
          :value="fyEndOptions[data.item.to.slice(5,10)]">
        </b-input>
      </template>
      <template #cell(delete)="data">
        <b-btn variant="danger" size="sm"
          v-if="data.index < fiscalYearItems.length-1"
          @click="confirmDeleteBreak(data.index)"
        >
          <font-awesome-icon :icon="['fa', 'trash-alt']" />
        </b-btn>
      </template>
    </b-table>
    <template v-if="isBusy==false">
      <b-btn variant="success" @click="addBreak">Add break to fiscal years</b-btn>
      <hr />
      <b-btn variant="primary" @click="submitFiscalYears">Update fiscal years</b-btn>
    </template>
  </div>
</template>
<script>
import FinancesInput from '~/components/ActivityEditor/subcomponents/finances-input.vue'
import FinancesSelect from '~/components/ActivityEditor/subcomponents/finances-select.vue'
export default {
  data() {
    return {
      isBusy: true,
      invalid: [],
      fiscalYearItems: [],
      fiscalYearFields: [
        { key: 'from' },
        { key: 'to' },
        { key: 'fyStart', label: 'FY Start' },
        { key: 'fyEnd', label: 'FY End' },
        { key: 'delete', label: 'Delete' },
      ],
      fyStartOptions: {
        '01-01': '1st January',
        '04-01': '1st April',
        '07-01': '1st July',
        '10-01': '1st October'
      },
      fyEndOptions: {
        '03-31': '31st March',
        '06-30': '30th June',
        '09-30': '30th September',
        '12-31': '31st December'
      },
      earliestDate: null,
      latestDate: null
    }
  },
  components: {
    FinancesInput,
    FinancesSelect
  },
  head() {
    return {
      title: `Fiscal Years | ${this.$config.title}`
    }
  },
  middleware: 'auth',
  mounted: function() {
    this.getFiscalYears()
  },
  computed: {
    fyStartValues() {
      return Object.keys(this.fyStartOptions)
    },
    fyEndValues() {
      return Object.keys(this.fyEndOptions)
    }
  },
  methods: {
    getFiscalYears() {
      this.$axios.get(`admin/fiscal-year-choices/`)
      .then(response => {
        this.fiscalYearItems = response.data.fiscalYearChoices.map(item => {
          const start_date = new Date(item.start_date)
          const end_date = new Date(item.end_date)
          return {
            from: new Date(item.start_date).toISOString().slice(0,10),
            to: new Date(item.end_date).toISOString().slice(0,10),
          }
        })
        this.earliestDate = response.data.earliestDate
        this.latestDate = response.data.latestDate
        this.ensureStartAndEnd()
        this.isBusy = false
      })
    },
    updateFinances(value) {
      return
    },
    ensureStartAndEnd() {
      this.fiscalYearItems[0].from = this.earliestDate
      this.fiscalYearItems[this.fiscalYearItems.length-1].to = this.latestDate
    },
    addBreak() {
      const today = new Date().toISOString().slice(0,10)
      const lastItemIndex = this.fiscalYearItems.length-1
      this.$set(this.fiscalYearItems, lastItemIndex,
        {
          from: this.fiscalYearItems[lastItemIndex].from,
          to: today
        }
      )
      this.fiscalYearItems.push({
        from: today,
        to: this.latestDate
      })
      this.ensureStartAndEnd()
    },
    validateFiscalYears() {
      // Sort fiscal years by end date
      // Check they are contiguous and not overlapping
      this.invalid = []
      const sortedItems = [...this.fiscalYearItems].sort((a,b) => {
        return new Date(a.to) - new Date(b.to)
      })
      const makeDate = (date) => {
        return new Date(date)
      }
      const validated = sortedItems.reduce((summary, item, index) => {
        if (index == 0) { return summary }
        const previous = {
          from: makeDate(sortedItems[index-1].from),
          to: makeDate(sortedItems[index-1].to)
        }
        const current = {
          from: makeDate(item.from),
          to: makeDate(item.to)
        }
        // Check that previous from is not after current from
        if (makeDate(sortedItems[index-1].from) > makeDate(item.from)) {
          this.invalid.push('overlapping')
          summary = false
        }
        // Check that previous to is not after current to
        if (makeDate(sortedItems[index-1].to) > makeDate(item.to)) {
          this.invalid.push('overlapping')
          summary = false
        }
        // Check that previous to is one day before current from
        previous.to.setDate(previous.to.getDate()+1)
        if (previous.to.toISOString() != current.from.toISOString()) {
          this.invalid.push('gaps')
          summary = false
        }
        if (!(this.fyStartValues.includes(current.from.toISOString().substr(5,5)))) {
          this.invalid.push('calendarQuarters')
        }
        if (!(this.fyEndValues.includes(current.to.toISOString().substr(5,5)))) {
          this.invalid.push('calendarQuarters')
        }
        return summary
      }, true)
      return validated
    },
    confirmDeleteBreak(index) {
      this.$bvModal.msgBoxConfirm('Are you sure you want to delete this break in fiscal years?', {
        title: 'Confirm',
        okVariant: 'danger',
        okTitle: 'Confirm',
        hideHeaderClose: false,
        centered: true
      })
      .then(value => {
        if (value) {
          this.$delete(this.fiscalYearItems, index)
          this.ensureStartAndEnd()
        }
      })
    },
    submitFiscalYears() {
      if (this.validateFiscalYears()) {
        this.doSubmitFiscalYears()
      }
    },
    doSubmitFiscalYears() {
      this.$bvModal.msgBoxConfirm('Are you sure you want to update fiscal years? This process may take a moment.', {
        title: 'Confirm',
        okVariant: 'danger',
        okTitle: 'Confirm',
        hideHeaderClose: false,
        centered: true
      })
      .then(value => {
        if (value) {
          this.$axios.post(`admin/fiscal-year-choices/`,
            this.fiscalYearItems)
          .then(response => {
            this.$bvToast.toast('Your fiscal years were successfully updated.', {
              title: 'Updated',
              autoHideDelay: 5000,
              variant: 'success',
              solid: true,
              appendToast: true
            })
          })
          .catch(error => {
            this.$bvToast.toast('Sorry, there was an error, and your fiscal years could not be updated.', {
              title: 'Error',
              autoHideDelay: 5000,
              variant: 'danger',
              solid: true,
              appendToast: true
            })
          })
        }
      })
    }
  },
  provide: function () {
    return {
      updateFinances: this.updateFinances
    }
  }
}
</script>
