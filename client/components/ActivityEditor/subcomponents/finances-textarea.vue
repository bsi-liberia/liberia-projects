<template>
  <b-form-group :state="validation"
    :label="label"
    :label-cols-sm="labelColsSm"
    :label-for="name">
    <b-textarea :name="name" :placeholder="placeholder"
    v-model="_value" :rows="rows" :disabled="disabled"
    v-on:change="update" :state="validation">
    </b-textarea>
  </b-form-group>
</template>
<script>
export default {
  data() {
    return { validation: null }
  },
  props: ["transaction", "name", "placeholder", "value", "rows", "disabled", "label", "label-cols-sm"],
  inject: ['updateFinances'],
  methods: {
    update(newValue, oldValue) {
      this.updateFinances(this, this.transaction, this.name, newValue, oldValue)
      this.$emit('update:value', newValue)
    },
  },
  computed: {
    _value: {
     // getter
      get: function () {
        return this.value
      },
      // setter
      set: function (newValue) {
        return
      }
    }
  }
}
</script>