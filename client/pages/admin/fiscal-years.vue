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
      <template #cell(start_date)="data">
        <finances-input
          :disabled="data.index == 0"
          :transaction="data"
          type="date"
          name="start_date"
          :placeholder="data.item.start_date ? 'yyyy-mm-dd' : ''"
          :value.sync="data.item.start_date">
        </finances-input>
      </template>
      <template #cell(end_date)="data">
        <finances-input
          :disabled="data.index == fiscalYearItems.length-1"
          :transaction="data"
          type="date"
          name="end_date"
          :placeholder="data.item.end_date != null ? 'yyyy-mm-dd' : ''"
          :value.sync="data.item.end_date">
        </finances-input>
      </template>
      <template #cell(fyStart)="data">
        <b-input
          plaintext
          :value="fyStartOptions[data.item.start_date.slice(5,10)]">
        </b-input>
      </template>
      <template #cell(fyEnd)="data">
        <b-input
          plaintext
          :value="fyEndOptions[data.item.end_date.slice(5,10)]">
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
        { key: 'start_date' },
        { key: 'end_date' },
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
            start_date: new Date(item.start_date).toISOString().slice(0,10),
            end_date: new Date(item.end_date).toISOString().slice(0,10),
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
      this.fiscalYearItems[0].start_date = this.earliestDate
      this.fiscalYearItems[this.fiscalYearItems.length-1].end_date = this.latestDate
    },
    addBreak() {
      const today = new Date().toISOString().slice(0,10)
      const lastItemIndex = this.fiscalYearItems.length-1
      this.$set(this.fiscalYearItems, lastItemIndex,
        {
          start_date: this.fiscalYearItems[lastItemIndex].start_date,
          end_date: today
        }
      )
      this.fiscalYearItems.push({
        start_date: today,
        end_date: this.latestDate
      })
      this.ensureStartAndEnd()
    },
    validateFiscalYears() {
      // Sort fiscal years by end date
      // Check they are contiguous and not overlapping
      this.invalid = []
      const sortedItems = [...this.fiscalYearItems].sort((a,b) => {
        return new Date(a.end_date) - new Date(b.end_date)
      })
      const makeDate = (date) => {
        return new Date(date)
      }
      const validated = sortedItems.reduce((summary, item, index) => {
        if (index == 0) { return summary }
        const previous = {
          start_date: makeDate(sortedItems[index-1].start_date),
          end_date: makeDate(sortedItems[index-1].end_date)
        }
        const current = {
          start_date: makeDate(item.start_date),
          end_date: makeDate(item.end_date)
        }
        // Check that previous from is not after current from
        if (makeDate(sortedItems[index-1].start_date) > makeDate(item.start_date)) {
          this.invalid.push('overlapping')
          summary = false
        }
        // Check that previous to is not after current to
        if (makeDate(sortedItems[index-1].end_date) > makeDate(item.end_date)) {
          this.invalid.push('overlapping')
          summary = false
        }
        // Check that previous to is one day before current from
        previous.end_date.setDate(previous.end_date.getDate()+1)
        if (previous.end_date.toISOString() != current.start_date.toISOString()) {
          this.invalid.push('gaps')
          summary = false
        }
        if (!(this.fyStartValues.includes(current.start_date.toISOString().substr(5,5)))) {
          this.invalid.push('calendarQuarters')
        }
        if (!(this.fyEndValues.includes(current.end_date.toISOString().substr(5,5)))) {
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
