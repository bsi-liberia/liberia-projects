<template>
  <b-form-group :state="validation">
    <b-form-checkbox :state="validation"
      v-model="_value">{{ label }}</b-form-checkbox>
  </b-form-group>
</template>
<script>
export default {
  data() {
    return { validation: null }
  },
  props: ["transaction", "name", "label", "value"],
  inject: ['updateFinances'],
  computed: {
    _value: {
     // getter
      get: function () {
        return this.value
      },
      // setter
      set: function (newValue) {
        this.updateFinances(this, this.transaction, this.name, newValue, null)
        this.$emit('update:value', newValue)
      }
    }
  }
}
</script>