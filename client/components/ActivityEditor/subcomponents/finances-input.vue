<template>
  <b-form-group :state="validation"
    :label="label"
    :label-cols-sm="labelColsSm"
    :label-for="name">
    <template v-if="currency!=null">
      <b-input-group>
        <b-input :type="type" step=".01"
        :name="name" :placeholder="placeholder"
        v-model="_value" size="30" :disabled="disabled"
        v-on:change="update" :state="validation"
        :min="minDate" :max="maxDate">
        </b-input>
        <b-input-group-append is-text>
          {{ currency }}
        </b-input-group-append>
      </b-input-group>
    </template>
    <template v-else>
      <b-input :type="type" step=".01"
      :name="name" :placeholder="placeholder"
      v-model="_value" size="30" :disabled="disabled"
      v-on:change="update" :state="validation"
      :min="minDate" :max="maxDate">
      </b-input>
    </template>
  </b-form-group>
</template>
<script>
export default {
  data() {
    return { validation: null }
  },
  props: ["transaction", "type", "name", "placeholder", "value",
    "disabled", "label", "label-cols-sm", "currency"],
  inject: ['updateFinances'],
  methods: {
    update(newValue, oldValue) {
      if (this.type=='date') {
        if ((newValue > this.maxDate) || (newValue < this.minDate)) {
          this.validation = false
          return false
        } else {
          this.validation = null
        }
      }
      this.updateFinances(this, this.transaction, this.name, newValue, oldValue)
      this.$emit('update:value', newValue)
    },
  },
  computed: {
    minDate() {
      if (this.type=='date') {
        return "1990-01-01"
      }
    },
    maxDate() {
      if (this.type=='date') {
        return "2099-12-31"
      }
    },
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