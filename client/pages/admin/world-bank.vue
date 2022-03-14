<template>
  <div>
    <h1>World Bank Data Management</h1>
    <template v-if="step==1">
      <WorldBankUploadCCData :loadTransactions="loadTransactions" />
      <WorldBankCCTransactionsTable
        :transactions="transactions"
        :is-busy="isBusy"
        :change-step="changeStep"
        :import-all="importAll"
        :messages="messages"
      />
    </template>
    <template v-if="step==2">
      <WorldBankMatchActivities
        :change-step="changeStep"
        :change-matches="changeMatches"
        :cc-projects.sync="ccProjects" />
    </template>
    <template v-if="step==3">
      <WorldBankMergeActivities
        :change-step="changeStep"
        :matches="matches"
        :cc-projects="ccProjects" />
    </template>
  </div>
</template>
<script>
import WorldBankUploadCCData from '~/components/WorldBank/UploadCCData.vue'
import WorldBankCCTransactionsTable from '~/components/WorldBank/CCTransactionsTable.vue'
import WorldBankMatchActivities from '~/components/WorldBank/MatchActivities.vue'
import WorldBankMergeActivities from '~/components/WorldBank/MergeActivities.vue'
export default {
  head() {
    return {
      title: `Import World Bank data | ${this.$config.title}`
    }
  },
  data() {
    return {
      isBusy: true,
      transactions: [],
      step: 1,
      matches: [],
      ccProjects: [],
      messages: []
    }
  },
  components: {
    WorldBankUploadCCData,
    WorldBankCCTransactionsTable,
    WorldBankMatchActivities,
    WorldBankMergeActivities
  },
  methods: {
    async loadTransactions() {
      const url = '/client-connection/transactions/'
      await this.$axios.get(url)
        .then(response => {
          this.transactions = response.data.transactions
          this.isBusy = false
        })
    },
    async importAll() {
      const url = '/client-connection/import-all/'
      await this.$axios.get(url)
        .then(response => {
          this.messages = response.data.status
        })
    },
    changeStep(step) {
      this.step = step
    },
    changeMatches(matches) {
      this.matches = matches
    }
  },
  mounted() {
    this.loadTransactions()
  }
}
</script>
