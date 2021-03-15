<template>
  <b-form-radio-group
    :transaction="transaction"
    v-model="_value"
    :options="options"
    :name="name"
    :disabled="disabled"
  ></b-form-radio-group>
</template>
<script>
export default {
  data() {
    return { validation: null }
  },
  props: ["transaction", "name", "options", "value", "disabled"],
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