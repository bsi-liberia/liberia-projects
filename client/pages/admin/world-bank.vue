<template>
  <div>
    <h1>World Bank Data Management</h1>
    <template v-if="step==1">
      <WorldBankUploadCCData :loadTransactions="loadTransactions" />
      <WorldBankCCTransactionsTable
        :transactions="transactions"
        :isBusy="isBusy"
        :changeStep="changeStep"
      />
    </template>
    <template v-if="step==2">
      <WorldBankMatchActivities
        :changeStep="changeStep"
        :changeMatches="changeMatches"
        :ccProjects.sync="ccProjects" />
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
  data() {
    return {
      isBusy: true,
      transactions: [],
      step: 1,
      matches: [],
      ccProjects: []
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
