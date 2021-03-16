<template>
  <b-form-group :state="validation"
    :label="label"
    :label-cols-sm="labelColsSm"
    :label-for="name">
    <b-select :options="options" v-model="_value"
    :name="name" value-field="id" text-field="name"
    :state="validation" :required="required"
    :disabled="disabled">
    </b-select>
  </b-form-group>
</template>
<script>
export default {
  data() {
    return { validation: null }
  },
  props: ["transaction", "name", "options", "value", "label", "label-cols-sm", "required", "disabled"],
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