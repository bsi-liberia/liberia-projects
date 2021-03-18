<template>
  <div>
    <b-form-group
      :label="role.name"
      label-cols-sm="2"
      v-for="role in activity.organisations"
      v-bind:key="role.role">
      <b-input-group
       class="nowrap no-margin">
        <finances-select
          style="width: 100%;"
          :transaction="organisation"
          name="organisation_id"
          :options="codelists.organisation"
          :value.sync="organisation.id"
          v-for="organisation in role.entries"
          v-bind:key="`${role.role}-code`"></finances-select>
        <b-input-group-append>
          <b-btn size="sm" @click="addOrganisation(role.role)">
            <font-awesome-icon :icon="['fa', 'plus']" />
          </b-btn>
        </b-input-group-append>
      </b-input-group>
    </b-form-group>
    <add-organisation-modal
      :activity.sync="activity"
      :codelists.sync="codelists"
      :role="addOrganisationRole" />
  </div>
</template>
<style scoped>
div.input-group.nowrap {
  flex-wrap: nowrap;
  width: 100%;
}
.no-margin .form-group {
  margin-bottom: 0px;
}
.number {
  text-align: right;
}
</style>
<script>
import AddOrganisationModal from './subcomponents/add-organisation-modal.vue'
import FinancesSelect from './subcomponents/finances-select.vue'
export default {
  data() {
    return {
      addOrganisationRole: null
    }
  },
  components: {
    FinancesSelect,
    AddOrganisationModal
  },
  props: ["activity", "codelists", "api_routes", "mode"],
  provide: function () {
    return {
      updateFinances: this.updateOrganisation
    }
  },
  methods: {
    addOrganisation(role, index) {
      this.addOrganisationRole = role
      this.$bvModal.show('add-organisation')
    },
    updateOrganisation(_this, data, attr, value, oldValue) {
      if (this.mode=="edit") {
        var postdata = {
          type: "organisation",
          activityorganisation_id: data.activityorganisation_id,
          attr: attr,
          value: value
        }
        this.$axios.post(this.api_routes.activity_update, postdata)
        .then(response => {
          _this.validation = true
        })
        .catch(error => {
          _this.validation = false
        })
      }
    }
  }
}
</script>