<template>
  <div>
    <b-form-group
      :label="policy_marker.name"
      label-cols-sm="3"
      v-for="policy_marker in activity.policy_markers"
      v-bind:key="policy_marker.code"
      :description="descriptionText(policy_marker.significance)">
      <finances-select
        :transaction="policy_marker"
        name="significance"
        :options="significance"
        :value.sync="policy_marker.significance"></finances-select>
    </b-form-group>
  </div>
</template>
<script>
import FinancesSelect from './subcomponents/finances-select.vue'
export default {
  data() {
    return {
      significance: [
        {
          'id': null,
          'name': 'Unknown',
          'description': 'The activity has not been assessed as to whether it targets the policy objective.'
        },
        {
          'id': 0,
          'name': 'Not targeted',
          'description': 'The activity was examined but found not to target the policy objective.'
        },
        {
          'id': 1,
          'name': 'Significant objective',
          'description': 'Significant (secondary) policy objectives are those which, although important, were not the prime motivation for undertaking the activity.'
        },
        {
          'id': 2,
          'name': 'Principal objective',
          'description': 'Principal (primary) policy objectives are those which can be identified as being fundamental in the design and impact of the activity and which are an explicit objective of the activity. They may be selected by answering the question "Would the activity have been undertaken without this objective?"'
        }
      ]
    }
  },
  components: {
    FinancesSelect,
  },
  props: ["activity", "codelists", "api_routes", "mode"],
  provide: function () {
    return {
      updateFinances: this.updateSector
    }
  },
  methods: {
    descriptionText(significance) {
      return this.significance.filter(item => {
        return item.id == significance
      })[0].description
    },
    updateSector(_this, data, attr, value, oldValue) {
      if (this.mode=="edit") {
        var postdata = {
          type: "policy_marker",
          code: data.code,
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
