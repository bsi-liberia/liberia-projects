<template>
  <b-form-group :state="validation" v-if="data.item[quarter]">
    <b-input
      type="number"
      step="0.01"
      :value="_value"
      @change="updateForwardSpends"
      :disabled="disabled"
      :state="validation"></b-input>
  </b-form-group>
  <b-form-group v-else>
    <b-input disabled></b-input>
  </b-form-group>
</template>
<script>
export default {
  data() {
    return { validation: null }
  },
  props: ["quarter", "data", "api_routes", "disabled"],
  methods: {
    updateForwardSpends: function(newValue) {
      var _id = this.data.item[this.quarter].id
      var _value = newValue
      this.$axios.post(this.api_routes.forwardspends, {
        'id': _id,
        'value': _value
      })
      .then(response => {
        this.validation = true
      })
      .catch(error => {
        this.validation = false
      })
    },
  },
  computed: {
    _value: {
     // getter
      get: function () {
        return this.data.item[this.quarter].value
      },
      // setter
      set: function (newValue) {
        return
      }
    }
  }
}
</script>