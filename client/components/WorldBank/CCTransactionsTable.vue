<template>
  <div>
    <b-card title="Transactions ready to process" class="mt-2">
      <b-card-text>
        <b-btn variant="success" class="mb-2" @click="changeStep(2)">Process transactions &raquo;</b-btn>
        <b-table
          :busy="isBusy"
          :items="transactions"
          :fields="transactionsFields"
          sortable
          >
          <template v-slot:table-busy>
            <div class="text-center my-2">
              <b-spinner class="align-middle" label="Loading..."></b-spinner>
              <strong>Loading...</strong>
            </div>
          </template>
        </b-table>
      </b-card-text>
    </b-card>
  </div>
</template>
<script>
export default {
  props: ['isBusy', 'transactions', 'change-step'],
  data() {
    return {
      transactionsFields: [
        {
          key: 'project_code',
          sortable: true
        },
        {
          key: 'project_title',
          sortable: true
        },
        {
          key: 'loan_number',
          sortable: true
        },
        {
          key: 'grant_loan',
          sortable: true
        },
        {
          key: 'transaction_date',
          sortable: true
        },
        {
          key: 'value',
          sortable: true
        }]
    }
  },
  methods: {
  },
  mounted() {
  }
}
</script>
