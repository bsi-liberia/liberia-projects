<template>
  <div>
    <template v-if="labelColsSm">
      <b-form-group :state="validation"
        :label="label"
        :label-cols-sm="labelColsSm">
        <b-form-checkbox :state="validation"
          :disabled="disabled"
          v-model="_value" switch>{{ labels[_value] }}</b-form-checkbox>
      </b-form-group>
    </template>
    <template v-else>
      <b-form-group :state="validation">
        <b-form-checkbox :state="validation"
          :disabled="disabled"
          v-model="_value">{{ label }}</b-form-checkbox>
      </b-form-group>
    </template>
  </div>
</template>
<script>
export default {
  data() {
    return { validation: null }
  },
  props: ["transaction", "labels", "label-cols-sm", "name", "label", "value", "disabled"],
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
