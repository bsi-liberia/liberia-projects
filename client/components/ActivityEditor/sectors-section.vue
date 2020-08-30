<template>
  <div>
    <b-form-group
      :label="classification.name"
      label-cols-sm="3"
      v-for="classification in activity.classifications"
      v-bind:key="classification.codelist">
      <finances-select
        :transaction="code"
        name="codelist_code_id"
        :options="codelists[classification.codelist]"
        :value.sync="code.code"
        v-for="code in classification.entries"
        v-bind:key="`${classification.codelist}-code`"></finances-select>
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
  methods: {
    updateSector(_this, data, attr, value, oldValue) {
      if (this.mode=="edit") {
        var postdata = {
          type: "classification",
          activitycodelist_id: data.activitycodelist_id,
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
