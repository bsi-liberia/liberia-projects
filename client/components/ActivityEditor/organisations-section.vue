<template>
  <div id="organisations">
    <b-form-group
      :label="role.name"
      label-cols-sm="2"
      v-for="role in activity.organisations"
      v-bind:key="role.role">
      <finances-select
        :transaction="organisation"
        name="organisation_id"
        :options="codelists.organisation"
        :value.sync="organisation.id"
        v-for="organisation in role.entries" v-bind:key="organisation.id"></finances-select>
    </b-form-group>
  </div>
</template>
<script>
import FinancesSelect from './subcomponents/finances-select.vue'
export default {
  data() {
    return {
    }
  },
  components: {
    FinancesSelect,
  },
  props: ["activity", "codelists", "api_routes", "mode"],
  provide: function () {
    return {
      updateFinances: this.updateOrganisation
    }
  },
  methods: {
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