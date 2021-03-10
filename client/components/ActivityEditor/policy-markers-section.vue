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
  computed: {
    significance() {
      if (this.codelists.PolicySignificance == undefined) { return [] }
      return this.codelists.PolicySignificance.map(item=> {
        if (item.id == "") { item.id = null }
        return item
      })
    }
  },
  methods: {
    descriptionText(significance) {
      if (this.significance.length == 0) { return "" }
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
