<template>
  <div>
    <b-card title="Merge activities" class="mt-2">
      <b-card-text>
        <b-btn variant="warning" class="mb-2" @click="changeStep(2)">&laquo; Go back</b-btn>
      </b-card-text>
      <b-form-group label="Client Connection Project">
        <b-select
          :options="ccProjectOptions"
          v-model="ccProjectCode" class="mb-2">
        </b-select>
      </b-form-group>
      <template v-if="this.selectedActivitiesForProject.length == 0">
        <b-alert variant="secondary" show>There are no Dashboard projects matched to this Client Connection project.</b-alert>
      </template>
      <template v-if="this.selectedActivitiesFields.length > 1">
        <SelectMergeActivities
          :selected-activities-fields="selectedActivitiesFields"
          :selected-activities-fields-options="selectedActivitiesFieldsOptions"
        />
      </template>
      <template v-if="this.selectedActivitiesForProject.length > 0">
        <b-btn variant="success" @click="importCCData">Import</b-btn>
      </template>
    </b-card>
  </div>
</template>
<script>

import SelectMergeActivities from '~/components/ActivityEditor/MergeActivities/SelectMergeActivities.vue'
export default {
  data() {
    return {
      ccProjectCode: 'P113266',
      selectedActivitiesFieldsOptions: {},
      selectedActivitiesFields: []
    }
  },
  components: {
    SelectMergeActivities
  },
  props: ['matches', 'change-step', 'cc-projects'],
  computed: {
    ccProjectOptions() {
      return this.ccProjects.reduce((summary, project) => {
        summary.push({
          'value': project.project_code,
          'text': `${project.project_code}: ${project.project_title}`
        })
        return summary
      },
      [{ 'value': null, 'text': 'No match' }]
      )
    },
    selectedActivities() {
      return this.matches.reduce((summary, item) => {
          if (item.client_connection_project_code == null) { return summary}
          if (!(item.client_connection_project_code in summary)) {
            summary[item.client_connection_project_code] = []
          }
          summary[item.client_connection_project_code].push(item.id)
          return summary
        }, {})
    },
    selectedActivitiesForProject() {
      const activities = this.selectedActivities[this.ccProjectCode]
      if (activities != undefined) { return activities }
      return []
    }
  },
  methods: {
    async selectMerge2() {
      const data = {
        activity_ids: this.selectedActivities[this.ccProjectCode]
      }
      const url = '/activities/activity_summaries.json'
      if (this.selectedActivitiesForProject.length == 0) {
        this.selectedActivitiesFieldsOptions = {}
        this.selectedActivitiesFields = []
        return false
      }
      await this.$axios.post(url, data)
      .then(response => {
        this.selectedActivitiesFieldsOptions = Object.keys(response.data.fields).reduce((summary, item) => {
          summary[item] = this.selectedActivitiesForProject[0]
          return summary
        }, {})
        this.selectedActivitiesFields = Object.entries(response.data.fields).map(item=> {
          return {'field': item[0], 'alternatives': item[1]}
        })
      })
    },
    async importCCData() {
      const data = {
        ccProjectCode: this.ccProjectCode,
        selectedActivitiesFieldsOptions: this.selectedActivitiesFieldsOptions,
        selectedActivities: this.selectedActivities[this.ccProjectCode]
      }
      const url = '/client-connection/import/'
      await this.$axios.post(url, data)
      .then(response => {
        this.$root.$bvToast.toast('Imported!', {
          title: 'Data imported',
          autoHideDelay: 7000,
          variant: 'success',
          solid: true
        })
      })
    }
  },
  mounted() {
    this.selectMerge2()
  },
  watch: {
    ccProjectCode() {
      this.selectMerge2()
    }
  }
}
</script>