<template>
  <b-table
    :fields="fields"
    :items="milestones">
    <template v-slot:cell(name)="data">
      <b>{{ data.item.name }}</b>
    </template>
    <template v-slot:cell(achieved)="data">
      <finances-checkbox
        :transaction="data"
        name="achieved"
        :value="data.item.achieved.status"
        label="Achieved">
      </finances-checkbox>
    </template>
    <template v-slot:cell(notes)="data">
      <finances-textarea
        :transaction="data"
        name="notes"
        :value="data.item.notes"
        :rows="1">
        </finances-textarea>
    </template>
  </b-table>
</template>
<script>
import FinancesTextarea from './subcomponents/finances-textarea.vue'
import FinancesCheckbox from './subcomponents/finances-checkbox.vue'
export default {
  data() {
    return {
      fields: ['name', 'achieved', 'notes', "api_routes"],
      milestones: []
    }
  },
  components: {
    FinancesTextarea,
    FinancesCheckbox
  },
  mounted: function() {
    this.setupMilestones()
  },
  provide: function () {
    return {
      updateFinances: this.updateMilestones
    }
  },
  methods: {
    setupMilestones() {
      this.$axios.get(this.api_routes.milestones)
      .then(response => {
        this.milestones = response.data.milestones
      })
    },
    updateMilestones(_this, data, attr, value, oldValue) {
      var postdata = {
        milestone_id: data.item.id,
        attr: attr,
        value: value,
        action: 'update'
      }
      this.$axios.post(this.api_routes.milestones, postdata)
      .then(response => {
        _this.validation = true
      })
      .catch(error => {
        _this.validation = false
      })
    }
  }
}
</script>