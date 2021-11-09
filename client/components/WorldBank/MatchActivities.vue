<template>
  <div>
    <b-card title="Activities to match" class="mt-2">
      <b-card-text>
        <b-btn variant="warning" class="mb-2" @click="changeStep(1)">&laquo; Go back</b-btn>
        <b-btn variant="success" class="mb-2" @click="nextStep()">Continue &raquo;</b-btn>
        <b-table
          :busy="isBusy"
          :items="matches"
          :fields="fields"
          sortable
          >
          <template v-slot:table-busy>
            <div class="text-center my-2">
              <b-spinner class="align-middle" label="Loading..."></b-spinner>
              <strong>Loading...</strong>
            </div>
          </template>
          <template v-slot:cell(match)="data">
            <b-select
              :options="ccProjectOptions"
              v-model="data.item.client_connection_project_code"></b-select>
          </template>
        </b-table>
      </b-card-text>
    </b-card>
  </div>
</template>
<script>
export default {
  props: ['change-step', 'change-matches', 'cc-projects'],
  data() {
    return {
      isBusy: true,
      matches: [],
      dbActivities: [],
      step: 1,
      fields: [
        {
          key: 'id',
          label: 'ID',
          sortable: true,
          style: 'width: 10%;'
        },
        {
          key: 'iati_identifier',
          label: 'IATI Identifier',
          sortable: true,
          style: 'width: 10%;'
        },
        {
          key: 'title',
          label: 'Title',
          sortable: true,
          thStyle: 'width: 40%;'
        },
        {
          key: 'match',
          label: 'Match',
          sortable: true,
          thStyle: 'width: 40%;'
        }
      ]
    }
  },
  computed: {
    clientConnectionProjects: {
      get() {
        return this.ccProjects
      },
      set(newValue) {
        this.$emit('update:ccProjects', newValue)
      }
    },
    ccProjectOptions() {
      return this.clientConnectionProjects.reduce((summary, project) => {
        summary.push({
          'value': project.project_code,
          'text': `${project.project_code}: ${project.project_title}`
        })
        return summary
      },
      [{ 'value': null, 'text': 'No match' }]
      )
    }
  },
  methods: {
    nextStep() {
      this.changeMatches(this.matches)
      this.changeStep(3)
    },
    async loadData() {
      const url = '/client-connection/similar/'
      await this.$axios.get(url)
        .then(response => {
          this.matches = Object.values(response.data.matches)
          this.clientConnectionProjects = response.data.clientConnectionProjects
          this.dbActivities = response.data.dbActivities
          this.isBusy = false
        })
    },
  },
  mounted() {
    this.loadData()
  }
}
</script>
