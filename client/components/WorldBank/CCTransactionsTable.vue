<template>
  <div>
    <b-card title="Transactions ready to process" class="mt-2">
      <b-card-text>
        <b-btn variant="success" class="mb-2" @click="changeStep(2)">Process transactions &raquo;</b-btn>
        <hr />
        <b-row>
          <b-col md="6">
            <b-form-group
              label="Filter"
              label-for="filter-input"
            >
              <b-input-group>
                <b-form-input
                  id="filter-input"
                  v-model="filter"
                  type="search"
                  placeholder="Type to Search"
                ></b-form-input>
              </b-input-group>
            </b-form-group>
          </b-col>
          <b-col md="6">
            <b-form-group
              label="Page"
              label-for="pagination"
            >
              <b-pagination
                v-model="currentPage"
                :total-rows="rows"
                :per-page="perPage"
                :limit="10"
                align="fill"
              ></b-pagination>
            </b-form-group>
          </b-col>
        </b-row>
        <b-row>
          <b-col>
            <b-table
              :busy="isBusy"
              :items="transactions"
              :per-page="perPage"
              :current-page="currentPage"
              :fields="transactionsFields"
              :filter="filter"
              sortable
              >
              <template v-slot:table-busy>
                <div class="text-center my-2">
                  <b-spinner class="align-middle" label="Loading..."></b-spinner>
                  <strong>Loading...</strong>
                </div>
              </template>
            </b-table>
          </b-col>
        </b-row>
      </b-card-text>
    </b-card>
  </div>
</template>
<script>
export default {
  props: ['isBusy', 'transactions', 'change-step'],
  data() {
    return {
      filter: null,
      perPage: 50,
      currentPage: 1,
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
  computed: {
    rows() {
      return this.transactions.length
    }
  },
  methods: {
  },
  mounted() {
  }
}
</script>
